/* vknip's terminal and file-watching glue: isatty, the terminal's width, and inotify (Linux) for
   --watch. Elsewhere vk_watch_open returns -1 and vknip polls. */
#include <unistd.h>
#include <sys/ioctl.h>
#include <poll.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#ifdef __linux__
#include <sys/inotify.h>
#endif

bool vk_isatty(int64_t fd) { return isatty((int)fd) == 1; }

/* the processors online (Linux and macOS alike) */
int64_t vk_cpus(void) { long n = sysconf(_SC_NPROCESSORS_ONLN); return n < 1 ? 1 : (int64_t)n; }

int64_t vk_columns(int64_t fd) {
    struct winsize w;
    if (ioctl((int)fd, TIOCGWINSZ, &w) == 0 && w.ws_col > 0) return w.ws_col;
    return 0;
}

int64_t vk_watch_open(void) {
#ifdef __linux__
    return inotify_init1(IN_CLOEXEC);
#else
    return -1;
#endif
}

int64_t vk_watch_add(int64_t fd, const vu_str *path) {
#ifdef __linux__
    char buf[4096];
    if (path->len >= (int64_t)sizeof buf) return -1;
    memcpy(buf, path->data, path->len);
    buf[path->len] = 0;
    return inotify_add_watch((int)fd, buf, IN_CREATE | IN_DELETE | IN_MODIFY | IN_MOVED_FROM | IN_MOVED_TO | IN_CLOSE_WRITE | IN_DELETE_SELF | IN_ONLYDIR);
#else
    (void)fd; (void)path;
    return -1;
#endif
}

/* Waits up to timeout_ms for events; returns them as lines "wd \t kind \t name \n" (kind: c created,
   d deleted, m modified, D a created folder, X a deleted folder), "" when none came. */
vu_str vk_watch_read(int64_t fd, int64_t timeout_ms) {
#ifdef __linux__
    struct pollfd p = { (int)fd, POLLIN, 0 };
    if (poll(&p, 1, (int)timeout_ms) <= 0) return vu_str_from("", 0);
    char buf[65536] __attribute__((aligned(__alignof__(struct inotify_event))));
    ssize_t n = read((int)fd, buf, sizeof buf);
    if (n <= 0) return vu_str_from("", 0);
    size_t cap = 1024, len = 0;
    char *out = malloc(cap);
    for (char *q = buf; q < buf + n;) {
        struct inotify_event *e = (struct inotify_event *)q;
        char kind = 'm';
        bool dir = (e->mask & IN_ISDIR) != 0;
        if (e->mask & (IN_CREATE | IN_MOVED_TO)) kind = dir ? 'D' : 'c';
        else if (e->mask & (IN_DELETE | IN_MOVED_FROM)) kind = dir ? 'X' : 'd';
        else if (e->mask & IN_DELETE_SELF) kind = 'X';
        size_t nl = e->len ? strlen(e->name) : 0;
        size_t need = len + nl + 48;
        if (need > cap) { while (need > cap) cap *= 2; out = realloc(out, cap); }
        len += (size_t)snprintf(out + len, cap - len, "%d\t%c\t", e->wd, kind);
        memcpy(out + len, e->name, nl);
        len += nl;
        out[len++] = '\n';
        q += sizeof(struct inotify_event) + e->len;
    }
    vu_str r = vu_str_from(out, (int64_t)len);
    free(out);
    return r;
#else
    (void)fd;
    usleep((useconds_t)(timeout_ms * 1000));
    return vu_str_from("", 0);
#endif
}

/* A cache of the file system for one run: each folder is read once (its names as fs.list gives
   them, sorted by bytes with "/" after folders, and which of them are symbolic links) and each path
   is stat-ed once. vknip writes files only after the analysis (--fix, --cache), and nothing it
   reads is looked at again after that. */
