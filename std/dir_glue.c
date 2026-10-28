/* Folders for std/dir.vu: a Dir is an open folder, and every path given to it is resolved inside
   that folder by the kernel, so neither "..", nor a symlink, nor a folder renamed in the middle of
   an operation can reach a file outside it.

   Linux: openat2() with RESOLVE_BENEATH (5.6 and later): ".." and symlinks are followed only while
   they stay inside, and an absolute symlink is refused. Elsewhere (or on an older kernel) the path
   is walked one name at a time with openat(O_NOFOLLOW), and any symlink or ".." on the way is
   refused: stricter, but never outside.

   Errors read like Node's ("ENOENT: no such file or directory"), so the MCP filesystem server can
   report them as the reference server does; dir.vu adds the operation and the path. */
#include <dirent.h>
#include <limits.h>
#include <fcntl.h>
#include <sys/stat.h>
#ifdef __linux__
#include <sys/syscall.h>
#endif

typedef struct { int fd; char *path; } vdir;

static void vdir_close(void *p) {
    vdir *d = (vdir *)p;
    close(d->fd);
    free(d->path);
    free(d);
}

/* libuv's names and messages for the errors a file operation meets (uv_err_name, uv_strerror) */
static vu_str vdir_err(int e) {
    const char *n = NULL, *m = NULL;
    switch (e) {
    case ENOENT: n = "ENOENT"; m = "no such file or directory"; break;
    case EACCES: n = "EACCES"; m = "permission denied"; break;
    case EPERM: n = "EPERM"; m = "operation not permitted"; break;
    case EEXIST: n = "EEXIST"; m = "file already exists"; break;
    case ENOTDIR: n = "ENOTDIR"; m = "not a directory"; break;
    case EISDIR: n = "EISDIR"; m = "illegal operation on a directory"; break;
    case ENOTEMPTY: n = "ENOTEMPTY"; m = "directory not empty"; break;
    case ELOOP: n = "ELOOP"; m = "too many symbolic links encountered"; break;
    case ENAMETOOLONG: n = "ENAMETOOLONG"; m = "name too long"; break;
    case ENOSPC: n = "ENOSPC"; m = "no space left on device"; break;
    case EROFS: n = "EROFS"; m = "read-only file system"; break;
    case EXDEV: n = "EXDEV"; m = "cross-device link not permitted"; break;
    case EBUSY: n = "EBUSY"; m = "resource busy or locked"; break;
    case EINVAL: n = "EINVAL"; m = "invalid argument"; break;
    case EMFILE: n = "EMFILE"; m = "too many open files"; break;
    case EIO: n = "EIO"; m = "i/o error"; break;
    case EFBIG: n = "EFBIG"; m = "file too large"; break;
    case ETXTBSY: n = "ETXTBSY"; m = "text file is busy"; break;
    case EAGAIN: n = "EAGAIN"; m = "resource temporarily unavailable"; break;
    default: break;
    }
    if (n) return vu_errf("%s: %s", n, m);
    return vu_errf("E%d: %s", e, strerror(e));
}

/* The path, as C text: no zero byte, and relative (it names something inside the folder). */
static char *vdir_rel(const vu_str *rel, vu_str *err) {
    char *p = vu_cstr(rel);
    if (!p) { *err = vu_errf("EINVAL: a path can't contain a zero byte"); return NULL; }
    if (p[0] == '/') { free(p); *err = vu_errf("EINVAL: a path in a folder is relative, not '/...'"); return NULL; }
    return p;
}

