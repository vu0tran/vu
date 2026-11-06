/* JS plugins (ljs.vu): long-lived node processes running the plugin host. vlint writes a request (one
   line of JSON) to a process's fd 3 and reads the answer (one line) from its fd 4; the process's
   standard output and error are vlint's (as a plugin's console.log is oxlint's). Each linting thread
   uses its own process (up to VL_MAXW, shared beyond that, one request at a time); a process is
   started when first needed and is first sent the prelude (the plugin loads and the rules'
   options), so every process registers the same rules. Processes end when their fd 3 closes. */
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <errno.h>
#include <sys/wait.h>
#include <pthread.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
extern char **environ;
#define VL_MAXW 8
typedef struct { pid_t pid; int in, out; char *buf; size_t len, cap; pthread_mutex_t mu; } vl_worker;
static vl_worker vlw[VL_MAXW];
static pthread_mutex_t vl_mu = PTHREAD_MUTEX_INITIALIZER;
static char *vl_script = NULL;
static char **vl_args = NULL;     /* vlint's own arguments, passed on (plugins read process.argv) */
static int vl_nargs = 0;
static char *vl_prelude = NULL;   /* lines */
static size_t vl_prelude_len = 0;
static int vl_slots = 1, vl_next_slot = 0, vl_inited = 0;
static __thread int vl_slot = -1;

static void vl_stop(vl_worker *w) {
    if (w->pid < 0) return;
    close(w->in);
    close(w->out);
    int st;
    while (waitpid(w->pid, &st, 0) < 0 && errno == EINTR) {}
    w->pid = -1; w->in = w->out = -1;
}

static void vl_atexit(void) { for (int i = 0; i < VL_MAXW; i++) vl_stop(&vlw[i]); }

static void vl_init_once(void) {
    if (vl_inited) return;
    vl_inited = 1;
    for (int i = 0; i < VL_MAXW; i++) {
        vlw[i].pid = -1; vlw[i].in = vlw[i].out = -1; vlw[i].buf = NULL; vlw[i].len = vlw[i].cap = 0;
        pthread_mutex_init(&vlw[i].mu, NULL);
    }
    atexit(vl_atexit);
}

static bool vl_write(int fd, const char *p, size_t n) {
    sigset_t set, old;
    sigemptyset(&set);
    sigaddset(&set, SIGPIPE);
    pthread_sigmask(SIG_BLOCK, &set, &old);
    bool ok = true;
    while (n > 0) {
        ssize_t w = write(fd, p, n);
        if (w < 0 && errno == EINTR) continue;
        if (w <= 0) { ok = false; break; }
        p += w; n -= (size_t)w;
    }
    if (!ok) {
        struct timespec zero = { 0, 0 };
        sigset_t pend;
        sigpending(&pend);
        if (sigismember(&pend, SIGPIPE)) sigtimedwait(&set, NULL, &zero);
    }
    pthread_sigmask(SIG_SETMASK, &old, NULL);
    return ok;
}

/* reads one answer line into w->buf (without the newline): false when the process died */
static bool vl_recv(vl_worker *w) {
    w->len = 0;
    for (;;) {
        if (w->cap - w->len < 65536) { w->cap = w->cap ? w->cap * 2 : 131072; w->buf = realloc(w->buf, w->cap); }
        ssize_t r;
        do r = read(w->out, w->buf + w->len, w->cap - w->len); while (r < 0 && errno == EINTR);
        if (r <= 0) { vl_stop(w); return false; }
        size_t start = w->len;
        w->len += (size_t)r;
        char *nl = memchr(w->buf + start, '\n', (size_t)r);
        if (nl) { w->len = (size_t)(nl - w->buf); return true; }
    }
}

