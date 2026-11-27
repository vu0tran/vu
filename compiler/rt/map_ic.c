/* (no hash kept: an Int key's is a few multiplications, and an entry is 24 bytes for {Int: Int}, was 32) */
struct ME_@@M@@ { @@KC@@ key; @@VC@@ val; bool live; };
/* Small maps (up to VU_SMALL_MAP entries) have no index: a scan comparing keys beats hashing them.
   Bigger maps hash with SipHash and probe an index into the entries. */
static int64_t vu_mfind_@@M@@(const @@M@@ *m, const @@KC@@ *k) {
    if (!m->nidx) {
        for (int64_t i = 0; i < m->nents; i++) {
            const ME_@@M@@ *en = &m->ents[i];
            if (en->live && (en->key == *k)) return i;
        }
        return -1;
    }
    uint64_t h = vu_hash_int((int64_t)*k);
    uint64_t mask = (uint64_t)m->nidx - 1;
    for (uint64_t i = h & mask;; i = (i + 1) & mask) {
        int64_t e = m->idx[i];
        if (e == 0) return -1;
        const ME_@@M@@ *en = &m->ents[e - 1];
        if (en->live && (en->key == *k)) return e - 1;
    }
}
static void vu_mindex_@@M@@(@@M@@ *m, int64_t want) {
    int64_t j = 0;
    for (int64_t i = 0; i < m->nents; i++) if (m->ents[i].live) m->ents[j++] = m->ents[i];
    m->nents = j;
    int64_t n = 8;
    while (n < want) { if (n > INT64_MAX / 4) vu_oom(); n *= 2; }
    vu_lfree(m->idx, (size_t)m->nidx * sizeof(uint32_t));
    m->idx = (uint32_t *)vu_lalloc((size_t)n * sizeof(uint32_t));
    memset(m->idx, 0, (size_t)n * sizeof(uint32_t));
    m->nidx = n;
    for (int64_t i = 0; i < m->nents; i++) {
        uint64_t s = vu_hash_int((int64_t)m->ents[i].key) & ((uint64_t)n - 1);
        while (m->idx[s]) s = (s + 1) & ((uint64_t)n - 1);
        m->idx[s] = (uint32_t)(i + 1);
    }
}
static void vu_mbig_@@M@@(@@M@@ *m) {
    vu_mindex_@@M@@(m, (m->live + 1) * 2);
}
static void vu_mput_@@M@@(@@M@@ *m, @@KC@@ *k, @@VC@@ v, bool take) {
    int64_t e = vu_mfind_@@M@@(m, k);
    if (e >= 0) { ME_@@M@@ *en = &m->ents[e];  en->val = v; if (take) {  } return; }
    if (!m->nidx) {
        if (m->nents >= VU_SMALL_MAP) vu_mbig_@@M@@(m);
    } else if ((m->nents + 1) * 4 > m->nidx * 3) vu_mindex_@@M@@(m, (m->live + 1) * 2);
    uint64_t h = m->nidx ? vu_hash_int((int64_t)*k) : 0;
    if (m->nents >= (int64_t)UINT32_MAX - 1) vu_oom();   /* (the index holds an entry's number + 1 in 32 bits) */
    if (m->nents == m->cap) {
        if (m->cap > (int64_t)(PTRDIFF_MAX / sizeof(ME_@@M@@) / 2)) vu_oom();
        /* 4 entries first (most objects are small), then 12, so a typical record grows once; then 1.5x. */
        int64_t c = m->cap == 0 ? 4 : m->cap == 4 ? 12 : m->cap + m->cap / 2;
        ME_@@M@@ *d = (ME_@@M@@ *)vu_lgrow(m->ents, (size_t)m->cap * sizeof(ME_@@M@@), (size_t)c * sizeof(ME_@@M@@), (size_t)m->nents * sizeof(ME_@@M@@));
        m->ents = d;
        m->cap = c;
    }
    ME_@@M@@ *en = &m->ents[m->nents];
    en->key = take ? *k : *k; en->val = v; en->live = true;
    m->nents++;
    m->live++;
    if (m->nidx) {
        uint64_t mask = (uint64_t)m->nidx - 1, s = h & mask;
        while (m->idx[s]) s = (s + 1) & mask;
        m->idx[s] = (uint32_t)m->nents;
    }
}
static void vu_mset_@@M@@(@@M@@ *m, const @@KC@@ *k, @@VC@@ v, int line) { (void)line; vu_mput_@@M@@(m, (@@KC@@ *)k, v, false); }
/* Takes ownership of *k: the map keeps it, or frees it if the key was already there. */
static void vu_mtake_@@M@@(@@M@@ *m, @@KC@@ *k, @@VC@@ v, int line) { (void)line; vu_mput_@@M@@(m, k, v, true); }
static @@VC@@ *vu_mget_@@M@@(@@M@@ *m, const @@KC@@ *k, int line) {
    int64_t e = vu_mfind_@@M@@(m, k);
    if (e < 0) vu_fail(line, "key not found in map");
    return &m->ents[e].val;
}
static bool vu_mhas_@@M@@(const @@M@@ *m, const @@KC@@ *k) { return vu_mfind_@@M@@(m, k) >= 0; }
static bool vu_mremove_@@M@@(@@M@@ *m, const @@KC@@ *k) {
    int64_t e = vu_mfind_@@M@@(m, k);
    if (e < 0) return false;
    ME_@@M@@ *en = &m->ents[e];
     
    en->live = false;
    m->live--;
    return true;
}
static @@VC@@ vu_mgetor_@@M@@(const @@M@@ *m, const @@KC@@ *k, @@VC@@ d) {
    int64_t e = vu_mfind_@@M@@(m, k);
    return e < 0 ? d : m->ents[e].val;
}
static void vu_dropents_@@M@@(ME_@@M@@ *ents, int64_t n) {
    for (int64_t i = 0; i < n; i++) { ME_@@M@@ *en = &ents[i]; if (!en->live) continue;   }
}
static void vu_freeents_@@M@@(void *v, int64_t n) { vu_dropents_@@M@@((ME_@@M@@ *)v, n); free(v); }
static void drop_@@M@@(@@M@@ *p) {
    vu_lfree(p->idx, (size_t)p->nidx * sizeof(uint32_t));
    if (!p->ents) return;
    if (__builtin_expect(vu_drop_depth < VU_MAX_DROP_DEPTH, 1)) { vu_drop_depth++; vu_dropents_@@M@@(p->ents, p->nents); vu_lfree(p->ents, (size_t)p->cap * sizeof(ME_@@M@@)); vu_drop_depth--; }
    else vu_defer(vu_freeents_@@M@@, p->ents, p->nents);
}