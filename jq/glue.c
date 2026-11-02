/* glue.c: the C library pieces vjq uses, as jq does: libm's functions, the C library's
   time functions (strftime, strptime, timegm, gmtime, localtime), the environment, and
   Oniguruma for regular expressions (the library jq itself uses, so patterns mean the same).
   Oniguruma's declarations are written out here (from oniguruma.h, BSD licensed) so that only
   its shared library, not its development headers, is needed. */
#define _GNU_SOURCE
#include <math.h>
#include <float.h>
#include <stdint.h>
#include <time.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <unistd.h>

/* exp10 as the glibc jq 1.7.1's release binaries are linked with computes it (e_exp10.c before
   glibc 2.39: exp of the argument split in two parts times ln 10, not correctly rounded) */
static double jq_exp10(double arg) {
    static const double log10_high = 0x2.4d7637p0;
    static const double log10_low = 0x1.daaa8ac16ea57p-26;
    if (!isfinite(arg)) return exp(arg);
    if (arg < DBL_MIN_10_EXP - DBL_DIG - 10) return DBL_MIN * DBL_MIN;
    if (arg > DBL_MAX_10_EXP + 1) return DBL_MAX * DBL_MAX;
    if (fabs(arg) < 0x1p-56) return 1.0;
    union { double d; uint64_t u; } h = { arg };
    h.u &= 0xfffffffff8000000ULL;
    double arg_high = h.d, arg_low = arg - arg_high;
    double exp_high = arg_high * log10_high;
    double exp_low = arg_high * log10_low + arg_low * M_LN10;
    return exp(exp_high) * exp(exp_low);
}

/* ---- math: one entry point per arity, op chosen by number (see run.vu's math table) */
double vjq_m1(int64_t op, double x) {
    switch (op) {
    case 0: return acos(x);   case 1: return acosh(x);  case 2: return asin(x);
    case 3: return asinh(x);  case 4: return atan(x);   case 5: return atanh(x);
    case 6: return cbrt(x);   case 7: return ceil(x);   case 8: return cos(x);
    case 9: return cosh(x);   case 10: return erf(x);   case 11: return erfc(x);
    case 12: return exp(x);   case 13: return jq_exp10(x); case 14: return exp2(x);
    case 15: return expm1(x); case 16: return fabs(x);  case 17: return floor(x);
    case 18: return lgamma(x); case 19: return j0(x);   case 20: return j1(x);
    case 21: return lgamma(x); case 22: return log(x);  case 23: return log10(x);
    case 24: return log1p(x); case 25: return log2(x);  case 26: return logb(x);
    case 27: return nearbyint(x); case 28: return exp10(x); case 29: return rint(x);
    case 30: return round(x); case 31: return significand(x); case 32: return sin(x);
    case 33: return sinh(x);  case 34: return sqrt(x);  case 35: return tan(x);
    case 36: return tanh(x);  case 37: return tgamma(x); case 38: return trunc(x);
    case 39: return y0(x);    case 40: return y1(x);
    case 41: { int e; return frexp(x, &e); }
    case 42: { int e; frexp(x, &e); return (double)e; }
    case 43: { double ip; return modf(x, &ip); }
    case 44: { double ip; modf(x, &ip); return ip; }
    case 45: { int s; return lgamma_r(x, &s); }
    case 46: { int s; lgamma_r(x, &s); return (double)s; }
    }
    return NAN;
}

double vjq_m2(int64_t op, double x, double y) {
    switch (op) {
    case 0: return atan2(x, y);   case 1: return copysign(x, y); case 2: return drem(x, y);
    case 3: return fdim(x, y);    case 4: return fmax(x, y);     case 5: return fmin(x, y);
    case 6: return fmod(x, y);    case 7: return hypot(x, y);    case 8: return jn((int)x, y);
    case 9: return ldexp(x, (int)y); case 10: return nextafter(x, y); case 11: return nexttoward(x, y);
    case 12: return pow(x, y);    case 13: return remainder(x, y); case 14: return scalb(x, y);
    case 15: return scalbln(x, (long)y); case 16: return yn((int)x, y);
    }
    return NAN;
}

double vjq_m3(int64_t op, double x, double y, double z) {
    (void)op;
    return fma(x, y, z);
}

