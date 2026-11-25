/* -- SharedMap[K, V]: one table that tasks on several threads (and par loop threads) read and add to
   at once. Keys are Int, Byte, Bool or Str; values plain scalars (Int, Float, Bool, Byte), kept as 8
   bytes, so no value has a reference count another thread could touch. An entry, once added, never
   changes and never goes: m.add(k, v) puts v only when k has no value yet and returns the value k has
   (v, or the one another thread added first), so two tasks interning the same key get the same value.
   Reads take no lock: the table is split into shards by the key's hash, each an open-addressed array of
   slots; a writer holds its shard's spin lock, writes a slot's key and value, then its hash word with a
   release store, and a reader that sees the hash word (acquire) sees the key and value. A shard that
   fills past half is copied into one twice the size, published by pointer; the old array stays (until
   the last handle goes), so a reader still probing it never reads freed memory: it may just miss what
   was added since, as any read racing an add may. */
#include <sched.h>
#define VU_SM_SHARDS 64
typedef struct { uint64_t h; int64_t k; int64_t v; char *s; } vu_sm_slot;   /* h: 0 empty, else the hash | top bit; s: a Str key's bytes (k its length) */
typedef struct vu_sm_tab { int64_t cap; struct vu_sm_tab *old; vu_sm_slot sl[]; } vu_sm_tab;
typedef struct { vu_sm_tab *t; int64_t n; int lk; char pad[64 - sizeof(void *) - sizeof(int64_t) - sizeof(int)]; } vu_sm_shard;
typedef struct vu_smap { int64_t refs; vu_sm_shard sh[VU_SM_SHARDS]; } vu_smap;

