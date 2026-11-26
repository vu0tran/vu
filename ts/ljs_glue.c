/* JS plugins (ljs.vu): long-lived node processes running the plugin host. vlint writes a request (one
   line of JSON) to a process's fd 3 and reads the answer (one line) from its fd 4; the process's
   standard output and error are vlint's (as a plugin's console.log is oxlint's). The linting threads
   share the processes (one process for each two cores by default, see vl_node_setup): a thread
   writes its request without waiting for the others' answers, so the next file is already there
   when the process finishes one, and reads its answer when its turn comes (the process answers in
   the order it was asked: tickets). A thread of the process's own (vl_reader, a plain pthread) reads
   the answers as they come and keeps each until its asker takes it. (The askers used to read them
   in turn, the holder of the current ticket reading next; but the linting threads are tasks,
   several to an OS thread at times, and a task waiting for its turn blocked its thread and could
   keep the ticket's holder from running: nobody read, node stopped on a full fd 4, and the run
   waited for VLINT_JS_TIMEOUT, losing those files' JS diagnostics; once in a dozen runs on a
   36,000-file monorepo with tsgolint running beside the linting.) A process is started when first needed and is first sent the
   prelude (the plugin loads and the rules' options), so every process registers the same rules.
   Processes end when their fd 3 closes.

   Nothing here waits forever (issue #7): every read and write on a process's pipes (each wait for
   room in fd 3 too, which is non-blocking) gives up after VLINT_JS_TIMEOUT seconds (default 120; 0: no limit), and the process is then killed, so the file
   gets an error instead of the run hanging; at exit a process that doesn't end within 2 s of its
   fd 3 closing is killed. Processes are started one at a time with close-on-exec pipes, so no
   process inherits another's pipe ends (which would keep it from ever seeing its fd 3 close).
   VLINT_JS_DEBUG=1 traces each request and answer on stderr. */
#include <poll.h>
#include <time.h>
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
static int vl_timeout_ms = 120000;
static int vl_debug = 0;
static pthread_mutex_t vl_spawn_mu = PTHREAD_MUTEX_INITIALIZER;
static double vl_now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec / 1e9; }
#define VL_DBG(...) do { if (vl_debug) { fprintf(stderr, "vlint js %.3f: ", vl_now()); fprintf(stderr, __VA_ARGS__); fputc('\n', stderr); } } while (0)
/* mu: starting the process and writing requests (taking a ticket); rmu, cv: the answers (ans[t]
   for ticket t, nans read so far). broken: the process died or a write failed; the next writer
   restarts it (gen counts restarts, so the waiters of a dead process give up). Lock order: mu, then
   rmu. The reader thread alone uses buf while it runs, and takes rmu to store an answer. */
