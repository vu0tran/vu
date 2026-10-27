#define VU_NODE_@@X@@ (sizeof(@@T@@) < 2 * sizeof(void *) ? 2 * sizeof(void *) : sizeof(@@T@@))
static __thread @@T@@ *vu_free_@@X@@;
static __thread int64_t vu_nfree_@@X@@;   /* how many are on it (counted with several threads) */
/* Free nodes shared between threads (see vu_share_free): chunks, each a whole free list whose first
   node links the next chunk in its second word. */
static void *vu_chunks_@@X@@;
static pthread_mutex_t vu_chunks_lock_@@X@@ = PTHREAD_MUTEX_INITIALIZER;
/* Takes up to VU_TAKE nodes from the first chunk (the rest of it stays shared), so that threads
   share a big list instead of one of them taking all of it. */
__attribute__((noinline)) static void vu_take_chunk_@@X@@(void) {
    pthread_mutex_lock(&vu_chunks_lock_@@X@@);
    char *c = (char *)vu_chunks_@@X@@;
    if (c) {
        void *next_chunk, *rest;
        VU_UNPOISON(c, 2 * sizeof(void *));
        memcpy(&next_chunk, c + sizeof(void *), sizeof(void *));
        VU_POISON(c, 2 * sizeof(void *));
        char *p = c;
        for (int i = 1;; i++) {
            VU_UNPOISON(p, sizeof(void *));
            memcpy(&rest, p, sizeof(void *));
            if (!rest || i == VU_TAKE) {
                memset(p, 0, sizeof(void *));   /* p ends the list this thread takes */
                VU_POISON(p, sizeof(void *));
                break;
            }
            VU_POISON(p, sizeof(void *));
            p = (char *)rest;
        }
        if (rest) {
            VU_UNPOISON((char *)rest + sizeof(void *), sizeof(void *));
            memcpy((char *)rest + sizeof(void *), &next_chunk, sizeof(void *));
            VU_POISON((char *)rest + sizeof(void *), sizeof(void *));
            next_chunk = rest;
        }
        __atomic_store_n(&vu_chunks_@@X@@, next_chunk, __ATOMIC_RELAXED);
        vu_free_@@X@@ = (@@T@@ *)c;
        vu_nfree_@@X@@ = VU_TAKE;   /* (at most; it only decides when to give some back) */
    }
    pthread_mutex_unlock(&vu_chunks_lock_@@X@@);
}
static void vu_give_chunk_@@X@@(void) {
    char *c = (char *)vu_free_@@X@@;
    if (!c) return;
    pthread_mutex_lock(&vu_chunks_lock_@@X@@);
    VU_UNPOISON(c + sizeof(void *), sizeof(void *));
    memcpy(c + sizeof(void *), &vu_chunks_@@X@@, sizeof(void *));
    VU_POISON(c + sizeof(void *), sizeof(void *));
    __atomic_store_n(&vu_chunks_@@X@@, (void *)c, __ATOMIC_RELAXED);
    pthread_mutex_unlock(&vu_chunks_lock_@@X@@);
    vu_free_@@X@@ = NULL;
    vu_nfree_@@X@@ = 0;
}
static vu_pool vu_pool_@@X@@ = { vu_give_chunk_@@X@@, NULL };
__attribute__((constructor)) static void vu_pool_init_@@X@@(void) { vu_pool_@@X@@.next = vu_pools; vu_pools = &vu_pool_@@X@@; }
static inline @@T@@ *vu_box_@@X@@(@@T@@ v) {
#ifdef VU_MALLOC
    @@T@@ *p = (@@T@@ *)vu_malloc(sizeof(@@T@@));
#else
#if defined(_OPENMP) || defined(VU_MT)
    if (!vu_free_@@X@@ && __atomic_load_n(&vu_chunks_@@X@@, __ATOMIC_RELAXED)) vu_take_chunk_@@X@@();
#endif
    @@T@@ *p = vu_free_@@X@@;
    if (p) {
        VU_UNPOISON(p, VU_NODE_@@X@@);
        memcpy(&vu_free_@@X@@, p, sizeof(void *));
#if defined(_OPENMP) || defined(VU_MT)
        vu_nfree_@@X@@--;
#endif
    }
    else p = (@@T@@ *)vu_bump(VU_NODE_@@X@@);
#endif
    *p = v;
    return p;
}
static inline void vu_release_@@X@@(@@T@@ *p) {
#ifdef VU_MALLOC
    free(p);
#else
    memcpy(p, &vu_free_@@X@@, sizeof(void *));
    vu_free_@@X@@ = p;
    VU_POISON(p, VU_NODE_@@X@@);   /* any later access to this freed node is reported */
#if defined(_OPENMP) || defined(VU_MT)
    /* nodes made on other threads and freed here (a task receiving values from another thread)
       would pile up on this list: past a limit the list goes to the shared pool */
    if (++vu_nfree_@@X@@ >= 4 * VU_TAKE) vu_give_chunk_@@X@@();
#endif
#endif
}