/* JSON for to_json and from_json: string escaping for the encoder, and the decoder's scanner. The
   code for each type (vu_jenc_T, vu_jdec_T) is generated; these handle the plain values. */
static void vu_jcat(vu_str *o, const char *s, int64_t n) { vu_str_cat_bytes(o, (const uint8_t *)s, n); }
/* A JSON string: quotes, backslashes and control characters escaped; bytes that aren't UTF-8 become U+FFFD. */
static void vu_jenc_bytes(vu_str *o, const uint8_t *s, int64_t n) {
    static const char hex[] = "0123456789abcdef";
    vu_str_reserve(o, n + 2);
    vu_jcat(o, "\"", 1);
    int64_t i = 0, run = 0;
    while (i < n) {
        uint8_t c = s[i];
        if (c >= 0x20 && c < 0x80 && c != '"' && c != '\\') { i++; continue; }
        if (i > run) vu_str_cat_bytes(o, s + run, i - run);
        if (c == '"' || c == '\\') { char e[2] = {'\\', (char)c}; vu_jcat(o, e, 2); i++; }
        else if (c < 0x20) {
            const char *sh = c == '\n' ? "\\n" : c == '\t' ? "\\t" : c == '\r' ? "\\r" : c == '\b' ? "\\b" : c == '\f' ? "\\f" : NULL;
            if (sh) vu_jcat(o, sh, 2);
            else { char e[6] = {'\\', 'u', '0', '0', hex[c >> 4], hex[c & 15]}; vu_jcat(o, e, 6); }
            i++;
        } else {
            size_t k = vu_utf8_len(s + i, (size_t)(n - i));
            if (!k) { vu_jcat(o, "\\ufffd", 6); i++; }
            else { vu_str_cat_bytes(o, s + i, (int64_t)k); i += (int64_t)k; }
        }
        run = i;
    }
    if (i > run) vu_str_cat_bytes(o, s + run, i - run);
    vu_jcat(o, "\"", 1);
}
static void vu_jenc_Str(vu_str *o, const vu_str *v) { vu_jenc_bytes(o, v->data, v->len); }
static void vu_jenc_Int(vu_str *o, const int64_t *v) {
    char b[24];
    int n = snprintf(b, sizeof b, "%lld", (long long)*v);
    vu_jcat(o, b, n);
}
static void vu_jenc_Byte(vu_str *o, const uint8_t *v) { int64_t x = *v; vu_jenc_Int(o, &x); }
static void vu_jenc_Bool(vu_str *o, const bool *v) { if (*v) vu_jcat(o, "true", 4); else vu_jcat(o, "false", 5); }
/* NaN and the infinities have no JSON form: they become null, as in JavaScript. */
static void vu_jenc_Float(vu_str *o, const double *v) {
    if (!isfinite(*v)) { vu_jcat(o, "null", 4); return; }
    char b[40];
    const char *q = vu_shortest(*v, b);
    vu_jcat(o, q, (int64_t)strlen(q));
}
#define VU_JSON_DEPTH 1000
typedef struct {
    const uint8_t *s, *p, *end;
    int depth;
    vu_str err;    /* what went wrong, and where */
    vu_str path;   /* where in the value: items[3].qty (built as the decoders return) */
} vu_jp;
static bool vu_jfail(vu_jp *j, const char *what) {
    if (!j->err.len) {
        drop_Str(&j->err);
        j->err = vu_errf("%s at byte %lld", what, (long long)(j->p - j->s));
    }
    return false;
}
/* Puts a field name or a list index in front of the path to the error. Past 200 bytes the outer
   part is left out ("...") so deep data can't make a huge message. */