typedef struct {
    pid_t pid; int in, out; char *buf; size_t len, cap, have, next;
    pthread_mutex_t mu, rmu; pthread_cond_t cv;
    long tickets, serving; int gen, broken, timed_out;
    char **ans; size_t *alen; long nans, acap;
    pthread_t reader; int has_reader;
    /* the request being answered when the process died (it gets "!", "!t" when it was stuck) */
    int died_gen, died_to; long died_t;
    /* what its answers took: each request's sending time (by ticket), the time it was busy on the
       requests answered (an answer's time less its request's sending or the previous answer's,
       whichever is later), how many, and the last answer's time */
    double *sent_at; long scap; double busy, last_ans; long served;
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
/* With the number of lint requests known (vl_node_expect), the calls go to the first vl_inuse
   processes, each to the one with the fewest requests waiting, and another process is started
   only when the work left (the requests not sent yet, at the time the answers so far took each)
   is more than VL_SPAWN_SECS for each process in use: a process costs about 0.2 s of CPU to start
   (node, the host, the plugins), so a package of a few dozen files used to start four of them for
   a fraction of a second of work. Unknown (-1): every thread keeps to one of vl_slots processes. */
static long vl_expect = -1, vl_nsent = 0;
static int vl_inuse = 1;
static double vl_spawned_at = 0;
#define VL_SPAWN_SECS 1.0
static char vl_pool[32] = "";     /* --v8-pool-size=N for the processes, or "" */
static __thread int vl_slot = -1;

/* (rmu not held: the reader may be waiting for it) */
static void vl_stop(vl_worker *w) {
    if (w->pid < 0) return;
    if (w->in >= 0) close(w->in);
    w->in = -1;
    if (!w->has_reader) close(w->out);
    int st;
    /* (it ends when its fd 3 closes; one that doesn't within 2 s, or that was found stuck, is killed) */
    if (w->timed_out) kill(w->pid, SIGKILL);
    double until = vl_now() + 2.0;
    for (;;) {
        pid_t r = waitpid(w->pid, &st, WNOHANG);
        if (r == w->pid || (r < 0 && errno != EINTR)) break;
        if (vl_now() > until) {
            VL_DBG("process %d didn't end: killed", (int)w->pid);
            kill(w->pid, SIGKILL);
            while (waitpid(w->pid, &st, 0) < 0 && errno == EINTR) {}
            break;
        }
        struct timespec ts = {0, 10000000};
        nanosleep(&ts, NULL);
    }
    /* (the process has ended: its fd 4 is at its end and the reader stops) */
    if (w->has_reader) { pthread_join(w->reader, NULL); w->has_reader = 0; close(w->out); }
    pthread_mutex_lock(&w->rmu);
    for (long i = 0; i < w->nans; i++) free(w->ans[i]);
    w->nans = 0;
    pthread_mutex_unlock(&w->rmu);
    w->timed_out = 0;
    w->last_ans = 0;
    w->pid = -1; w->in = w->out = -1;
    w->have = w->next = 0;
}

/* (every process's fd 3 closed first, then each waited for: they end at once, not one after another;
   four React Compiler hosts took 0.3-0.5 s to end in turn) */
static void vl_stop_all(void) {
    for (int i = 0; i < VL_MAXW; i++)
        if (vlw[i].pid >= 0 && vlw[i].in >= 0) { close(vlw[i].in); vlw[i].in = -1; }
    for (int i = 0; i < VL_MAXW; i++) vl_stop(&vlw[i]);
}
static void vl_atexit(void) { vl_stop_all(); }

static void vl_init_once(void) {
    if (vl_inited) return;
    vl_inited = 1;
    for (int i = 0; i < VL_MAXW; i++) {
        vlw[i].pid = -1; vlw[i].in = vlw[i].out = -1; vlw[i].buf = NULL; vlw[i].len = vlw[i].cap = 0;
        pthread_mutex_init(&vlw[i].mu, NULL);
        pthread_mutex_init(&vlw[i].rmu, NULL);
        pthread_cond_init(&vlw[i].cv, NULL);
        vlw[i].have = vlw[i].next = 0;
        vlw[i].tickets = vlw[i].serving = 0; vlw[i].gen = 0; vlw[i].broken = 0; vlw[i].timed_out = 0;
        vlw[i].ans = NULL; vlw[i].alen = NULL; vlw[i].nans = vlw[i].acap = 0; vlw[i].has_reader = 0;
        vlw[i].died_gen = -1; vlw[i].died_t = -1; vlw[i].died_to = 0;
        vlw[i].sent_at = NULL; vlw[i].scap = 0; vlw[i].busy = vlw[i].last_ans = 0; vlw[i].served = 0;
    }
    atexit(vl_atexit);
    const char *t = getenv("VLINT_JS_TIMEOUT");
    if (t && *t) { long v = atol(t); vl_timeout_ms = v > 0 ? (int)(v > 86400 ? 86400000 : v * 1000) : -1; }
    const char *d = getenv("VLINT_JS_DEBUG");
    vl_debug = d && *d && strcmp(d, "0") != 0;
}

/* waits until fd is ready (POLLIN or POLLOUT); false after vl_timeout_ms (with no limit, waits) */
static bool vl_ready(int fd, short ev) {
    struct pollfd p = {fd, ev, 0};
    if (vl_timeout_ms < 0) {
        for (;;) {
            int r = poll(&p, 1, -1);
            if (r > 0 || errno != EINTR) return true;
        }
    }
    double until = vl_now() + vl_timeout_ms / 1000.0;
    for (;;) {
        int left = (int)((until - vl_now()) * 1000.0);
        if (left < 0) left = 0;
        int r = poll(&p, 1, left);
        if (r > 0) return true;
        if (r == 0) return false;
        if (errno != EINTR) return true;   /* (let the read or write report the error) */
    }
}

/* Writes all of p to the process's fd 3. The pipe's write end is non-blocking (vl_start), so a
   request larger than the pipe's buffer is written as the process reads it, and the time limit
   holds for each wait for room, not only the first: poll's "writable" means some room, and a
   blocking write of the rest would wait for the process however long it takes (issue #7: a
   178 KB request stuck in write). */
static bool vl_write(vl_worker *wk, int fd, const char *p, size_t n) {
    sigset_t set, old;
    sigemptyset(&set);
    sigaddset(&set, SIGPIPE);
    pthread_sigmask(SIG_BLOCK, &set, &old);
    bool ok = true;
    size_t total = n, done = 0;
    double t0 = vl_now();
    int traced = 0;
    while (n > 0) {
        ssize_t w = write(fd, p, n);
        if (w > 0) { p += w; n -= (size_t)w; done += (size_t)w; continue; }
        if (w < 0 && errno == EINTR) continue;
        if (w < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (!traced && vl_now() - t0 > 1.0) {
                traced = 1;
                VL_DBG("process %d: fd 3 full, %zu of %zu bytes written; waiting for it to read", (int)wk->pid, done, total);
            }
            if (!vl_ready(fd, POLLOUT)) {
                VL_DBG("process %d took no request for %d s (fd 3, %zu of %zu bytes written): killed", (int)wk->pid, vl_timeout_ms / 1000, done, total);
                wk->timed_out = 1;
                kill(wk->pid, SIGKILL);
                ok = false;
                break;
            }
            continue;
        }
        ok = false;
        break;
    }
    if (ok && traced) VL_DBG("process %d: request of %zu bytes written after %.1f s", (int)wk->pid, total, vl_now() - t0);
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
static bool vl_recv(vl_worker *w, bool limit) {
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
        if (limit && !vl_ready(w->out, POLLIN)) {
            VL_DBG("process %d gave no answer for %d s: killed", (int)w->pid, vl_timeout_ms / 1000);
            w->timed_out = 1;
            kill(w->pid, SIGKILL);
            return false;
        }
        ssize_t r;
        do r = read(w->out, w->buf + w->have, w->cap - w->have); while (r < 0 && errno == EINTR);
        if (r <= 0) return false;
        w->have += (size_t)r;
    }
}

/* A request's line, with U+2028 and U+2029 written as \u2028 and \u2029: node's readline ends a
   line at either (JSON.stringify leaves them as they are, and so does vlint), so a file holding one
   was read as two requests and answered twice, and every later answer of that process went to the
   file after its own (thousands of JS diagnostics on the wrong files in a 36,000-file monorepo
   with one such file). Raw, they can only be inside a JSON string, where the escape means the same. */
static bool vl_write_req(vl_worker *w, const char *p, size_t n) {
    size_t from = 0;
    for (size_t i = 0; i + 2 < n; i++) {
        if ((unsigned char)p[i] == 0xE2 && (unsigned char)p[i + 1] == 0x80 && ((unsigned char)p[i + 2] == 0xA8 || (unsigned char)p[i + 2] == 0xA9)) {
            if (!vl_write(w, w->in, p + from, i - from)) return false;
            if (!vl_write(w, w->in, (unsigned char)p[i + 2] == 0xA8 ? "\\u2028" : "\\u2029", 6)) return false;
            i += 2;
            from = i + 1;
        }
    }
    return vl_write(w, w->in, p + from, n - from);
}

/* A process's reader: each answer line kept for its ticket, in order; at the end of the output (the
   process died, was killed or was stopped) its waiters are told (broken, gen). */
typedef struct { vl_worker *w; int gen; } vl_rarg;
static void *vl_reader(void *arg) {
    vl_rarg *ra = arg;
    vl_worker *w = ra->w;
    int gen = ra->gen;
    free(ra);
    for (;;) {
        bool ok = vl_recv(w, false);
        pthread_mutex_lock(&w->rmu);
        if (w->gen != gen) { pthread_mutex_unlock(&w->rmu); return NULL; }
        if (!ok) {
            w->died_gen = gen; w->died_t = w->nans; w->died_to = w->timed_out;
            w->broken = 1; w->gen++;
            pthread_cond_broadcast(&w->cv);
            pthread_mutex_unlock(&w->rmu);
            return NULL;
        }
        if (w->nans == w->acap) {
            w->acap = w->acap ? w->acap * 2 : 1024;
            w->ans = realloc(w->ans, (size_t)w->acap * sizeof *w->ans);
            w->alen = realloc(w->alen, (size_t)w->acap * sizeof *w->alen);
        }
        char *a = malloc(w->len + 1);
        memcpy(a, w->buf, w->len);
        if (w->nans < w->scap) {
            double now = vl_now(), from = w->sent_at[w->nans];
            if (w->last_ans > from) from = w->last_ans;
            if (now > from) w->busy += now - from;
            w->last_ans = now;
            w->served++;
        }
        w->ans[w->nans] = a;
        w->alen[w->nans] = w->len;
        VL_DBG("process %d: answer %ld, %zu bytes", (int)w->pid, w->nans, w->len);
        w->nans++;
        pthread_cond_broadcast(&w->cv);
        pthread_mutex_unlock(&w->rmu);
    }
}

static int vl_pipe(int f[2]) {
    if (pipe(f) != 0) return -1;
    fcntl(f[0], F_SETFD, FD_CLOEXEC);
    fcntl(f[1], F_SETFD, FD_CLOEXEC);
    return 0;
}

static bool vl_start(vl_worker *w) {
    int a[2], b[2];
    if (!vl_script) return false;
    /* (one start at a time: another thread's spawn can't catch these pipes before they're
       close-on-exec) */
    pthread_mutex_lock(&vl_spawn_mu);
    if (vl_pipe(a) != 0) { pthread_mutex_unlock(&vl_spawn_mu); return false; }
    if (vl_pipe(b) != 0) { close(a[0]); close(a[1]); pthread_mutex_unlock(&vl_spawn_mu); return false; }
    int r3 = fcntl(a[0], F_DUPFD_CLOEXEC, 10), wp = fcntl(a[1], F_DUPFD_CLOEXEC, 10);
    int rp = fcntl(b[0], F_DUPFD_CLOEXEC, 10), w4 = fcntl(b[1], F_DUPFD_CLOEXEC, 10);
    close(a[0]); close(a[1]); close(b[0]); close(b[1]);
    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_addopen(&fa, 0, "/dev/null", O_RDONLY, 0);
    posix_spawn_file_actions_adddup2(&fa, r3, 3);
    posix_spawn_file_actions_adddup2(&fa, w4, 4);
    posix_spawnattr_t sa;
    posix_spawnattr_init(&sa);
#ifdef POSIX_SPAWN_CLOEXEC_DEFAULT
    /* (macOS: the process gets only the descriptors named here, whatever else vlint has open) */
    posix_spawn_file_actions_addinherit_np(&fa, 1);
    posix_spawn_file_actions_addinherit_np(&fa, 2);
    posix_spawnattr_setflags(&sa, POSIX_SPAWN_CLOEXEC_DEFAULT);
#endif
    char **argv = calloc((size_t)vl_nargs + 5, sizeof *argv);
    int a0 = 0;
    argv[a0++] = "node"; argv[a0++] = "--no-warnings";
    if (vl_pool[0]) argv[a0++] = vl_pool;
    argv[a0++] = vl_script;
    for (int i = 0; i < vl_nargs; i++) argv[a0 + i] = vl_args[i];
    pid_t pid;
    int rc = posix_spawnp(&pid, "node", &fa, &sa, argv, vl_env ? vl_env : environ);
    free(argv);
    posix_spawn_file_actions_destroy(&fa);
    posix_spawnattr_destroy(&sa);
    close(r3); close(w4);
    pthread_mutex_unlock(&vl_spawn_mu);
    if (rc != 0) { close(wp); close(rp); return false; }
    w->pid = pid; w->in = wp; w->out = rp;
    fcntl(wp, F_SETFL, fcntl(wp, F_GETFL) | O_NONBLOCK);
    VL_DBG("process %d started", (int)pid);
    /* the prelude: each line answered, the answers dropped */
    const char *p = vl_prelude, *e = vl_prelude ? vl_prelude + vl_prelude_len : NULL;
    while (p && p < e) {
        const char *nl = memchr(p, '\n', (size_t)(e - p));
        if (!nl) nl = e;
        if (nl > p) {
            if (!vl_write_req(w, p, (size_t)(nl - p)) || !vl_write(w, w->in, "\n", 1) || !vl_recv(w, true)) { vl_stop(w); return false; }
        }
        p = nl + 1;
    }
    /* (what the prelude's answers left in buf is the reader's now) */
    vl_rarg *ra = malloc(sizeof *ra);
    ra->w = w;
    pthread_mutex_lock(&w->rmu);
    ra->gen = w->gen;
    pthread_mutex_unlock(&w->rmu);
    if (pthread_create(&w->reader, NULL, vl_reader, ra) != 0) { free(ra); vl_stop(w); return false; }
    w->has_reader = 1;
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

/* the request's file, for the trace: the "path" of a lint request (escapes left as they are) */
static void vl_req_path(const vu_str *req, char *out, size_t cap) {
    static const char key[] = "\"path\":\"";
    out[0] = 0;
    const char *d = (const char *)req->data;
    size_t n = (size_t)req->len, k = sizeof key - 1;
    if (n > 4096) n = 4096;
    for (size_t i = 0; i + k <= n; i++) {
        if (memcmp(d + i, key, k) != 0) continue;
        size_t j = i + k, o = 0;
        while (j < n && d[j] != '"' && o + 2 < cap) { if (d[j] == '\\' && j + 1 < n) out[o++] = d[j++]; out[o++] = d[j++]; }
        out[o] = 0;
        return;
    }
}

/* Sends a request and takes a ticket for its answer: the ticket and the process's generation, or
   false when node can't be started. A dead process is stopped and started again first. */
static bool vl_send(vl_worker *w, const vu_str *req, long *t, int *g) {
    pthread_mutex_lock(&w->mu);
    if (w->broken || w->pid < 0) {
        if (w->pid >= 0) vl_stop(w);
        pthread_mutex_lock(&w->rmu);
        w->broken = 0; w->gen++; w->tickets = w->serving = 0;
        pthread_cond_broadcast(&w->cv);
        pthread_mutex_unlock(&w->rmu);
        if (!vl_start(w)) { vl_stop(w); w->broken = 1; pthread_mutex_unlock(&w->mu); return false; }
    }
    if (vl_debug) {
        char path[512];
        vl_req_path(req, path, sizeof path);
        VL_DBG("process %d: sending request of %lld bytes on its fd 3 (vlint's fd %d), ticket %ld%s%s", (int)w->pid, (long long)req->len, w->in, w->tickets, path[0] ? ": " : "", path);
    }
    /* (a frame, ljs.lint_frame: its JSON line, then its bytes as they are; any other request: one
       line) */
    static const char frame[] = "{\"op\":\"lintb\"";
    const char *rd = (const char *)req->data, *nl = NULL;
    if ((size_t)req->len > sizeof frame - 1 && memcmp(rd, frame, sizeof frame - 1) == 0) nl = memchr(rd, '\n', (size_t)req->len);
    bool ok = nl ? vl_write_req(w, rd, (size_t)(nl + 1 - rd)) && vl_write(w, w->in, nl + 1, (size_t)(rd + req->len - (nl + 1)))
                 : vl_write_req(w, rd, (size_t)req->len) && vl_write(w, w->in, "\n", 1);
    pthread_mutex_lock(&w->rmu);
    VL_DBG("process %d: request of %lld bytes sent (%s), ticket %ld", (int)w->pid, (long long)req->len, ok ? "ok" : "failed", w->tickets);
    if (ok && !w->broken) {
        if (w->tickets >= w->scap) {
            w->scap = w->scap ? w->scap * 2 : 1024;
            w->sent_at = realloc(w->sent_at, (size_t)w->scap * sizeof *w->sent_at);
        }
        w->sent_at[w->tickets] = vl_now();
        *t = w->tickets++; *g = w->gen;
    }
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
/* The number of lint requests the run will send (at most): see vl_expect. */
void vl_node_expect(int64_t n) {
    pthread_mutex_lock(&vl_mu);
    vl_expect = n < 0 ? -1 : (long)n;
    pthread_mutex_unlock(&vl_mu);
}

/* the process a call goes to (vl_mu held) */
static int vl_pick(void) {
    if (vl_expect < 0) {
        if (vl_slot < 0) vl_slot = (vl_next_slot++) % vl_slots;
        return vl_slot;
    }
    vl_nsent++;
    double busy = 0;
    long served = 0, bestq = -1;
    int best = 0;
    for (int i = 0; i < vl_inuse; i++) {
        vl_worker *w = &vlw[i];
        pthread_mutex_lock(&w->rmu);
        long q = w->tickets - w->nans;
        busy += w->busy;
        served += w->served;
        pthread_mutex_unlock(&w->rmu);
        if (bestq < 0 || q < bestq) { bestq = q; best = i; }
    }
    if (vl_inuse < vl_slots && served >= 16 && bestq > 0) {
        double now = vl_now();
        double left = (double)(vl_expect - vl_nsent) * busy / (double)served;
        if (now - vl_spawned_at > 0.05 && left / vl_inuse > VL_SPAWN_SECS) {
            vl_spawned_at = now;
            VL_DBG("%ld of %ld requests sent, %.2f s of work left: process %d added", vl_nsent, vl_expect, left, vl_inuse);
            best = vl_inuse++;
        }
    }
    return best;
}

vu_str vl_node_call(const vu_str *req) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    int slot = vl_pick();
    pthread_mutex_unlock(&vl_mu);
    vl_worker *w = &vlw[slot];
    for (int attempt = 0; attempt <= 3; attempt++) {
        long t = 0;
        int g = 0;
        if (!vl_send(w, req, &t, &g)) return vu_str_from("!", 1);
        if (g < 0) continue;
        pthread_mutex_lock(&w->rmu);
        /* (no answer to the oldest request for VLINT_JS_TIMEOUT seconds: the process is stuck and is
           killed; its reader then tells the waiters) */
        bool killed = false;
        double until = vl_now() + (vl_timeout_ms < 0 ? 0 : vl_timeout_ms / 1000.0);
        long seen = w->nans;
        while (w->gen == g && w->nans <= t) {
            if (vl_timeout_ms < 0 || killed) { pthread_cond_wait(&w->cv, &w->rmu); continue; }
            struct timespec ts;
            clock_gettime(CLOCK_REALTIME, &ts);
            double left = until - vl_now();
            if (left < 0) left = 0;
            ts.tv_sec += (time_t)left;
            ts.tv_nsec += (long)((left - (double)(time_t)left) * 1e9);
            if (ts.tv_nsec >= 1000000000L) { ts.tv_sec++; ts.tv_nsec -= 1000000000L; }
            pthread_cond_timedwait(&w->cv, &w->rmu, &ts);
            if (w->gen != g || w->nans > t) break;
            /* (an answer came: the process is alive, the time starts again) */
            if (w->nans != seen) { seen = w->nans; until = vl_now() + vl_timeout_ms / 1000.0; continue; }
            if (vl_now() >= until) {
                VL_DBG("process %d gave no answer for %d s: killed", (int)w->pid, vl_timeout_ms / 1000);
                w->timed_out = 1;
                kill(w->pid, SIGKILL);
                killed = true;
            }
        }
        if (w->gen != g) {
            /* (the process died answering this one: "!", "!t" when it was stuck; the ones after it
               are sent again) */
            bool mine = w->died_gen == g && w->died_t == t;
            int to = w->died_to;
            pthread_mutex_unlock(&w->rmu);
            if (mine) return to ? vu_str_from("!t", 2) : vu_str_from("!", 1);
            continue;
        }
        char *a = w->ans[t];
        size_t al = w->alen[t];
        w->ans[t] = NULL;
        w->serving++;
        pthread_mutex_unlock(&w->rmu);
        vu_str res = vu_str_from(a, (int64_t)al);
        free(a);
        return res;
    }
    return vu_str_from("!", 1);
}

/* Ends the processes (they finish the work they have). */
void vl_node_stop(void) {
    pthread_mutex_lock(&vl_mu);
    vl_init_once();
    for (int i = 0; i < VL_MAXW; i++) pthread_mutex_lock(&vlw[i].mu);
    vl_stop_all();
    for (int i = 0; i < VL_MAXW; i++) pthread_mutex_unlock(&vlw[i].mu);
    pthread_mutex_unlock(&vl_mu);
}


/* tsgolint as a process of its own, started without waiting (vl_proc_start: exe "headless", standard
   input from the payload file, output and errors to files) and waited for when its answer is
   needed (vl_proc_wait: the exit status, 128 + the signal when one ended it, -1 when it couldn't
   start). (A task running it with os.run held its thread, the main thread's at times, for the
   whole run.) */
int64_t vl_proc_start(const vu_str *exe, const vu_str *pin, const vu_str *pout, const vu_str *perr) {
    char *e = vu_cstr(exe), *i = vu_cstr(pin), *o = vu_cstr(pout), *r = vu_cstr(perr);
    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_addopen(&fa, 0, i, O_RDONLY, 0);
    posix_spawn_file_actions_addopen(&fa, 1, o, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    posix_spawn_file_actions_addopen(&fa, 2, r, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    char *argv[3] = { e, "headless", NULL };
    pid_t pid;
    int rc = posix_spawnp(&pid, e, &fa, NULL, argv, environ);
    posix_spawn_file_actions_destroy(&fa);
    free(e); free(i); free(o); free(r);
    return rc == 0 ? (int64_t)pid : -1;
}
int64_t vl_proc_wait(int64_t pid) {
    if (pid <= 0) return -1;
    int st;
    while (waitpid((pid_t)pid, &st, 0) < 0) { if (errno != EINTR) return -1; }
    if (WIFEXITED(st)) return WEXITSTATUS(st);
    if (WIFSIGNALED(st)) return 128 + WTERMSIG(st);
    return -1;
}

/* Which program tsgolint puts each file in: tsgolint run on the payload with OXC_LOG=debug prints,
   once it has looked up every file's tsconfig ("Got tsconfig for file F: T", T "<none>" for its
   inferred program) and before it builds any program, "Done assigning files to programs"; it is
   stopped there. Returns "F\tT\n" per file ("" when that line never came: an exit, or another
   log format). */
vu_str vl_tsgo_assign(const vu_str *exe, const vu_str *pin) {
    char *e = vu_cstr(exe), *in = vu_cstr(pin);
    int p[2];
    if (pipe(p) != 0) { free(e); free(in); return vu_str_from("", 0); }
    fcntl(p[0], F_SETFD, FD_CLOEXEC);
    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_addopen(&fa, 0, in, O_RDONLY, 0);
    posix_spawn_file_actions_addopen(&fa, 1, "/dev/null", O_WRONLY, 0);
    posix_spawn_file_actions_adddup2(&fa, p[1], 2);
    posix_spawn_file_actions_addclose(&fa, p[1]);
    size_t ne = 0;
    while (environ[ne]) ne++;
    char **env = malloc((ne + 2) * sizeof *env);
    size_t k = 0;
    for (size_t i = 0; i < ne; i++) if (strncmp(environ[i], "OXC_LOG=", 8) != 0) env[k++] = environ[i];
    env[k++] = "OXC_LOG=debug";
    env[k] = NULL;
    char *argv[3] = { e, "headless", NULL };
    pid_t pid;
    int rc = posix_spawnp(&pid, e, &fa, NULL, argv, env);
    posix_spawn_file_actions_destroy(&fa);
    free(env);
    close(p[1]);
    free(e); free(in);
    if (rc != 0) { close(p[0]); return vu_str_from("", 0); }
    size_t cap = 1 << 20, len = 0, scan = 0;
    char *buf = malloc(cap);
    char *out = NULL; size_t olen = 0, ocap = 0;
    int done = 0;
    static const char got[] = "Got tsconfig for file ";
    static const char fin[] = "Done assigning files to programs";
    while (!done) {
        if (cap - len < 65536) { cap *= 2; buf = realloc(buf, cap); }
        ssize_t r = read(p[0], buf + len, cap - len);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0) break;
        len += (size_t)r;
        for (;;) {
            char *nl = memchr(buf + scan, '\n', len - scan);
            if (!nl) break;
            char *ln = buf + scan;
            size_t ll = (size_t)(nl - ln);
            scan = (size_t)(nl - buf) + 1;
            char *g = memmem(ln, ll, got, sizeof got - 1);
            if (g) {
                char *f = g + sizeof got - 1;
                size_t fl = (size_t)(nl - f);
                /* (the last ": " splits the file from its tsconfig) */
                char *sep = NULL;
                for (char *q = f; q + 1 < nl; q++) if (q[0] == ':' && q[1] == ' ') sep = q;
                if (!sep) continue;
                if (olen + fl + 2 > ocap) { ocap = (olen + fl + 2) * 2 + 4096; out = realloc(out, ocap); }
                memcpy(out + olen, f, (size_t)(sep - f)); olen += (size_t)(sep - f);
                out[olen++] = '\t';
                memcpy(out + olen, sep + 2, (size_t)(nl - sep - 2)); olen += (size_t)(nl - sep - 2);
                out[olen++] = '\n';
                (void)fl;
            } else if (memmem(ln, ll, fin, sizeof fin - 1)) { done = 1; break; }
        }
    }
    kill(pid, SIGKILL);
    close(p[0]);
    int st;
    while (waitpid(pid, &st, 0) < 0 && errno == EINTR) {}
    free(buf);
    vu_str res = done && out ? vu_str_from(out, (int64_t)olen) : vu_str_from("", 0);
    free(out);
    return res;
}

