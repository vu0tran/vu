// vlint's result cache: a file's size, modification and change times (ns) and inode, and the clock.
#include <sys/stat.h>
#include <time.h>

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

int64_t vl_now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  return (int64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}