/* openat() of each name in turn, refusing symlinks and "..": the portable way to stay inside. */
static int vdir_walk(int root, const char *rel, int flags, mode_t mode) {
    int cur = root;
    const char *s = rel;
    char name[NAME_MAX + 1];
    for (;;) {
        while (*s == '/') s++;
        const char *e = s;
        while (*e && *e != '/') e++;
        const char *next = e;
        while (*next == '/') next++;
        bool last = *next == 0;
        size_t n = (size_t)(e - s);
        if (n == 0) {   /* "" or "." or a path ending in '/': the folder reached so far */
            int fd = openat(cur, ".", (flags & ~(O_CREAT | O_EXCL | O_TRUNC)) | O_CLOEXEC, mode);
            if (cur != root) close(cur);
            return fd;
        }
        if (n > NAME_MAX) { if (cur != root) close(cur); errno = ENAMETOOLONG; return -1; }
        memcpy(name, s, n);
        name[n] = 0;
        if (strcmp(name, "..") == 0) { if (cur != root) close(cur); errno = EXDEV; return -1; }
        if (strcmp(name, ".") == 0 && !last) { s = next; continue; }
        int fd;
        if (last) fd = openat(cur, name, flags | O_NOFOLLOW | O_CLOEXEC, mode);
        else fd = openat(cur, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
        int saved = errno;
        if (cur != root) close(cur);
        if (fd < 0) { errno = saved; return -1; }
        if (last) return fd;
        cur = fd;
        s = next;
    }
}

#if defined(__linux__) && defined(SYS_openat2)
struct vdir_how { uint64_t flags, mode, resolve; };
#define VDIR_BENEATH 0x08
#define VDIR_NO_MAGICLINKS 0x02
#endif

/* An open file descriptor for rel inside d (O_PATH-like flags allowed on Linux), or -1 with errno. */
static int vdir_at(vdir *d, const char *rel, int flags, mode_t mode) {
    if (!*rel) rel = ".";
#if defined(__linux__) && defined(SYS_openat2)
    static int no_openat2 = -1;   /* -1: not decided yet; VU_DIR_WALK=1 tests the portable walk */
    if (__atomic_load_n(&no_openat2, __ATOMIC_RELAXED) < 0) {
        const char *w = getenv("VU_DIR_WALK");
        __atomic_store_n(&no_openat2, w && w[0] == '1' ? 1 : 0, __ATOMIC_RELAXED);
    }
    if (!__atomic_load_n(&no_openat2, __ATOMIC_RELAXED)) {
        struct vdir_how how;
        memset(&how, 0, sizeof how);
        how.flags = (uint64_t)(flags | O_CLOEXEC);
        how.mode = (flags & O_CREAT) ? (uint64_t)mode : 0;
        how.resolve = VDIR_BENEATH | VDIR_NO_MAGICLINKS;
        for (int tries = 0; tries < 64; tries++) {
            long fd = syscall(SYS_openat2, d->fd, rel, &how, sizeof how);
            if (fd >= 0) return (int)fd;
            if (errno == EAGAIN || errno == EINTR) continue;   /* a rename raced the lookup */
            if (errno == ENOSYS || errno == EPERM) break;      /* no openat2 (or a seccomp filter) */
            return -1;
        }
        if (errno != EAGAIN && errno != EINTR) __atomic_store_n(&no_openat2, 1, __ATOMIC_RELAXED);
        else { errno = EAGAIN; return -1; }
    }
#endif
#ifdef O_PATH
    if (flags & O_PATH) flags = (flags & ~O_PATH) | O_RDONLY;   /* the walk opens for reading instead */
#endif
    return vdir_walk(d->fd, rel, flags, mode);
}

/* rel split into its folder (opened, inside d) and its last name, which must be a real name. */
static int vdir_parent(vdir *d, const char *rel, char *leaf, vu_str *err) {
    size_t n = strlen(rel);
    while (n > 0 && rel[n - 1] == '/') n--;
    size_t k = n;
    while (k > 0 && rel[k - 1] != '/') k--;
    size_t ln = n - k;
    if (ln == 0 || ln > NAME_MAX) { *err = vdir_err(ln == 0 ? EINVAL : ENAMETOOLONG); return -1; }
    memcpy(leaf, rel + k, ln);
    leaf[ln] = 0;
    if (strcmp(leaf, ".") == 0 || strcmp(leaf, "..") == 0) { *err = vdir_err(EINVAL); return -1; }
    char *pp = (char *)vu_malloc(k + 2);
    memcpy(pp, rel, k);
    pp[k] = 0;
#ifdef O_PATH
    int fd = vdir_at(d, pp, O_PATH | O_DIRECTORY, 0);
#else
    int fd = vdir_at(d, pp, O_RDONLY | O_DIRECTORY, 0);
#endif
    free(pp);
    if (fd < 0) *err = vdir_err(errno);
    return fd;
}

static bool vdir_open(const vu_str *path, void **out, vu_str *err) {
    char *p = vu_cstr(path);
    if (!p) { *err = vu_errf("EINVAL: a path can't contain a zero byte"); return false; }
    int fd = open(p, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (fd < 0) { *err = vdir_err(errno); free(p); return false; }
    char *real = realpath(p, NULL);
    free(p);
    if (!real) { *err = vdir_err(errno); close(fd); return false; }
    vdir *d = (vdir *)vu_malloc(sizeof(vdir));
    d->fd = fd;
    d->path = real;
    *out = d;
    return true;
}

static vu_str vdir_path(void *h) { return vu_str_from_c(((vdir *)h)->path); }

/* Only regular files are read or written: a FIFO would block forever, a device is never wanted.
   Opened with O_NONBLOCK so opening a FIFO doesn't block either, then checked. */
static int vdir_regular(vdir *d, const char *rel, int flags, mode_t mode, vu_str *err) {
    int fd = vdir_at(d, rel, flags | O_NONBLOCK, mode);
    if (fd < 0) { *err = vdir_err(errno); return -1; }
    struct stat st;
    if (fstat(fd, &st) != 0) { *err = vdir_err(errno); close(fd); return -1; }
    if (!S_ISREG(st.st_mode)) {
        close(fd);
        *err = S_ISDIR(st.st_mode) ? vdir_err(EISDIR) : vu_errf("EINVAL: not a regular file");
        return -1;
    }
    int fl = fcntl(fd, F_GETFL);
    if (fl >= 0) fcntl(fd, F_SETFL, fl & ~O_NONBLOCK);
    return fd;
}

static bool vdir_read(void *h, const vu_str *rel, vu_str *out, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    int fd = vdir_regular((vdir *)h, r, O_RDONLY, 0, err);
    free(r);
    if (fd < 0) return false;
    vu_str s = {0};
    uint8_t buf[65536];
    for (;;) {
        ssize_t k = read(fd, buf, sizeof buf);
        if (k < 0 && errno == EINTR) continue;
        if (k < 0) { *err = vdir_err(errno); drop_Str(&s); close(fd); return false; }
        if (k == 0) break;
        vu_str_cat_bytes(&s, buf, k);
    }
    close(fd);
    *out = s;
    return true;
}

/* Creates the file or replaces what's in it, in place (the same inode, so its links, permissions and
   creation time stay). A symlink as the last name is refused (O_NOFOLLOW), so nothing is written
   through one. */
static bool vdir_write(void *h, const vu_str *rel, const vu_str *data, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    int fd = vdir_regular((vdir *)h, r, O_WRONLY | O_CREAT | O_NOFOLLOW, 0666, err);
    free(r);
    if (fd < 0) return false;
    if (ftruncate(fd, 0) != 0) { *err = vdir_err(errno); close(fd); return false; }
    int64_t off = 0;
    while (off < data->len) {
        ssize_t k = write(fd, data->data + off, (size_t)(data->len - off));
        if (k < 0 && errno == EINTR) continue;
        if (k < 0) { *err = vdir_err(errno); close(fd); return false; }
        off += k;
    }
    if (close(fd) != 0) { *err = vdir_err(errno); return false; }
    return true;
}

typedef struct { char kind; char *name; } vdir_ent;
static int vdir_ent_cmp(const void *a, const void *b) {
    return strcmp(((const vdir_ent *)a)->name, ((const vdir_ent *)b)->name);
}

/* The folder's entries, sorted byte by byte (as libuv's scandir sorts them for Node), each as
   its kind ('d' folder, 'f' file, 'l' symlink, 'o' anything else, as the entry itself is: a symlink
   isn't followed), its name and a zero byte. */
static bool vdir_list(void *h, const vu_str *rel, vu_str *out, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    int fd = vdir_at((vdir *)h, r, O_RDONLY | O_DIRECTORY, 0);
    free(r);
    if (fd < 0) { *err = vdir_err(errno); return false; }
    DIR *dp = fdopendir(fd);
    if (!dp) { *err = vdir_err(errno); close(fd); return false; }
    vdir_ent *es = NULL;
    size_t n = 0, cap = 0;
    struct dirent *de;
    errno = 0;
    while ((de = readdir(dp)) != NULL) {
        if (strcmp(de->d_name, ".") == 0 || strcmp(de->d_name, "..") == 0) continue;
        char k = 'o';
        unsigned char t = de->d_type;
        if (t == DT_UNKNOWN) {
            struct stat st;
            if (fstatat(dirfd(dp), de->d_name, &st, AT_SYMLINK_NOFOLLOW) == 0) {
                if (S_ISDIR(st.st_mode)) t = DT_DIR;
                else if (S_ISREG(st.st_mode)) t = DT_REG;
                else if (S_ISLNK(st.st_mode)) t = DT_LNK;
            }
        }
        if (t == DT_DIR) k = 'd';
        else if (t == DT_REG) k = 'f';
        else if (t == DT_LNK) k = 'l';
        if (n == cap) {
            cap = cap ? cap * 2 : 64;
            vdir_ent *ne = (vdir_ent *)vu_malloc(cap * sizeof(vdir_ent));
            if (n) memcpy(ne, es, n * sizeof(vdir_ent));
            free(es);
            es = ne;
        }
        size_t ln = strlen(de->d_name);
        es[n].kind = k;
        es[n].name = (char *)vu_malloc(ln + 1);
        memcpy(es[n].name, de->d_name, ln + 1);
        n++;
        errno = 0;
    }
    int rerr = errno;
    closedir(dp);
    if (rerr) {
        for (size_t i = 0; i < n; i++) free(es[i].name);
        free(es);
        *err = vdir_err(rerr);
        return false;
    }
    if (n > 1) qsort(es, n, sizeof(vdir_ent), vdir_ent_cmp);
    vu_str s = {0};
    for (size_t i = 0; i < n; i++) {
        vu_str_cat_bytes(&s, (const uint8_t *)&es[i].kind, 1);
        vu_str_cat_bytes(&s, (const uint8_t *)es[i].name, (int64_t)strlen(es[i].name));
        vu_str_cat_bytes(&s, (const uint8_t *)"", 1);
        free(es[i].name);
    }
    free(es);
    *out = s;
    return true;
}

static void vdir_cat_time(vu_str *s, int64_t sec, int64_t nsec) {
    char b[64];
    int m = snprintf(b, sizeof b, " %lld.%09lld", (long long)sec, (long long)nsec);
    vu_str_cat_bytes(s, (const uint8_t *)b, m);
}

/* What rel is: "kind size mode modified accessed changed created", the times in seconds since 1970
   with nine decimals (created is "-1" where the file system doesn't record it). follow: a symlink as
   the last name is followed (inside the folder only), else it's described itself. */
static bool vdir_info(void *h, const vu_str *rel, bool follow, vu_str *out, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    vdir *d = (vdir *)h;
    int fd = -1;
    char leaf[NAME_MAX + 1];
    const char *at = "";
    int atflags = 0;
    bool whole = true;   /* rel is the folder itself */
    for (const char *c = r; *c; c++) if (*c != '/' && *c != '.') whole = false;
    if (follow || whole) {
#ifdef O_PATH
        fd = vdir_at(d, r, O_PATH, 0);
#else
        fd = vdir_at(d, r, O_RDONLY | O_NONBLOCK, 0);
#endif
        if (fd < 0) { *err = vdir_err(errno); free(r); return false; }
    } else {
        fd = vdir_parent(d, r, leaf, err);
        if (fd < 0) { free(r); return false; }
        at = leaf;
        atflags = AT_SYMLINK_NOFOLLOW;
    }
    free(r);
    char kind = 'o';
    int64_t size = 0, mode = 0;
    int64_t ts[8];
    for (int i = 0; i < 8; i++) ts[i] = 0;
    int64_t bsec = -1, bnsec = 0;
#if defined(__linux__) && defined(STATX_BTIME)
    struct statx sx;
    int rc = statx(fd, at, atflags | (at[0] ? 0 : AT_EMPTY_PATH), STATX_BASIC_STATS | STATX_BTIME, &sx);
    if (rc != 0) { *err = vdir_err(errno); close(fd); return false; }
    mode = sx.stx_mode;
    size = (int64_t)sx.stx_size;
    ts[0] = sx.stx_mtime.tv_sec; ts[1] = sx.stx_mtime.tv_nsec;
    ts[2] = sx.stx_atime.tv_sec; ts[3] = sx.stx_atime.tv_nsec;
    ts[4] = sx.stx_ctime.tv_sec; ts[5] = sx.stx_ctime.tv_nsec;
    if (sx.stx_mask & STATX_BTIME) { bsec = sx.stx_btime.tv_sec; bnsec = sx.stx_btime.tv_nsec; }
#else
    struct stat st;
    int rc = at[0] ? fstatat(fd, at, &st, atflags) : fstat(fd, &st);
    if (rc != 0) { *err = vdir_err(errno); close(fd); return false; }
    mode = st.st_mode;
    size = (int64_t)st.st_size;
#ifdef __APPLE__
    ts[0] = st.st_mtimespec.tv_sec; ts[1] = st.st_mtimespec.tv_nsec;
    ts[2] = st.st_atimespec.tv_sec; ts[3] = st.st_atimespec.tv_nsec;
    ts[4] = st.st_ctimespec.tv_sec; ts[5] = st.st_ctimespec.tv_nsec;
    bsec = st.st_birthtimespec.tv_sec; bnsec = st.st_birthtimespec.tv_nsec;
#else
    ts[0] = st.st_mtim.tv_sec; ts[1] = st.st_mtim.tv_nsec;
    ts[2] = st.st_atim.tv_sec; ts[3] = st.st_atim.tv_nsec;
    ts[4] = st.st_ctim.tv_sec; ts[5] = st.st_ctim.tv_nsec;
#endif
#endif
    close(fd);
    if (S_ISDIR(mode)) kind = 'd';
    else if (S_ISREG(mode)) kind = 'f';
    else if (S_ISLNK(mode)) kind = 'l';
    vu_str s = {0};
    char b[64];
    int m = snprintf(b, sizeof b, "%c %lld %lld", kind, (long long)size, (long long)(mode & 07777));
    vu_str_cat_bytes(&s, (const uint8_t *)b, m);
    vdir_cat_time(&s, ts[0], ts[1]);
    vdir_cat_time(&s, ts[2], ts[3]);
    vdir_cat_time(&s, ts[4], ts[5]);
    if (bsec < 0) vu_str_cat_bytes(&s, (const uint8_t *)" -1", 3);
    else vdir_cat_time(&s, bsec, bnsec);
    *out = s;
    return true;
}

/* mkdir -p, one name at a time, each inside the folder; a folder that's already there is fine. */
static bool vdir_mkdir(void *h, const vu_str *rel, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    vdir *d = (vdir *)h;
    size_t n = strlen(r);
    for (size_t i = 0; i <= n; i++) {
        if (i < n && r[i] != '/') continue;
        if (i == 0 || r[i - 1] == '/') continue;
        char save = r[i];
        r[i] = 0;
#ifdef O_PATH
        int fd = vdir_at(d, r, O_PATH | O_DIRECTORY, 0);
#else
        int fd = vdir_at(d, r, O_RDONLY | O_DIRECTORY, 0);
#endif
        if (fd >= 0) { close(fd); r[i] = save; continue; }
        if (errno != ENOENT) { *err = vdir_err(errno); free(r); return false; }
        char leaf[NAME_MAX + 1];
        int pfd = vdir_parent(d, r, leaf, err);
        if (pfd < 0) { free(r); return false; }
        int rc = mkdirat(pfd, leaf, 0777);
        int e = errno;
        close(pfd);
        if (rc != 0 && e != EEXIST) { *err = vdir_err(e); free(r); return false; }
        if (rc != 0) {   /* made by someone else meanwhile: it must be a folder */
#ifdef O_PATH
            fd = vdir_at(d, r, O_PATH | O_DIRECTORY, 0);
#else
            fd = vdir_at(d, r, O_RDONLY | O_DIRECTORY, 0);
#endif
            if (fd < 0) { *err = vdir_err(errno); free(r); return false; }
            close(fd);
        }
        r[i] = save;
    }
    free(r);
    return true;
}

/* Moves rel (in d) to rel2 (in d2); fails if something is already at rel2, without replacing it. */
static bool vdir_rename(void *h, const vu_str *rel, void *h2, const vu_str *rel2, vu_str *err) {
    char *a = vdir_rel(rel, err);
    if (!a) return false;
    char *b = vdir_rel(rel2, err);
    if (!b) { free(a); return false; }
    char la[NAME_MAX + 1], lb[NAME_MAX + 1];
    int pa = vdir_parent((vdir *)h, a, la, err);
    int pb = pa < 0 ? -1 : vdir_parent((vdir *)h2, b, lb, err);
    free(a);
    free(b);
    if (pa < 0 || pb < 0) { if (pa >= 0) close(pa); return false; }
    int rc;
#if defined(__linux__) && defined(SYS_renameat2)
    rc = (int)syscall(SYS_renameat2, pa, la, pb, lb, 1 /* RENAME_NOREPLACE */);
    if (rc != 0 && (errno == EINVAL || errno == ENOSYS)) {
        /* a file system without RENAME_NOREPLACE: link-free fallback, checked first (a small race) */
        struct stat st;
        if (fstatat(pb, lb, &st, AT_SYMLINK_NOFOLLOW) == 0) { errno = EEXIST; rc = -1; }
        else rc = renameat(pa, la, pb, lb);
    }
#elif defined(__APPLE__) && defined(RENAME_EXCL)
    rc = renameatx_np(pa, la, pb, lb, RENAME_EXCL);
#else
    struct stat st;
    if (fstatat(pb, lb, &st, AT_SYMLINK_NOFOLLOW) == 0) { errno = EEXIST; rc = -1; }
    else rc = renameat(pa, la, pb, lb);
#endif
    int e = errno;
    close(pa);
    close(pb);
    if (rc != 0) { *err = vdir_err(e); return false; }
    return true;
}

/* Removes a file, a symlink (not what it points to) or an empty folder. */
static bool vdir_remove(void *h, const vu_str *rel, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    char leaf[NAME_MAX + 1];
    int pfd = vdir_parent((vdir *)h, r, leaf, err);
    free(r);
    if (pfd < 0) return false;
    struct stat st;
    int rc = fstatat(pfd, leaf, &st, AT_SYMLINK_NOFOLLOW);
    if (rc == 0) rc = unlinkat(pfd, leaf, S_ISDIR(st.st_mode) ? AT_REMOVEDIR : 0);
    int e = errno;
    close(pfd);
    if (rc != 0) { *err = vdir_err(e); return false; }
    return true;
}

/* Where rel really is: its absolute path with every symlink resolved (it is inside the folder). */
static bool vdir_real(void *h, const vu_str *rel, vu_str *out, vu_str *err) {
    char *r = vdir_rel(rel, err);
    if (!r) return false;
    vdir *d = (vdir *)h;
#ifdef O_PATH
    int fd = vdir_at(d, r, O_PATH, 0);
#else
    int fd = vdir_at(d, r, O_RDONLY | O_NONBLOCK, 0);
#endif
    if (fd < 0) { *err = vdir_err(errno); free(r); return false; }
    char buf[PATH_MAX + 1];
    bool ok = false;
#ifdef __linux__
    char link[64];
    snprintf(link, sizeof link, "/proc/self/fd/%d", fd);
    ssize_t k = readlink(link, buf, PATH_MAX);
    if (k > 0 && buf[0] == '/') { buf[k] = 0; ok = true; }
#elif defined(F_GETPATH)
    if (fcntl(fd, F_GETPATH, buf) == 0) ok = true;
#endif
    close(fd);
    if (!ok) {
        /* no way to ask the kernel: the folder's path and rel, which the walk confirmed has no symlinks */
        vu_str s = vu_str_from_c(d->path);
        if (*r && strcmp(r, ".") != 0) {
            vu_str_cat_bytes(&s, (const uint8_t *)"/", 1);
            vu_str_cat_bytes(&s, (const uint8_t *)r, (int64_t)strlen(r));
        }
        free(r);
        *out = s;
        return true;
    }
    free(r);
    *out = vu_str_from_c(buf);
    return true;
}