#include <dirent.h>
#include <sys/stat.h>
#include <limits.h>
#include <pthread.h>
typedef struct { char *key; size_t klen; int kind; bool listed, list_ok; char *list; size_t list_len; char *links; size_t links_len; } vk_fent;
static vk_fent *vkf_tab = NULL;
static size_t vkf_cap = 0, vkf_n = 0;
static pthread_mutex_t vkf_mu = PTHREAD_MUTEX_INITIALIZER;
static uint64_t vkf_hash(const char *p, size_t n) {
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) { h ^= (uint8_t)p[i]; h *= 1099511628211ULL; }
    return h;
}
static vk_fent *vkf_get(const char *p, size_t n) {
    if (vkf_n * 2 >= vkf_cap) {
        size_t nc = vkf_cap ? vkf_cap * 2 : 4096;
        vk_fent *nt = calloc(nc, sizeof(vk_fent));
        for (size_t i = 0; i < vkf_cap; i++) {
            if (!vkf_tab[i].key) continue;
            size_t h = (size_t)vkf_hash(vkf_tab[i].key, vkf_tab[i].klen) & (nc - 1);
            while (nt[h].key) h = (h + 1) & (nc - 1);
            nt[h] = vkf_tab[i];
        }
        free(vkf_tab);
        vkf_tab = nt;
        vkf_cap = nc;
    }
    size_t h = (size_t)vkf_hash(p, n) & (vkf_cap - 1);
    while (vkf_tab[h].key) {
        if (vkf_tab[h].klen == n && memcmp(vkf_tab[h].key, p, n) == 0) return &vkf_tab[h];
        h = (h + 1) & (vkf_cap - 1);
    }
    vk_fent *e = &vkf_tab[h];
    e->key = malloc(n + 1);
    memcpy(e->key, p, n);
    e->key[n] = 0;
    e->klen = n;
    e->kind = -1;
    vkf_n++;
    return e;
}
typedef struct { char *s; size_t n; } vkf_name;
static int vkf_cmp(const void *a, const void *b) {
    const vkf_name *x = a, *y = b;
    size_t n = x->n < y->n ? x->n : y->n;
    int c = n ? memcmp(x->s, y->s, n) : 0;
    return c ? c : (x->n < y->n ? -1 : x->n > y->n);
}
/* (the folder's names, "\0" after each, and its links, "\n" after each) */
static void vkf_list(vk_fent *e, const char *path) {
    e->listed = true;
    DIR *d = opendir(path);
    if (!d) return;
    e->list_ok = true;
    size_t n = 0, cap = 64, lcap = 64, llen = 0;
    vkf_name *names = malloc(cap * sizeof(vkf_name));
    char *links = malloc(lcap);
    struct dirent *ent;
    size_t plen = strlen(path);
    while ((ent = readdir(d))) {
        if (!strcmp(ent->d_name, ".") || !strcmp(ent->d_name, "..")) continue;
        size_t nl = strlen(ent->d_name);
        bool dir = ent->d_type == DT_DIR;
        bool link = ent->d_type == DT_LNK;
        if (ent->d_type == DT_UNKNOWN || ent->d_type == DT_LNK) {
            char *full = malloc(plen + nl + 2);
            memcpy(full, path, plen);
            full[plen] = '/';
            memcpy(full + plen + 1, ent->d_name, nl + 1);
            struct stat st;
            dir = stat(full, &st) == 0 && S_ISDIR(st.st_mode);
            if (ent->d_type == DT_UNKNOWN) link = lstat(full, &st) == 0 && S_ISLNK(st.st_mode);
            free(full);
        }
        if (n == cap) { cap *= 2; names = realloc(names, cap * sizeof(vkf_name)); }
        names[n].s = malloc(nl + 2);
        memcpy(names[n].s, ent->d_name, nl);
        if (dir) names[n].s[nl++] = '/';
        names[n].s[nl] = 0;
        names[n].n = nl;
        n++;
        if (link) {
            size_t ln = strlen(ent->d_name);
            while (llen + ln + 1 > lcap) { lcap *= 2; links = realloc(links, lcap); }
            memcpy(links + llen, ent->d_name, ln);
            llen += ln;
            links[llen++] = '\n';
        }
    }
    closedir(d);
    qsort(names, n, sizeof(vkf_name), vkf_cmp);
    size_t tot = 0;
    for (size_t i = 0; i < n; i++) tot += names[i].n + 1;
    e->list = malloc(tot + 1);
    size_t k = 0;
    for (size_t i = 0; i < n; i++) { memcpy(e->list + k, names[i].s, names[i].n); k += names[i].n; e->list[k++] = 0; free(names[i].s); }
    free(names);
    e->list_len = k;
    e->links = links;
    e->links_len = llen;
}
static bool vkf_cpath(const vu_str *path, char *buf, size_t size) {
    if (path->len >= (int64_t)size - 1) return false;
    memcpy(buf, path->data, path->len);
    buf[path->len] = 0;
    if (path->len == 0) { buf[0] = '.'; buf[1] = 0; }
    return true;
}
/* fs.list, cached: "1" then each name and "\0", or "0" when the folder can't be read */
vu_str vk_list(const vu_str *path) {
    char buf[4096];
    if (!vkf_cpath(path, buf, sizeof buf)) return vu_str_from("0", 1);
    pthread_mutex_lock(&vkf_mu);
    vk_fent *e = vkf_get(path->data, (size_t)path->len);
    if (!e->listed) vkf_list(e, buf);
    vu_str r;
    if (!e->list_ok) r = vu_str_from("0", 1);
    else {
        char *t = malloc(e->list_len + 1);
        t[0] = '1';
        memcpy(t + 1, e->list, e->list_len);
        r = vu_str_from(t, (int64_t)e->list_len + 1);
        free(t);
    }
    pthread_mutex_unlock(&vkf_mu);
    return r;
}
/* The names of a folder's entries that are symbolic links, one per line ("" none or unreadable). */
vu_str vk_links(const vu_str *path) {
    char buf[4096];
    if (!vkf_cpath(path, buf, sizeof buf)) return vu_str_from("", 0);
    pthread_mutex_lock(&vkf_mu);
    vk_fent *e = vkf_get(path->data, (size_t)path->len);
    if (!e->listed) vkf_list(e, buf);
    vu_str r = e->list_ok ? vu_str_from(e->links, (int64_t)e->links_len) : vu_str_from("", 0);
    pthread_mutex_unlock(&vkf_mu);
    return r;
}
/* stat, cached: 0 nothing there, 1 a file (or anything but a folder), 2 a folder */
int64_t vk_kind(const vu_str *path) {
    char buf[4096];
    if (path->len >= (int64_t)sizeof buf - 1) return 0;
    memcpy(buf, path->data, path->len);
    buf[path->len] = 0;
    pthread_mutex_lock(&vkf_mu);
    vk_fent *e = vkf_get(path->data, (size_t)path->len);
    if (e->kind < 0) {
        struct stat st;
        e->kind = stat(buf, &st) != 0 ? 0 : S_ISDIR(st.st_mode) ? 2 : 1;
    }
    int64_t k = e->kind;
    pthread_mutex_unlock(&vkf_mu);
    return k;
}

