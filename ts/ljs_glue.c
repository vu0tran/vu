/* JS plugins (ljs.vu): long-lived node processes running the plugin host. vlint writes a request (one
   line of JSON) to a process's fd 3 and reads the answer (one line) from its fd 4; the process's
   standard output and error are vlint's (as a plugin's console.log is oxlint's). The linting threads
   share the processes (one process for each two cores by default, see vl_node_setup): a thread
   writes its request without waiting for the others' answers, so the next file is already there
   when the process finishes one, and reads its answer when its turn comes (the process answers in
   the order it was asked: tickets). A process is started when first needed and is first sent the
   prelude (the plugin loads and the rules' options), so every process registers the same rules.
   Processes end when their fd 3 closes. */
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
/* mu: starting the process and writing requests (taking a ticket); rmu, cv: reading answers in
   ticket order. broken: the process died or a write failed; the next writer restarts it (gen
   counts restarts, so the waiters of a dead process give up). Lock order: mu, then rmu. */
typedef struct {
    pid_t pid; int in, out; char *buf; size_t len, cap, have, next;
    pthread_mutex_t mu, rmu; pthread_cond_t cv;
    long tickets, serving; int gen, broken;
} vl_worker;
static vl_worker vlw[VL_MAXW];
static pthread_mutex_t vl_mu = PTHREAD_MUTEX_INITIALIZER;
static char *vl_script = NULL;
static char **vl_args = NULL;     /* vlint's own arguments, passed on (plugins read process.argv) */
static int vl_nargs = 0;
static char **vl_env = NULL;      /* the processes' environment: vlint's, with NODE_COMPILE_CACHE */
static char *vl_prelude = NULL;   /* lines */
static size_t vl_prelude_len = 0;
static int vl_slots = 1, vl_next_slot = 0, vl_inited = 0;
static char vl_pool[32] = "";     /* --v8-pool-size=N for the processes, or "" */
static __thread int vl_slot = -1;

static void vl_stop(vl_worker *w) {
    if (w->pid < 0) return;
    close(w->in);
    close(w->out);
    int st;
    while (waitpid(w->pid, &st, 0) < 0 && errno == EINTR) {}
    w->pid = -1; w->in = w->out = -1;
    w->have = w->next = 0;
}

static void vl_atexit(void) { for (int i = 0; i < VL_MAXW; i++) vl_stop(&vlw[i]); }

static void vl_init_once(void) {
    if (vl_inited) return;
    vl_inited = 1;
    for (int i = 0; i < VL_MAXW; i++) {
        vlw[i].pid = -1; vlw[i].in = vlw[i].out = -1; vlw[i].buf = NULL; vlw[i].len = vlw[i].cap = 0;
        pthread_mutex_init(&vlw[i].mu, NULL);
        pthread_mutex_init(&vlw[i].rmu, NULL);
        pthread_cond_init(&vlw[i].cv, NULL);
        vlw[i].have = vlw[i].next = 0;
        vlw[i].tickets = vlw[i].serving = 0; vlw[i].gen = 0; vlw[i].broken = 0;
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
        /* a SIGPIPE left pending by the failed write is consumed (sigwait returns at once for a
           pending signal; sigtimedwait isn't on macOS) */
        sigset_t pend;
        sigpending(&pend);
        if (sigismember(&pend, SIGPIPE)) { int sig; sigwait(&set, &sig); }
    }
    pthread_sigmask(SIG_SETMASK, &old, NULL);
    return ok;
}

/* reads one answer line: w->buf[0..w->len) (without the newline), false when the process died.
   What was read past the line (the next answers) stays in the buffer for the next call. */