static bool vl_start(vl_worker *w) {
    int a[2], b[2];
    if (!vl_script) return false;
    if (pipe(a) != 0) return false;
    if (pipe(b) != 0) { close(a[0]); close(a[1]); return false; }
    int r3 = fcntl(a[0], F_DUPFD_CLOEXEC, 10), wp = fcntl(a[1], F_DUPFD_CLOEXEC, 10);
    int rp = fcntl(b[0], F_DUPFD_CLOEXEC, 10), w4 = fcntl(b[1], F_DUPFD_CLOEXEC, 10);
    close(a[0]); close(a[1]); close(b[0]); close(b[1]);
    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_addopen(&fa, 0, "/dev/null", O_RDONLY, 0);
    posix_spawn_file_actions_adddup2(&fa, r3, 3);
    posix_spawn_file_actions_adddup2(&fa, w4, 4);
    char **argv = calloc((size_t)vl_nargs + 4, sizeof *argv);
    argv[0] = "node"; argv[1] = "--no-warnings"; argv[2] = vl_script;
    for (int i = 0; i < vl_nargs; i++) argv[3 + i] = vl_args[i];
    pid_t pid;
    int rc = posix_spawnp(&pid, "node", &fa, NULL, argv, environ);
    free(argv);
    posix_spawn_file_actions_destroy(&fa);
    close(r3); close(w4);
    if (rc != 0) { close(wp); close(rp); return false; }
    w->pid = pid; w->in = wp; w->out = rp;
    /* the prelude: each line answered, the answers dropped */
    const char *p = vl_prelude, *e = vl_prelude ? vl_prelude + vl_prelude_len : NULL;
    while (p && p < e) {
        const char *nl = memchr(p, '\n', (size_t)(e - p));
        if (!nl) nl = e;
        if (nl > p) {
            if (!vl_write(w->in, p, (size_t)(nl - p)) || !vl_write(w->in, "\n", 1) || !vl_recv(w)) { vl_stop(w); return false; }
        }
        p = nl + 1;
    }
    return true;
}

/* The host script's path, vlint's arguments (one per line), and how many processes linting may use. */
void vl_node_setup(const vu_str *script, const vu_str *args, int64_t slots) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    free(vl_script);
    vl_script = vu_cstr(script);
    char *all = vu_cstr(args);
    vl_nargs = 0;
    if (all && *all) {
        int n = 1;
        for (char *p = all; *p; p++) if (*p == '\n') n++;
        vl_args = calloc((size_t)n, sizeof *vl_args);
        char *p = all;
        while (p) {
            char *nl = strchr(p, '\n');
            if (nl) *nl = 0;
            vl_args[vl_nargs++] = p;
            p = nl ? nl + 1 : NULL;
        }
    }
    vl_slots = slots < 1 ? 1 : slots > VL_MAXW ? VL_MAXW : (int)slots;
    pthread_mutex_unlock(&vl_mu);
}

/* What every new process is sent first (lines). */
void vl_node_prelude(const vu_str *lines) {
    pthread_mutex_lock(&vl_mu);
    free(vl_prelude);
    vl_prelude = malloc((size_t)lines->len + 1);
    memcpy(vl_prelude, lines->data, (size_t)lines->len);
    vl_prelude_len = (size_t)lines->len;
    pthread_mutex_unlock(&vl_mu);
}

/* The answer to a request from this thread's process, or "!" when node can't be started or died. */
vu_str vl_node_call(const vu_str *req) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    if (vl_slot < 0) vl_slot = (vl_next_slot++) % vl_slots;
    pthread_mutex_unlock(&vl_mu);
    vl_worker *w = &vlw[vl_slot];
    pthread_mutex_lock(&w->mu);
    vu_str res;
    if (w->pid < 0 && !vl_start(w)) { res = vu_str_from("!", 1); goto out; }
    if (!vl_write(w->in, req->data, (size_t)req->len) || !vl_write(w->in, "\n", 1)) { vl_stop(w); res = vu_str_from("!", 1); goto out; }
    if (!vl_recv(w)) { res = vu_str_from("!", 1); goto out; }
    res = vu_str_from(w->buf, (int64_t)w->len);
out:
    pthread_mutex_unlock(&w->mu);
    return res;
}

/* Ends the processes (they finish the work they have). */
void vl_node_stop(void) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    for (int i = 0; i < VL_MAXW; i++) { pthread_mutex_lock(&vlw[i].mu); vl_stop(&vlw[i]); pthread_mutex_unlock(&vlw[i].mu); }
    pthread_mutex_unlock(&vl_mu);
}

