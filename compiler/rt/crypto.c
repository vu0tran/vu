/* ---- Hashing and encoding: sha256, hmac_sha256, pbkdf2_sha256, random_bytes, base64 and hex. Written
   here (FIPS 180-4, RFC 2104, RFC 8018, RFC 4648) rather than taken from OpenSSL, so a program that
   hashes doesn't link libcrypto. tests/run_crypto.py checks them against Python's hashlib, hmac and
   base64. */
typedef struct { uint32_t h[8]; uint64_t n; uint8_t buf[64]; size_t used; } vu_sha;
static const uint32_t vu_sha_k[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
};
#define VU_ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
static void vu_sha_block(vu_sha *c, const uint8_t *p) {
    uint32_t w[64];
    for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 | (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = VU_ROR(w[i - 15], 7) ^ VU_ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = VU_ROR(w[i - 2], 17) ^ VU_ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = c->h[0], b = c->h[1], cc = c->h[2], d = c->h[3], e = c->h[4], f = c->h[5], g = c->h[6], h = c->h[7];
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h + (VU_ROR(e, 6) ^ VU_ROR(e, 11) ^ VU_ROR(e, 25)) + ((e & f) ^ (~e & g)) + vu_sha_k[i] + w[i];
        uint32_t t2 = (VU_ROR(a, 2) ^ VU_ROR(a, 13) ^ VU_ROR(a, 22)) + ((a & b) ^ (a & cc) ^ (b & cc));
        h = g; g = f; f = e; e = d + t1; d = cc; cc = b; b = a; a = t1 + t2;
    }
    c->h[0] += a; c->h[1] += b; c->h[2] += cc; c->h[3] += d; c->h[4] += e; c->h[5] += f; c->h[6] += g; c->h[7] += h;
}
static void vu_sha_init(vu_sha *c) {
    static const uint32_t iv[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    memcpy(c->h, iv, sizeof iv);
    c->n = 0;
    c->used = 0;
}
static void vu_sha_add(vu_sha *c, const uint8_t *p, size_t n) {
    c->n += n;
    if (c->used) {
        size_t take = 64 - c->used < n ? 64 - c->used : n;
        memcpy(c->buf + c->used, p, take);
        c->used += take; p += take; n -= take;
        if (c->used < 64) return;
        vu_sha_block(c, c->buf);
        c->used = 0;
    }
    while (n >= 64) { vu_sha_block(c, p); p += 64; n -= 64; }
    if (n) { memcpy(c->buf, p, n); c->used = n; }
}
static void vu_sha_end(vu_sha *c, uint8_t out[32]) {
    uint64_t bits = c->n * 8;
    uint8_t pad[72] = {0x80};
    size_t padn = (c->used < 56 ? 56 : 120) - c->used;
    for (int i = 0; i < 8; i++) pad[padn + i] = (uint8_t)(bits >> (56 - 8 * i));
    vu_sha_add(c, pad, padn + 8);
    for (int i = 0; i < 8; i++) { out[4 * i] = (uint8_t)(c->h[i] >> 24); out[4 * i + 1] = (uint8_t)(c->h[i] >> 16); out[4 * i + 2] = (uint8_t)(c->h[i] >> 8); out[4 * i + 3] = (uint8_t)c->h[i]; }
}
static vu_str vu_bytes_str(const uint8_t *p, int64_t n) { vu_str r = {0}; vu_str_cat_bytes(&r, p, n); return r; }
static vu_str vu_sha256(const vu_str *s) {
    vu_sha c; uint8_t d[32];
    vu_sha_init(&c);
    vu_sha_add(&c, s->data ? s->data : (const uint8_t *)"", (size_t)s->len);
    vu_sha_end(&c, d);
    return vu_bytes_str(d, 32);
}
/* HMAC-SHA256 with the key's inner and outer states prepared once (pbkdf2 reuses them). */
typedef struct { vu_sha in, out; } vu_hmac;
static void vu_hmac_init(vu_hmac *m, const uint8_t *key, size_t kn) {
    uint8_t k[64] = {0}, pad[64];
    if (kn > 64) { vu_sha c; vu_sha_init(&c); vu_sha_add(&c, key, kn); vu_sha_end(&c, k); }
    else if (kn) memcpy(k, key, kn);
    for (int i = 0; i < 64; i++) pad[i] = k[i] ^ 0x36;
    vu_sha_init(&m->in); vu_sha_add(&m->in, pad, 64);
    for (int i = 0; i < 64; i++) pad[i] = k[i] ^ 0x5c;
    vu_sha_init(&m->out); vu_sha_add(&m->out, pad, 64);
}
static void vu_hmac_run(const vu_hmac *m, const uint8_t *p, size_t n, uint8_t out[32]) {
    vu_sha c = m->in; uint8_t d[32];
    vu_sha_add(&c, p, n); vu_sha_end(&c, d);
    c = m->out; vu_sha_add(&c, d, 32); vu_sha_end(&c, out);
}
static vu_str vu_hmac_sha256(const vu_str *key, const vu_str *msg) {
    vu_hmac m; uint8_t d[32];
    vu_hmac_init(&m, key->data, (size_t)key->len);
    vu_hmac_run(&m, msg->data ? msg->data : (const uint8_t *)"", (size_t)msg->len, d);
    return vu_bytes_str(d, 32);
}
#ifdef VU_MT
static void vu_task_yield(void);
#endif
/* PBKDF2-HMAC-SHA256 with a 32-byte result (one block), as SCRAM-SHA-256 uses it. A password hash takes
   about half a second on purpose; in a program with tasks it gives the other tasks on its thread a turn
   every 16,384 iterations (about 10 ms), so a server signing someone in doesn't stall the connections
   that share the thread. */
static vu_str vu_pbkdf2_sha256(const vu_str *pw, const vu_str *salt, int64_t iters, int line) {
    if (iters < 1 || iters > 100000000) vu_fail(line, "pbkdf2_sha256(): %lld iterations (it takes 1 to 100,000,000)", (long long)iters);
    vu_hmac m; uint8_t u[32], t[32];
    vu_hmac_init(&m, pw->data, (size_t)pw->len);
    vu_str first = {0};
    vu_str_cat_bytes(&first, salt->data, salt->len);
    vu_str_cat_bytes(&first, (const uint8_t *)"\x00\x00\x00\x01", 4);
    vu_hmac_run(&m, first.data, (size_t)first.len, u);
    free(first.data);
    memcpy(t, u, 32);
    for (int64_t i = 1; i < iters; i++) {
        vu_hmac_run(&m, u, 32, u);
        for (int j = 0; j < 32; j++) t[j] ^= u[j];
#ifdef VU_MT
        if ((i & 16383) == 0) vu_task_yield();
#endif
    }
    return vu_bytes_str(t, 32);
}
/* random_bytes(n): from the kernel's generator (getrandom), for keys and nonces. */
static vu_str vu_random_bytes(int64_t n, int line) {
    if (n < 0 || n > (1 << 26)) vu_fail(line, "random_bytes(%lld): it gives 0 to 67,108,864 bytes", (long long)n);
    vu_str r = {0};
    vu_str_reserve(&r, n);
    int64_t got = 0;
    while (got < n) {
        ssize_t k = getrandom(r.data + got, (size_t)(n - got), 0);
        if (k < 0) { if (errno == EINTR) continue; vu_fail(line, "random_bytes(): the system's random generator failed (%s)", strerror(errno)); }
        got += k;
    }
    r.len = n;
    return r;
}
static const char vu_b64[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static vu_str vu_b64encode(const vu_str *s) {
    vu_str r = {0};
    vu_str_reserve(&r, (s->len + 2) / 3 * 4);
    const uint8_t *d = s->data;
    int64_t i = 0;
    for (; i + 2 < s->len; i += 3) {
        uint32_t v = (uint32_t)d[i] << 16 | (uint32_t)d[i + 1] << 8 | d[i + 2];
        uint8_t o[4] = {(uint8_t)vu_b64[v >> 18], (uint8_t)vu_b64[(v >> 12) & 63], (uint8_t)vu_b64[(v >> 6) & 63], (uint8_t)vu_b64[v & 63]};
        vu_str_cat_bytes(&r, o, 4);
    }
    if (i < s->len) {
        uint32_t v = (uint32_t)d[i] << 16 | (i + 1 < s->len ? (uint32_t)d[i + 1] << 8 : 0);
        uint8_t o[4] = {(uint8_t)vu_b64[v >> 18], (uint8_t)vu_b64[(v >> 12) & 63], i + 1 < s->len ? (uint8_t)vu_b64[(v >> 6) & 63] : '=', '='};
        vu_str_cat_bytes(&r, o, 4);
    }
    return r;
}
/* b64decode(s): standard alphabet with padding, as Python's b64decode(s, validate=True). */
static bool vu_b64decode(const vu_str *s, vu_str *out, vu_str *err) {
    *out = (vu_str){0};
    if (s->len % 4) { *err = vu_errf("not base64: the length (%lld) isn't a multiple of 4", (long long)s->len); return false; }
    vu_str_reserve(out, s->len / 4 * 3);
    for (int64_t i = 0; i < s->len; i += 4) {
        uint32_t v = 0;
        int pad = 0;
        for (int j = 0; j < 4; j++) {
            uint8_t c = s->data[i + j];
            int x;
            if (c >= 'A' && c <= 'Z') x = c - 'A';
            else if (c >= 'a' && c <= 'z') x = c - 'a' + 26;
            else if (c >= '0' && c <= '9') x = c - '0' + 52;
            else if (c == '+') x = 62;
            else if (c == '/') x = 63;
            else if (c == '=' && i + 4 == s->len && j >= 2 && (j == 3 || s->data[i + 3] == '=')) { x = 0; pad++; }
            else { free(out->data); *out = (vu_str){0}; *err = vu_errf("not base64: byte %lld", (long long)(i + j)); return false; }
            if (pad && c != '=') { free(out->data); *out = (vu_str){0}; *err = vu_errf("not base64: byte %lld", (long long)(i + j)); return false; }
            v = v << 6 | (uint32_t)x;
        }
        uint8_t o[3] = {(uint8_t)(v >> 16), (uint8_t)(v >> 8), (uint8_t)v};
        vu_str_cat_bytes(out, o, 3 - pad);
    }
    return true;
}
static vu_str vu_hex(const vu_str *s) {
    static const char d[] = "0123456789abcdef";
    vu_str r = {0};
    vu_str_reserve(&r, s->len * 2);
    for (int64_t i = 0; i < s->len; i++) { uint8_t o[2] = {(uint8_t)d[s->data[i] >> 4], (uint8_t)d[s->data[i] & 15]}; vu_str_cat_bytes(&r, o, 2); }
    return r;
}
/* from_hex(s): two hex digits per byte (either case), as Python's bytes.fromhex without spaces. */
static bool vu_from_hex(const vu_str *s, vu_str *out, vu_str *err) {
    *out = (vu_str){0};
    if (s->len % 2) { *err = vu_errf("not hex: an odd number of digits (%lld)", (long long)s->len); return false; }
    vu_str_reserve(out, s->len / 2);
    for (int64_t i = 0; i < s->len; i += 2) {
        int v[2];
        for (int j = 0; j < 2; j++) {
            uint8_t c = s->data[i + j];
            if (c >= '0' && c <= '9') v[j] = c - '0';
            else if (c >= 'a' && c <= 'f') v[j] = c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') v[j] = c - 'A' + 10;
            else { free(out->data); *out = (vu_str){0}; *err = vu_errf("not hex: byte %lld", (long long)(i + j)); return false; }
        }
        uint8_t b = (uint8_t)(v[0] << 4 | v[1]);
        vu_str_cat_bytes(out, &b, 1);
    }
    return true;
}
/* sha1(data): only for protocols that require it (the WebSocket handshake); it isn't collision-safe. */
static vu_str vu_sha1(const vu_str *s) {
    uint32_t h[5] = {0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0};
    uint64_t n = (uint64_t)s->len;
    uint64_t total = ((n + 8) / 64 + 1) * 64;
    uint8_t *m = (uint8_t *)vu_malloc((size_t)total);
    memset(m, 0, (size_t)total);
    if (n) memcpy(m, s->data, (size_t)n);
    m[n] = 0x80;
    for (int i = 0; i < 8; i++) m[total - 1 - i] = (uint8_t)((n * 8) >> (8 * i));
    for (uint64_t off = 0; off < total; off += 64) {
        uint32_t w[80];
        for (int i = 0; i < 16; i++) w[i] = (uint32_t)m[off + 4 * i] << 24 | (uint32_t)m[off + 4 * i + 1] << 16 | (uint32_t)m[off + 4 * i + 2] << 8 | m[off + 4 * i + 3];
        for (int i = 16; i < 80; i++) { uint32_t x = w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16]; w[i] = (x << 1) | (x >> 31); }
        uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4];
        for (int i = 0; i < 80; i++) {
            uint32_t f, k;
            if (i < 20) { f = (b & c) | (~b & d); k = 0x5A827999; }
            else if (i < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1; }
            else if (i < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC; }
            else { f = b ^ c ^ d; k = 0xCA62C1D6; }
            uint32_t t = ((a << 5) | (a >> 27)) + f + e + k + w[i];
            e = d; d = c; c = (b << 30) | (b >> 2); b = a; a = t;
        }
        h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e;
    }
    free(m);
    uint8_t out[20];
    for (int i = 0; i < 5; i++) { out[4 * i] = (uint8_t)(h[i] >> 24); out[4 * i + 1] = (uint8_t)(h[i] >> 16); out[4 * i + 2] = (uint8_t)(h[i] >> 8); out[4 * i + 3] = (uint8_t)h[i]; }
    return vu_bytes_str(out, 20);
}
