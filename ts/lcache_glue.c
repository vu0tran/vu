// vlint's result cache: a file's size, modification and change times (ns) and inode, and the clock.
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef __APPLE__
#define st_mtim st_mtimespec
#define st_ctim st_ctimespec
#endif

bool vl_stat(const vu_str *path, int64_t *out, int64_t n) {
  if (n < 4) return false;
  char buf[4096];
  char *p = buf;
  if (path->len >= (int64_t)sizeof buf) { p = vu_cstr(path); if (!p) return false; }
  else {
    if (memchr(path->data, 0, (size_t)path->len)) return false;
    memcpy(buf, path->data, (size_t)path->len);
    buf[path->len] = 0;
  }
  struct stat st;
  int r = stat(p, &st);
  if (p != buf) free(p);
  if (r != 0 || !S_ISREG(st.st_mode)) return false;
  out[0] = (int64_t)st.st_size;
  out[1] = (int64_t)st.st_mtim.tv_sec * 1000000000 + st.st_mtim.tv_nsec;
  out[2] = (int64_t)st.st_ctim.tv_sec * 1000000000 + st.st_ctim.tv_nsec;
  out[3] = (int64_t)st.st_ino;
  return true;
}

// Whether a path's modification or change time is at t (ns) or later ("racy": a state a cache
// can't trust yet, as git has it); false when it isn't there.
bool vl_changed_since(const vu_str *path, int64_t t) {
  char buf[4096];
  char *p = buf;
  if (path->len >= (int64_t)sizeof buf) { p = vu_cstr(path); if (!p) return false; }
  else {
    if (memchr(path->data, 0, (size_t)path->len)) return false;
    memcpy(buf, path->data, (size_t)path->len);
    buf[path->len] = 0;
  }
  struct stat st;
  int r = stat(p, &st);
  if (p != buf) free(p);
  if (r != 0) return false;
  int64_t m = (int64_t)st.st_mtim.tv_sec * 1000000000 + st.st_mtim.tv_nsec;
  int64_t c = (int64_t)st.st_ctim.tv_sec * 1000000000 + st.st_ctim.tv_nsec;
  return m >= t || c >= t;
}

// A file's or folder's modification time (ns) mixed with its size and inode, 0 when it isn't there.
int64_t vl_stat_any(const vu_str *path) {
  char buf[4096];
  char *p = buf;
  if (path->len >= (int64_t)sizeof buf) { p = vu_cstr(path); if (!p) return 0; }
  else {
    if (memchr(path->data, 0, (size_t)path->len)) return 0;
    memcpy(buf, path->data, (size_t)path->len);
    buf[path->len] = 0;
  }
  struct stat st;
  int r = stat(p, &st);
  if (p != buf) free(p);
  if (r != 0) return 0;
  uint64_t h = (uint64_t)st.st_mtim.tv_sec * 1000000000u + (uint64_t)st.st_mtim.tv_nsec;
  h = h * 0x9E3779B97F4A7C15u ^ (uint64_t)st.st_size;
  h = h * 0x9E3779B97F4A7C15u ^ (uint64_t)st.st_ino;
  h = h * 0x9E3779B97F4A7C15u ^ ((uint64_t)st.st_ctim.tv_sec * 1000000000u + (uint64_t)st.st_ctim.tv_nsec);
  return (int64_t)(h | 1);
}

int64_t vl_now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  return (int64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}

