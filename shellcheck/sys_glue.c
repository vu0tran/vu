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

// 1 when the path is a regular file (following links)
int64_t sc_is_reg(const vu_str *p) {
  char *c = vu_cstr(p);
  if (!c) return 0;
  struct stat st;
  int ok = stat(c, &st) == 0 && S_ISREG(st.st_mode);
  free(c);
  return ok ? 1 : 0;
}

// 1 when the environment variable is set (maybe to "")
int64_t sc_env_has(const vu_str *name) {
  char *c = vu_cstr(name);
  if (!c) return 0;
  int ok = getenv(c) != NULL;
  free(c);
  return ok ? 1 : 0;
}

// the home directory of the password entry (getHomeDirectory without $HOME)
#include <pwd.h>
vu_str sc_pw_home(void) {
  struct passwd *pw = getpwuid(geteuid());
  if (!pw || !pw->pw_dir) return vu_str_from("", 0);
  return vu_str_from(pw->pw_dir, (int64_t)strlen(pw->pw_dir));
}

// readlink, or "" when the path isn't a symbolic link (a link's target is never empty)
vu_str sc_readlink(const vu_str *p) {
  char *c = vu_cstr(p);
  if (!c) return vu_str_from("", 0);
  char buf[PATH_MAX];
  ssize_t n = readlink(c, buf, sizeof buf);
  free(c);
  if (n <= 0) return vu_str_from("", 0);
  return vu_str_from(buf, n);
}

