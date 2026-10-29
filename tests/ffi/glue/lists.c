/* Lists of numbers and bytes as pointers: read, changed in place, empty (the pointer may be NULL). */
static int64_t sum_i(const int64_t *p, int64_t n) { int64_t s = 0; for (int64_t i = 0; i < n; i++) s += p[i]; return s; }
static double sum_f(const double *p, int64_t n) { double s = 0; for (int64_t i = 0; i < n; i++) s += p[i]; return s; }
static int64_t count_b(const uint8_t *p, int64_t n, uint8_t b) { int64_t c = 0; for (int64_t i = 0; i < n; i++) c += p[i] == b; return c; }
static void scale(double *p, int64_t n, double k) { for (int64_t i = 0; i < n; i++) p[i] *= k; }
static void negate(int64_t *p, int64_t n) { for (int64_t i = 0; i < n; i++) p[i] = -p[i]; }
/* writes "abc..." into the buffer, returns how many bytes it wrote */
static int64_t fill(uint8_t *p, int64_t n, int64_t want) {
    int64_t m = want < n ? want : n;
    for (int64_t i = 0; i < m; i++) p[i] = (uint8_t)('a' + i % 26);
    return m;
}
static bool checked_sum(const int64_t *p, int64_t n, int64_t *out, vu_str *err) {
    if (n == 0) { *err = vu_errf("empty"); return false; }
    *out = sum_i(p, n);
    return true;
}
/* two lists in one call */
static double dot(const double *a, int64_t n, const double *b, int64_t m) {
    double s = 0; for (int64_t i = 0; i < n && i < m; i++) s += a[i] * b[i]; return s;
}