// The CPUs this process may use: the online ones, on Linux fewer when its affinity mask or its
// cgroup's CPU quota (v2 cpu.max, v1 cpu.cfs_quota_us) allows fewer. (A container's limit shows in
// neither /proc/cpuinfo nor the affinity mask: a CI pod limited to a few CPUs of a large node saw
// all of the node's.)
#ifdef __linux__
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static long vl_quota_cpus(void) {
  FILE *f = fopen("/sys/fs/cgroup/cpu.max", "r");
  long long q = -1, per = 0;
  if (f) {
    char a[64] = {0};
    if (fscanf(f, "%63s %lld", a, &per) == 2 && strcmp(a, "max") != 0) q = atoll(a);
    fclose(f);
  } else {
    f = fopen("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", "r");
    if (f) { if (fscanf(f, "%lld", &q) != 1) q = -1; fclose(f); }
    f = fopen("/sys/fs/cgroup/cpu/cpu.cfs_period_us", "r");
    if (f) { if (fscanf(f, "%lld", &per) != 1) per = 0; fclose(f); }
  }
  if (q <= 0 || per <= 0) return -1;
  return (long)((q + per - 1) / per);
}
#endif
int64_t vl_ncpu(void) {
  long n = sysconf(_SC_NPROCESSORS_ONLN);
#ifdef __linux__
  cpu_set_t cs;
  if (sched_getaffinity(0, sizeof cs, &cs) == 0) {
    long a = CPU_COUNT(&cs);
    if (a > 0 && (n <= 0 || a < n)) n = a;
  }
  long q = vl_quota_cpus();
  if (q > 0 && (n <= 0 || q < n)) n = q;
#endif
  return n > 0 ? (int64_t)n : 1;
}

// For values a process hands its workers through the environment (VLINT_BUILD_ID).
void vl_setenv(const vu_str *name, const vu_str *value) {
  char k[256], v[256];
  if (name->len <= 0 || name->len >= (int64_t)sizeof k || value->len >= (int64_t)sizeof v) return;
  memcpy(k, name->data, (size_t)name->len);
  k[name->len] = 0;
  memcpy(v, value->data, (size_t)value->len);
  v[value->len] = 0;
  setenv(k, v, 1);
}


// For the command line: whether a descriptor is a terminal, the working directory, a real path.
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdlib.h>

bool vl_isatty(int64_t fd) { return isatty((int)fd) == 1; }

vu_str vl_cwd(void) {
  char buf[PATH_MAX];
  if (!getcwd(buf, sizeof buf)) return vu_str_from("", 0);
  return vu_str_from(buf, (int64_t)strlen(buf));
}

vu_str vl_realpath(const vu_str *path) {
  char *p = vu_cstr(path);
  if (!p) return vu_str_from("", 0);
  char buf[PATH_MAX];
  char *r = realpath(p, buf);
  free(p);
  if (!r) return vu_str_from("", 0);
  return vu_str_from(buf, (int64_t)strlen(buf));
}

// The running executable's full path (its links resolved), or "".
#ifdef __APPLE__
#include <mach-o/dyld.h>
#endif
vu_str vl_self_exe(void) {
  char buf[PATH_MAX];
#ifdef __APPLE__
  char raw[PATH_MAX];
  uint32_t n = sizeof raw;
  if (_NSGetExecutablePath(raw, &n) != 0) return vu_str_from("", 0);
  if (!realpath(raw, buf)) return vu_str_from("", 0);
#else
  if (!realpath("/proc/self/exe", buf)) return vu_str_from("", 0);
#endif
  return vu_str_from(buf, (int64_t)strlen(buf));
}

// Whether a path is a symbolic link (lstat).
bool vl_is_link(const vu_str *path) {
  char *p = vu_cstr(path);
  if (!p) return false;
  struct stat st;
  int r = lstat(p, &st);
  free(p);
  return r == 0 && S_ISLNK(st.st_mode);
}

