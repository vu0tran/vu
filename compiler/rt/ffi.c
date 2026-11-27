/* The C side of extern blocks (SPEC.md, Calling C). A glue file can use these, vu_str, and
   vu_errf(fmt, ...) to build error messages. */
/* Inside a par loop? Only programs with par loops are built with OpenMP (VU_PAR is defined then;
   without an OpenMP compiler, as Apple's clang without libomp, par loops run on one thread). */
#if defined(VU_PAR) && defined(_OPENMP)
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
__attribute__((noreturn, cold, noinline)) static void vu_ffi_in_par(const char *fn, int line) {
    char m[300];
    int n = snprintf(m, sizeof m, "%.200s() is C code, which can't be called inside a par loop", fn);
    vu_panic(line, m, n);
}
/* A call in a par loop's own body: asked each time. */
static inline void vu_ffi_here(const char *fn, int line) {
    if (vu_in_par()) vu_ffi_in_par(fn, line);
}
/* Any other call: its function asked once, at its start (OpenMP only while some par loop runs), since
   whether a frame runs inside a par loop doesn't change while it runs. */
__attribute__((noinline)) static bool vu_ffi_par_slow(void) { return vu_in_par(); }
static inline bool vu_ffi_par_entry(void) {
    return __atomic_load_n(&vu_par_live, __ATOMIC_RELAXED) != 0 && vu_ffi_par_slow();
}
#define VU_FFI_ENTRY const bool vu_inpar = vu_ffi_par_entry()
/* A function no par loop can reach (ffi_reach in c5_build.vu): no check. */
#define VU_FFI_OFF const bool vu_inpar = false
#define VU_FFI_CK(fn, line) (vu_inpar ? vu_ffi_in_par(fn, line) : (void)0)
__attribute__((noreturn)) static void vu_ffi_null(const char *fn, int line) {
    char m[300];
    int n = snprintf(m, sizeof m, "%.200s() returned no handle (NULL) without reporting an error", fn);
    vu_panic(line, m, n);
}