/* The path with symbolic links resolved (absolute), "" when it doesn't exist. */
vu_str vk_realpath(const vu_str *path) {
    char buf[4096];
    if (path->len >= (int64_t)sizeof buf - 1) return vu_str_from("", 0);
    memcpy(buf, path->data, path->len);
    buf[path->len] = 0;
    if (path->len == 0) { buf[0] = '.'; buf[1] = 0; }
    char res[PATH_MAX];
    if (!realpath(buf, res)) return vu_str_from("", 0);
    return vu_str_from(res, (int64_t)strlen(res));
}

/* Long-lived node processes that load the JavaScript configs of a run (loader.vu). vknip writes a
   request (one line of JSON) to a process's fd 3 and reads the answer (one line) from its fd 4. Its
   standard output and error go to an unlinked temporary file, read back when it dies before
   answering. Process 0 serves requests one at a time (vk_node); a batch of independent requests
   (vk_node_par) is spread over up to VK_MAXW processes. Each is started when first needed and ends
   when its fd 3 closes: at vknip's exit, which waits for them (so their time is vknip's). */
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <errno.h>
#include <sys/wait.h>
#include <pthread.h>
#include <time.h>
extern char **environ;
#define VK_MAXW 4
/* (warm: the answer to vk_node_warm's request is still to be read; used: it has answered a request) */
typedef struct { pid_t pid; int in, out, log; off_t from; char *buf; size_t len, cap; bool warm, used; } vk_worker;
static vk_worker vkw[VK_MAXW] = { { -1, -1, -1, -1, 0, NULL, 0, 0, false, false }, { -1, -1, -1, -1, 0, NULL, 0, 0, false, false }, { -1, -1, -1, -1, 0, NULL, 0, 0, false, false }, { -1, -1, -1, -1, 0, NULL, 0, 0, false, false } };

