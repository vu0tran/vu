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
static inline int64_t ct_len(void *h) { return __atomic_load_n(&((const int64_t *)h)[-2], __ATOMIC_ACQUIRE); }