/* ---- time */
double vjq_now(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

/* broken-down time <-> jq's array [sec(with fraction), min, hour, mday, mon, year-1900... ]:
   jq's arrays are [year, month(0-11), mday, hours, minutes, seconds(float), wday, yday]. */
static void to_tm(const double *p, int64_t n, struct tm *tm) {
    memset(tm, 0, sizeof *tm);
    if (n > 0) tm->tm_year = (int)p[0] - 1900;
    if (n > 1) tm->tm_mon = (int)p[1];
    if (n > 2) tm->tm_mday = (int)p[2];
    if (n > 3) tm->tm_hour = (int)p[3];
    if (n > 4) tm->tm_min = (int)p[4];
    if (n > 5) tm->tm_sec = (int)p[5];
    if (n > 6) tm->tm_wday = (int)p[6];
    if (n > 7) tm->tm_yday = (int)p[7];
}

static void from_tm(const struct tm *tm, double *out, int64_t n, double frac) {
    if (n < 8) return;
    out[0] = tm->tm_year + 1900.0;
    out[1] = tm->tm_mon;
    out[2] = tm->tm_mday;
    out[3] = tm->tm_hour;
    out[4] = tm->tm_min;
    out[5] = tm->tm_sec + frac;
    out[6] = tm->tm_wday;
    out[7] = tm->tm_yday;
}

/* gmtime/localtime of t seconds into out[8]; false when it can't be represented */
bool vjq_brokendown(double t, bool local, double *out, int64_t n) {
    time_t secs = (time_t)t;
    struct tm tm;
    if (local) { if (!localtime_r(&secs, &tm)) return false; }
    else { if (!gmtime_r(&secs, &tm)) return false; }
    from_tm(&tm, out, n, t - floor(t));
    return true;
}

double vjq_timegm(const double *p, int64_t n) {
    struct tm tm;
    to_tm(p, n, &tm);
    return (double)timegm(&tm);
}

/* strftime of a broken-down time, as jq does it (zone fields left zero); "" when strftime
   reports failure (it returned 0) */
vu_str vjq_strftime(const vu_str *fmt, const double *p, int64_t n) {
    struct tm tm;
    to_tm(p, n, &tm);
    char *f = vu_cstr(fmt);
    if (!f) return vu_str_from("", 0);
    size_t cap = strlen(f) + 100;
    char *buf = malloc(cap);
    size_t len = strftime(buf, cap, f, &tm);
    vu_str r = vu_str_from(buf, (int64_t)len);
    free(buf);
    free(f);
    return r;
}

/* strptime: fills out[8] and returns the number of bytes consumed, or -1 (as jq's f_strptime,
   with its set_tm_wday and set_tm_yday for fields strptime left unset) */
static void set_tm_wday(struct tm *tm) {
    int century = (1900 + tm->tm_year) / 100;
    int year = (1900 + tm->tm_year) % 100;
    if (tm->tm_mon < 2) year--;
    int mon = tm->tm_mon - 1;
    if (mon < 1) mon += 12;
    int wday = (tm->tm_mday + (int)floor((2.6 * mon - 0.2)) + year + (int)floor(year / 4.0) + (int)floor(century / 4.0) - 2 * century) % 7;
    if (wday < 0) wday += 7;
    tm->tm_wday = wday;
}

static void set_tm_yday(struct tm *tm) {
    static const int d[] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
    int mon = tm->tm_mon;
    int year = 1900 + tm->tm_year;
    int leap_day = 0;
    if (tm->tm_mon > 1 && ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0))) leap_day = 1;
    if (mon < 0) mon = -mon;
    if (mon > 11) mon %= 12;
    tm->tm_yday = d[mon] + leap_day + tm->tm_mday - 1;
}

