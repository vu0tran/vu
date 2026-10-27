struct ME_@@M@@ { @@KC@@ key; @@VC@@ val; uint64_t hash; bool live; };
/* Small maps (up to VU_SMALL_MAP entries) have no index: a scan comparing keys beats hashing them.
   Bigger maps hash with SipHash and probe an index into the entries. */
static int64_t vu_mfind_@@M@@(const @@M@@ *m, const @@KC@@ *k) {
    if (!m->nidx) {
        for (int64_t i = 0; i < m->nents; i++) {
            const ME_@@M@@ *en = &m->ents[i];
            if (en->live && (vu_str_eq(&en->key, k))) return i;
        }
        return -1;
    }
    uint64_t h = vu_siphash(k->data, (size_t)k->len);
    uint64_t mask = (uint64_t)m->nidx - 1;
    for (uint64_t i = h & mask;; i = (i + 1) & mask) {
        int64_t e = m->idx[i];
        if (e == 0) return -1;
        const ME_@@M@@ *en = &m->ents[e - 1];
        if (en->live && en->hash == h && (vu_str_eq(&en->key, k))) return e - 1;
    }
}
static void vu_mindex_@@M@@(@@M@@ *m, int64_t want) {
    int64_t j = 0;
    for (int64_t i = 0; i < m->nents; i++) if (m->ents[i].live) m->ents[j++] = m->ents[i];
    m->nents = j;
    int64_t n = 8;
    while (n < want) { if (n > INT64_MAX / 4) vu_oom(); n *= 2; }
    free(m->idx);
    m->idx = (int64_t *)calloc((size_t)n, sizeof(int64_t));
    if (!m->idx) vu_oom();
    m->nidx = n;
    for (int64_t i = 0; i < m->nents; i++) {
        uint64_t s = m->ents[i].hash & ((uint64_t)n - 1);
        while (m->idx[s]) s = (s + 1) & ((uint64_t)n - 1);
        m->idx[s] = i + 1;
    }
}
static void vu_mbig_@@M@@(@@M@@ *m) {
    for (int64_t i = 0; i < m->nents; i++) {
        ME_@@M@@ *en = &m->ents[i];
        if (!en->live) continue;
        const @@KC@@ *k = &en->key;
        en->hash = vu_siphash(k->data, (size_t)k->len);
    }
    vu_mindex_@@M@@(m, (m->live + 1) * 2);
}
static void vu_mput_@@M@@(@@M@@ *m, @@KC@@ *k, @@VC@@ v, bool take) {
    int64_t e = vu_mfind_@@M@@(m, k);
    if (e >= 0) { ME_@@M@@ *en = &m->ents[e]; drop_@@VM@@(&en->val); en->val = v; if (take) { drop_Str(k); } return; }
    if (!m->nidx) {
        if (m->nents >= VU_SMALL_MAP) vu_mbig_@@M@@(m);
    } else if ((m->nents + 1) * 4 > m->nidx * 3) vu_mindex_@@M@@(m, (m->live + 1) * 2);
    uint64_t h = m->nidx ? vu_siphash(k->data, (size_t)k->len) : 0;
    if (m->nents == m->cap) {
        if (m->cap > (int64_t)(PTRDIFF_MAX / sizeof(ME_@@M@@) / 2)) vu_oom();
        /* 4 entries first (most objects are small), then 12, so a typical record grows once; then 1.5x. */
        int64_t c = m->cap == 0 ? 4 : m->cap == 4 ? 12 : m->cap + m->cap / 2;
        ME_@@M@@ *d = (ME_@@M@@ *)realloc(m->ents, (size_t)c * sizeof(ME_@@M@@));
        if (!d) vu_oom();
        m->ents = d;
        m->cap = c;
    }
    ME_@@M@@ *en = &m->ents[m->nents];
    en->key = take ? *k : vu_str_dup(k); en->val = v; en->hash = h; en->live = true;
    m->nents++;
    m->live++;
    if (m->nidx) {
        uint64_t mask = (uint64_t)m->nidx - 1, s = h & mask;
        while (m->idx[s]) s = (s + 1) & mask;
        m->idx[s] = m->nents;
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
    drop_Str(&en->key); drop_@@VM@@(&en->val);
    en->live = false;
    m->live--;
    return true;
}
static void vu_freeents_@@M@@(void *v, int64_t n) {
    ME_@@M@@ *ents = (ME_@@M@@ *)v;
    for (int64_t i = 0; i < n; i++) { ME_@@M@@ *en = &ents[i]; if (!en->live) continue; drop_Str(&en->key); drop_@@VM@@(&en->val); }
    free(ents);
}
static void drop_@@M@@(@@M@@ *p) {
    free(p->idx);
    if (!p->ents) return;
    if (__builtin_expect(vu_drop_depth < VU_MAX_DROP_DEPTH, 1)) { vu_drop_depth++; vu_freeents_@@M@@(p->ents, p->nents); vu_drop_depth--; }
    else vu_defer(vu_freeents_@@M@@, p->ents, p->nents);
}