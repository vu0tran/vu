// The checker's flat Int tables as C columns: each in one reserved region (pages committed as they
// are touched, never moved), so a reader needs no lock and no indirection, and a fork shares it
// copy-on-write. The length is kept before the first entry and published with a release store
// (ts/NOTES.md, "Checking one program on several workers").
#include <stdint.h>
#include <stdlib.h>
#include <sys/mman.h>
#define CT_MAX ((int64_t)1 << 28)  // entries a column can hold (2 GB of address space, reserved only)

// The tables a checker uses are made through one store (types.Store, the owner: the task that made
// it keeps it until every task that reads the tables is done). What a checker's state holds are
// views (types.Tab, Lst, Ph, Grp): their drop does nothing, and a view can be made again in another
// task from its address as an Int (ct_addr, ct_view). The store's own bookkeeping is filled only
// while the tables are made, by one task.
typedef struct { void **p; uint8_t *k; int64_t n, cap; } cs_t;
static inline void *cs_new(void) {
  cs_t *s = calloc(1, sizeof *s);
  if (!s) vu_panic(0, "cs_new: out of memory", 21);
  return s;
}
static inline void cs_add(cs_t *s, void *p, uint8_t k) {
  if (s->n == s->cap) {
    s->cap = s->cap ? 2 * s->cap : 64;
    s->p = realloc(s->p, (size_t)s->cap * sizeof *s->p);
    s->k = realloc(s->k, (size_t)s->cap);
    if (!s->p || !s->k) vu_panic(0, "cs_add: out of memory", 21);
  }
  s->p[s->n] = p;
  s->k[s->n] = k;
  s->n += 1;
}
static inline void ct_keep(void *h) { (void)h; }
static inline void cl_keep(void *h) { (void)h; }
static inline void ph_keep(void *h) { (void)h; }
static inline void cg_keep(void *h) { (void)h; }
static inline int64_t ct_addr(void *h) { return (int64_t)(intptr_t)h; }
static inline void *ct_view(int64_t a) {
  if (a == 0) vu_panic(0, "ct_view: no table", 17);
  return (void *)(intptr_t)a;
}
static inline int64_t cl_addr(void *h) { return ct_addr(h); }
static inline void *cl_view(int64_t a) { return ct_view(a); }
static inline int64_t ph_addr(void *h) { return ct_addr(h); }
static inline void *ph_view(int64_t a) { return ct_view(a); }
static inline int64_t cg_addr(void *h) { return ct_addr(h); }
static inline void *cg_view(int64_t a) { return ct_view(a); }

// A table group: the row counter several columns share (a type's tk tf ta tb, an object's columns,
// a signature's, a symbol's). A row is taken once (cg_row, a fetch-add), its entries written
// (ct_put, cl_init), and the row's index handed to other tasks only after that.
static inline void *cg_new(void *st) {
  int64_t *g = calloc(1, 64);
  if (!g) vu_panic(0, "cg_new: out of memory", 21);
  cs_add(st, g, 3);
  return g;
}
static inline int64_t cg_row(void *g) {
  int64_t r = __atomic_fetch_add((int64_t *)g, 1, __ATOMIC_RELAXED);
  if (r >= CT_MAX / 2) vu_panic(0, "cg_row: a table group is full", 29);
  return r;
}
static inline int64_t cg_len(void *g) { return __atomic_load_n((const int64_t *)g, __ATOMIC_ACQUIRE); }
static inline void *ct_mk(void) {
  int64_t *r = mmap(NULL, (size_t)(CT_MAX + 2) * 8, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON | MAP_NORESERVE, -1, 0);
  if (r == MAP_FAILED) {
    vu_panic(0, "ct_new: no address space for a column", 37);
  }
  r[0] = 0;
  return r + 2;
}
static inline void ct_free(void *h) { munmap((int64_t *)h - 2, (size_t)(CT_MAX + 2) * 8); }
static inline void *ct_new(void *st) {
  void *t = ct_mk();
  cs_add(st, t, 0);
  return t;
}
// the column's length raised to at least n (a row of its group written: ct_put, cl_init)
static inline void ct_cover(int64_t *p, int64_t n) {
  int64_t l = __atomic_load_n(&p[-2], __ATOMIC_RELAXED);
  while (l < n && !__atomic_compare_exchange_n(&p[-2], &l, n, true, __ATOMIC_RELEASE, __ATOMIC_RELAXED)) {
  }
}
// entry r of a row its group gave (cg_row) written
static inline void ct_put(void *h, int64_t r, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)r >= (uint64_t)CT_MAX) vu_panic(0, "ct_put: index out of range", 26);
  p[r] = v;
  ct_cover(p, r + 1);
}
// xs appended as one run (a union's or intersection's members): where it starts
static inline int64_t ct_run(void *h, const int64_t *xs, int64_t n) {
  int64_t *p = h;
  int64_t at = __atomic_fetch_add(&p[-1], n, __ATOMIC_RELAXED);
  if (at + n > CT_MAX) vu_panic(0, "ct_run: a column is full", 24);
  for (int64_t i = 0; i < n; i++) p[at + i] = xs[i];
  ct_cover(p, at + n);
  return at;
}
static inline int64_t ct_at(void *h, int64_t i) {
  const int64_t *p = h;
  // (a plain load: a reader only asks for entries made before it was given their index)
  if (__builtin_expect((uint64_t)i >= (uint64_t)p[-2], 0)) vu_panic(0, "ct_at: index out of range", 25);
  return p[i];
}
static inline void ct_set(void *h, int64_t i, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)p[-2]) vu_panic(0, "ct_set: index out of range", 26);
  p[i] = v;
}
// An entry set once: from -1 (unset) to v with a compare-and-swap; -1 when this call set it, else the
// value that was there (which a second publisher must find equal to its own: types.sty_put).
static inline int64_t ct_publish(void *h, int64_t i, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)p[-2]) vu_panic(0, "ct_publish: index out of range", 30);
  int64_t old = -1;
  if (__atomic_compare_exchange_n(&p[i], &old, v, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) return -1;
  return old;
}
static inline int64_t ct_len(void *h) { return __atomic_load_n(&((const int64_t *)h)[-2], __ATOMIC_ACQUIRE); }

