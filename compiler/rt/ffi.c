/* The C side of extern blocks (SPEC.md, Calling C). A glue file can use these, vu_str, and
   vu_errf(fmt, ...) to build error messages. */
/* Inside a par loop? Only programs with par loops are built with OpenMP (VU_PAR is defined then). */
#ifdef VU_PAR
#include <omp.h>
#define vu_in_par() omp_in_parallel()
#else
#define vu_in_par() 0
#endif
/* A new Str holding a copy of n bytes at p. */
static vu_str vu_str_from(const void *p, int64_t n) {
    vu_str s = {0};
    if (n > 0) vu_str_cat_bytes(&s, (const uint8_t *)p, n);
    return s;
}
/* A NUL-terminated copy of s for C APIs (free it with free()); NULL if s contains a zero byte. */
static char *vu_cstr(const vu_str *s) {
    if (s->len && memchr(s->data, 0, (size_t)s->len)) return NULL;
    char *p = (char *)vu_malloc((size_t)s->len + 1);
    if (s->len) memcpy(p, s->data, (size_t)s->len);
    p[s->len] = 0;
    return p;
}
static void vu_ffi_here(const char *fn, int line) {
    if (vu_in_par()) {
        char m[300];
        int n = snprintf(m, sizeof m, "%.200s() is C code, which can't be called inside a par loop", fn);
        vu_panic(line, m, n);
    }
}
__attribute__((noreturn)) static void vu_ffi_null(const char *fn, int line) {
    char m[300];
    int n = snprintf(m, sizeof m, "%.200s() returned no handle (NULL) without reporting an error", fn);
    vu_panic(line, m, n);
}