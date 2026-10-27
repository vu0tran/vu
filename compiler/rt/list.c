static inline @@E@@ *vu_at_@@M@@(@@L@@ *l, int64_t i, int line) {
    /* one unsigned comparison: also catches i < 0, and measured faster than two signed ones (n-body 17%) */
    if (__builtin_expect((uint64_t)i >= (uint64_t)l->len, 0)) vu_oob(i, l->len, line);
    return &l->data[i];
}
static void vu_grow_@@M@@(@@L@@ *l) {
    if (l->cap > (int64_t)(PTRDIFF_MAX / sizeof(@@E@@) / 2)) vu_oom();
    int64_t c = l->cap ? l->cap * 2 : 4;
    @@E@@ *d = (@@E@@ *)realloc(l->data, (size_t)c * sizeof(@@E@@));
    if (!d) vu_oom();
    l->data = d;
    l->cap = c;
}
static void vu_reserve_@@M@@(@@L@@ *l, int64_t n, int line) {
    if (n < 0) vu_fail(line, "reserve(%lld): the count can't be negative", (long long)n);
    if (n <= l->cap - l->len) return;
    if (n > (int64_t)(PTRDIFF_MAX / sizeof(@@E@@)) - l->len) vu_oom();
    int64_t c = l->len + n;
    @@E@@ *d = (@@E@@ *)realloc(l->data, (size_t)c * sizeof(@@E@@));
    if (!d) vu_oom();
    l->data = d;
    l->cap = c;
}
static inline @@E@@ vu_pop_@@M@@(@@L@@ *l, int line) {
    if (__builtin_expect(l->len == 0, 0)) vu_fail(line, "pop() from an empty list");
    return l->data[--l->len];
}
static inline void vu_push_@@M@@(@@L@@ *l, @@E@@ v) {
    if (l->len == l->cap) vu_grow_@@M@@(l);
    l->data[l->len++] = v;
}
static @@L@@ vu_rep_@@M@@(@@L@@ src, int64_t n, int line) {
    @@L@@ r = {0};
    if (n > 0 && src.len > 0) {
        if (n > INT64_MAX / src.len || src.len * n > (int64_t)(PTRDIFF_MAX / sizeof(@@E@@)))
            vu_fail(line, "list of %lld x %lld elements is too large", (long long)src.len, (long long)n);
        int64_t total = src.len * n;
        r.data = (@@E@@ *)vu_malloc((size_t)total * sizeof(@@E@@));
        r.len = r.cap = total;
        if (src.len == 1) { @@E@@ v = src.data[0]; for (int64_t k = 0; k < total; k++) r.data[k] = v; }
        else for (int64_t k = 0; k < n; k++) memcpy(r.data + k * src.len, src.data, (size_t)src.len * sizeof(@@E@@));
    }
    free(src.data);
    return r;
}