// A list column: a list of Ints per row, each row an (offset, length) pair into a pool of Ints, both
// append-only regions as above. A row is changed by writing its list again at the pool's end (or, when
// it already ends the pool, by appending to it), so an entry once written is never moved or overwritten
// by another row's list.
typedef struct { int64_t *row; int64_t *pool; } cl_t;
static inline void *cl_new(void *st) {
  cl_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "cl_new: out of memory", 21);
  h->row = ct_mk();
  h->pool = ct_mk();
  cs_add(st, h, 1);
  return h;
}
static inline void cl_free(void *p) {
  cl_t *h = p;
  ct_free(h->row);
  ct_free(h->pool);
  free(h);
}
static inline int64_t cl_rows(void *p) { return ct_len(((cl_t *)p)->row) >> 1; }
// row r (from its group: cg_row) made, holding an empty list (the region is zero: (0, 0) already)
static inline void cl_init(void *p, int64_t r) {
  cl_t *h = p;
  if ((uint64_t)r >= (uint64_t)(CT_MAX / 2)) vu_panic(0, "cl_init: row out of range", 25);
  h->row[2 * r] = 0;
  h->row[2 * r + 1] = 0;
  ct_cover(h->row, 2 * r + 2);
}
static inline int64_t *cl_rp(cl_t *h, int64_t r) {
  if (__builtin_expect((uint64_t)r >= (uint64_t)(h->row[-2] >> 1), 0)) vu_panic(0, "cl: row out of range", 20);
  return &h->row[2 * r];
}
static inline int64_t cl_len(void *p, int64_t r) { return cl_rp(p, r)[1]; }
static inline int64_t cl_at(void *p, int64_t r, int64_t i) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  if (__builtin_expect((uint64_t)i >= (uint64_t)rp[1], 0)) vu_panic(0, "cl_at: index out of range", 25);
  return h->pool[rp[0] + i];
}
static inline void cl_put(void *p, int64_t r, int64_t i, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  if ((uint64_t)i >= (uint64_t)rp[1]) vu_panic(0, "cl_put: index out of range", 26);
  h->pool[rp[0] + i] = v;
}
static inline void cl_need(cl_t *h, int64_t n) {
  if (h->pool[-2] + n > CT_MAX) vu_panic(0, "cl: a list pool is full", 23);
}
// the row's list moved to the pool's end (unless it is there already), so that it can grow there
static inline int64_t *cl_tail(cl_t *h, int64_t r, int64_t extra) {
  int64_t *rp = cl_rp(h, r);
  int64_t off = rp[0], n = rp[1], end = h->pool[-2];
  if (off + n != end || n == 0) {
    cl_need(h, n + extra);
    for (int64_t i = 0; i < n; i++) h->pool[end + i] = h->pool[off + i];
    __atomic_store_n(&h->pool[-2], end + n, __ATOMIC_RELEASE);
    rp[0] = end;
  } else {
    cl_need(h, extra);
  }
  return rp;
}
static inline void cl_add(void *p, int64_t r, int64_t v) {
  cl_t *h = p;
  int64_t *rp = cl_tail(h, r, 1);
  int64_t end = h->pool[-2];
  h->pool[end] = v;
  __atomic_store_n(&h->pool[-2], end + 1, __ATOMIC_RELEASE);
  rp[1] += 1;
}
static inline void cl_pop(void *p, int64_t r) {
  int64_t *rp = cl_rp(p, r);
  if (rp[1] == 0) vu_panic(0, "cl_pop: the list is empty", 25);
  rp[1] -= 1;
}
static inline void cl_set(void *p, int64_t r, const int64_t *xs, int64_t n) {
  cl_t *h = p;
  int64_t *rp = cl_rp(h, r);
  int64_t end = h->pool[-2];
  cl_need(h, n);
  for (int64_t i = 0; i < n; i++) h->pool[end + i] = xs[i];
  __atomic_store_n(&h->pool[-2], end + n, __ATOMIC_RELEASE);
  rp[0] = end;
  rp[1] = n;
}
static inline void cl_fill(void *p, int64_t r, int64_t *out, int64_t n) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  if (n > rp[1]) n = rp[1];
  for (int64_t i = 0; i < n; i++) out[i] = h->pool[rp[0] + i];
}
static inline bool cl_has(void *p, int64_t r, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  const int64_t *xs = &h->pool[rp[0]];
  for (int64_t i = 0; i < rp[1]; i++)
    if (xs[i] == v) return true;
  return false;
}

