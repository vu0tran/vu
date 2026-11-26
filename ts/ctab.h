// The checker's flat Int tables as C columns: each in one reserved region (pages committed as they
// are touched, never moved), so a reader needs no lock and no indirection, and a fork shares it
// copy-on-write. The length is kept before the first entry and published with a release store
// (ts/NOTES.md, "Checking one program on several workers").
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sched.h>
#include <time.h>
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
  // (a cache line of its own: every new row of the group is a fetch-add on it)
  int64_t *g = NULL;
  if (posix_memalign((void **)&g, 128, 128) != 0) g = NULL;
  if (!g) vu_panic(0, "cg_new: out of memory", 21);
  memset(g, 0, 128);
  cs_add(st, g, 3);
  return g;
}
static int64_t ct_slack_n;
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
// (the length and the run counter, p[-2] and p[-1], in a cache line before the entries': read by
// every bounds check, it is written only as the column grows)
#define CT_HEAD 16
static inline void *ct_mk(void) {
  int64_t *r = mmap(NULL, (size_t)(CT_MAX + CT_HEAD) * 8, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON | MAP_NORESERVE, -1, 0);
  if (r == MAP_FAILED) {
    vu_panic(0, "ct_new: no address space for a column", 37);
  }
  return r + CT_HEAD;
}
static inline void ct_free(void *h) { munmap((int64_t *)h - CT_HEAD, (size_t)(CT_MAX + CT_HEAD) * 8); }
static inline void *ct_new(void *st) {
  void *t = ct_mk();
  cs_add(st, t, 0);
  return t;
}
// a column's length, as a bounds check reads it (relaxed: no order needed, see ct_at)
static inline int64_t ct_len0(const int64_t *p) { return __atomic_load_n(&p[-2], __ATOMIC_RELAXED); }
// How far past what's written a column's length is raised (ct_cover): 0, the exact length, but
// while several threads write the tables (types.worker_checker), 63: the length (a cache line every
// reader's bounds check reads) then changes once in 64 rows, not at every row each thread makes. An
// entry past the end then reads 0, as one never written does.
static inline void ct_slack(int64_t n) { ct_slack_n = n; }
// the column's length raised to at least n (a row of its group written: ct_put, cl_init)
static inline void ct_cover(int64_t *p, int64_t n) {
  int64_t l = __atomic_load_n(&p[-2], __ATOMIC_RELAXED);
  if (__builtin_expect(l >= n, 1)) return;
  int64_t m = (n + ct_slack_n) & ~ct_slack_n;
  if (m > CT_MAX) m = CT_MAX;
  if (m < n) m = n;
  while (l < n && !__atomic_compare_exchange_n(&p[-2], &l, m, true, __ATOMIC_RELEASE, __ATOMIC_RELAXED)) {
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
// entry i with an acquire load: a state word another task may publish (ct_cas) after what it points to
static inline int64_t ct_acq(void *h, int64_t i) {
  const int64_t *p = h;
  if (__builtin_expect((uint64_t)i >= (uint64_t)ct_len0(p), 0)) vu_panic(0, "ct_acq: index out of range", 26);
  return __atomic_load_n(&p[i], __ATOMIC_ACQUIRE);
}
// The row object o's members are in (types.orow): res is ho_resolved (0 not filled, 1 its own row,
// r >= 2 the row r - 2 a fill published), mine the worker's own column of the objects it is filling
// (the row + 1). o is a row its group gave.
static inline int64_t ct_orow(void *res, void *mine, int64_t o) {
  int64_t r = __atomic_load_n(&((const int64_t *)res)[o], __ATOMIC_ACQUIRE);
  if (__builtin_expect(r == 1, 1)) return o;
  // (this worker's own row while it fills o, even once another worker's fill is published: the
  // members are written into the row being filled, never into a published one others read)
  int64_t m = ct_get0(mine, o);
  if (m != 0) return m - 1;
  return r >= 2 ? r - 2 : o;
}
// An object's lazy fill claimed (VTSC_OFILL=1 with threads, bind.ensure_resolved): ho_resolved from 0
// to -(k + 1), k the filling worker's number, so one worker fills it and the others wait for its
// row rather than fill rows of their own (whose member symbols and signatures would be other ones).
// A worker's column of the objects it fills (ho_mine) keeps, in its header, its number (p[-3]) and
// the object it waits for + 1 (p[-4]); ct_wk finds the column by the number, to follow a chain of
// waits: one that comes back to the waiting worker (each waits for an object another one is filling)
// is a cycle, which serial checking meets as a fill reading its own rows so far.
#define CT_NW 128
static int64_t *ct_wk[CT_NW];
static inline void ct_worker(void *mine, int64_t k) {
  int64_t *p = mine;
  if ((uint64_t)k >= CT_NW) vu_panic(0, "ct_worker: too many workers", 27);
  p[-3] = k;
  p[-4] = 0;
  __atomic_store_n(&ct_wk[k], p, __ATOMIC_SEQ_CST);
}
static inline void ct_workers_done(void) {
  for (int i = 0; i < CT_NW; i++) __atomic_store_n(&ct_wk[i], NULL, __ATOMIC_SEQ_CST);
}
static inline int64_t ct_now_ms(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (int64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}
// 1: o claimed by this call (fill it, then ct_filled); 0: filled, maybe by another worker this call
// waited for; 2: claimed by another worker that waits, through others maybe, for an object this one
// is filling (or for more than 10 s: a worker that can't run): fill it too, into a row of its own
static inline int64_t ct_claim(void *res, void *mine, int64_t o) {
  int64_t *R = res, *M = mine;
  int64_t k = M[-3];
  if ((uint64_t)o >= (uint64_t)ct_len0(R)) vu_panic(0, "ct_claim: index out of range", 28);
  int64_t spins = 0, t0 = 0;
  for (;;) {
    int64_t r = __atomic_load_n(&R[o], __ATOMIC_ACQUIRE);
    int64_t got = -1;
    if (r > 0) got = 0;
    else if (r == 0) {
      int64_t z = 0;
      if (__atomic_compare_exchange_n(&R[o], &z, -(k + 1), false, __ATOMIC_SEQ_CST, __ATOMIC_ACQUIRE)) got = 1;
      else continue;
    } else if (-r - 1 == k) got = 2;
    else {
      __atomic_store_n(&M[-4], o + 1, __ATOMIC_SEQ_CST);
      int64_t x = -r - 1;
      for (int step = 0; step < CT_NW && got < 0; step++) {
        int64_t *X = __atomic_load_n(&ct_wk[x], __ATOMIC_SEQ_CST);
        if (!X) break;
        int64_t wo = __atomic_load_n(&X[-4], __ATOMIC_SEQ_CST);
        if (wo <= 0 || (uint64_t)(wo - 1) >= (uint64_t)ct_len0(R)) break;
        int64_t r2 = __atomic_load_n(&R[wo - 1], __ATOMIC_SEQ_CST);
        if (r2 >= 0) break;
        x = -r2 - 1;
        if (x == k) got = 2;
      }
      if (got < 0) {
        spins += 1;
        if (spins > 64) sched_yield();
        if ((spins & 1023) == 0) {
          int64_t t = ct_now_ms();
          if (t0 == 0) t0 = t;
          else if (t - t0 > 10000) got = 2;
        }
      }
    }
    if (got >= 0) {
      __atomic_store_n(&M[-4], 0, __ATOMIC_SEQ_CST);
      return got;
    }
  }
}
// o's fill published: its row + 2, by the worker that claimed it
static inline void ct_filled(void *res, int64_t o, int64_t v) {
  int64_t *R = res;
  if ((uint64_t)o >= (uint64_t)ct_len0(R)) vu_panic(0, "ct_filled: index out of range", 29);
  __atomic_store_n(&R[o], v, __ATOMIC_RELEASE);
}
// entry i from old to v with a compare-and-swap (release): whether this call set it
static inline bool ct_cas(void *h, int64_t i, int64_t old, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)ct_len0(p)) vu_panic(0, "ct_cas: index out of range", 26);
  return __atomic_compare_exchange_n(&p[i], &old, v, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE);
}
static inline int64_t ct_len(void *h) { return __atomic_load_n(&((const int64_t *)h)[-2], __ATOMIC_ACQUIRE); }
// entry i, or 0 past the column's end: a column written only at some rows of a group (the region is
// zero, so a row never written reads 0 too; such columns keep a value + 1)
static inline int64_t ct_get0(void *h, int64_t i) {
  const int64_t *p = h;
  if ((uint64_t)i >= (uint64_t)ct_len0(p)) return 0;
  return __atomic_load_n(&p[i], __ATOMIC_RELAXED);
}
// a Float kept in an Int column (its bits)
// (relaxed atomics: two threads making one numeric literal both write its value, the same bits)
static inline void ct_putf(void *h, int64_t r, double v) {
  int64_t b, *p = h;
  memcpy(&b, &v, 8);
  if ((uint64_t)r >= (uint64_t)CT_MAX) vu_panic(0, "ct_put: index out of range", 26);
  __atomic_store_n(&p[r], b, __ATOMIC_RELAXED);
  ct_cover(p, r + 1);
}
static inline double ct_atf(void *h, int64_t i) {
  const int64_t *p = h;
  if (__builtin_expect((uint64_t)i >= (uint64_t)ct_len0(p), 0)) vu_panic(0, "ct_at: index out of range", 25);
  int64_t b = __atomic_load_n(&p[i], __ATOMIC_RELAXED);
  double v;
  memcpy(&v, &b, 8);
  return v;
}

// A list column: a list of Ints per row, each row an (offset, length) pair into a pool of Ints, both
// append-only regions as above. A row is changed by writing its list again at the pool's end (or, when
// it already ends the pool, by appending to it), so an entry once written is never moved or overwritten
// by another row's list.
//
// A sparse list column (cl_snew, ckl_snew: most rows never get a list) keeps its rows' (offset,
// length) pairs in a hash instead (sh: CL_SBUCKETS bucket heads, chains of (next, row, offset,
// length) entries in the append-only region se, linked by a compare-and-swap on the head as ik_*
// below, so an entry never moves and two tasks making one row make one entry): a row without one
// reads (0, 0). On macOS a page of an untouched region is made resident by a read as well as by a
// write, so a dense row region whose rows are read throughout is resident whole, however few hold a
// list: 3.2 M rows of ht_sigs (52 MB) for 63,000 lists.
typedef struct { int64_t *row; int64_t *pool; int64_t *sh; int64_t *se; } cl_t;
#define CL_SBITS 17
#define CL_SBUCKETS ((int64_t)1 << CL_SBITS)
static inline void *cl_new(void *st) {
  cl_t *h = calloc(1, sizeof *h);
  if (!h) vu_panic(0, "cl_new: out of memory", 21);
  h->row = ct_mk();
  h->pool = ct_mk();
  cs_add(st, h, 1);
  return h;
}
static inline void *cl_snew(void *st) {
  cl_t *h = cl_new(st);
  h->sh = calloc((size_t)CL_SBUCKETS, 8);
  if (!h->sh) vu_panic(0, "cl_snew: out of memory", 22);
  h->se = ct_mk();
  h->se[-1] = 4;  // (entry 0 is "none")
  return h;
}
static inline void cl_free(void *p) {
  cl_t *h = p;
  ct_free(h->row);
  ct_free(h->pool);
  if (h->sh) {
    free(h->sh);
    ct_free(h->se);
  }
  free(h);
}
static inline int64_t cl_shash(int64_t r) { return (int64_t)(((uint64_t)r * 0x9E3779B97F4A7C15ULL) >> (64 - CL_SBITS)); }
// a sparse column's row r: its (offset, length) pair, NULL when it has none (create: made then)
static int64_t *cl_srp(cl_t *h, int64_t r, bool create) {
  int64_t *hd = &h->sh[cl_shash(r)];
  int64_t e = __atomic_load_n(hd, __ATOMIC_ACQUIRE);
  for (int64_t x = e; x; x = h->se[x])
    if (h->se[x + 1] == r) return &h->se[x + 2];
  if (!create) return NULL;
  int64_t ne = __atomic_fetch_add(&h->se[-1], 4, __ATOMIC_RELAXED);
  if (ne + 4 > CT_MAX) vu_panic(0, "cl: a sparse column is full", 27);
  h->se[ne + 1] = r;
  h->se[ne + 2] = 0;
  h->se[ne + 3] = 0;
  for (;;) {
    int64_t old = e;
    h->se[ne] = old;
    if (__atomic_compare_exchange_n(hd, &e, ne, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) {
      ct_cover(h->se, ne + 4);
      return &h->se[ne + 2];
    }
    // (another task linked entries meanwhile: one of them may be this row's; ne is then left unused)
    for (int64_t x = e; x != old; x = h->se[x])
      if (h->se[x + 1] == r) return &h->se[x + 2];
  }
}
static const int64_t cl_none[2] = {0, 0};
static inline int64_t cl_rows(void *p) { return ct_len(((cl_t *)p)->row) >> 1; }
// row r (from its group: cg_row) made, holding an empty list (the region is zero: (0, 0) already)
static inline void cl_init(void *p, int64_t r) {
  cl_t *h = p;
  if ((uint64_t)r >= (uint64_t)(CT_MAX / 2)) vu_panic(0, "cl_init: row out of range", 25);
  if (h->sh) return;
  h->row[2 * r] = 0;
  h->row[2 * r + 1] = 0;
  ct_cover(h->row, 2 * r + 2);
}
// row r's pair to read (a sparse column's row without one: (0, 0), never written through)
static inline int64_t *cl_rp(cl_t *h, int64_t r) {
  if (__builtin_expect(h->sh != NULL, 0)) {
    int64_t *rp = cl_srp(h, r, false);
    return rp ? rp : (int64_t *)cl_none;
  }
  if (__builtin_expect((uint64_t)r >= (uint64_t)(ct_len0(h->row) >> 1), 0)) vu_panic(0, "cl: row out of range", 20);
  return &h->row[2 * r];
}
// row r's pair to write
static inline int64_t *cl_wp(cl_t *h, int64_t r) {
  if (__builtin_expect(h->sh != NULL, 0)) {
    if ((uint64_t)r >= (uint64_t)(CT_MAX / 2)) vu_panic(0, "cl: row out of range", 20);
    return cl_srp(h, r, true);
  }
  return cl_rp(h, r);
}
static inline int64_t cl_len(void *p, int64_t r) { return cl_rp(p, r)[1]; }
// A row's offset may carry CL_CAP: its list was written by cl_add into a reservation of cl_cap(n)
// entries (a power of two, at least 4), so it grows in place while it fits, the row's own; else a
// list that ends the pool's reserved part grows there (a compare-and-swap), and otherwise it's
// written again into twice the room. (Without the doubling, a list that other tasks' reservations
// keep from ending the pool was copied whole at every add: quadratic, and with 8 threads a pool ran
// out of its 2^28 entries.) A shorter list (cl_pop) keeps its reservation, which is at least cl_cap
// of its length, so the in-place test stays safe.
#define CL_CAP ((int64_t)1 << 62)
static inline int64_t cl_off(const int64_t *rp) { return rp[0] & (CL_CAP - 1); }
static inline int64_t cl_cap(int64_t n) {
  int64_t c = 4;
  while (c < n) c <<= 1;
  return c;
}
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
  return h->pool[cl_off(rp) + i];
}
static inline void cl_put(void *p, int64_t r, int64_t i, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  if ((uint64_t)i >= (uint64_t)rp[1]) vu_panic(0, "cl_put: index out of range", 26);
  h->pool[cl_off(rp) + i] = v;
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
  int64_t *rp = cl_wp(h, r);
  int64_t off = cl_off(rp), n = rp[1], end = off + n;
  if ((rp[0] & CL_CAP) && n + 1 <= cl_cap(n)) {
    h->pool[end] = v;
  } else if (n > 0 && __atomic_compare_exchange_n(&h->pool[-1], &end, end + 1, false, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {
    if (end + 1 > CT_MAX) vu_panic(0, "cl: a list pool is full", 23);
    h->pool[end] = v;
    rp[0] = off;
  } else {
    // (a first entry gets room for itself alone, as most lists stay that short)
    int64_t c = n == 0 ? 1 : cl_cap(2 * n);
    int64_t at = cl_res(h, c);
    for (int64_t i = 0; i < n; i++) h->pool[at + i] = h->pool[off + i];
    h->pool[at + n] = v;
    rp[0] = n == 0 ? at : (at | CL_CAP);
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
  if (h->sh && n == 0 && !cl_srp(h, r, false)) return;
  int64_t *rp = cl_wp(h, r);
  int64_t at = cl_res(h, n);
  for (int64_t i = 0; i < n; i++) h->pool[at + i] = xs[i];
  rp[0] = at;
  rp[1] = n;
}
static inline void cl_fill(void *p, int64_t r, int64_t *out, int64_t n) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  if (n > rp[1]) n = rp[1];
  for (int64_t i = 0; i < n; i++) out[i] = h->pool[cl_off(rp) + i];
}
static inline bool cl_has(void *p, int64_t r, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = cl_rp(h, r);
  const int64_t *xs = &h->pool[cl_off(rp)];
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
  const int64_t *p = h;
  int64_t v = (uint64_t)k >= (uint64_t)ct_len0(p) ? 0 : __atomic_load_n(&p[k], __ATOMIC_ACQUIRE);
  if (v == 0) vu_panic(0, "cx_at: no value for that row", 28);
  return v - CX_OFF;
}
static inline void cx_put(void *h, int64_t k, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)k >= (uint64_t)CT_MAX) vu_panic(0, "cx_put: index out of range", 26);
  __atomic_store_n(&p[k], v + CX_OFF, __ATOMIC_RELEASE);
  ct_cover(p, k + 1);
}
// k's value set once: from none to v with a compare-and-swap; the value k has after (v when this
// call set it, else the one another task set first)
static inline int64_t cx_publish(void *h, int64_t k, int64_t v) {
  int64_t *p = h;
  if ((uint64_t)k >= (uint64_t)CT_MAX) vu_panic(0, "cx_publish: index out of range", 30);
  int64_t old = 0;
  if (__atomic_compare_exchange_n(&p[k], &old, v + CX_OFF, false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) {
    ct_cover(p, k + 1);
    return v;
  }
  ct_cover(p, k + 1);
  return old - CX_OFF;
}
static inline void cx_del(void *h, int64_t k) {
  int64_t *p = h;
  if ((uint64_t)k < (uint64_t)ct_len0(p)) __atomic_store_n(&p[k], 0, __ATOMIC_RELEASE);
}
// A column of 32-bit entries (ct4_*, cx4_*): for a column whose values are ids, kinds and flags under
// 2^31 (a symbol's, an object's), half the memory of an Int column. The same header (length and run
// counter as Ints before the entries, ct_len), so ct_len, ct_cover and the views work on it. A value
// out of range stops the program. cx4_ keeps a value + 2^31 (0: none).
#define CT4_BYTES ((size_t)CT_MAX * 4 + (size_t)CT_HEAD * 8)
static inline void *ct4_new(void *st) {
  char *r = mmap(NULL, CT4_BYTES, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON | MAP_NORESERVE, -1, 0);
  if (r == MAP_FAILED) vu_panic(0, "ct4_new: no address space for a column", 38);
  void *t = r + CT_HEAD * 8;
  cs_add(st, t, 6);
  return t;
}
static inline void ct4_free(void *h) { munmap((char *)h - CT_HEAD * 8, CT4_BYTES); }
static inline int32_t ct4_v(int64_t v) {
  if (__builtin_expect(v < INT32_MIN || v > INT32_MAX, 0)) vu_panic(0, "ct4: a value past 32 bits", 25);
  return (int32_t)v;
}
static inline void ct4_put(void *h, int64_t r, int64_t v) {
  if ((uint64_t)r >= (uint64_t)CT_MAX) vu_panic(0, "ct4_put: index out of range", 27);
  ((int32_t *)h)[r] = ct4_v(v);
  ct_cover(h, r + 1);
}
static inline int64_t ct4_at(void *h, int64_t i) {
  if (__builtin_expect((uint64_t)i >= (uint64_t)ct_len0(h), 0)) vu_panic(0, "ct4_at: index out of range", 26);
  return ((const int32_t *)h)[i];
}
static inline void ct4_set(void *h, int64_t i, int64_t v) {
  if ((uint64_t)i >= (uint64_t)ct_len0(h)) vu_panic(0, "ct4_set: index out of range", 27);
  ((int32_t *)h)[i] = ct4_v(v);
}
static inline int64_t ct4_acq(void *h, int64_t i) {
  if (__builtin_expect((uint64_t)i >= (uint64_t)ct_len0(h), 0)) vu_panic(0, "ct4_acq: index out of range", 27);
  return __atomic_load_n(&((const int32_t *)h)[i], __ATOMIC_ACQUIRE);
}
static inline int64_t ct4_publish(void *h, int64_t i, int64_t v) {
  if ((uint64_t)i >= (uint64_t)ct_len0(h)) vu_panic(0, "ct4_publish: index out of range", 31);
  int32_t old = -1;
  if (__atomic_compare_exchange_n(&((int32_t *)h)[i], &old, ct4_v(v), false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) return -1;
  return old;
}
static inline int64_t ct4_get0(void *h, int64_t i) {
  if ((uint64_t)i >= (uint64_t)ct_len0(h)) return 0;
  return __atomic_load_n(&((const int32_t *)h)[i], __ATOMIC_RELAXED);
}
#define CX4_OFF ((int64_t)1 << 31)
static inline uint32_t cx4_v(int64_t v) {
  if (__builtin_expect(v <= -CX4_OFF || v >= CX4_OFF, 0)) vu_panic(0, "cx4: a value past 32 bits", 25);
  return (uint32_t)(v + CX4_OFF);
}
static inline uint32_t cx4_ld(void *h, int64_t k) {
  if ((uint64_t)k >= (uint64_t)ct_len0(h)) return 0;
  return __atomic_load_n(&((const uint32_t *)h)[k], __ATOMIC_ACQUIRE);
}
static inline bool cx4_has(void *h, int64_t k) { return cx4_ld(h, k) != 0; }
static inline int64_t cx4_get(void *h, int64_t k, int64_t d) {
  uint32_t v = cx4_ld(h, k);
  return v == 0 ? d : (int64_t)v - CX4_OFF;
}
static inline int64_t cx4_at(void *h, int64_t k) {
  uint32_t v = cx4_ld(h, k);
  if (v == 0) vu_panic(0, "cx_at: no value for that row", 28);
  return (int64_t)v - CX4_OFF;
}
static inline void cx4_put(void *h, int64_t k, int64_t v) {
  if ((uint64_t)k >= (uint64_t)CT_MAX) vu_panic(0, "cx_put: index out of range", 26);
  __atomic_store_n(&((uint32_t *)h)[k], cx4_v(v), __ATOMIC_RELEASE);
  ct_cover(h, k + 1);
}
static inline int64_t cx4_publish(void *h, int64_t k, int64_t v) {
  if ((uint64_t)k >= (uint64_t)CT_MAX) vu_panic(0, "cx_publish: index out of range", 30);
  uint32_t old = 0;
  bool won = __atomic_compare_exchange_n(&((uint32_t *)h)[k], &old, cx4_v(v), false, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE);
  ct_cover(h, k + 1);
  return won ? v : (int64_t)old - CX4_OFF;
}
static inline void cx4_del(void *h, int64_t k) {
  if ((uint64_t)k < (uint64_t)ct_len0(h)) __atomic_store_n(&((uint32_t *)h)[k], 0, __ATOMIC_RELEASE);
}
static inline void *ckl_new(void *st) {
  cl_t *h = cl_new(st);
  h->pool[-1] = 1;
  return h;
}
static inline void *ckl_snew(void *st) {
  cl_t *h = cl_snew(st);
  h->pool[-1] = 1;
  return h;
}
// row k's pair to write (made in a sparse column)
static inline int64_t *ckl_wp(cl_t *h, int64_t k) {
  if (h->sh) return cl_srp(h, k, true);
  ct_cover(h->row, 2 * k + 2);
  return &h->row[2 * k];
}
// row k's (offset, length), NULL when it holds no list
static inline const int64_t *ckl_rp(const cl_t *h, int64_t k) {
  const int64_t *rp;
  if (h->sh) {
    rp = cl_srp((cl_t *)h, k, false);
    if (!rp) return NULL;
  } else {
    if ((uint64_t)k >= (uint64_t)(ct_len0(h->row) >> 1)) return NULL;
    rp = &h->row[2 * k];
  }
  // (0: no list; -1: claimed by a ckl_publish, its list not written yet)
  if (__atomic_load_n(&rp[0], __ATOMIC_ACQUIRE) <= 0) return NULL;
  return rp;
}
static inline bool ckl_has(void *p, int64_t k) { return ckl_rp(p, k) != NULL; }
// (the length read with a relaxed load: another task may set the row meanwhile)
static inline int64_t ckl_n(const int64_t *rp) { return __atomic_load_n(&rp[1], __ATOMIC_RELAXED); }
static inline int64_t ckl_off(const int64_t *rp) { return __atomic_load_n(&rp[0], __ATOMIC_RELAXED); }
static inline int64_t ckl_len(void *p, int64_t k) {
  const int64_t *rp = ckl_rp(p, k);
  return rp ? ckl_n(rp) : 0;
}
static inline int64_t ckl_at(void *p, int64_t k, int64_t i) {
  const cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp || (uint64_t)i >= (uint64_t)ckl_n(rp)) vu_panic(0, "ckl_at: index out of range", 26);
  return h->pool[ckl_off(rp) + i];
}
static inline void ckl_fill(void *p, int64_t k, int64_t *out, int64_t n) {
  const cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp) return;
  if (n > ckl_n(rp)) n = ckl_n(rp);
  for (int64_t i = 0; i < n; i++) out[i] = h->pool[ckl_off(rp) + i];
}
// row k's list set to xs (written at the pool's end, then published)
static inline void ckl_set(void *p, int64_t k, const int64_t *xs, int64_t n) {
  cl_t *h = p;
  if ((uint64_t)k >= (uint64_t)(CT_MAX / 2)) vu_panic(0, "ckl_set: row out of range", 25);
  int64_t at = cl_res(h, n);
  for (int64_t i = 0; i < n; i++) h->pool[at + i] = xs[i];
  int64_t *rp = ckl_wp(h, k);
  __atomic_store_n(&rp[1], n, __ATOMIC_RELAXED);
  __atomic_store_n(&rp[0], at, __ATOMIC_RELEASE);
}
// entry i of row k's list set (in place)
static inline void ckl_put(void *p, int64_t k, int64_t i, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp || (uint64_t)i >= (uint64_t)ckl_n(rp)) vu_panic(0, "ckl_put: index out of range", 27);
  h->pool[ckl_off(rp) + i] = v;
}
// v appended to row k's list (a list made when it has none): the list written again after the
// pool's end with v, then published, so a reader sees the old list or the new one whole
static inline void ckl_add(void *p, int64_t k, int64_t v) {
  cl_t *h = p;
  const int64_t *rp = ckl_rp(h, k);
  if (!rp) {
    ckl_set(p, k, &v, 1);
    return;
  }
  int64_t off = ckl_off(rp), n = ckl_n(rp);
  int64_t at = cl_res(h, n + 1);
  for (int64_t i = 0; i < n; i++) h->pool[at + i] = h->pool[off + i];
  h->pool[at + n] = v;
  int64_t *w = (int64_t *)rp;
  __atomic_store_n(&w[1], n + 1, __ATOMIC_RELAXED);
  __atomic_store_n(&w[0], at, __ATOMIC_RELEASE);
}
// row k's list set to xs unless it has one: true when this call set it, false when another task's
// list is there (read it with ckl_*). The row is claimed first (its offset from 0 to -1 by a
// compare-and-swap), then its list written and published; a second publisher waits for the
// claimer's few stores (no fill: the claimer waits on nothing), so it returns only once that list
// can be read.
static inline bool ckl_publish(void *p, int64_t k, const int64_t *xs, int64_t n) {
  cl_t *h = p;
  if ((uint64_t)k >= (uint64_t)(CT_MAX / 2)) vu_panic(0, "ckl_publish: row out of range", 29);
  int64_t *rp = ckl_wp(h, k);
  int64_t old = 0;
  if (!__atomic_compare_exchange_n(&rp[0], &old, -1, false, __ATOMIC_ACQUIRE, __ATOMIC_ACQUIRE)) {
    while (__atomic_load_n(&rp[0], __ATOMIC_ACQUIRE) < 0) sched_yield();
    return false;
  }
  int64_t at = cl_res(h, n);
  for (int64_t i = 0; i < n; i++) h->pool[at + i] = xs[i];
  __atomic_store_n(&rp[1], n, __ATOMIC_RELAXED);
  __atomic_store_n(&rp[0], at, __ATOMIC_RELEASE);
  return true;
}
static inline void ckl_del(void *p, int64_t k) {
  cl_t *h = p;
  int64_t *rp;
  if (h->sh) {
    rp = cl_srp(h, k, false);
    if (!rp) return;
  } else {
    if ((uint64_t)k >= (uint64_t)(ct_len0(h->row) >> 1)) return;
    rp = &h->row[2 * k];
  }
  __atomic_store_n(&rp[0], 0, __ATOMIC_RELEASE);
  __atomic_store_n(&rp[1], 0, __ATOMIC_RELAXED);
}