static void vk_node_stop(vk_worker *w) {
    if (w->pid < 0) return;
    /* (one that was only warmed up is stopped rather than waited for) */
    if (!w->used) kill(w->pid, SIGKILL);
    close(w->in);
    close(w->out);
    int st;
    while (waitpid(w->pid, &st, 0) < 0 && errno == EINTR) {}
    if (w->log >= 0) close(w->log);
    w->pid = -1; w->in = w->out = w->log = -1;
    w->warm = w->used = false;
}

static void vk_node_atexit(void) { for (int i = 0; i < VK_MAXW; i++) vk_node_stop(&vkw[i]); }

static bool vk_node_start(vk_worker *w, const vu_str *js) {
    static bool registered = false;
    if (!registered) { registered = true; atexit(vk_node_atexit); }
    int a[2], b[2];
    if (pipe(a) != 0) return false;
    if (pipe(b) != 0) { close(a[0]); close(a[1]); return false; }
    const char *tmp = getenv("TMPDIR");
    char lp[4096];
    snprintf(lp, sizeof lp, "%s/vknip-node-XXXXXX", tmp && *tmp ? tmp : "/tmp");
    int lf = mkstemp(lp);
    if (lf >= 0) unlink(lp);
    /* every descriptor moves above 10 and closes on exec; the child gets its copies by dup2 */
    int r3 = fcntl(a[0], F_DUPFD_CLOEXEC, 10), wp = fcntl(a[1], F_DUPFD_CLOEXEC, 10);
    int rp = fcntl(b[0], F_DUPFD_CLOEXEC, 10), w4 = fcntl(b[1], F_DUPFD_CLOEXEC, 10);
    int lg = lf >= 0 ? fcntl(lf, F_DUPFD_CLOEXEC, 10) : -1;
    close(a[0]); close(a[1]); close(b[0]); close(b[1]);
    if (lf >= 0) close(lf);
    lf = lg;
    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_addopen(&fa, 0, "/dev/null", O_RDONLY, 0);
    if (lf >= 0) { posix_spawn_file_actions_adddup2(&fa, lf, 1); posix_spawn_file_actions_adddup2(&fa, lf, 2); }
    else { posix_spawn_file_actions_addopen(&fa, 1, "/dev/null", O_WRONLY, 0); posix_spawn_file_actions_addopen(&fa, 2, "/dev/null", O_WRONLY, 0); }
    posix_spawn_file_actions_adddup2(&fa, r3, 3);
    posix_spawn_file_actions_adddup2(&fa, w4, 4);
    char *src = vu_cstr(js);
    if (!src) { posix_spawn_file_actions_destroy(&fa); close(r3); close(w4); close(wp); close(rp); if (lf >= 0) close(lf); return false; }
    char *argv[] = { "node", "--no-warnings", "--input-type=module", "-e", src, NULL };
    pid_t pid;
    int rc = posix_spawnp(&pid, "node", &fa, NULL, argv, environ);
    posix_spawn_file_actions_destroy(&fa);
    free(src);
    close(r3); close(w4);
    if (rc != 0) { close(wp); close(rp); if (lf >= 0) close(lf); return false; }
#ifdef F_SETNOSIGPIPE
    fcntl(wp, F_SETNOSIGPIPE, 1);
#endif
    w->pid = pid; w->in = wp; w->out = rp; w->log = lf;
    return true;
}