static bool vl_recv(vl_worker *w) {
    if (w->next > 0) {
        memmove(w->buf, w->buf + w->next, w->have - w->next);
        w->have -= w->next;
        w->next = 0;
    }
    size_t scanned = 0;
    for (;;) {
        char *nl = w->have > scanned ? memchr(w->buf + scanned, '\n', w->have - scanned) : NULL;
        if (nl) {
            w->len = (size_t)(nl - w->buf);
            w->next = w->len + 1;
            return true;
        }
        scanned = w->have;
        if (w->cap - w->have < 65536) { w->cap = w->cap ? w->cap * 2 : 131072; w->buf = realloc(w->buf, w->cap); }
        ssize_t r;
        do r = read(w->out, w->buf + w->have, w->cap - w->have); while (r < 0 && errno == EINTR);
        if (r <= 0) return false;
        w->have += (size_t)r;
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
    char **argv = calloc((size_t)vl_nargs + 5, sizeof *argv);
    int a0 = 0;
    argv[a0++] = "node"; argv[a0++] = "--no-warnings";
    if (vl_pool[0]) argv[a0++] = vl_pool;
    argv[a0++] = vl_script;
    for (int i = 0; i < vl_nargs; i++) argv[a0 + i] = vl_args[i];
    pid_t pid;
    int rc = posix_spawnp(&pid, "node", &fa, NULL, argv, vl_env ? vl_env : environ);
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
    /* How many node processes: one for each two cores (a busy node process keeps about one and a
       half cores busy, with V8's own threads), at most one per linting thread; the threads share
       them. VLINT_JS_PROCS sets it (for measuring). */
    long ncpu = sysconf(_SC_NPROCESSORS_ONLN);
    long procs = ncpu > 1 ? ncpu / 2 : 1;
    if (procs > slots) procs = slots;
    const char *jp = getenv("VLINT_JS_PROCS");
    if (jp && atoi(jp) > 0) procs = atoi(jp);
    vl_slots = procs < 1 ? 1 : procs > VL_MAXW ? VL_MAXW : (int)procs;
    /* Node gives each process 4 background V8 threads (GC, optimizing compiles) whatever the
       machine; with a process per core they only take turns with the processes' own threads.
       Each gets the cores left over per process, at least 1 (AFFiNE's config with six JS plugins
       on 2 cores: 5-8% less wall and CPU time), unless NODE_OPTIONS sets it. */
    const char *no = getenv("NODE_OPTIONS");
    if (!(no && strstr(no, "v8-pool-size"))) {
        long k = ncpu > 0 ? ncpu / vl_slots - 1 : 1;
        if (k < 1) k = 1;
        if (k > 4) k = 4;
        snprintf(vl_pool, sizeof vl_pool, "--v8-pool-size=%ld", k);
    } else vl_pool[0] = 0;
    /* Node's compile cache (Node 22.1 and later; older ones ignore it) in a folder beside the host
       script, so later runs don't compile the host and the plugins again (about 0.5 s a process),
       unless the user chose a cache or turned it off */
    const char *sl = vl_script ? strrchr(vl_script, '/') : NULL;
    if (!vl_env && sl && sl > vl_script && !getenv("NODE_COMPILE_CACHE") && !getenv("NODE_DISABLE_COMPILE_CACHE")) {
        size_t dl = (size_t)(sl - vl_script);
        const char *pre = "NODE_COMPILE_CACHE=", *suf = "/node-compile-cache";
        char *var = malloc(strlen(pre) + dl + strlen(suf) + 1);
        sprintf(var, "%s%.*s%s", pre, (int)dl, vl_script, suf);
        int n = 0;
        while (environ[n]) n++;
        vl_env = calloc((size_t)n + 2, sizeof *vl_env);
        for (int i = 0; i < n; i++) vl_env[i] = environ[i];
        vl_env[n] = var;
    }
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

/* Sends a request and takes a ticket for its answer: the ticket and the process's generation, or
   false when node can't be started. A dead process is stopped and started again first. */
static bool vl_send(vl_worker *w, const vu_str *req, long *t, int *g) {
    pthread_mutex_lock(&w->mu);
    if (w->broken || w->pid < 0) {
        pthread_mutex_lock(&w->rmu);
        if (w->pid >= 0) vl_stop(w);
        w->broken = 0; w->gen++; w->tickets = w->serving = 0;
        pthread_cond_broadcast(&w->cv);
        pthread_mutex_unlock(&w->rmu);
        if (!vl_start(w)) { vl_stop(w); w->broken = 1; pthread_mutex_unlock(&w->mu); return false; }
    }
    bool ok = vl_write(w->in, req->data, (size_t)req->len) && vl_write(w->in, "\n", 1);
    pthread_mutex_lock(&w->rmu);
    if (ok && !w->broken) { *t = w->tickets++; *g = w->gen; }
    else if (ok) *g = -1;  /* (it died meanwhile, found by a reader: no answer will come) */
    else {
        /* (the process died: its waiters give up, the request goes again) */
        w->broken = 1; w->gen++;
        *g = -1;
        pthread_cond_broadcast(&w->cv);
    }
    pthread_mutex_unlock(&w->rmu);
    pthread_mutex_unlock(&w->mu);
    return true;
}

/* The answer to a request from this thread's process, or "!" when node can't be started or died
   answering it. A request queued behind the one that made the process die is sent again (up to
   3 times) to the new process. */
vu_str vl_node_call(const vu_str *req) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    if (vl_slot < 0) vl_slot = (vl_next_slot++) % vl_slots;
    pthread_mutex_unlock(&vl_mu);
    vl_worker *w = &vlw[vl_slot];
    for (int attempt = 0; attempt <= 3; attempt++) {
        long t = 0;
        int g = 0;
        if (!vl_send(w, req, &t, &g)) return vu_str_from("!", 1);
        if (g < 0) continue;
        pthread_mutex_lock(&w->rmu);
        while (w->gen == g && w->serving != t) pthread_cond_wait(&w->cv, &w->rmu);
        if (w->gen != g) { pthread_mutex_unlock(&w->rmu); continue; }
        vu_str res;
        if (vl_recv(w)) {
            res = vu_str_from(w->buf, (int64_t)w->len);
            w->serving++;
        } else {
            w->broken = 1; w->gen++;
            res = vu_str_from("!", 1);
        }
        pthread_cond_broadcast(&w->cv);
        pthread_mutex_unlock(&w->rmu);
        return res;
    }
    return vu_str_from("!", 1);
}

/* Ends the processes (they finish the work they have). */
void vl_node_stop(void) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    for (int i = 0; i < VL_MAXW; i++) { pthread_mutex_lock(&vlw[i].mu); vl_stop(&vlw[i]); pthread_mutex_unlock(&vlw[i].mu); }
    pthread_mutex_unlock(&vl_mu);
}