// Object types' properties by (object, name): the key object << 32 | name (both under 2^31). A fixed
// array of bucket heads, each a chain of entries (next, key, symbol) in an append-only pool, linked in
// by a compare-and-swap on the head as ik_* below, so nothing is ever moved under a reader and two
// tasks adding one key make one entry. The names in insertion order are a list column beside it
// (types.add_prop).
#define PH_BUCKETS ((int64_t)1 << 20)
// (bloom: per object, a word with a bit for each of its names' hashes, set before the entry is linked:
// a name whose bit is clear is none of the object's, found without walking a chain)
typedef struct { int64_t *head; int64_t *pool; int64_t *bloom; } ph_t;
static inline void *ph_new(void *st) {
  ph_t *h = malloc(sizeof *h);
  if (!h) vu_panic(0, "ph_new: out of memory", 21);
  h->head = calloc((size_t)PH_BUCKETS, 8);
  if (!h->head) vu_panic(0, "ph_new: out of memory", 21);
  h->pool = ct_mk();
  h->pool[-1] = 3;  // (offset 0 is "none")
  h->bloom = ct_mk();
  cs_add(st, h, 2);
  return h;
}
// the entries in the table (VTSC_PHASES)
static inline int64_t ph_count(void *p) { return (((ph_t *)p)->pool[-1] - 3) / 3; }
#include <sys/resource.h>
// the process's peak resident memory so far, in MB (VTSC_PHASES)
static inline int64_t ct_maxrss(void) {
  struct rusage r;
  getrusage(RUSAGE_SELF, &r);
#ifdef __APPLE__
  return (int64_t)r.ru_maxrss >> 20;
#else
  return (int64_t)r.ru_maxrss >> 10;
#endif
}
static inline void ph_free(void *p) {
  ph_t *h = p;
  free(h->head);
  ct_free(h->pool);
  ct_free(h->bloom);
  free(h);
}
static inline uint64_t ph_hash(int64_t k) {
  uint64_t x = (uint64_t)k * 0x9E3779B97F4A7C15ull;
  return x ^ (x >> 31);
}
static inline int64_t ph_bit(int64_t name) { return (int64_t)1 << (((uint64_t)name * 0x9E3779B97F4A7C15ull) >> 58); }
// the entry of key k in the chain from e to stop (0: its end), 0 none
static inline int64_t ph_walk(const int64_t *p, int64_t e, int64_t stop, int64_t k) {
  for (; e != stop; e = p[e])
    if (p[e + 1] == k) return e;
  return 0;
}
// the symbol of o's property name, -1 none
static inline int64_t ph_get(void *p, int64_t o, int64_t name) {
  const ph_t *h = p;
  if ((uint64_t)o < (uint64_t)CT_MAX && (__atomic_load_n(&h->bloom[o], __ATOMIC_ACQUIRE) & ph_bit(name)) == 0) return -1;
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
  if ((uint64_t)o < (uint64_t)CT_MAX) __atomic_fetch_or(&h->bloom[o], ph_bit(name), __ATOMIC_RELEASE);
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
      case 6: ct4_free(s->p[i]); break;
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
// (VTSC_MEM) the store's tables by the memory their entries take, the largest 25 and each kind's sum
#include <stdio.h>
#include <unistd.h>
#ifdef __APPLE__
#include <malloc/malloc.h>
#endif
static int ct_res_nz;
static int64_t ct_res_nzb;
// the bytes of a column's region in memory (its pages touched)
static inline int64_t ct_resident_w(void *h, size_t w) {
  int64_t *base = (int64_t *)h - CT_HEAD;
  size_t len = (size_t)CT_MAX * w + CT_HEAD * 8, pg = (size_t)getpagesize();
  // (only up to the highest entry reserved or written: the length, or the run counter)
  int64_t hi = ((int64_t *)h)[-2] > ((int64_t *)h)[-1] ? ((int64_t *)h)[-2] : ((int64_t *)h)[-1];
  size_t want = (size_t)hi * w + CT_HEAD * 8 + pg;
  if (want < len) len = want;
  size_t np = (len + pg - 1) / pg;
  char *v = malloc(np);
  if (!v) return 0;
  int64_t n = 0, nz = 0;
  if (mincore((void *)base, len, v) == 0)
    for (size_t i = 0; i < np; i++) {
      if (!(v[i] & 1)) continue;
      n += 1;
      // (VTSC_MEM=2: how many of them hold anything but zeros)
      if (ct_res_nz) {
        const int64_t *q = (const int64_t *)((char *)base + i * pg);
        for (size_t j = 0; j < pg / 8; j++) if (q[j] != 0) { nz += 1; break; }
      }
    }
  free(v);
  ct_res_nzb += nz * (int64_t)pg;
  return n * (int64_t)pg;
}
static inline int64_t ct_resident(void *h) { return ct_resident_w(h, 8); }
static inline void cs_report(void *p) {
  cs_t *s = p;
  int64_t tot[6] = {0};
  int64_t *by = calloc((size_t)s->n + 1, sizeof *by);
  const char *mv = getenv("VTSC_MEM");
  ct_res_nz = mv && mv[0] == '2';
  int64_t *nzb = calloc((size_t)s->n + 1, sizeof *nzb);
  for (int64_t i = 0; i < s->n; i++) {
    int64_t b = 0;
    void *x = s->p[i];
    ct_res_nzb = 0;
    // (resident: the pages of each region the process has touched, mincore)
    switch (s->k[i]) {
      case 0: b = ct_resident(x); break;
      case 6: b = ct_resident_w(x, 4); break;
      case 1: b = ct_resident(((cl_t *)x)->row) + ct_resident(((cl_t *)x)->pool) + (((cl_t *)x)->sh ? ct_resident(((cl_t *)x)->se) + CL_SBUCKETS * 8 : 0); break;
      case 2: b = ct_resident(((ph_t *)x)->pool) + ct_resident(((ph_t *)x)->bloom) + PH_BUCKETS * 8; break;
      case 4: b = ct_resident(((ik_t *)x)->pool) + IK_BUCKETS * 8; break;
      case 5: b = ct_resident(((ns_t *)x)->pool) + ct_resident(((ns_t *)x)->ids) + IK_BUCKETS * 8; break;
      default: b = 0;
    }
    by[i] = b;
    nzb[i] = ct_res_nzb;
    if (s->k[i] < 6) tot[s->k[i]] += b;
    else if (s->k[i] == 6) tot[0] += b;
  }
#ifdef __APPLE__
  {
    malloc_statistics_t ms;
    malloc_zone_statistics(NULL, &ms);
    fprintf(stderr, "MEMT malloc in use %lld MB (allocated %lld MB)\n", (long long)(ms.size_in_use >> 20), (long long)(ms.size_allocated >> 20));
  }
#endif
  fprintf(stderr, "MEMT kinds MB: columns %lld lists %lld props %lld interned %lld names %lld\n", (long long)(tot[0] >> 20), (long long)(tot[1] >> 20), (long long)(tot[2] >> 20), (long long)(tot[4] >> 20), (long long)(tot[5] >> 20));
  for (int r = 0; r < 40; r++) {
    int64_t bi = -1;
    for (int64_t i = 0; i < s->n; i++) if (by[i] > 0 && (bi < 0 || by[i] > by[bi])) bi = i;
    if (bi < 0) break;
    fprintf(stderr, "MEMT #%lld kind %d %lld MB (%lld MB not all zeros)", (long long)bi, s->k[bi], (long long)(by[bi] >> 20), (long long)(nzb[bi] >> 20));
    if (s->k[bi] == 1) {
      // (a list column: its rows, the entries their lists hold, and the pool's entries reserved)
      cl_t *h = s->p[bi];
      int64_t nr = ct_len0(h->row) >> 1, live = 0, ne = 0;
      for (int64_t r = 0; r < nr; r++) { live += h->row[2 * r + 1]; ne += h->row[2 * r + 1] > 0; }
      if (h->sh) {
        nr = (h->se[-1] - 4) / 4;
        for (int64_t x = 4; x < h->se[-1]; x += 4) { live += h->se[x + 3]; ne += h->se[x + 3] > 0; }
      }
      fprintf(stderr, " rows %lld (%lld not empty) entries %lld pool %lld", (long long)nr, (long long)ne, (long long)live, (long long)h->pool[-1]);
    }
    fprintf(stderr, "\n");
    by[bi] = 0;
  }
  free(by);
  free(nzb);
}
