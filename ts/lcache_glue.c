// vlint's result cache: a file's size, modification and change times (ns) and inode, and the clock.
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
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

// The online CPUs, where /proc/cpuinfo isn't there (macOS).
int64_t vl_ncpu(void) {
  long n = sysconf(_SC_NPROCESSORS_ONLN);
  return n > 0 ? (int64_t)n : 1;
}

// For the command line: whether a descriptor is a terminal, the working directory, a real path.
#include <unistd.h>
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
