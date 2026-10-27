/* Reading floats from text. Three steps, each exact:
   1. Clinger: the digits form m < 2^53 and the power of ten is at most 22, so m and 10^e are exact
      doubles and one multiply or divide is correctly rounded.
   2. Eisel-Lemire: up to 19 significant digits, using a table of 128-bit powers of ten. It either
      produces the correctly rounded result or reports that it can't decide.
   3. Otherwise, strtod.
   All three give the same double strtod would. */
static bool vu_eisel_lemire(uint64_t man, int64_t e10, bool neg, double *out) {
    if (man == 0) { *out = neg ? -0.0 : 0.0; return true; }
    if (e10 < -348 || e10 > 347) return false;
    int clz = __builtin_clzll(man);
    man <<= clz;
    uint64_t ret_exp2 = (uint64_t)(((217706 * e10) >> 16) + 64 + 1023) - (uint64_t)clz;
    const uint64_t *pw = vu_pow10_128[e10 + 348];
    unsigned __int128 x = (unsigned __int128)man * pw[1];
    uint64_t x_hi = (uint64_t)(x >> 64), x_lo = (uint64_t)x;
    if ((x_hi & 0x1FF) == 0x1FF && x_lo + man < man) {
        unsigned __int128 y = (unsigned __int128)man * pw[0];
        uint64_t y_hi = (uint64_t)(y >> 64), y_lo = (uint64_t)y;
        uint64_t merged_hi = x_hi, merged_lo = x_lo + y_hi;
        if (merged_lo < x_lo) merged_hi++;
        if ((merged_hi & 0x1FF) == 0x1FF && merged_lo + 1 == 0 && y_lo + man < man) return false;
        x_hi = merged_hi;
        x_lo = merged_lo;
    }
    uint64_t msb = x_hi >> 63;
    uint64_t ret_man = x_hi >> (msb + 9);
    ret_exp2 -= 1 ^ msb;
    if (x_lo == 0 && (x_hi & 0x1FF) == 0 && (ret_man & 3) == 1) return false;
    ret_man += ret_man & 1;
    ret_man >>= 1;
    if (ret_man >> 53 > 0) { ret_man >>= 1; ret_exp2 += 1; }
    if (ret_exp2 - 1 >= 0x7FF - 1) return false;
    uint64_t bits = ret_exp2 << 52 | (ret_man & 0x000FFFFFFFFFFFFFULL);
    if (neg) bits |= 0x8000000000000000ULL;
    memcpy(out, &bits, sizeof *out);
    return true;
}
static bool vu_float_fast(const uint8_t *d, int64_t n, double *out) {
    static const double p10[] = {1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11,
                                 1e12, 1e13, 1e14, 1e15, 1e16, 1e17, 1e18, 1e19, 1e20, 1e21, 1e22};
    int64_t i = 0;
    bool neg = false;
    if (i < n && (d[i] == '-' || d[i] == '+')) { neg = d[i] == '-'; i++; }
    uint64_t m = 0;
    int digits = 0, ndig = 0;
    int64_t scale = 0;
    for (; i < n && d[i] >= '0' && d[i] <= '9'; i++, ndig++) {
        if (m || d[i] != '0') { if (++digits > 19) return false; m = m * 10 + (uint64_t)(d[i] - '0'); }
    }
    if (i < n && d[i] == '.') {
        for (i++; i < n && d[i] >= '0' && d[i] <= '9'; i++, ndig++) {
            if (m || d[i] != '0') { if (++digits > 19) return false; m = m * 10 + (uint64_t)(d[i] - '0'); }
            scale--;
        }
    }
    if (ndig == 0) return false;
    if (i < n && (d[i] == 'e' || d[i] == 'E')) {
        i++;
        bool eneg = false;
        if (i < n && (d[i] == '-' || d[i] == '+')) { eneg = d[i] == '-'; i++; }
        if (i >= n) return false;
        int64_t e = 0;
        for (; i < n && d[i] >= '0' && d[i] <= '9'; i++) { if (e > 100000) return false; e = e * 10 + (d[i] - '0'); }
        scale += eneg ? -e : e;
    }
    if (i != n) return false;
    if (m <= (1ULL << 53) && scale >= -22 && scale <= 22) {
        double v = (double)m;
        v = scale < 0 ? v / p10[-scale] : v * p10[scale];
        *out = neg ? -v : v;
        return true;
    }
    return vu_eisel_lemire(m, scale, neg, out);
}
static bool vu_parse_float(const vu_str *s, double *out, vu_str *err) {
    if (s->len > 0 && vu_float_fast(s->data, s->len, out)) return true;
    char buf[400];
    if (s->len <= 0 || s->len >= (int64_t)sizeof buf) { *err = vu_errf("not a number (%lld bytes)", (long long)s->len); return false; }
    bool digit = false;
    for (int64_t i = 0; i < s->len; i++) {
        uint8_t c = s->data[i];
        if (c >= '0' && c <= '9') digit = true;
        else if (c != '+' && c != '-' && c != '.' && c != 'e' && c != 'E') { digit = false; break; }
    }
    memcpy(buf, s->data, (size_t)s->len);
    buf[s->len] = 0;
    char *end;
    double v = digit ? strtod(buf, &end) : 0;
    if (!digit || *end) { *err = vu_errf("not a number: '%.100s'", buf); return false; }
    *out = v;
    return true;
}
static bool vu_parse_float_at(const vu_str *s, int64_t a, int64_t b, double *out, vu_str *err, int line) {
    vu_slice_check(s, a, b, line);
    vu_str view = {s->data ? s->data + a : NULL, b - a, 0};
    return vu_parse_float(&view, out, err);
}
