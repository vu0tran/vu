// System calls vsc needs that Vu's standard library doesn't offer: whether stdout is a terminal
// (for --color=auto), the current directory and canonical paths (canonicalizePath, used to find
// .shellcheckrc and to tell whether a sourced file was given as input).
#include <unistd.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

int64_t sc_isatty(int64_t fd) { return isatty((int)fd) ? 1 : 0; }

vu_str sc_getcwd(void) {
  char buf[PATH_MAX];
  if (!getcwd(buf, sizeof buf)) return vu_str_from("", 0);
  return vu_str_from(buf, (int64_t)strlen(buf));
}

// realpath, or "" when the path doesn't resolve
vu_str sc_realpath(const vu_str *p) {
  char *c = vu_cstr(p);
  if (!c) return vu_str_from("", 0);
  char buf[PATH_MAX];
  char *r = realpath(c, buf);
  free(c);
  if (!r) return vu_str_from("", 0);
  return vu_str_from(buf, (int64_t)strlen(buf));
}

// 1 when the path is an existing regular file (following links): doesFileExist
int64_t sc_is_file(const vu_str *p) {
  char *c = vu_cstr(p);
  if (!c) return 0;
  struct stat st;
  int ok = stat(c, &st) == 0 && !S_ISDIR(st.st_mode);
  free(c);
  return ok ? 1 : 0;
}
