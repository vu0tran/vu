// The checker's flat Int tables as C columns: each in one reserved region (pages committed as they
// are touched, never moved), so a reader needs no lock and no indirection, and a fork shares it
// copy-on-write. The length is kept before the first entry and published with a release store
// (ts/NOTES.md, "Checking one program on several workers").
#include <stdint.h>
#include <stdlib.h>
#include <sys/mman.h>
#define CT_MAX ((int64_t)1 << 28)  // entries a column can hold (2 GB of address space, reserved only)
static inline void *ct_new(void) {
  int64_t *r = mmap(NULL, (size_t)(CT_MAX + 2) * 8, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON | MAP_NORESERVE, -1, 0);
  if (r == MAP_FAILED) {
    vu_panic(0, "ct_new: no address space for a column", 37);
  }
  r[0] = 0;
  return r + 2;
}
static inline void ct_free(void *h) { munmap((int64_t *)h - 2, (size_t)(CT_MAX + 2) * 8); }
static inline int64_t ct_push(void *h, int64_t v) {
  int64_t *p = h;
  int64_t n = p[-2];
  if (n >= CT_MAX) vu_panic(0, "ct_push: a column is full", 25);
  p[n] = v;
  __atomic_store_n(&p[-2], n + 1, __ATOMIC_RELEASE);
  return n;
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
static inline void *cl_new(void) {
  cl_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "cl_new: out of memory", 21);
  h->row = ct_new();
  h->pool = ct_new();
  return h;
}
static inline void cl_free(void *p) {
  cl_t *h = p;
  ct_free(h->row);
  ct_free(h->pool);
  free(h);
}
static inline int64_t cl_rows(void *p) { return ct_len(((cl_t *)p)->row) >> 1; }
// a new row holding an empty list; its index
static inline int64_t cl_row(void *p) {
  cl_t *h = p;
  int64_t r = h->row[-2];
  if (r + 2 > CT_MAX) vu_panic(0, "cl_row: a list column is full", 29);
  h->row[r] = h->pool[-2];
  h->row[r + 1] = 0;
  __atomic_store_n(&h->row[-2], r + 2, __ATOMIC_RELEASE);
  return r >> 1;
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