/* (a write to a node that died must not kill vknip with SIGPIPE) */
static bool vk_node_write(int fd, const char *p, size_t n) {
#ifndef F_SETNOSIGPIPE
    sigset_t set, old;
    sigemptyset(&set);
    sigaddset(&set, SIGPIPE);
    pthread_sigmask(SIG_BLOCK, &set, &old);
#endif
    bool ok = true;
    while (n > 0) {
        ssize_t w = write(fd, p, n);
        if (w < 0 && errno == EINTR) continue;
        if (w <= 0) { ok = false; break; }
        p += w; n -= (size_t)w;
    }
#ifndef F_SETNOSIGPIPE
    if (!ok) {
        struct timespec zero = { 0, 0 };
        sigset_t pend;
        sigpending(&pend);
        if (sigismember(&pend, SIGPIPE)) sigtimedwait(&set, NULL, &zero);
    }
    pthread_sigmask(SIG_SETMASK, &old, NULL);
#endif
    return ok;
}

static int vk_node_recv(vk_worker *w);

/* sends a request (starting the process if needed); false when that fails */
static bool vk_node_send(vk_worker *w, const vu_str *js, const char *req, size_t n) {
    if (w->warm) {
        w->warm = false;
        w->len = 0;
        int r;
        while ((r = vk_node_recv(w)) == 0) {}
    }
    if (w->pid < 0 && !vk_node_start(w, js)) return false;
    w->used = true;
    w->from = w->log >= 0 ? lseek(w->log, 0, SEEK_END) : 0;
    w->len = 0;
    if (vk_node_write(w->in, req, n) && vk_node_write(w->in, "\n", 1)) return true;
    vk_node_stop(w);
    return false;
}

/* reads what's there of the answer: 1 when it's complete (in w->buf, w->len, without the newline),
   0 when more is to come, -1 when the process died (then w->buf holds "!" and the first line it
   printed since the request) */
static int vk_node_recv(vk_worker *w) {
    if (w->cap - w->len < 65536) { w->cap = w->cap ? w->cap * 2 : 131072; w->buf = realloc(w->buf, w->cap); }
    ssize_t r;
    do r = read(w->out, w->buf + w->len, w->cap - w->len); while (r < 0 && errno == EINTR);
    if (r > 0) {
        size_t start = w->len;
        w->len += (size_t)r;
        char *nl = memchr(w->buf + start, '\n', (size_t)r);
        if (!nl) return 0;
        w->len = (size_t)(nl - w->buf);
        return 1;
    }
    w->len = 0;
    w->buf[w->len++] = '!';
    if (w->log >= 0 && w->from >= 0) {
        char tmp[4096];
        ssize_t k = pread(w->log, tmp, sizeof tmp, w->from);
        size_t m = 0;
        /* (the first line that isn't empty) */
        while (k > 0 && m < (size_t)k && (tmp[m] == '\n' || tmp[m] == ' ' || tmp[m] == '\t' || tmp[m] == '\r')) m++;
        while (k > 0 && m < (size_t)k && tmp[m] != '\n') w->buf[w->len++] = tmp[m++];
    }
    vk_node_stop(w);
    return -1;
}

/* Starts `workers` processes (if they aren't running) on a request that gets jiti ready, while vknip
   reads the project; the first real request reads its answer first. */
void vk_node_warm(const vu_str *js, const vu_str *req, int64_t workers) {
    for (int i = 0; i < workers && i < VK_MAXW; i++) {
        vk_worker *w = &vkw[i];
        if (w->pid >= 0 || !vk_node_start(w, js)) continue;
        w->from = w->log >= 0 ? lseek(w->log, 0, SEEK_END) : 0;
        if (vk_node_write(w->in, req->data, (size_t)req->len) && vk_node_write(w->in, "\n", 1)) w->warm = true;
        else vk_node_stop(w);
    }
}

