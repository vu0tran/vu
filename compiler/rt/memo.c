/* -- Memo[K, V]: a value for each key, computed once, by the first task (or par loop thread) that asks
   for it, and then frozen: every caller gets a handle to the same Shared value (vu_sh_*, whose first
   field is its reference count). One lock for every Memo, held only to find, claim or fill an entry,
   never while a value is computed. A caller asking for a value being computed waits on the condition
   variable, holding its thread; so the computing task must not give its thread away while it computes
   (vu_block fails while vu_memo_depth > 0, and vu_task_yield doesn't yield), or a waiter on the same
   thread would keep it from finishing. A computation that needs its own key, directly or through
   others (a waits for b, which waits for a), is reported instead of waiting forever. */
typedef struct vu_memo_ent vu_memo_ent;
typedef struct vu_memo_who { vu_memo_ent *waiting; } vu_memo_who;   /* a thread: the entry it waits for */
struct vu_memo_ent {
    uint64_t h;
    char *key;
    int64_t klen;
    void *val;                 /* NULL while it's computed */
    vu_memo_who *owner;        /* the thread computing it */
    vu_memo_ent *next;
};
typedef struct vu_memo {
    int64_t refs;
    void (*dropv)(void *);     /* drops a value's handle */
    vu_memo_ent **b;
    int64_t nb, n, done;
} vu_memo;
/* (VU_G, not static: a program built in parts (VU_PART) has one copy of each for all of them; static,
   each part had its own lock, condition variable and thread identity, so two threads running
   different parts' code claimed and grew one Memo's table at once: freed it twice, corrupted the heap,
   and a waiter could miss the fill that would wake it) */
VU_G pthread_mutex_t vu_memo_lock VU_GI(PTHREAD_MUTEX_INITIALIZER);
VU_G pthread_cond_t vu_memo_cond VU_GI(PTHREAD_COND_INITIALIZER);
VU_G __thread int vu_memo_depth;   /* how many values this thread is computing */
VU_G __thread vu_memo_who vu_memo_me;

static vu_memo *vu_memo_new(void (*dropv)(void *)) {
    vu_memo *m = (vu_memo *)calloc(1, sizeof *m);
    if (!m) vu_oom();
    m->refs = 1;
    m->dropv = dropv;
    m->nb = 16;
    m->b = (vu_memo_ent **)calloc((size_t)m->nb, sizeof *m->b);
    if (!m->b) vu_oom();
    return m;
}
static vu_memo *vu_memo_share(vu_memo *m) { __atomic_add_fetch(&m->refs, 1, __ATOMIC_RELAXED); return m; }
static void vu_memo_release(vu_memo **p) {
    vu_memo *m = *p;
    if (!m) return;
    *p = NULL;
    if (__atomic_sub_fetch(&m->refs, 1, __ATOMIC_ACQ_REL) > 0) return;
    /* (no value is being computed: the task computing one holds a handle) */
    for (int64_t i = 0; i < m->nb; i++)
        for (vu_memo_ent *e = m->b[i], *nx; e; e = nx) {
            nx = e->next;
            if (e->val) m->dropv(e->val);
            free(e->key);
            free(e);
        }
    free(m->b);
    free(m);
}
static int64_t vu_memo_len(vu_memo *m) {
    pthread_mutex_lock(&vu_memo_lock);
    int64_t n = m->done;
    pthread_mutex_unlock(&vu_memo_lock);
    return n;
}
/* With the lock held */
static void vu_memo_grow(vu_memo *m) {
    int64_t nb = m->nb * 2;
    vu_memo_ent **b = (vu_memo_ent **)calloc((size_t)nb, sizeof *b);
    if (!b) vu_oom();
    for (int64_t i = 0; i < m->nb; i++)
        for (vu_memo_ent *e = m->b[i], *nx; e; e = nx) {
            nx = e->next;
            int64_t s = (int64_t)(e->h & (uint64_t)(nb - 1));
            e->next = b[s];
            b[s] = e;
        }
    free(m->b);
    m->b = b;
    m->nb = nb;
}
/* The value for key k (a new handle to it), waiting for it if another thread is computing it; or NULL,
   with *ent set, when it's this caller's to compute: it then calls vu_memo_fill(m, *ent, value). */
static void *vu_memo_claim(vu_memo *m, const void *k, int64_t klen, void **ent, int line) {
    uint64_t h = vu_siphash((const uint8_t *)k, (size_t)klen);
    pthread_mutex_lock(&vu_memo_lock);
    vu_memo_ent *e = m->b[h & (uint64_t)(m->nb - 1)];
    while (e && !(e->h == h && e->klen == klen && (klen == 0 || memcmp(e->key, k, (size_t)klen) == 0))) e = e->next;
    if (!e) {
        if (m->n * 2 >= m->nb) vu_memo_grow(m);
        e = (vu_memo_ent *)calloc(1, sizeof *e);
        if (!e) vu_oom();
        e->h = h;
        e->klen = klen;
        e->key = (char *)vu_malloc((size_t)klen + 1);
        if (klen) memcpy(e->key, k, (size_t)klen);
        e->owner = &vu_memo_me;
        int64_t s = (int64_t)(h & (uint64_t)(m->nb - 1));
        e->next = m->b[s];
        m->b[s] = e;
        m->n++;
        vu_memo_depth++;
        pthread_mutex_unlock(&vu_memo_lock);
        *ent = e;
        return NULL;
    }
    if (!e->val) {
        /* being computed: by this thread (its computation needs its own value), or by one that waits,
           through others, for a value this thread is computing */
        for (vu_memo_ent *x = e; x;) {
            vu_memo_who *o = x->owner;
            if (!o) break;
            if (o == &vu_memo_me) {
                pthread_mutex_unlock(&vu_memo_lock);
                vu_fail(line, "m.get(key, compute): computing this key's value needs that value itself (the computations wait for each other)");
            }
            x = o->waiting;
        }
        vu_memo_me.waiting = e;
        while (!e->val) pthread_cond_wait(&vu_memo_cond, &vu_memo_lock);
        vu_memo_me.waiting = NULL;
    }
    void *v = e->val;
    __atomic_add_fetch((int64_t *)v, 1, __ATOMIC_RELAXED);
    pthread_mutex_unlock(&vu_memo_lock);
    *ent = NULL;
    return v;
}
/* v: the caller's handle to the value it computed; the Memo keeps another */
static void vu_memo_fill(vu_memo *m, void *ent, void *v) {
    vu_memo_ent *e = (vu_memo_ent *)ent;
    __atomic_add_fetch((int64_t *)v, 1, __ATOMIC_RELAXED);
    pthread_mutex_lock(&vu_memo_lock);
    e->val = v;
    e->owner = NULL;
    m->done++;
    pthread_cond_broadcast(&vu_memo_cond);
    pthread_mutex_unlock(&vu_memo_lock);
    vu_memo_depth--;
}
static void vu_memo_parked(void) {
    vu_fail(0, "a Memo's compute function waited (on a channel, a sleep, the network or a select): it can't, since tasks waiting for its value hold their threads");
}
