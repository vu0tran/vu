// vgolint's few system calls: the working directory, whether a stream is a terminal, a file's
// modification time.
#include <unistd.h>
#include <limits.h>
#include <sys/stat.h>

vu_str gl_getcwd(void) {
  char buf[PATH_MAX];
  if (!getcwd(buf, sizeof buf)) return vu_str_from("", 0);
  return vu_str_from(buf, (int64_t)strlen(buf));
}

bool gl_isatty(int64_t fd) {
  return isatty((int)fd) == 1;
}

bool gl_is_dir(const vu_str *path) {
  char *p = vu_cstr(path);
  if (!p) return false;
  struct stat st;
  int r = stat(p, &st);
  free(p);
  return r == 0 && S_ISDIR(st.st_mode);
}

// The online CPUs, where /proc/cpuinfo isn't there (macOS).
int64_t gl_ncpu(void) {
  long n = sysconf(_SC_NPROCESSORS_ONLN);
  return n > 0 ? (int64_t)n : 1;
}