int64_t vjq_strptime(const vu_str *s, const vu_str *fmt, double *out, int64_t n) {
    struct tm tm;
    memset(&tm, 0, sizeof tm);
    tm.tm_wday = 8;
    tm.tm_yday = 367;
    char *cs = vu_cstr(s), *cf = vu_cstr(fmt);
    if (!cs || !cf) { free(cs); free(cf); return -1; }
    const char *end = strptime(cs, cf, &tm);
    int64_t r = -1;
    if (end) {
        r = end - cs;
        if (tm.tm_wday == 8 && tm.tm_mday != 0 && tm.tm_mon >= 0 && tm.tm_mon <= 11) set_tm_wday(&tm);
        if (tm.tm_yday == 367 && tm.tm_mday != 0 && tm.tm_mon >= 0 && tm.tm_mon <= 11) set_tm_yday(&tm);
        from_tm(&tm, out, n, 0.0);
    }
    free(cs); free(cf);
    return r;
}

/* the environment as NUL-separated NAME=value entries */
extern char **environ;
vu_str vjq_environ(void) {
    vu_str r = {0};
    for (char **e = environ; e && *e; e++) {
        vu_str_cat_bytes(&r, (const uint8_t *)*e, (int64_t)strlen(*e) + 1);
    }
    return r;
}

/* ---- Oniguruma, loaded at the first regex (dlopen), so vjq runs without it until a regex is
   used. Its declarations are written out here (from oniguruma.h, BSD licensed). */
#include <dlfcn.h>
typedef unsigned char OnigUChar;
typedef unsigned int OnigOptionType;
typedef struct OnigEncodingTypeST OnigEncodingType;
typedef OnigEncodingType *OnigEncoding;
typedef struct OnigSyntaxTypeST OnigSyntaxType;
typedef struct re_pattern_buffer *OnigRegex;
struct re_registers { int allocated; int num_regs; int *beg; int *end; void *history_root; };
typedef struct re_registers OnigRegion;
typedef struct { OnigEncoding enc; OnigUChar *par; OnigUChar *par_end; } OnigErrorInfo;
static OnigEncoding p_utf8;
static OnigSyntaxType *p_perl_ng;
static int (*p_onig_initialize)(OnigEncoding encodings[], int n);
static int (*p_onig_new)(OnigRegex *, const OnigUChar *, const OnigUChar *, OnigOptionType, OnigEncoding, OnigSyntaxType *, OnigErrorInfo *);
static void (*p_onig_free)(OnigRegex);
static OnigRegion *(*p_onig_region_new)(void);
static void (*p_onig_region_free)(OnigRegion *, int);
static int (*p_onig_search)(OnigRegex, const OnigUChar *, const OnigUChar *, const OnigUChar *, const OnigUChar *, OnigRegion *, OnigOptionType);
static int (*p_onig_foreach_name)(OnigRegex, int (*)(const OnigUChar *, const OnigUChar *, int, int *, OnigRegex, void *), void *);
static int (*p_onig_number_of_captures)(OnigRegex);
static int (*p_onig_error_code_to_str)(OnigUChar *, int, ...);

static int onig_load(void) {
    static int state = 0;   /* 0 not tried, 1 loaded, -1 unavailable */
    if (state) return state;
    const char *names[] = {"libonig.so.5", "libonig.so", "libonig.5.dylib", "libonig.dylib", NULL};
    void *h = NULL;
    for (int i = 0; names[i] && !h; i++) h = dlopen(names[i], RTLD_NOW);
    if (!h) { state = -1; return state; }
    p_utf8 = dlsym(h, "OnigEncodingUTF8");
    p_perl_ng = dlsym(h, "OnigSyntaxPerl_NG");
    *(void **)&p_onig_initialize = dlsym(h, "onig_initialize");
    *(void **)&p_onig_new = dlsym(h, "onig_new");
    *(void **)&p_onig_free = dlsym(h, "onig_free");
    *(void **)&p_onig_region_new = dlsym(h, "onig_region_new");
    *(void **)&p_onig_region_free = dlsym(h, "onig_region_free");
    *(void **)&p_onig_search = dlsym(h, "onig_search");
    *(void **)&p_onig_foreach_name = dlsym(h, "onig_foreach_name");
    *(void **)&p_onig_number_of_captures = dlsym(h, "onig_number_of_captures");
    *(void **)&p_onig_error_code_to_str = dlsym(h, "onig_error_code_to_str");
    if (!p_utf8 || !p_perl_ng || !p_onig_initialize || !p_onig_new || !p_onig_free || !p_onig_region_new ||
        !p_onig_region_free || !p_onig_search || !p_onig_foreach_name || !p_onig_number_of_captures || !p_onig_error_code_to_str) {
        state = -1;
        return state;
    }
    OnigEncoding encs[1] = {p_utf8};
    p_onig_initialize(encs, 1);
    state = 1;
    return state;
}