// 1 when the path exists (following links): doesPathExist
int64_t sc_exists(const vu_str *p) {
  char *c = vu_cstr(p);
  if (!c) return 0;
  struct stat st;
  int ok = stat(c, &st) == 0;
  free(c);
  return ok ? 1 : 0;
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

// ---------------------------------------------------------------- text I/O as GHC does it
//
// ShellCheck's release binary is GHC 9.8 linked with musl. Its text handles encode with the
// locale's codeset, which musl reports as ASCII when LC_ALL, LC_CTYPE or LANG (the first that
// is set and not empty) is "C" or "POSIX", and as UTF-8 otherwise. A character the codeset can't
// hold (any non-ASCII one under ASCII; a surrogate under UTF-8) makes the write fail after the
// characters before it. stdout is block buffered (8192 bytes) or, on a terminal, line buffered;
// stderr is unbuffered. File names, arguments and environment variables are decoded with the same
// codeset, bytes that don't decode becoming U+DC80..U+DCFF ("roundtrip"), and encoded back that
// way when they go to the system. Inside vsc a string is bytes read as ShellCheck's decodeString
// reads them (UTF-8 where it decodes, surrogates and overlong forms included, otherwise one
// Latin-1 character per byte); decoded names are kept as UTF-8 with surrogates (WTF-8).
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <pthread.h>

/* errno values Linux has and macOS doesn't: distinct values no call returns, so the switches
   below compile everywhere and keep Linux's texts */
#ifndef EBADFD
#define EBADFD (-1000)
#endif
#ifndef ECOMM
#define ECOMM (-1001)
#endif
#ifndef EKEYEXPIRED
#define EKEYEXPIRED (-1002)
#endif
#ifndef EKEYREJECTED
#define EKEYREJECTED (-1003)
#endif
#ifndef EKEYREVOKED
#define EKEYREVOKED (-1004)
#endif
#ifndef EMEDIUMTYPE
#define EMEDIUMTYPE (-1005)
#endif
#ifndef ENOKEY
#define ENOKEY (-1006)
#endif
#ifndef ENOMEDIUM
#define ENOMEDIUM (-1007)
#endif
#ifndef ENONET
#define ENONET (-1008)
#endif
#ifndef EREMCHG
#define EREMCHG (-1009)
#endif
#ifndef EREMOTEIO
#define EREMOTEIO (-1010)
#endif
#ifndef ESRMNT
#define ESRMNT (-1011)
#endif

static int sc_ascii = 0, sc_linebuf = 0;
static uint8_t sc_ob[8192];
static int64_t sc_on = 0;

// decodeString for one character at s[i]: the code point, *adv set to the bytes used
static int64_t sc_dec(const uint8_t *s, int64_t n, int64_t i, int64_t *adv) {
  int64_t b0 = s[i];
  *adv = 1;
  if (b0 < 0x80 || b0 >= 0xF8 || b0 < 0xC0) return b0;
  int64_t x, k;
  if (b0 >= 0xF0) { x = b0 & 7; k = 3; } else if (b0 >= 0xE0) { x = b0 & 15; k = 2; } else { x = b0 & 31; k = 1; }
  for (int64_t j = 1; j <= k; j++) {
    if (i + j >= n) return b0;
    int64_t b = s[i + j];
    if (b < 0x80 || b > 0xBF) return b0;
    x = (x << 6) | (b & 63);
  }
  if (x > 0x10FFFF) return b0;
  *adv = k + 1;
  return x;
}

static int sc_enc(int64_t c, uint8_t *o) {
  if (c < 0x80) { o[0] = (uint8_t)c; return 1; }
  if (c < 0x800) { o[0] = (uint8_t)(0xC0 | (c >> 6)); o[1] = (uint8_t)(0x80 | (c & 63)); return 2; }
  if (c < 0x10000) { o[0] = (uint8_t)(0xE0 | (c >> 12)); o[1] = (uint8_t)(0x80 | ((c >> 6) & 63)); o[2] = (uint8_t)(0x80 | (c & 63)); return 3; }
  o[0] = (uint8_t)(0xF0 | (c >> 18)); o[1] = (uint8_t)(0x80 | ((c >> 12) & 63)); o[2] = (uint8_t)(0x80 | ((c >> 6) & 63)); o[3] = (uint8_t)(0x80 | (c & 63));
  return 4;
}

// musl's strerror texts (ShellCheck's binary prints these, not glibc's)
static const char *sc_musl_strerror(int e) {
  switch (e) {
  case EILSEQ: return "Illegal byte sequence"; case EDOM: return "Domain error";
  case ERANGE: return "Result not representable"; case ENOTTY: return "Not a tty";
  case EACCES: return "Permission denied"; case EPERM: return "Operation not permitted";
  case ENOENT: return "No such file or directory"; case ESRCH: return "No such process";
  case EEXIST: return "File exists"; case EOVERFLOW: return "Value too large for data type";
  case ENOSPC: return "No space left on device"; case ENOMEM: return "Out of memory";
  case EBUSY: return "Resource busy"; case EINTR: return "Interrupted system call";
  case EAGAIN: return "Resource temporarily unavailable"; case ESPIPE: return "Invalid seek";
  case EXDEV: return "Cross-device link"; case EROFS: return "Read-only file system";
  case ENOTEMPTY: return "Directory not empty"; case ECONNRESET: return "Connection reset by peer";
  case ETIMEDOUT: return "Operation timed out"; case ECONNREFUSED: return "Connection refused";
  case EHOSTDOWN: return "Host is down"; case EHOSTUNREACH: return "Host is unreachable";
  case EADDRINUSE: return "Address in use"; case EPIPE: return "Broken pipe";
  case EIO: return "I/O error"; case ENXIO: return "No such device or address";
  case ENOTBLK: return "Block device required"; case ENODEV: return "No such device";
  case ENOTDIR: return "Not a directory"; case EISDIR: return "Is a directory";
  case ETXTBSY: return "Text file busy"; case ENOEXEC: return "Exec format error";
  case EINVAL: return "Invalid argument"; case E2BIG: return "Argument list too long";
  case ELOOP: return "Symbolic link loop"; case ENAMETOOLONG: return "Filename too long";
  case ENFILE: return "Too many open files in system"; case EMFILE: return "No file descriptors available";
  case EBADF: return "Bad file descriptor"; case ECHILD: return "No child process";
  case EFAULT: return "Bad address"; case EFBIG: return "File too large";
  case EMLINK: return "Too many links"; case ENOLCK: return "No locks available";
  case EDEADLK: return "Resource deadlock would occur"; case ENOTRECOVERABLE: return "State not recoverable";
  case EOWNERDEAD: return "Previous owner died"; case ECANCELED: return "Operation canceled";
  case ENOSYS: return "Function not implemented"; case ENOMSG: return "No message of desired type";
  case EIDRM: return "Identifier removed"; case ENOSTR: return "Device not a stream";
  case ENODATA: return "No data available"; case ETIME: return "Device timeout";
  case ENOSR: return "Out of streams resources"; case ENOLINK: return "Link has been severed";
  case EPROTO: return "Protocol error"; case EBADMSG: return "Bad message";
  case EBADFD: return "File descriptor in bad state"; case ENOTSOCK: return "Not a socket";
  case EDESTADDRREQ: return "Destination address required"; case EMSGSIZE: return "Message too large";
  case EPROTOTYPE: return "Protocol wrong type for socket"; case ENOPROTOOPT: return "Protocol not available";
  case EPROTONOSUPPORT: return "Protocol not supported"; case ESOCKTNOSUPPORT: return "Socket type not supported";
  case ENOTSUP: return "Not supported"; case EPFNOSUPPORT: return "Protocol family not supported";
  case EAFNOSUPPORT: return "Address family not supported by protocol"; case EADDRNOTAVAIL: return "Address not available";
  case ENETDOWN: return "Network is down"; case ENETUNREACH: return "Network unreachable";
  case ENETRESET: return "Connection reset by network"; case ECONNABORTED: return "Connection aborted";
  case ENOBUFS: return "No buffer space available"; case EISCONN: return "Socket is connected";
  case ENOTCONN: return "Socket not connected"; case ESHUTDOWN: return "Cannot send after socket shutdown";
  case EALREADY: return "Operation already in progress"; case EINPROGRESS: return "Operation in progress";
  case ESTALE: return "Stale file handle"; case EREMOTEIO: return "Remote I/O error";
  case EDQUOT: return "Quota exceeded"; case ENOMEDIUM: return "No medium found";
  case EMEDIUMTYPE: return "Wrong medium type"; case EMULTIHOP: return "Multihop attempted";
  case ENOKEY: return "Required key not available"; case EKEYEXPIRED: return "Key has expired";
  case EKEYREVOKED: return "Key has been revoked"; case EKEYREJECTED: return "Key was rejected by service";
  case 0: return "No error information";
  }
  return "No error information";
}

// Foreign.C.Error.errnoToIOError: the IOErrorType of an errno, as `show` prints it
static const char *sc_ghc_type(int e) {
  switch (e) {
  case 0: return "failed";
  case E2BIG: case EAGAIN: case EMFILE: case EMLINK: case EMSGSIZE: case ENFILE: case ENOBUFS:
  case ENOLCK: case ENOMEM: case ENOSPC: case ENOSR: case ETOOMANYREFS: case EUSERS:
    return "resource exhausted";
  case EACCES: case EDQUOT: case EFBIG: case EPERM: case EROFS: return "permission denied";
  case EADDRINUSE: case EBUSY: case EDEADLK: case ETXTBSY: return "resource busy";
  case EADDRNOTAVAIL: case EAFNOSUPPORT: case EMULTIHOP: case ENODEV: case ENOPROTOOPT: case ENOSYS:
  case EOPNOTSUPP: case EPFNOSUPPORT: case ERANGE: case ESOCKTNOSUPPORT: case ESPIPE: case EXDEV:
    return "unsupported operation";
  case EALREADY: case EEXIST: case EINPROGRESS: case EISCONN: return "already exists";
  case EBADF: case EDESTADDRREQ: case EDOM: case EILSEQ: case EINVAL: case ELOOP: case ENAMETOOLONG:
  case ENOEXEC: case ENOSTR: case ENOTBLK: case ENOTCONN: case ENOTSOCK:
    return "invalid argument";
  case EBADMSG: case EISDIR: case ENOTDIR: return "inappropriate type";
  case ECHILD: case ECONNREFUSED: case EHOSTDOWN: case EHOSTUNREACH: case ENETUNREACH: case ENODATA:
  case ENOENT: case ENOMSG: case ENONET: case ENXIO: case ESRCH:
    return "does not exist";
  case ECOMM: case ECONNRESET: case EIDRM: case ENETDOWN: case ENETRESET: case ENOLINK: case EPIPE:
  case EREMCHG: case ESTALE:
    return "resource vanished";
  case EINTR: return "interrupted";
  case EIO: return "hardware fault";
  case ENOTEMPTY: case ESRMNT: return "unsatisfied constraints";
  case ENOTTY: case EREMOTE: case ESHUTDOWN: return "illegal operation";
  case EPROTO: case EPROTONOSUPPORT: case EPROTOTYPE: return "protocol error";
  case ETIME: case ETIMEDOUT: return "timeout";
  }
  return "failed";
}

// an IOError as `show` prints it: "name: location: type (strerror)"
static vu_str sc_ioe_n(const uint8_t *name, int64_t nlen, const char *loc, const char *type, const char *detail) {
  vu_str t = {0};
  vu_str_cat_bytes(&t, name, nlen);
  char m[512];
  int n = snprintf(m, sizeof m, ": %s: %s (%s)", loc, type, detail);
  vu_str_cat_bytes(&t, (const uint8_t *)m, n);
  return t;
}

static vu_str sc_ioe(const char *where, const char *loc, int e) {
  return sc_ioe_n((const uint8_t *)where, (int64_t)strlen(where), loc, sc_ghc_type(e), sc_musl_strerror(e));
}

static vu_str sc_enc_err(const char *where, const char *loc, int64_t c) {
  char m[256];
  int n = snprintf(m, sizeof m, "%s%s%s: invalid argument (cannot encode character '\\%lld')", where, where[0] ? ": " : "", loc, (long long)c);
  return vu_str_from(m, n);
}

int64_t sc_io_init(void) {
  signal(SIGPIPE, SIG_IGN);
  const char *v = getenv("LC_ALL");
  if (!v || !*v) v = getenv("LC_CTYPE");
  if (!v || !*v) v = getenv("LANG");
  sc_ascii = v && (strcmp(v, "C") == 0 || strcmp(v, "POSIX") == 0);
  sc_linebuf = isatty(1);
  return sc_ascii;
}

// writes the stdout buffer; 0 or an errno (the buffer is kept then, as GHC keeps it)
static int sc_oflush(void) {
  int64_t off = 0;
  while (off < sc_on) {
    ssize_t w = write(1, sc_ob + off, (size_t)(sc_on - off));
    if (w < 0) {
      if (errno == EINTR) continue;
      return errno;
    }
    off += w;
  }
  sc_on = 0;
  return 0;
}

static int sc_bad(int64_t c) { return sc_ascii ? c >= 0x80 : (c >= 0xD800 && c <= 0xDFFF); }

// hPutStr stdout s: "" or the IOException it raises (`show`n)
vu_str sc_out(const vu_str *s) {
  const uint8_t *p = s->data;
  int64_t n = s->len, i = 0;
  while (i < n) {
    int64_t adv, c;
    if (p[i] < 0x80) { c = p[i]; adv = 1; } else c = sc_dec(p, n, i, &adv);
    i += adv;
    if (sc_bad(c)) return sc_enc_err("<stdout>", "commitBuffer", c);
    uint8_t b[4];
    int k = sc_enc(c, b);
    if (sc_on + k > (int64_t)sizeof sc_ob) {
      int e = sc_oflush();
      if (e) return sc_ioe("<stdout>", "commitBuffer", e);
    }
    memcpy(sc_ob + sc_on, b, (size_t)k);
    sc_on += k;
    if (sc_on == (int64_t)sizeof sc_ob || (c == '\n' && sc_linebuf)) {
      int e = sc_oflush();
      if (e) return sc_ioe("<stdout>", "commitBuffer", e);
    }
  }
  return vu_str_from("", 0);
}

// hPut stdout of a lazy ByteString (aeson's json, with the newline): the characters as UTF-8,
// surrogates included. The first 4080 bytes are aeson's first chunk; hPutBuf copies a chunk into
// the buffer when it fits, and otherwise flushes the buffer and writes the chunk itself.
vu_str sc_out_bytes(const vu_str *s) {
  vu_str t = {0};
  const uint8_t *p = s->data;
  int64_t n = s->len, i = 0;
  while (i < n) {
    int64_t adv, c;
    if (p[i] < 0x80) { c = p[i]; adv = 1; } else c = sc_dec(p, n, i, &adv);
    i += adv;
    uint8_t b[4];
    int k = sc_enc(c, b);
    vu_str_cat_bytes(&t, b, k);
  }
  int64_t off = 0;
  vu_str r = vu_str_from("", 0);
  while (off < t.len) {
    int64_t cnt = t.len - off;
    if (off == 0 && cnt > 4080) cnt = 4080;
    if (cnt < (int64_t)sizeof sc_ob && cnt <= (int64_t)sizeof sc_ob - sc_on) {
      memcpy(sc_ob + sc_on, t.data + off, (size_t)cnt);
      sc_on += cnt;
      if (sc_on == (int64_t)sizeof sc_ob || sc_linebuf) {
        int e = sc_oflush();
        if (e) { r = sc_ioe("<stdout>", "hPutBuf", e); break; }
      }
    } else {
      int e = sc_on > 0 ? sc_oflush() : 0;
      if (e) { r = sc_ioe("<stdout>", "hPutBuf", e); break; }
      int64_t w0 = 0;
      while (w0 < cnt) {
        ssize_t w = write(1, t.data + off + w0, (size_t)(cnt - w0));
        if (w < 0) { if (errno == EINTR) continue; e = errno; break; }
        w0 += w;
      }
      if (e) { r = sc_ioe("<stdout>", "hPutBuf", e); break; }
    }
    off += cnt;
  }
  free(t.data);
  return r;
}

// hPutStr stderr s (unbuffered, a character at a time): "" or the IOException
vu_str sc_err(const vu_str *s) {
  const uint8_t *p = s->data;
  int64_t n = s->len, i = 0;
  vu_str t = {0};
  vu_str r = vu_str_from("", 0);
  int64_t bad = -1;
  while (i < n) {
    int64_t adv, c;
    if (p[i] < 0x80) { c = p[i]; adv = 1; } else c = sc_dec(p, n, i, &adv);
    i += adv;
    if (sc_bad(c)) { bad = c; break; }
    uint8_t b[4];
    int k = sc_enc(c, b);
    vu_str_cat_bytes(&t, b, k);
  }
  int64_t off = 0;
  while (off < t.len) {
    ssize_t w = write(2, t.data + off, (size_t)(t.len - off));
    if (w < 0) {
      if (errno == EINTR) continue;
      r = sc_ioe("<stderr>", "hPutChar", errno);
      break;
    }
    off += w;
  }
  free(t.data);
  if (r.len == 0 && bad >= 0) r = sc_enc_err("<stderr>", "hPutChar", bad);
  return r;
}

// bytes to stderr as they are, errors ignored (the RTS's errorBelch)
void sc_raw_err(const vu_str *s) {
  int64_t off = 0;
  while (off < s->len) {
    ssize_t w = write(2, s->data + off, (size_t)(s->len - off));
    if (w < 0) { if (errno == EINTR) continue; return; }
    off += w;
  }
}

// hFlush stdout at exit: errors are ignored
void sc_flush(void) { sc_oflush(); sc_on = 0; }

// a name from the system (argument, environment, getcwd, realpath) as GHC decodes it
vu_str sc_fs_decode(const vu_str *s) {
  const uint8_t *p = s->data;
  int64_t n = s->len, i = 0;
  int plain = 1;
  for (int64_t j = 0; j < n; j++) if (p[j] >= 0x80) { plain = 0; break; }
  if (plain) return vu_str_from(p, n);
  vu_str t = {0};
  while (i < n) {
    uint8_t b[4];
    int64_t c = p[i], adv = 1;
    if (c >= 0x80) {
      if (sc_ascii) c = 0xDC00 + c;
      else {
        // GHC's UTF-8 decoder: shortest forms only, no surrogates, at most U+10FFFF
        int64_t b0 = p[i], k = 0, x = 0, lo = 0;
        if (b0 >= 0xC2 && b0 <= 0xDF) { k = 1; x = b0 & 31; lo = 0x80; }
        else if (b0 >= 0xE0 && b0 <= 0xEF) { k = 2; x = b0 & 15; lo = 0x800; }
        else if (b0 >= 0xF0 && b0 <= 0xF4) { k = 3; x = b0 & 7; lo = 0x10000; }
        int ok = k > 0;
        for (int64_t j = 1; ok && j <= k; j++) {
          if (i + j >= n) { ok = 0; break; }
          int64_t bb = p[i + j];
          if (bb < 0x80 || bb > 0xBF) { ok = 0; break; }
          x = (x << 6) | (bb & 63);
        }
        if (ok && (x < lo || x > 0x10FFFF || (x >= 0xD800 && x <= 0xDFFF))) ok = 0;
        if (ok) { c = x; adv = k + 1; } else c = 0xDC00 + b0;
      }
    }
    i += adv;
    int k = sc_enc(c, b);
    vu_str_cat_bytes(&t, b, k);
  }
  return t;
}

static __thread int64_t sc_bad_char = -1;

// a name for the system: the characters encoded back (U+DC80..U+DCFF as the bytes they stand
// for); when a character can't be encoded, sc_enc_bad() gives it and the result is empty
vu_str sc_fs_encode(const vu_str *s) {
  const uint8_t *p = s->data;
  int64_t n = s->len, i = 0;
  sc_bad_char = -1;
  int plain = 1;
  for (int64_t j = 0; j < n; j++) if (p[j] >= 0x80) { plain = 0; break; }
  if (plain) return vu_str_from(p, n);
  vu_str t = {0};
  while (i < n) {
    int64_t adv, c = sc_dec(p, n, i, &adv);
    i += adv;
    if (c >= 0xDC80 && c <= 0xDCFF) { uint8_t b = (uint8_t)(c - 0xDC00); vu_str_cat_bytes(&t, &b, 1); continue; }
    if (sc_bad(c)) { sc_bad_char = c; free(t.data); return vu_str_from("", 0); }
    uint8_t b[4];
    int k = sc_enc(c, b);
    vu_str_cat_bytes(&t, b, k);
  }
  return t;
}

int64_t sc_enc_bad(void) { return sc_bad_char; }

// "recoverEncode: invalid argument (cannot encode character '\N')" for the last failed encode
vu_str sc_enc_msg(void) { return sc_enc_err("", "recoverEncode", sc_bad_char); }

// ---------------------------------------------------------------- reading files as inputFile does
//
// openBinaryFile (a directory is "inappropriate type (is a directory)"), then the whole contents;
// a file that can't be reopened (not a regular file or block device: stdin, pipes, FIFOs,
// terminals) is cached by name for later reads in this run, as ShellCheck's siReadFile does.
// The name is vsc's string (decoded); `os` is the same name for the system.

typedef struct sc_centry { char *name; int64_t nlen; uint8_t *data; int64_t len; struct sc_centry *next; } sc_centry;
static sc_centry *sc_cache = NULL;
static pthread_mutex_t sc_cache_mu = PTHREAD_MUTEX_INITIALIZER;
static __thread vu_str sc_read_error;

static int sc_cache_get(const vu_str *name, vu_str *out) {
  pthread_mutex_lock(&sc_cache_mu);
  for (sc_centry *e = sc_cache; e; e = e->next)
    if (e->nlen == name->len && memcmp(e->name, name->data, (size_t)name->len) == 0) {
      *out = vu_str_from(e->data, e->len);
      pthread_mutex_unlock(&sc_cache_mu);
      return 1;
    }
  pthread_mutex_unlock(&sc_cache_mu);
  return 0;
}

static void sc_cache_put(const vu_str *name, const vu_str *data) {
  sc_centry *e = (sc_centry *)malloc(sizeof *e);
  e->name = (char *)malloc((size_t)name->len + 1);
  memcpy(e->name, name->data, (size_t)name->len);
  e->nlen = name->len;
  e->data = (uint8_t *)malloc((size_t)data->len + 1);
  if (data->len) memcpy(e->data, data->data, (size_t)data->len);
  e->len = data->len;
  pthread_mutex_lock(&sc_cache_mu);
  e->next = sc_cache;
  sc_cache = e;
  pthread_mutex_unlock(&sc_cache_mu);
}

static void sc_set_err(vu_str m) {
  free(sc_read_error.data);
  sc_read_error = m;
}

int64_t sc_cached(const vu_str *name) {
  vu_str t = {0};
  if (!sc_cache_get(name, &t)) return 0;
  free(t.data);
  return 1;
}

// the contents of a file ("-" is stdin); on failure "" and sc_read_err() is the message. With
// use_cache, siReadFile's cache is used (readConfig doesn't use it).
vu_str sc_read(const vu_str *name, const vu_str *os, int64_t use_cache) {
  sc_set_err(vu_str_from("", 0));
  vu_str out = {0};
  if (use_cache && sc_cache_get(name, &out)) return out;
  int is_stdin = name->len == 1 && name->data[0] == '-';
  int fd;
  if (is_stdin) fd = 0;
  else {
    char *c = vu_cstr(os);
    if (!c) { sc_set_err(sc_ioe_n(name->data, name->len, "openBinaryFile", "invalid argument", "FilePaths must not contain internal NUL code units.")); return vu_str_from("", 0); }
    do fd = open(c, O_RDONLY | O_NOCTTY | O_NONBLOCK); while (fd < 0 && errno == EINTR);
    free(c);
    if (fd < 0) { int e = errno; sc_set_err(sc_ioe_n(name->data, name->len, "openBinaryFile", sc_ghc_type(e), sc_musl_strerror(e))); return vu_str_from("", 0); }
  }
  struct stat st;
  int cache = 1;
  if (fstat(fd, &st) == 0) {
    if (!is_stdin && S_ISDIR(st.st_mode)) {
      close(fd);
      sc_set_err(sc_ioe_n(name->data, name->len, "openBinaryFile", "inappropriate type", "is a directory"));
      return vu_str_from("", 0);
    }
    if (!is_stdin && (S_ISREG(st.st_mode) || S_ISBLK(st.st_mode))) cache = 0;
  }
  if (!is_stdin) {
    int fl = fcntl(fd, F_GETFL);
    if (fl >= 0) fcntl(fd, F_SETFL, fl & ~O_NONBLOCK);
  }
  uint8_t buf[65536];
  for (;;) {
    ssize_t r = read(fd, buf, sizeof buf);
    if (r < 0) {
      if (errno == EINTR) continue;
      int e = errno;
      if (!is_stdin) close(fd);
      free(out.data);
      if (is_stdin) sc_set_err(sc_ioe("<stdin>", "hGetContents", e));
      else sc_set_err(sc_ioe_n(name->data, name->len, "hGetContents", sc_ghc_type(e), sc_musl_strerror(e)));
      return vu_str_from("", 0);
    }
    if (r == 0) break;
    vu_str_cat_bytes(&out, buf, r);
  }
  if (!is_stdin) close(fd);
  if (cache && use_cache) sc_cache_put(name, &out);
  return out;
}

vu_str sc_read_err(void) { return vu_str_from(sc_read_error.data, sc_read_error.len); }

// the program's name as the RTS prints it in uncaught-exception messages (argv[0]'s last part)
vu_str sc_basename(const vu_str *p) {
  int64_t i = p->len;
  while (i > 0 && p->data[i - 1] != '/') i--;
  return vu_str_from(p->data + i, p->len - i);
}

// set by the source resolver when a name can't be encoded: the whole file fails with it
static __thread vu_str sc_fatal_msg;
void sc_fatal_set(const vu_str *m) { free(sc_fatal_msg.data); sc_fatal_msg = vu_str_from(m->data, m->len); }
vu_str sc_fatal_take(void) { vu_str r = sc_fatal_msg; sc_fatal_msg = (vu_str){0}; return r.len ? r : vu_str_from("", 0); }