static void vu_jpath(vu_jp *j, const char *name, int64_t n, int64_t index) {
    if (j->path.len >= 200) {
        if (j->path.data[0] != '.') { vu_str p = {0}; vu_jcat(&p, "...", 3); vu_str_cat_bytes(&p, j->path.data, j->path.len); drop_Str(&j->path); j->path = p; }
        return;
    }
    vu_str p = {0};
    if (name) vu_str_cat_bytes(&p, (const uint8_t *)name, n);
    else { char b[32]; int k = snprintf(b, sizeof b, "[%lld]", (long long)index); vu_jcat(&p, b, k); }
    if (j->path.len && j->path.data[0] != '[') vu_jcat(&p, ".", 1);
    vu_str_cat_bytes(&p, j->path.data, j->path.len);
    drop_Str(&j->path);
    j->path = p;
}
static void vu_jws(vu_jp *j) {
    while (j->p < j->end && (*j->p == ' ' || *j->p == '\n' || *j->p == '\r' || *j->p == '\t')) j->p++;
}
static bool vu_jword(vu_jp *j, const char *w, size_t n) {
    if ((size_t)(j->end - j->p) >= n && memcmp(j->p, w, n) == 0) { j->p += n; return true; }
    return false;
}
/* Is the next value null? (Then it's read.) */
static bool vu_jnull(vu_jp *j) {
    vu_jws(j);
    return j->p < j->end && *j->p == 'n' && vu_jword(j, "null", 4);
}
static bool vu_jdec_Bool(vu_jp *j, bool *out) {
    vu_jws(j);
    if (vu_jword(j, "true", 4)) { *out = true; return true; }
    if (vu_jword(j, "false", 5)) { *out = false; return true; }
    return vu_jfail(j, "expected true or false");
}
/* The extent of a JSON number: -?(0|[1-9][0-9]*)(.[0-9]+)?([eE][+-]?[0-9]+)?; whole says it has no
   fraction or exponent. */
