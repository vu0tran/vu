/* Test glue header: no state of its own (each part of a split build has a copy), so its functions
   are inlined into their callers. A column of Ints in a growable buffer, freed by its handle. */
#define COL_SCALE 1
typedef struct { int64_t *p; int64_t n, cap; } col;
static inline void col_free(void *h) { free(((col *)h)->p); free(h); }
static inline void *col_new(void) { return calloc(1, sizeof(col)); }
static inline int64_t col_push(void *h, int64_t v) {
    col *c = h;
    if (c->n == c->cap) { c->cap = c->cap ? c->cap * 2 : 4; c->p = realloc(c->p, (size_t)c->cap * sizeof *c->p); }
    c->p[c->n] = v * COL_SCALE;
    return c->n++;
}
static inline int64_t col_at(void *h, int64_t i) {
    col *c = h;
    if (i < 0 || i >= c->n) vu_panic(0, "col_at: out of range", 20);
    return c->p[i];
}
static inline int64_t col_len(void *h) { return ((col *)h)->n; }