/* The answer to one request (a line of JSON), or "!" and the first line node printed when it died
   before answering. An empty request stops the processes. */
vu_str vk_node(const vu_str *js, const vu_str *req) {
    vk_worker *w = &vkw[0];
    if (req->len == 0) { vk_node_atexit(); return vu_str_from("", 0); }
    if (!vk_node_send(w, js, req->data, (size_t)req->len)) return vu_str_from("!", 1);
    int r;
    while ((r = vk_node_recv(w)) == 0) {}
    return vu_str_from(w->buf, (int64_t)w->len);
}

/* Independent requests, one per line, spread over up to `workers` processes (each takes the next
   request when it has answered one); their answers, one per line in the same order. */
vu_str vk_node_par(const vu_str *js, const vu_str *reqs, int64_t workers) {
    size_t n = 0;
    const char *p = reqs->data, *e = reqs->data + reqs->len;
    for (const char *q = p; q < e; q++) if (*q == '\n') n++;
    if (reqs->len > 0 && e[-1] != '\n') n++;
    if (n == 0) return vu_str_from("", 0);
    const char **rs = malloc(n * sizeof *rs);
    size_t *rl = malloc(n * sizeof *rl);
    char **ans = calloc(n, sizeof *ans);
    size_t *al = calloc(n, sizeof *al);
    size_t k = 0;
    for (const char *q = p; q < e && k < n;) {
        const char *nl = memchr(q, '\n', (size_t)(e - q));
        if (!nl) nl = e;
        rs[k] = q; rl[k] = (size_t)(nl - q); k++;
        q = nl + 1;
    }
    int W = (int)(workers < 1 ? 1 : workers > VK_MAXW ? VK_MAXW : workers);
    if ((size_t)W > n) W = (int)n;
    long cur[VK_MAXW];
    for (int i = 0; i < W; i++) cur[i] = -1;
    size_t next = 0, done = 0;
    while (done < n) {
        /* each idle process takes the next request */
        for (int i = 0; i < W && next < n; i++) {
            if (cur[i] >= 0) continue;
            size_t j = next++;
            if (vk_node_send(&vkw[i], js, rs[j], rl[j])) cur[i] = (long)j;
            else { ans[j] = strdup("!"); al[j] = 1; done++; }
        }
        struct pollfd pf[VK_MAXW];
        int idx[VK_MAXW], np = 0;
        for (int i = 0; i < W; i++) if (cur[i] >= 0) { pf[np].fd = vkw[i].out; pf[np].events = POLLIN; pf[np].revents = 0; idx[np++] = i; }
        if (np == 0) continue;
        if (poll(pf, (nfds_t)np, -1) < 0) { if (errno == EINTR) continue; break; }
        for (int m = 0; m < np; m++) {
            if (!pf[m].revents) continue;
            int i = idx[m];
            int r = vk_node_recv(&vkw[i]);
            if (r == 0) continue;
            size_t j = (size_t)cur[i];
            ans[j] = malloc(vkw[i].len + 1);
            memcpy(ans[j], vkw[i].buf, vkw[i].len);
            al[j] = vkw[i].len;
            cur[i] = -1;
            done++;
        }
    }
    size_t tot = 0;
    for (size_t j = 0; j < n; j++) tot += (ans[j] ? al[j] : 1) + 1;
    char *out = malloc(tot + 1);
    size_t o = 0;
    for (size_t j = 0; j < n; j++) {
        if (ans[j]) { memcpy(out + o, ans[j], al[j]); o += al[j]; free(ans[j]); }
        else out[o++] = '!';
        out[o++] = '\n';
    }
    vu_str res = vu_str_from(out, (int64_t)o);
    free(out); free(ans); free(al); free(rs); free(rl);
    return res;
}