static vu_smap *vu_smap_new(void) {
    vu_smap *m = (vu_smap *)calloc(1, sizeof *m);
    if (!m) vu_oom();
    m->refs = 1;
    return m;
}
static vu_smap *vu_smap_share(vu_smap *m) { __atomic_add_fetch(&m->refs, 1, __ATOMIC_RELAXED); return m; }
static void vu_smap_release(vu_smap **p) {
    vu_smap *m = *p;
    if (!m) return;
    *p = NULL;
    if (__atomic_sub_fetch(&m->refs, 1, __ATOMIC_ACQ_REL) > 0) return;
    for (int i = 0; i < VU_SM_SHARDS; i++) {
        vu_sm_tab *t = m->sh[i].t;
        /* (the keys' bytes are shared by a shard's arrays: freed once, from the newest) */
        if (t)
            for (int64_t j = 0; j < t->cap; j++)
                if (t->sl[j].h) free(t->sl[j].s);
        while (t) { vu_sm_tab *o = t->old; free(t); t = o; }
    }
    free(m);
}
static inline uint64_t vu_sm_mark(uint64_t h) { return h | ((uint64_t)1 << 63); }
static inline vu_sm_shard *vu_sm_shard_of(vu_smap *m, uint64_t h) { return &m->sh[(h >> 40) & (VU_SM_SHARDS - 1)]; }
static inline void vu_sm_lock(int *l) {
    int spins = 0;
    while (__atomic_exchange_n(l, 1, __ATOMIC_ACQUIRE)) {
        while (__atomic_load_n(l, __ATOMIC_RELAXED)) {
            if (++spins > 256) { sched_yield(); spins = 0; }
        }
    }
}
static inline void vu_sm_unlock(int *l) { __atomic_store_n(l, 0, __ATOMIC_RELEASE); }
/* The slot holding the key, or -1 */
static inline int64_t vu_sm_find(const vu_sm_tab *t, uint64_t mk, int64_t k, const uint8_t *s) {
    uint64_t mask = (uint64_t)t->cap - 1;
    for (uint64_t i = mk & mask;; i = (i + 1) & mask) {
        uint64_t h = __atomic_load_n(&t->sl[i].h, __ATOMIC_ACQUIRE);
        if (h == 0) return -1;
        if (h == mk && t->sl[i].k == k && (!s || k == 0 || memcmp(t->sl[i].s, s, (size_t)k) == 0)) return (int64_t)i;
    }
}
/* With the shard's lock held: room for one more entry */
static void vu_sm_room(vu_sm_shard *sh) {
    vu_sm_tab *t = sh->t;
    if (t && (sh->n + 1) * 2 <= t->cap) return;
    int64_t cap = t ? t->cap * 2 : 16;
    vu_sm_tab *nt = (vu_sm_tab *)calloc(1, sizeof *nt + (size_t)cap * sizeof(vu_sm_slot));
    if (!nt) vu_oom();
    nt->cap = cap;
    nt->old = t;
    if (t)
        for (int64_t j = 0; j < t->cap; j++) {
            vu_sm_slot *o = &t->sl[j];
            if (!o->h) continue;
            uint64_t i = o->h & (uint64_t)(cap - 1);
            while (nt->sl[i].h) i = (i + 1) & (uint64_t)(cap - 1);
            nt->sl[i] = *o;
        }
    __atomic_store_n(&sh->t, nt, __ATOMIC_RELEASE);
}
static int64_t vu_sm_add(vu_smap *m, uint64_t h, int64_t k, const uint8_t *s, int64_t v) {
    uint64_t mk = vu_sm_mark(h);
    vu_sm_shard *sh = vu_sm_shard_of(m, h);
    vu_sm_lock(&sh->lk);
    if (sh->t) {
        int64_t e = vu_sm_find(sh->t, mk, k, s);
        if (e >= 0) { int64_t r = sh->t->sl[e].v; vu_sm_unlock(&sh->lk); return r; }
    }
    vu_sm_room(sh);
    vu_sm_tab *t = sh->t;
    uint64_t mask = (uint64_t)t->cap - 1;
    uint64_t i = mk & mask;
    while (t->sl[i].h) i = (i + 1) & mask;
    t->sl[i].k = k;
    t->sl[i].v = v;
    if (s) {
        char *c = (char *)malloc((size_t)k + 1);
        if (!c) vu_oom();
        if (k) memcpy(c, s, (size_t)k);
        t->sl[i].s = c;
    }
    __atomic_store_n(&t->sl[i].h, mk, __ATOMIC_RELEASE);
    __atomic_store_n(&sh->n, sh->n + 1, __ATOMIC_RELAXED);
    vu_sm_unlock(&sh->lk);
    return v;
}
static inline int64_t vu_sm_get(vu_smap *m, uint64_t h, int64_t k, const uint8_t *s, int64_t d) {
    vu_sm_tab *t = __atomic_load_n(&vu_sm_shard_of(m, h)->t, __ATOMIC_ACQUIRE);
    if (!t) return d;
    int64_t e = vu_sm_find(t, vu_sm_mark(h), k, s);
    return e < 0 ? d : t->sl[e].v;
}
static inline int64_t vu_smap_get_i(vu_smap *m, int64_t k, int64_t d) { return vu_sm_get(m, vu_hash_int(k), k, NULL, d); }
static inline int64_t vu_smap_add_i(vu_smap *m, int64_t k, int64_t v) { return vu_sm_add(m, vu_hash_int(k), k, NULL, v); }
static inline int64_t vu_smap_get_s(vu_smap *m, const vu_str *k, int64_t d) {
    return vu_sm_get(m, vu_siphash((const uint8_t *)k->data, (size_t)k->len), k->len, (k->data ? (const uint8_t *)k->data : (const uint8_t *)""), d);
}
static inline int64_t vu_smap_add_s(vu_smap *m, const vu_str *k, int64_t v) {
    return vu_sm_add(m, vu_siphash((const uint8_t *)k->data, (size_t)k->len), k->len, (k->data ? (const uint8_t *)k->data : (const uint8_t *)""), v);
}
static int64_t vu_smap_len(vu_smap *m) {
    int64_t n = 0;
    for (int i = 0; i < VU_SM_SHARDS; i++) n += __atomic_load_n(&m->sh[i].n, __ATOMIC_RELAXED);
    return n;
}
/* A Float value travels as its 8 bytes */
static inline int64_t vu_sm_fbits(double x) { int64_t r; memcpy(&r, &x, 8); return r; }
static inline double vu_sm_bitsf(int64_t x) { double r; memcpy(&r, &x, 8); return r; }