typedef struct { OnigRegex re; OnigRegion *region; int ncap; } vjq_re;

void vjq_re_free(void *p) {
    vjq_re *r = p;
    if (!r) return;
    p_onig_region_free(r->region, 1);
    p_onig_free(r->re);
    free(r);
}


bool vjq_re_compile(const vu_str *pat, int64_t options, void **out, vu_str *err) {
    if (onig_load() < 0) {
        const char *m = "jq was compiled without ONIGURUMA regex library. match/test/sub and related functions are not available.";
        *err = vu_str_from(m, (int64_t)strlen(m));
        return false;
    }
    OnigErrorInfo einfo;
    OnigRegex re;
    const OnigUChar *pd = pat->data ? pat->data : (const OnigUChar *)"";
    int rc = p_onig_new(&re, pd, pd + pat->len, (OnigOptionType)options, p_utf8, p_perl_ng, &einfo);
    if (rc != 0) {
        OnigUChar buf[256];
        p_onig_error_code_to_str(buf, rc, &einfo);
        *err = vu_str_from((const char *)buf, (int64_t)strlen((const char *)buf));
        return false;
    }
    vjq_re *r = malloc(sizeof *r);
    r->re = re;
    r->region = p_onig_region_new();
    r->ncap = p_onig_number_of_captures(re);
    *out = r;
    return true;
}

int64_t vjq_re_ncap(void *p) { return ((vjq_re *)p)->ncap; }

/* Searches s from byte start; fills out with begin/end byte pairs for the match and each
   group (-1 when a group didn't take part). Returns 1 on a match, 0 on none, -1 on error. */
int64_t vjq_re_search(void *p, const vu_str *s, int64_t start, int64_t *out, int64_t n) {
    vjq_re *r = p;
    const OnigUChar *str = s->data ? s->data : (const OnigUChar *)"";
    const OnigUChar *end = str + s->len;
    int rc = p_onig_search(r->re, str, end, str + start, end, r->region, 0);
    if (rc == -1) return 0;
    if (rc < 0) return -1;
    for (int i = 0; i < r->region->num_regs && 2 * i + 1 < n; i++) {
        out[2 * i] = r->region->beg[i];
        out[2 * i + 1] = r->region->end[i];
    }
    return 1;
}

static int name_iter(const OnigUChar *name, const OnigUChar *name_end, int ngroups, int *groups, OnigRegex reg, void *arg) {
    (void)reg;
    vu_str *acc = arg;
    for (int i = 0; i < ngroups; i++) {
        char num[24];
        int k = snprintf(num, sizeof num, "%d=", groups[i]);
        vu_str_cat_bytes(acc, (const uint8_t *)num, k);
        vu_str_cat_bytes(acc, name, name_end - name);
        vu_str_cat_bytes(acc, (const uint8_t *)"\0", 1);
    }
    return 0;
}

/* group names as NUL-separated "N=name" entries */
vu_str vjq_re_names(void *p) {
    vu_str acc = {0};
    p_onig_foreach_name(((vjq_re *)p)->re, name_iter, &acc);
    return acc;
}

/* standard error, written at once (vjq keeps standard output in its own buffer, flushed where
   jq's stdio would have written it: see run.vu's flush_err) */
static void vjq_write_fd(int fd, const uint8_t *p, int64_t n) {
    while (n > 0) {
        ssize_t k = write(fd, p, (size_t)n);
        if (k < 0) { if (errno == EINTR) continue; return; }
        p += k; n -= k;
    }
}
void vjq_ewrite(const vu_str *s) {
    vjq_write_fd(2, s->data, s->len);
}
/* the first n bytes of b to standard output */
void vjq_owrite(uint8_t *b, int64_t nb, int64_t n) {
    if (n > nb) n = nb;
    vjq_write_fd(1, b, n);
}
/* how glibc buffers standard output (jq 1.7.1's release binaries are linked with it): 0 for a
   terminal (line buffered), else the buffer size (st_blksize when below BUFSIZ) */