static bool vu_jnum(vu_jp *j, const uint8_t **a, bool *whole) {
    vu_jws(j);
    const uint8_t *p = j->p, *e = j->end;
    *a = p;
    *whole = true;
    if (p < e && *p == '-') p++;
    if (p < e && *p == '0') p++;
    else if (p < e && *p >= '1' && *p <= '9') { while (p < e && *p >= '0' && *p <= '9') p++; }
    else return vu_jfail(j, "expected a number");
    if (p < e && *p == '.') {
        p++;
        *whole = false;
        if (!(p < e && *p >= '0' && *p <= '9')) { j->p = p; return vu_jfail(j, "expected a digit after '.'"); }
        while (p < e && *p >= '0' && *p <= '9') p++;
    }
    if (p < e && (*p == 'e' || *p == 'E')) {
        p++;
        *whole = false;
        if (p < e && (*p == '+' || *p == '-')) p++;
        if (!(p < e && *p >= '0' && *p <= '9')) { j->p = p; return vu_jfail(j, "expected a digit in the exponent"); }
        while (p < e && *p >= '0' && *p <= '9') p++;
    }
    j->p = p;
    return true;
}
static bool vu_jdec_Int(vu_jp *j, int64_t *out) {
    const uint8_t *a;
    bool whole;
    if (!vu_jnum(j, &a, &whole)) return false;
    if (!whole) { j->p = a; return vu_jfail(j, "expected a whole number"); }
    bool neg = *a == '-';
    uint64_t v = 0, lim = neg ? (uint64_t)INT64_MAX + 1 : (uint64_t)INT64_MAX;
    for (const uint8_t *q = a + neg; q < j->p; q++) {
        uint64_t d = (uint64_t)(*q - '0');
        if (v > (lim - d) / 10) { j->p = a; return vu_jfail(j, "number too large for an Int"); }
        v = v * 10 + d;
    }
    *out = neg ? (int64_t)(0 - v) : (int64_t)v;
    return true;
}
static bool vu_jdec_Byte(vu_jp *j, uint8_t *out) {
    const uint8_t *a = j->p;
    int64_t v;
    if (!vu_jdec_Int(j, &v)) return false;
    if (v < 0 || v > 255) { j->p = a; vu_jws(j); return vu_jfail(j, "expected a number from 0 to 255"); }
    *out = (uint8_t)v;
    return true;
}
static bool vu_jdec_Float(vu_jp *j, double *out) {
    const uint8_t *a;
    bool whole;
    if (!vu_jnum(j, &a, &whole)) return false;
    vu_str view = {(uint8_t *)a, (int64_t)(j->p - a), 0}, e = {0};
    if (!vu_parse_float(&view, out, &e)) { drop_Str(&e); j->p = a; return vu_jfail(j, "expected a number"); }
    if (!isfinite(*out)) { j->p = a; return vu_jfail(j, "number too large for a Float"); }
    return true;
}
static int vu_jhex4(const uint8_t *p) {
    int v = 0;
    for (int i = 0; i < 4; i++) {
        int c = p[i], d = c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1;
        if (d < 0) return -1;
        v = v * 16 + d;
    }
    return v;
}
static void vu_jutf8(vu_str *o, int cp) {
    uint8_t b[4];
    int n;
    if (cp < 0x80) { b[0] = (uint8_t)cp; n = 1; }
    else if (cp < 0x800) { b[0] = (uint8_t)(0xC0 | (cp >> 6)); b[1] = (uint8_t)(0x80 | (cp & 0x3F)); n = 2; }
    else if (cp < 0x10000) { b[0] = (uint8_t)(0xE0 | (cp >> 12)); b[1] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F)); b[2] = (uint8_t)(0x80 | (cp & 0x3F)); n = 3; }
    else { b[0] = (uint8_t)(0xF0 | (cp >> 18)); b[1] = (uint8_t)(0x80 | ((cp >> 12) & 0x3F)); b[2] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F)); b[3] = (uint8_t)(0x80 | (cp & 0x3F)); n = 4; }
    vu_str_cat_bytes(o, b, n);
}
/* A string (the opening quote is next): escapes decoded, UTF-8 checked. */
static bool vu_jdec_Str(vu_jp *j, vu_str *out) {
    vu_jws(j);
    if (j->p >= j->end || *j->p != '"') return vu_jfail(j, "expected a string");
    const uint8_t *p = ++j->p, *e = j->end;
    vu_str s = {0};
    for (;;) {
        const uint8_t *run = p;
        while (p < e && *p >= 0x20 && *p != '"' && *p != '\\' && *p < 0x80) p++;
        if (p > run) vu_str_cat_bytes(&s, run, (int64_t)(p - run));
        if (p >= e) { j->p = p; drop_Str(&s); return vu_jfail(j, "unterminated string"); }
        uint8_t c = *p;
        if (c == '"') { j->p = p + 1; *out = s; return true; }
        if (c < 0x20) { j->p = p; drop_Str(&s); return vu_jfail(j, "control character in a string"); }
        if (c >= 0x80) {
            size_t k = vu_utf8_len(p, (size_t)(e - p));
            if (!k) { j->p = p; drop_Str(&s); return vu_jfail(j, "invalid UTF-8 in a string"); }
            vu_str_cat_bytes(&s, p, (int64_t)k);
            p += k;
            continue;
        }
        /* a backslash */
        if (p + 1 >= e) { j->p = p; drop_Str(&s); return vu_jfail(j, "unterminated string"); }
        uint8_t x = p[1];
        const char *simple = x == '"' ? "\"" : x == '\\' ? "\\" : x == '/' ? "/" : x == 'n' ? "\n" : x == 't' ? "\t"
                           : x == 'r' ? "\r" : x == 'b' ? "\b" : x == 'f' ? "\f" : NULL;
        if (simple) { vu_jcat(&s, simple, 1); p += 2; continue; }
        if (x != 'u') { j->p = p; drop_Str(&s); return vu_jfail(j, "bad escape in a string"); }
        int cp = e - p >= 6 ? vu_jhex4(p + 2) : -1;
        if (cp < 0) { j->p = p; drop_Str(&s); return vu_jfail(j, "bad \\u escape"); }
        p += 6;
        if (cp >= 0xD800 && cp < 0xDC00) {
            int lo = e - p >= 6 && p[0] == '\\' && p[1] == 'u' ? vu_jhex4(p + 2) : -1;
            if (lo < 0xDC00 || lo >= 0xE000) { j->p = p - 6; drop_Str(&s); return vu_jfail(j, "unpaired surrogate in a string"); }
            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
            p += 6;
        } else if (cp >= 0xDC00 && cp < 0xE000) { j->p = p - 6; drop_Str(&s); return vu_jfail(j, "unpaired surrogate in a string"); }
        vu_jutf8(&s, cp);
    }
}
static bool vu_jdeeper(vu_jp *j) {
    if (++j->depth > VU_JSON_DEPTH) return vu_jfail(j, "nested deeper than 1000 levels");
    return true;
}
/* Arrays: begin reads '['; next says whether a value follows (1), the array ended (0), or it's malformed (-1). */
static bool vu_jarr_begin(vu_jp *j) {
    vu_jws(j);
    if (j->p >= j->end || *j->p != '[') return vu_jfail(j, "expected a list");
    j->p++;
    return vu_jdeeper(j);
}
static int vu_jarr_next(vu_jp *j, bool first) {
    vu_jws(j);
    if (j->p < j->end && *j->p == ']') { j->p++; j->depth--; return 0; }
    if (!first) {
        if (j->p >= j->end || *j->p != ',') { vu_jfail(j, "expected ',' or ']'"); return -1; }
        j->p++;
    }
    return 1;
}
/* Objects: next reads a key and its ':' (1), the end '}' (0), or fails (-1). */
static bool vu_jobj_begin(vu_jp *j) {
    vu_jws(j);
    if (j->p >= j->end || *j->p != '{') return vu_jfail(j, "expected an object");
    j->p++;
    return vu_jdeeper(j);
}
static int vu_jobj_next(vu_jp *j, bool first, vu_str *key) {
    vu_jws(j);
    if (j->p < j->end && *j->p == '}') { j->p++; j->depth--; return 0; }
    if (!first) {
        if (j->p >= j->end || *j->p != ',') { vu_jfail(j, "expected ',' or '}'"); return -1; }
        j->p++;
        vu_jws(j);
    }
    if (!vu_jdec_Str(j, key)) return -1;
    vu_jws(j);
    if (j->p >= j->end || *j->p != ':') { drop_Str(key); vu_jfail(j, "expected ':'"); return -1; }
    j->p++;
    return 1;
}
static bool vu_jkey(const vu_str *k, const char *name, int64_t n) { return k->len == n && memcmp(k->data, name, (size_t)n) == 0; }
/* Skips any value (a field the type doesn't have). */
static bool vu_jskip(vu_jp *j) {
    vu_jws(j);
    if (j->p >= j->end) return vu_jfail(j, "expected a value");
    uint8_t c = *j->p;
    if (c == '"') { vu_str s = {0}; if (!vu_jdec_Str(j, &s)) return false; drop_Str(&s); return true; }
    if (c == 't' || c == 'f') { bool b; return vu_jdec_Bool(j, &b); }
    if (c == 'n') { if (vu_jnull(j)) return true; return vu_jfail(j, "expected a value"); }
    if (c == '[') {
        if (!vu_jarr_begin(j)) return false;
        for (bool first = true;; first = false) {
            int r = vu_jarr_next(j, first);
            if (r <= 0) return r == 0;
            if (!vu_jskip(j)) return false;
        }
    }
    if (c == '{') {
        if (!vu_jobj_begin(j)) return false;
        for (bool first = true;; first = false) {
            vu_str k = {0};
            int r = vu_jobj_next(j, first, &k);
            if (r <= 0) return r == 0;
            drop_Str(&k);
            if (!vu_jskip(j)) return false;
        }
    }
    const uint8_t *a;
    bool whole;
    return vu_jnum(j, &a, &whole);
}
/* After the whole value: only whitespace may follow. Then the error, if any, gets its path. */
static bool vu_jdone(vu_jp *j, bool ok, vu_str *err) {
    if (ok) {
        vu_jws(j);
        if (j->p != j->end) ok = vu_jfail(j, "extra data after the JSON value");
    }
    if (!ok) {
        if (j->path.len) {
            vu_str m = {0};
            vu_str_cat_bytes(&m, j->path.data, j->path.len);
            vu_jcat(&m, ": ", 2);
            vu_str_cat_bytes(&m, j->err.data, j->err.len);
            drop_Str(&j->err);
            *err = m;
        } else *err = j->err;
        j->err = (vu_str){0};
    }
    drop_Str(&j->path);
    return ok;
}