// A folder's entries in the order the file system gives them (as oxlint's walker sees them), each
// followed by "\n"; folders end with "/" (symbolic links are followed). "" when it can't be read.
#include <dirent.h>
vu_str vl_readdir(const vu_str *path) {
  char *p = vu_cstr(path);
  if (!p) return vu_str_from("", 0);
  DIR *d = opendir(p);
  if (!d) { free(p); return vu_str_from("", 0); }
  size_t cap = 4096, len = 0;
  char *buf = malloc(cap);
  size_t plen = strlen(p);
  struct dirent *e;
  while ((e = readdir(d)) != NULL) {
    const char *nm = e->d_name;
    if (nm[0] == '.' && (nm[1] == 0 || (nm[1] == '.' && nm[2] == 0))) continue;
    int is_dir = 0;
    if (e->d_type == DT_DIR) is_dir = 1;
    else if (e->d_type == DT_LNK || e->d_type == DT_UNKNOWN) {
      size_t n = plen + 1 + strlen(nm) + 1;
      char *full = malloc(n);
      snprintf(full, n, "%s/%s", p, nm);
      struct stat st;
      if (stat(full, &st) == 0 && S_ISDIR(st.st_mode)) is_dir = 1;
      free(full);
    }
    size_t nl = strlen(nm);
    while (len + nl + 3 > cap) { cap *= 2; buf = realloc(buf, cap); }
    memcpy(buf + len, nm, nl); len += nl;
    if (is_dir) buf[len++] = '/';
    buf[len++] = '\n';
  }
  closedir(d);
  free(p);
  vu_str r = vu_str_from(buf, (int64_t)len);
  free(buf);
  return r;
}

// The checker's workers as processes (tsprog.run_all): forked after the program is read, parsed and
// bound, so each shares that copy-on-write instead of making its own. Only where this process has
// one thread: another's locks (malloc's among them) would stay held in the child.
#include <sys/wait.h>
#include <sys/mman.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#ifdef __APPLE__
#include <mach/mach.h>
#endif
static int vl_child_flag = 0;

int64_t vl_threads(void) {
#ifdef __APPLE__
  thread_act_array_t list;
  mach_msg_type_number_t n = 0;
  if (task_threads(mach_task_self(), &list, &n) != KERN_SUCCESS) return -1;
  for (mach_msg_type_number_t i = 0; i < n; i++) mach_port_deallocate(mach_task_self(), list[i]);
  vm_deallocate(mach_task_self(), (vm_address_t)list, sizeof(thread_t) * n);
  return (int64_t)n;
#else
  FILE *f = fopen("/proc/self/status", "r");
  if (!f) return -1;
  char line[256];
  int64_t n = -1;
  while (fgets(line, sizeof line, f)) {
    if (strncmp(line, "Threads:", 8) == 0) { n = atoll(line + 8); break; }
  }
  fclose(f);
  return n;
#endif
}

int64_t vl_fork(void) {
  fflush(stdout);
  fflush(stderr);
  pid_t p = fork();
  if (p == 0) vl_child_flag = 1;
  return (int64_t)p;
}

bool vl_is_child(void) { return vl_child_flag != 0; }