int64_t vjq_stdout_blk(void) {
    struct stat st;
    int64_t size = BUFSIZ;
    if (fstat(1, &st) == 0) {
        if (S_ISCHR(st.st_mode) && isatty(1)) return 0;
        if (st.st_blksize > 0 && st.st_blksize < BUFSIZ) size = st.st_blksize;
    }
    return size;
}

#include <unistd.h>
bool vjq_isatty(int64_t fd) { return isatty((int)fd) != 0; }

/* Input files, read in pieces as jq reads them (so input needn't be held whole). */
void vjq_fclose(void *p) {
    if (p) fclose((FILE *)p);
}

bool vjq_fopen(const vu_str *path, void **out, vu_str *err) {
    char *z = vu_cstr(path);
    FILE *f = z ? fopen(z, "r") : NULL;
    int e = errno;
    free(z);
    if (!f) {
        const char *m = strerror(e);
        *err = vu_str_from(m, (int64_t)strlen(m));
        return false;
    }
    *out = f;
    return true;
}

/* up to n bytes; "" at the end. A read error (a directory...) is "" too, with bad[0] set to
   the errno. */
vu_str vjq_strerror(int64_t e) {
    const char *m = strerror((int)e);
    return vu_str_from(m, (int64_t)strlen(m));
}

vu_str vjq_fread(void *p, int64_t n, int64_t *bad, int64_t nb) {
    FILE *f = p;
    char *buf = malloc(n > 0 ? (size_t)n : 1);
    size_t got = fread(buf, 1, (size_t)n, f);
    if (nb > 0) bad[0] = (got == 0 && ferror(f)) ? errno : 0;
    vu_str r = vu_str_from(buf, (int64_t)got);
    free(buf);
    return r;
}

#include <sys/stat.h>
/* bytes left in a regular file, or -1 */
int64_t vjq_fleft(void *p) {
    FILE *f = p;
    struct stat sb;
    if (fstat(fileno(f), &sb) != 0 || !S_ISREG(sb.st_mode)) return -1;
    long pos = ftell(f);
    if (pos < 0) return -1;
    return (int64_t)sb.st_size - pos;
}

#include <limits.h>
/* realpath, or the path itself when it can't be resolved (as jq's jq_realpath) */
vu_str vjq_realpath(const vu_str *p) {
    char *z = vu_cstr(p);
    char buf[PATH_MAX];
    char *r = z ? realpath(z, buf) : NULL;
    vu_str out = r ? vu_str_from(r, (int64_t)strlen(r)) : vu_str_from(p->data ? (const char *)p->data : "", p->len);
    free(z);
    return out;
}

#include <libgen.h>
#include <fcntl.h>
#include <unistd.h>
/* C's dirname (as jq uses it for $ORIGIN and a module's folder) */
vu_str vjq_dirname(const vu_str *p) {
    char *z = vu_cstr(p);
    char *d = dirname(z ? z : (char *)".");
    vu_str out = vu_str_from(d, (int64_t)strlen(d));
    free(z);
    return out;
}

/* stat's errno for a path (0 when it exists) */
int64_t vjq_stat_errno(const vu_str *p) {
    char *z = vu_cstr(p);
    struct stat sb;
    int r = z ? stat(z, &sb) : -1;
    int e = r == 0 ? 0 : errno;
    free(z);
    return e;
}

/* jv_load_file's message when it can't open the file, or "" */
vu_str vjq_load_err(const vu_str *p) {
    char *z = vu_cstr(p);
    char buf[8192];
    buf[0] = 0;
    int fd = z ? open(z, O_RDONLY) : -1;
    if (fd == -1) {
        snprintf(buf, sizeof buf, "Could not open %s: %s", z ? z : "", strerror(errno));
    } else {
        struct stat sb;
        if (fstat(fd, &sb) == -1 || S_ISDIR(sb.st_mode))
            snprintf(buf, sizeof buf, "Could not open %s: %s", z, "It's a directory");
        close(fd);
    }
    free(z);
    return vu_str_from(buf, (int64_t)strlen(buf));
}

/* whether an environment variable is set (even to "") */
int64_t vjq_has_env(const vu_str *p) {
    char *z = vu_cstr(p);
    int r = z && getenv(z) != NULL;
    free(z);
    return r;
}
