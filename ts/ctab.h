// The checker's flat Int tables as C columns: each in one reserved region (pages committed as they
// are touched, never moved), so a reader needs no lock and no indirection, and a fork shares it
// copy-on-write. The length is kept before the first entry and published with a release store
// (ts/NOTES.md, "Checking one program on several workers").
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
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
// n consecutive rows taken at once (a literal type and its fresh copy): the first
static inline int64_t cg_rows(void *g, int64_t n) {
  int64_t r = __atomic_fetch_add((int64_t *)g, n, __ATOMIC_RELAXED);
  if (r + n > CT_MAX / 2) vu_panic(0, "cg_rows: a table group is full", 30);
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
// a column's length, as a bounds check reads it (relaxed: no order needed, see ct_at)
static inline int64_t ct_len0(const int64_t *p) { return __atomic_load_n(&p[-2], __ATOMIC_RELAXED); }
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
  // (the entry a plain load: a reader only asks for entries made before it was given their index;
  // the length a relaxed one, since other tasks raise it meanwhile: the same instruction)
  if (__builtin_expect((uint64_t)i >= (uint64_t)ct_len0(p), 0)) vu_panic(0, "ct_at: index out of range", 25);
  return p[i];
}
static inline void ct_set(void *h, int64_t i, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)ct_len0(p)) vu_panic(0, "ct_set: index out of range", 26);
  p[i] = v;
}
// An entry set once: from -1 (unset) to v with a compare-and-swap; -1 when this call set it, else the
// value that was there (which a second publisher must find equal to its own: types.sty_put).
static inline int64_t ct_publish(void *h, int64_t i, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)ct_len0(p)) vu_panic(0, "ct_publish: index out of range", 30);
  int64_t old = -1;
  if (__atomic_compare_exchange_n(&p[i], &old, v, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) return -1;
  return old;
}
static inline int64_t ct_len(void *h) { return __atomic_load_n(&((const int64_t *)h)[-2], __ATOMIC_ACQUIRE); }
// entry i, or 0 past the column's end: a column written only at some rows of a group (the region is
// zero, so a row never written reads 0 too; such columns keep a value + 1)
static inline int64_t ct_get0(void *h, int64_t i) {
  const int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)ct_len0(p)) return 0;
  return p[i];
}
// a Float kept in an Int column (its bits)
static inline void ct_putf(void *h, int64_t r, double v) {
  int64_t b;
  memcpy(&b, &v, 8);
  ct_put(h, r, b);
}
static inline double ct_atf(void *h, int64_t i) {
  int64_t b = ct_at(h, i);
  double v;
  memcpy(&v, &b, 8);
  return v;
}

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
  if (__builtin_expect((uint64_t)r >= (uint64_t)(ct_len0(h->row) >> 1), 0)) vu_panic(0, "cl: row out of range", 20);
  return &h->row[2 * r];
}
static inline int64_t cl_len(void *p, int64_t r) { return cl_rp(p, r)[1]; }
// a new row (an empty list) of a list column that numbers its own rows (a fetch-add on the row
// region's reservation counter, which nothing else uses): its index
static inline int64_t cl_row(void *p) {
  cl_t *h = p;
  int64_t r = __atomic_fetch_add(&h->row[-1], 1, __ATOMIC_RELAXED);
  cl_init(p, r);
  return r;
}
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
// n entries of the pool reserved (a fetch-add on its reservation counter): where they start
static inline int64_t cl_res(cl_t *h, int64_t n) {
  int64_t at = __atomic_fetch_add(&h->pool[-1], n, __ATOMIC_RELAXED);
  if (at + n > CT_MAX) vu_panic(0, "cl: a list pool is full", 23);
  return at;
}
// v appended to row r's list: in place when the list ends the pool's reserved part (a
// compare-and-swap moves the end past it, so no other task can take that entry), else the list
// written again in a new reservation with v after it
static inline void cl_add(void *p, int64_t r, int64_t v) {
  cl_t *h = p;
  int64_t *rp = cl_rp(h, r);
  int64_t off = rp[0], n = rp[1], end = off + n;
  if (n > 0 && __atomic_compare_exchange_n(&h->pool[-1], &end, end + 1, false, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {
    if (end + 1 > CT_MAX) vu_panic(0, "cl: a list pool is full", 23);
    h->pool[end] = v;
  } else {
    int64_t at = cl_res(h, n + 1);
    for (int64_t i = 0; i < n; i++) h->pool[at + i] = h->pool[off + i];
    h->pool[at + n] = v;
    rp[0] = at;
  }
  rp[1] = n + 1;
}
static inline void cl_pop(void *p, int64_t r) {
  int64_t *rp = cl_rp(p, r);
  if (rp[1] == 0) vu_panic(0, "cl_pop: the list is empty", 25);
  rp[1] -= 1;
}
static inline void cl_set(void *p, int64_t r, const int64_t *xs, int64_t n) {
  cl_t *h = p;
  int64_t *rp = cl_rp(h, r);
  int64_t at = cl_res(h, n);
  for (int64_t i = 0; i < n; i++) h->pool[at + i] = xs[i];
  rp[0] = at;
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

// Attributes kept by a row's index (a type's alias, a symbol's further declarations), written for few
// rows: a column (cx_*) or a list column (ckl_*) whose region is zero where nothing was written.
// cx_ keeps a value + CX_OFF (0: none, so -1 and other negative markers can be kept); ckl_'s pool
// starts at 1, so a row holding a list (even an empty one) has a nonzero offset. A value is written
// with a release store after what it points to, so a reader that sees it sees the rest; written
// again (a few sites still do: types.vu's CX notes), a reader may see either.
#define CX_OFF ((int64_t)1 << 40)
static inline bool cx_has(void *h, int64_t k) { return ct_get0(h, k) != 0; }
static inline int64_t cx_get(void *h, int64_t k, int64_t d) {
  const int64_t *p = h;
  if ((uint64_t)k >= (uint64_t)ct_len0(p)) return d;
  int64_t v = __atomic_load_n(&p[k], __ATOMIC_ACQUIRE);
  return v == 0 ? d : v - CX_OFF;
}
static inline int64_t cx_at(void *h, int64_t k) {
  int64_t v = ct_get0(h, k);
  if (v == 0) vu_panic(0, "cx_at: no value for that row", 28);
  return v - CX_OFF;
}
static inline void cx_put(void *h, int64_t k, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)k >= (uint64_t)CT_MAX) vu_panic(0, "cx_put: index out of range", 26);
  __atomic_store_n(&p[k], v + CX_OFF, __ATOMIC_RELEASE);
  ct_cover(p, k + 1);
}
static inline void cx_del(void *h, int64_t k) {
  int64_t *p = h;
  if ((uint64_t)k < (uint64_t)ct_len0(p)) __atomic_store_n(&p[k], 0, __ATOMIC_RELEASE);
}
static inline void *ckl_new(void *st) {
  cl_t *h = cl_new(st);
  h->pool[-1] = 1;
  return h;
}
// row k's (offset, length), NULL when it holds no list
static inline const int64_t *ckl_rp(const cl_t *h, int64_t k) {
  if ((uint64_t)k >= (uint64_t)(ct_len0(h->row) >> 1)) return NULL;
  const int64_t *rp = &h->row[2 * k];
  if (__atomic_load_n(&rp[0], __ATOMIC_ACQUIRE) == 0) return NULL;
  return rp;
}
static inline bool ckl_has(void *p, int64_t k) { return ckl_rp(p, k) != NULL; }
static inline int64_t ckl_len(void *p, int64_t k) {
  const int64_t *rp = ckl_rp(p, k);
  return rp ? rp[1] : 0;
}
static inline int64_t ckl_at(void *p, int64_t k, int64_t i) {
  const cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp || (uint64_t)i >= (uint64_t)rp[1]) vu_panic(0, "ckl_at: index out of range", 26);
  return h->pool[rp[0] + i];
}
static inline void ckl_fill(void *p, int64_t k, int64_t *out, int64_t n) {
  const cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp) return;
  if (n > rp[1]) n = rp[1];
  for (int64_t i = 0; i < n; i++) out[i] = h->pool[rp[0] + i];
}
// row k's list set to xs (written at the pool's end, then published)
static inline void ckl_set(void *p, int64_t k, const int64_t *xs, int64_t n) {
  cl_t *h = p;
  if ((uint64_t)k >= (uint64_t)(CT_MAX / 2)) vu_panic(0, "ckl_set: row out of range", 25);
  int64_t at = cl_res(h, n);
  for (int64_t i = 0; i < n; i++) h->pool[at + i] = xs[i];
  int64_t *rp = &h->row[2 * k];
  __atomic_store_n(&rp[1], n, __ATOMIC_RELAXED);
  __atomic_store_n(&rp[0], at, __ATOMIC_RELEASE);
  ct_cover(h->row, 2 * k + 2);
}
// v appended to row k's list (a list made when it has none)
static inline void ckl_add(void *p, int64_t k, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp) {
    ckl_set(p, k, &v, 1);
    return;
  }
  cl_add(p, k, v);
}
static inline void ckl_del(void *p, int64_t k) {
  cl_t *h = p;
  if ((uint64_t)k >= (uint64_t)(ct_len0(h->row) >> 1)) return;
  __atomic_store_n(&h->row[2 * k], 0, __ATOMIC_RELEASE);
  h->row[2 * k + 1] = 0;
}