// Object types' properties by (object, name): an open-addressed table of (key, symbol), the key
// object << 32 | name (both under 2^31), linear probing, doubled at half full. The names in insertion
// order are a list column beside it (types.add_prop).
typedef struct { int64_t *slot; int64_t cap; int64_t n; } ph_t;
static inline void *ph_new(void *st) {
  ph_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "ph_new: out of memory", 21);
  h->cap = 1 << 16;
  h->n = 0;
  h->slot = malloc((size_t)h->cap * 16);
  if (!h->slot) vu_panic(0, "ph_new: out of memory", 21);
  for (int64_t i = 0; i < h->cap; i++) h->slot[2 * i] = -1;
  cs_add(st, h, 2);
  return h;
}
static inline void ph_free(void *p) {
  ph_t *h = p;
  free(h->slot);
  free(h);
}
static inline uint64_t ph_hash(int64_t k) {
  uint64_t x = (uint64_t)k * 0x9E3779B97F4A7C15ull;
  return x ^ (x >> 31);
}
// the symbol of o's property name, -1 none
static inline int64_t ph_get(void *p, int64_t o, int64_t name) {
  const ph_t *h = p;
  int64_t k = o << 32 | name, m = h->cap - 1;
  for (int64_t i = (int64_t)(ph_hash(k) & (uint64_t)m);; i = (i + 1) & m) {
    int64_t s = h->slot[2 * i];
    if (s == k) return h->slot[2 * i + 1];
    if (s == -1) return -1;
  }
}
static inline void ph_grow(ph_t *h) {
  int64_t oc = h->cap, *os = h->slot;
  h->cap = oc * 2;
  h->slot = malloc((size_t)h->cap * 16);
  if (!h->slot) vu_panic(0, "ph_grow: out of memory", 22);
  for (int64_t i = 0; i < h->cap; i++) h->slot[2 * i] = -1;
  int64_t m = h->cap - 1;
  for (int64_t j = 0; j < oc; j++) {
    int64_t k = os[2 * j];
    if (k == -1) continue;
    int64_t i = (int64_t)(ph_hash(k) & (uint64_t)m);
    while (h->slot[2 * i] != -1) i = (i + 1) & m;
    h->slot[2 * i] = k;
    h->slot[2 * i + 1] = os[2 * j + 1];
  }
  free(os);
}
// o's property name set to sym: true when it is a new property
static inline bool ph_put(void *p, int64_t o, int64_t name, int64_t sym) {
  ph_t *h = p;
  if ((uint64_t)o >= ((uint64_t)1 << 31) || (uint64_t)name >= ((uint64_t)1 << 32) || sym < 0) vu_panic(0, "ph_put: out of range", 20);
  if (2 * (h->n + 1) > h->cap) ph_grow(h);
  int64_t k = o << 32 | name, m = h->cap - 1;
  for (int64_t i = (int64_t)(ph_hash(k) & (uint64_t)m);; i = (i + 1) & m) {
    int64_t s = h->slot[2 * i];
    if (s == k) {
      h->slot[2 * i + 1] = sym;
      return false;
    }
    if (s == -1) {
      h->slot[2 * i + 1] = sym;
      h->slot[2 * i] = k;
      h->n += 1;
      return true;
    }
  }
}

// every table the store made freed
static inline void cs_free(void *p) {
  cs_t *s = p;
  for (int64_t i = 0; i < s->n; i++) {
    switch (s->k[i]) {
      case 0: ct_free(s->p[i]); break;
      case 1: cl_free(s->p[i]); break;
      case 2: ph_free(s->p[i]); break;
      default: free(s->p[i]);
    }
  }
  free(s->p);
  free(s->k);
  free(s);
}