// n flags (zero) that processes forked after they're made share (an anonymous shared mapping):
// forked workers claiming work items. 0 when they can't be made.
int64_t vl_shared_flags(int64_t n) {
  if (n < 1) n = 1;
  void *p = mmap(NULL, (size_t)n * 8, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
  if (p == MAP_FAILED) return 0;
  return (int64_t)(intptr_t)p;
}
// flag i set by this call (a compare-and-swap from 0): whether it was this call that set it
bool vl_flag_claim(int64_t at, int64_t i) {
  int64_t old = 0;
  return __atomic_compare_exchange_n((int64_t *)(intptr_t)at + i, &old, 1, false, __ATOMIC_RELAXED, __ATOMIC_RELAXED);
}
int64_t vl_flag_get(int64_t at, int64_t i) { return __atomic_load_n((int64_t *)(intptr_t)at + i, __ATOMIC_RELAXED); }
void vl_flag_set(int64_t at, int64_t i, int64_t v) { __atomic_store_n((int64_t *)(intptr_t)at + i, v, __ATOMIC_RELAXED); }
void vl_flags_free(int64_t at, int64_t n) {
  if (n < 1) n = 1;
  if (at != 0) munmap((void *)(intptr_t)at, (size_t)n * 8);
}

// A child's exit status (128 + the signal that stopped it; -1 when it can't be waited for).
int64_t vl_wait(int64_t pid) {
  int st = 0;
  pid_t r;
  do { r = waitpid((pid_t)pid, &st, 0); } while (r < 0 && errno == EINTR);
  if (r < 0) return -1;
  if (WIFEXITED(st)) return (int64_t)WEXITSTATUS(st);
  if (WIFSIGNALED(st)) return 128 + (int64_t)WTERMSIG(st);
  return -1;
}

void vl_exit_now(int64_t code) {
  fflush(stdout);
  fflush(stderr);
  _exit((int)code);
}

// What path is, following links: 0 nothing (or unreadable), 1 a regular file, 2 a folder, 3 else.
int64_t vl_kind(const vu_str *path) {
  char *p = vu_cstr(path);
  if (!p) return 0;
  struct stat st;
  int r = stat(p, &st);
  free(p);
  if (r != 0) return 0;
  if (S_ISREG(st.st_mode)) return 1;
  if (S_ISDIR(st.st_mode)) return 2;
  return 3;
}

// A file's text; ok[0] is 1 when it could be read.
#include <stdio.h>
vu_str vl_read_text(const vu_str *path, int64_t *ok, int64_t n) {
  if (n > 0) ok[0] = 0;
  char *p = vu_cstr(path);
  if (!p) return vu_str_from("", 0);
  FILE *f = fopen(p, "rb");
  free(p);
  if (!f) return vu_str_from("", 0);
  size_t cap = 65536, len = 0;
  char *buf = malloc(cap);
  if (!buf) { fclose(f); return vu_str_from("", 0); }
  for (;;) {
    if (len == cap) {
      char *nb = realloc(buf, cap * 2);
      if (!nb) { free(buf); fclose(f); return vu_str_from("", 0); }
      buf = nb;
      cap *= 2;
    }
    size_t k = fread(buf + len, 1, cap - len, f);
    len += k;
    if (k == 0) break;
  }
  int err = ferror(f);
  fclose(f);
  vu_str s = vu_str_from(err ? "" : buf, err ? 0 : (int64_t)len);
  free(buf);
  if (!err && n > 0) ok[0] = 1;
  return s;
}

// ---- folders' listings, shared by the module graph's workers (vl_lkind, vl_llink)
// A stat costs about as much as listing a small folder, and resolving a request looks at up to 17
// paths of one folder, most of them not there. A folder asked about VL_LIST_AFTER times is listed,
// once (opendir, d_type; the others are answered by stat): a table of 64 parts by the folder's hash,
// each with its lock, held while a folder is listed. The entries are found by their name in ASCII
// lower case, so a name the file system could match under another case is seen. (Listing every
// folder asked about once listed home folders and a 43,000-file package four times, once for each
// worker, and made a small package's graph a third slower.)
#include <dirent.h>
#include <pthread.h>
typedef struct { char *name; uint32_t len; uint64_t lh; uint8_t dt; int8_t kind; } vl_dent;
#define VL_LIST_AFTER 4
typedef struct vl_dir {
  char *path; size_t plen; uint64_t h; int ok; int wide; int listed; int asked;
  uint32_t n; vl_dent *e; uint32_t mask; int32_t *slot;
  struct vl_dir *next;
} vl_dir;
#define VL_PARTS 64
#define VL_BUCKETS 1024
static pthread_mutex_t vl_dmu[VL_PARTS] = { [0 ... VL_PARTS - 1] = PTHREAD_MUTEX_INITIALIZER };
static vl_dir *vl_dtab[VL_PARTS][VL_BUCKETS];

static uint64_t vl_fnv(const char *s, size_t n, int fold) {
  uint64_t h = 1469598103934665603ULL;
  for (size_t i = 0; i < n; i++) {
    unsigned char c = (unsigned char)s[i];
    if (fold && c >= 'A' && c <= 'Z') c = (unsigned char)(c + 32);
    h = (h ^ c) * 1099511628211ULL;
  }
  return h;
}

static int vl_ieq(const char *a, const char *b, size_t n) {
  for (size_t i = 0; i < n; i++) {
    unsigned char x = (unsigned char)a[i], y = (unsigned char)b[i];
    if (x >= 'A' && x <= 'Z') x = (unsigned char)(x + 32);
    if (y >= 'A' && y <= 'Z') y = (unsigned char)(y + 32);
    if (x != y) return 0;
  }
  return 1;
}

static void vl_list(vl_dir *d) {
  d->listed = 1;
  DIR *dd = opendir(d->path);
  if (!dd) return;
  d->ok = 1;
  uint32_t cap = 16;
  d->e = malloc(cap * sizeof(vl_dent));
  struct dirent *x;
  while ((x = readdir(dd)) != NULL) {
    const char *nm = x->d_name;
    if (nm[0] == '.' && (nm[1] == 0 || (nm[1] == '.' && nm[2] == 0))) continue;
    size_t nl = strlen(nm);
    if (d->n == cap) { cap *= 2; d->e = realloc(d->e, cap * sizeof(vl_dent)); }
    vl_dent *e = &d->e[d->n++];
    e->name = malloc(nl + 1); memcpy(e->name, nm, nl + 1); e->len = (uint32_t)nl;
    e->lh = vl_fnv(nm, nl, 1);
    e->dt = x->d_type;
    e->kind = -1;
    if (x->d_type == DT_DIR) e->kind = 2;
    else if (x->d_type != DT_LNK && x->d_type != DT_UNKNOWN) e->kind = 1;
    for (size_t i = 0; i < nl; i++) if ((unsigned char)nm[i] >= 128) d->wide = 1;
  }
  closedir(dd);
  uint32_t sz = 16;
  while (sz < 2 * d->n + 2) sz *= 2;
  d->mask = sz - 1;
  d->slot = malloc(sz * sizeof(int32_t));
  for (uint32_t i = 0; i < sz; i++) d->slot[i] = -1;
  for (uint32_t k = 0; k < d->n; k++) {
    uint32_t s = (uint32_t)d->e[k].lh & d->mask;
    while (d->slot[s] >= 0) s = (s + 1) & d->mask;
    d->slot[s] = (int32_t)k;
  }
}

// the listing of path's folder (path[0..plen]), listed now if it's been asked about often
// enough; NULL while it hasn't
static vl_dir *vl_dir_of(const char *path, size_t plen) {
  uint64_t h = vl_fnv(path, plen, 0);
  int part = (int)(h % VL_PARTS);
  size_t b = (size_t)((h >> 6) % VL_BUCKETS);
  pthread_mutex_lock(&vl_dmu[part]);
  vl_dir *d = vl_dtab[part][b];
  while (d && !(d->h == h && d->plen == plen && memcmp(d->path, path, plen) == 0)) d = d->next;
  if (!d) {
    d = calloc(1, sizeof *d);
    d->path = malloc(plen + 1); memcpy(d->path, path, plen); d->path[plen] = 0;
    d->plen = plen; d->h = h;
    d->next = vl_dtab[part][b];
    vl_dtab[part][b] = d;
  }
  if (!d->listed && ++d->asked >= VL_LIST_AFTER) vl_list(d);
  vl_dir *out = d->listed ? d : NULL;
  pthread_mutex_unlock(&vl_dmu[part]);
  return out;
}

// (folders of links, where a listing says little: node_modules and its @scope folders)
static int vl_listable(const char *p, size_t plen) {
  size_t i = plen;
  while (i > 0 && p[i - 1] != '/') i--;
  const char *b = p + i; size_t bl = plen - i;
  if (bl == 0) return 0;
  if (bl == 12 && memcmp(b, "node_modules", 12) == 0) return 0;
  if (b[0] == '@' && i >= 14 && memcmp(p + i - 14, "/node_modules/", 14) == 0) return 0;
  return 1;
}

// the entry named exactly base in d: index, -1 none (and *ci set when one matches under case
// folding), -2 the name could match one the folding of the file system can't be told here
static int64_t vl_find(vl_dir *d, const char *base, size_t bl, int *ci) {
  *ci = 0;
  for (size_t i = 0; i < bl; i++) if ((unsigned char)base[i] >= 128) return -2;
  if (d->wide) return -2;
  uint64_t lh = vl_fnv(base, bl, 1);
  uint32_t s = (uint32_t)lh & d->mask;
  int64_t found = -1;
  while (d->slot[s] >= 0) {
    vl_dent *e = &d->e[d->slot[s]];
    if (e->lh == lh && e->len == bl && vl_ieq(e->name, base, bl)) {
      if (memcmp(e->name, base, bl) == 0) found = d->slot[s];
      else *ci = 1;
    }
    s = (s + 1) & d->mask;
  }
  return found;
}

static int vl_split(const vu_str *path, size_t *dl) {
  const char *p = (const char *)path->data;
  size_t n = (size_t)path->len;
  if (n == 0 || p[0] != '/' || memchr(p, 0, n)) return 0;
  size_t i = n;
  while (i > 0 && p[i - 1] != '/') i--;
  if (i == n) return 0;
  const char *b = p + i; size_t bl = n - i;
  if ((bl == 1 && b[0] == '.') || (bl == 2 && b[0] == '.' && b[1] == '.')) return 0;
  *dl = i > 1 ? i - 1 : 1;   // the folder: "/" for "/x"
  return 1;
}

// What stat says path is (0 nothing, 1 not a folder, 2 a folder, links followed), from its
// folder's listing: -1 when the listing can't say (a folder of links, a name it could match
// under case folding), -2 when the folder couldn't be listed.
int64_t vl_lkind(const vu_str *path) {
  size_t dl;
  if (!vl_split(path, &dl)) return -1;
  const char *p = (const char *)path->data;
  size_t n = (size_t)path->len;
  if (!vl_listable(p, dl)) return -1;
  vl_dir *d = vl_dir_of(p, dl);
  if (!d) return -1;
  if (!d->ok) return -2;
  size_t bs = dl == 1 ? 1 : dl + 1;
  int ci;
  int64_t k = vl_find(d, p + bs, n - bs, &ci);
  if (k == -2) return -1;
  if (k < 0) return ci ? -1 : 0;
  vl_dent *e = &d->e[k];
  int8_t kd = __atomic_load_n(&e->kind, __ATOMIC_RELAXED);
  if (kd >= 0) return kd;
  char *full = vu_cstr(path);
  if (!full) return -1;
  struct stat st;
  int r = stat(full, &st);
  free(full);
  kd = r != 0 ? 0 : (S_ISDIR(st.st_mode) ? 2 : 1);
  __atomic_store_n(&e->kind, kd, __ATOMIC_RELAXED);
  return kd;
}

// Whether path is a symbolic link, from its folder's listing: 1 yes, 0 no, -1 it can't say.
int64_t vl_llink(const vu_str *path) {
  size_t dl;
  if (!vl_split(path, &dl)) return -1;
  const char *p = (const char *)path->data;
  size_t n = (size_t)path->len;
  if (!vl_listable(p, dl)) return -1;
  vl_dir *d = vl_dir_of(p, dl);
  if (!d || !d->ok) return -1;
  size_t bs = dl == 1 ? 1 : dl + 1;
  int ci;
  int64_t k = vl_find(d, p + bs, n - bs, &ci);
  if (k < 0) return -1;
  uint8_t t = d->e[k].dt;
  if (t == DT_LNK) return 1;
  if (t == DT_UNKNOWN) return -1;
  return 0;
}