// Object types' properties by (object, name): the key object << 32 | name (both under 2^31). A fixed
// array of bucket heads, each a chain of entries (next, key, symbol) in an append-only pool, linked in
// by a compare-and-swap on the head as ik_* below, so nothing is ever moved under a reader and two
// tasks adding one key make one entry. The names in insertion order are a list column beside it
// (types.add_prop).
#define PH_BUCKETS ((int64_t)1 << 20)
typedef struct { int64_t *head; int64_t *pool; } ph_t;
static inline void *ph_new(void *st) {
  ph_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "ph_new: out of memory", 21);
  h->head = calloc((size_t)PH_BUCKETS, 8);
  if (!h->head) vu_panic(0, "ph_new: out of memory", 21);
  h->pool = ct_mk();
  h->pool[-1] = 3;  // (offset 0 is "none")
  cs_add(st, h, 2);
  return h;
}
static inline void ph_free(void *p) {
  ph_t *h = p;
  free(h->head);
  ct_free(h->pool);
  free(h);
}
static inline uint64_t ph_hash(int64_t k) {
  uint64_t x = (uint64_t)k * 0x9E3779B97F4A7C15ull;
  return x ^ (x >> 31);
}
// the entry of key k in the chain from e to stop (0: its end), 0 none
static inline int64_t ph_walk(const int64_t *p, int64_t e, int64_t stop, int64_t k) {
  for (; e != stop; e = p[e])
    if (p[e + 1] == k) return e;
  return 0;
}
// the symbol of o's property name, -1 none
static inline int64_t ph_get(void *p, int64_t o, int64_t name) {
  const ph_t *h = p;
  int64_t k = o << 32 | name;
  int64_t e = __atomic_load_n(&h->head[ph_hash(k) & (PH_BUCKETS - 1)], __ATOMIC_ACQUIRE);
  e = ph_walk(h->pool, e, 0, k);
  if (e == 0) return -1;
  return __atomic_load_n(&h->pool[e + 2], __ATOMIC_RELAXED);
}
// o's property name set to sym: true when it is a new property
static inline bool ph_put(void *p, int64_t o, int64_t name, int64_t sym) {
  ph_t *h = p;
  if ((uint64_t)o >= ((uint64_t)1 << 31) || (uint64_t)name >= ((uint64_t)1 << 32) || sym < 0) vu_panic(0, "ph_put: out of range", 20);
  int64_t k = o << 32 | name, *pool = h->pool;
  int64_t *hd = &h->head[ph_hash(k) & (PH_BUCKETS - 1)];
  int64_t e0 = __atomic_load_n(hd, __ATOMIC_ACQUIRE);
  int64_t w = ph_walk(pool, e0, 0, k);
  if (w != 0) {
    __atomic_store_n(&pool[w + 2], sym, __ATOMIC_RELAXED);
    return false;
  }
  int64_t ne = __atomic_fetch_add(&pool[-1], 3, __ATOMIC_RELAXED);
  if (ne + 3 > CT_MAX) vu_panic(0, "ph_put: the table is full", 25);
  pool[ne + 1] = k;
  pool[ne + 2] = sym;
  for (;;) {
    pool[ne] = e0;
    int64_t seen = e0;
    if (__atomic_compare_exchange_n(hd, &seen, ne, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) return true;
    w = ph_walk(pool, seen, e0, k);
    if (w != 0) {
      __atomic_store_n(&pool[w + 2], sym, __ATOMIC_RELAXED);
      return false;
    }
    e0 = seen;
  }
}

// Interned Int lists: (tag, prefix, list) -> a value (a type), found or added by several tasks at once
// without a lock. A fixed array of bucket heads, each a chain of entries in an append-only pool (an
// entry: next, hash, value, n, tag, prefix, the list); an entry is linked in by a compare-and-swap
// on its bucket's head, so of two tasks adding one key, one wins and the other gets its value
// (ik_put). An entry once linked never changes.
#define IK_BUCKETS ((int64_t)1 << 18)
typedef struct { int64_t *head; int64_t *pool; } ik_t;
static inline void *ik_new(void *st) {
  ik_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "ik_new: out of memory", 21);
  h->head = calloc((size_t)IK_BUCKETS, 8);
  if (!h->head) vu_panic(0, "ik_new: out of memory", 21);
  h->pool = ct_mk();
  h->pool[-1] = 1;  // (offset 0 is "none")
  cs_add(st, h, 4);
  return h;
}
static inline void ik_free(void *p) {
  ik_t *h = p;
  free(h->head);
  ct_free(h->pool);
  free(h);
}
static inline void ik_keep(void *h) { (void)h; }
static inline uint64_t ik_hash(int64_t tag, int64_t pre, const int64_t *xs, int64_t n) {
  uint64_t x = (uint64_t)tag * 0x9E3779B97F4A7C15ull ^ (uint64_t)pre * 0xC2B2AE3D27D4EB4Full ^ (uint64_t)n;
  for (int64_t i = 0; i < n; i++) {
    x ^= (uint64_t)xs[i];
    x *= 0xFF51AFD7ED558CCDull;
    x ^= x >> 29;
  }
  return x ^ (x >> 32);
}
// the value of a matching entry in the chain from e to stop (0: its end), -1 none
static inline int64_t ik_walk(const ik_t *h, int64_t e, int64_t stop, uint64_t hs, int64_t tag, int64_t pre, const int64_t *xs, int64_t n) {
  const int64_t *p = h->pool;
  for (; e != stop; e = p[e]) {
    if ((uint64_t)p[e + 1] != hs || p[e + 3] != n || p[e + 4] != tag || p[e + 5] != pre) continue;
    const int64_t *ys = &p[e + 6];
    int64_t i = 0;
    while (i < n && ys[i] == xs[i]) i++;
    if (i == n) return p[e + 2];
  }
  return -1;
}
static inline int64_t ik_get(void *ph, int64_t tag, int64_t pre, const int64_t *xs, int64_t n) {
  const ik_t *h = ph;
  uint64_t hs = ik_hash(tag, pre, xs, n);
  int64_t e = __atomic_load_n(&h->head[hs & (IK_BUCKETS - 1)], __ATOMIC_ACQUIRE);
  return ik_walk(h, e, 0, hs, tag, pre, xs, n);
}
// the key's value: v when this call added it, else the value another call added first
static inline int64_t ik_put(void *ph, int64_t tag, int64_t pre, const int64_t *xs, int64_t n, int64_t v) {
  ik_t *h = ph;
  uint64_t hs = ik_hash(tag, pre, xs, n);
  int64_t *hd = &h->head[hs & (IK_BUCKETS - 1)];
  int64_t e0 = __atomic_load_n(hd, __ATOMIC_ACQUIRE);
  int64_t w = ik_walk(h, e0, 0, hs, tag, pre, xs, n);
  if (w >= 0) return w;
  int64_t *p = h->pool;
  int64_t ne = __atomic_fetch_add(&p[-1], n + 6, __ATOMIC_RELAXED);
  if (ne + n + 6 > CT_MAX) vu_panic(0, "ik_put: the table is full", 25);
  p[ne + 1] = (int64_t)hs;
  p[ne + 2] = v;
  p[ne + 3] = n;
  p[ne + 4] = tag;
  p[ne + 5] = pre;
  for (int64_t i = 0; i < n; i++) p[ne + 6 + i] = xs[i];
  for (;;) {
    p[ne] = e0;
    int64_t seen = e0;
    if (__atomic_compare_exchange_n(hd, &seen, ne, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) return v;
    // (another entry linked in first: is it this key?)
    w = ik_walk(h, seen, e0, hs, tag, pre, xs, n);
    if (w >= 0) return w;
    e0 = seen;
  }
}
static inline int64_t ik_addr(void *h) { return ct_addr(h); }
static inline void *ik_view(int64_t a) { return ct_view(a); }

// Names made while checking: text -> an id (0, 1, 2 ... in the order added; the checker adds its
// frozen names table's length), found or added by several tasks at once without a lock, as ik_*: a
// chain per bucket of entries in an append-only pool (next, hash, length, the bytes in words), the
// ids an append-only column of entry offsets (ids taken by fetch-add: a task that loses the race
// for a name leaves its id unused).
typedef struct { int64_t *head; int64_t *pool; int64_t *ids; } ns_t;
static inline void *ns_new(void *st) {
  ns_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "ns_new: out of memory", 21);
  h->head = calloc((size_t)IK_BUCKETS, 8);
  if (!h->head) vu_panic(0, "ns_new: out of memory", 21);
  h->pool = ct_mk();
  h->pool[-1] = 1;
  h->ids = ct_mk();
  cs_add(st, h, 5);
  return h;
}
static inline void ns_free(void *p) {
  ns_t *h = p;
  free(h->head);
  ct_free(h->pool);
  ct_free(h->ids);
  free(h);
}
static inline void ns_keep(void *h) { (void)h; }
static inline uint64_t ns_hash(const uint8_t *d, int64_t n) {
  uint64_t x = 0xCBF29CE484222325ull ^ (uint64_t)n;
  for (int64_t i = 0; i < n; i++) x = (x ^ d[i]) * 0x100000001B3ull;
  return x ^ (x >> 29);
}
// the id of a matching entry from e to stop, -1 none (an entry: next, hash, length, id, bytes)
static inline int64_t ns_walk(const ns_t *h, int64_t e, int64_t stop, uint64_t hs, const uint8_t *d, int64_t n) {
  const int64_t *p = h->pool;
  for (; e != stop; e = p[e]) {
    if ((uint64_t)p[e + 1] != hs || p[e + 2] != n) continue;
    if (n == 0 || memcmp(&p[e + 4], d, (size_t)n) == 0) return p[e + 3];
  }
  return -1;
}
static inline int64_t ns_find(void *ph, const vu_str *s) {
  const ns_t *h = ph;
  uint64_t hs = ns_hash(s->data, s->len);
  int64_t e = __atomic_load_n(&h->head[hs & (IK_BUCKETS - 1)], __ATOMIC_ACQUIRE);
  return ns_walk(h, e, 0, hs, s->data, s->len);
}
static inline int64_t ns_put(void *ph, const vu_str *s) {
  ns_t *h = ph;
  const uint8_t *d = s->data;
  int64_t n = s->len;
  uint64_t hs = ns_hash(d, n);
  int64_t *hd = &h->head[hs & (IK_BUCKETS - 1)];
  int64_t e0 = __atomic_load_n(hd, __ATOMIC_ACQUIRE);
  int64_t w = ns_walk(h, e0, 0, hs, d, n);
  if (w >= 0) return w;
  int64_t *p = h->pool;
  int64_t words = (n + 7) / 8;
  int64_t ne = __atomic_fetch_add(&p[-1], words + 4, __ATOMIC_RELAXED);
  if (ne + words + 4 > CT_MAX) vu_panic(0, "ns_put: the names are full", 26);
  int64_t id = __atomic_fetch_add(&h->ids[-1], 1, __ATOMIC_RELAXED);
  if (id >= CT_MAX) vu_panic(0, "ns_put: the names are full", 26);
  p[ne + 1] = (int64_t)hs;
  p[ne + 2] = n;
  p[ne + 3] = id;
  if (n > 0) memcpy(&p[ne + 4], d, (size_t)n);
  h->ids[id] = ne;
  ct_cover(h->ids, id + 1);
  for (;;) {
    p[ne] = e0;
    int64_t seen = e0;
    if (__atomic_compare_exchange_n(hd, &seen, ne, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) return id;
    w = ns_walk(h, seen, e0, hs, d, n);
    if (w >= 0) return w;
    e0 = seen;
  }
}
static inline vu_str ns_str(void *ph, int64_t id) {
  const ns_t *h = ph;
  int64_t e = ct_at(h->ids, id);
  return vu_str_from(&h->pool[e + 4], h->pool[e + 2]);
}
static inline int64_t ns_addr(void *h) { return ct_addr(h); }
static inline void *ns_view(int64_t a) { return ct_view(a); }

// every table the store made freed
static inline void cs_free(void *p) {
  cs_t *s = p;
  for (int64_t i = 0; i < s->n; i++) {
    switch (s->k[i]) {
      case 0: ct_free(s->p[i]); break;
      case 1: cl_free(s->p[i]); break;
      case 2: ph_free(s->p[i]); break;
      case 4: ik_free(s->p[i]); break;
      case 5: ns_free(s->p[i]); break;
      default: free(s->p[i]);
    }
  }
  free(s->p);
  free(s->k);
  free(s);
}
