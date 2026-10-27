/* Test glue: a counted handle type, scalars and strings through every kind of signature. */
typedef struct { int64_t id; } box;
static int64_t live = 0;
static void box_free(void *p) { live--; free(p); }
static void *box_new(int64_t id) { box *b = (box *)calloc(1, sizeof *b); b->id = id; live++; return b; }
static int64_t box_id(void *p) { return ((box *)p)->id; }
static int64_t box_live(void) { return live; }
static void box_take(void *p) { box_free(p); }
static void *box_null(void) { return NULL; }
static bool box_fail(int64_t code, void **out, vu_str *err) {
    if (code == 0) { *out = box_new(7); return true; }
    if (code == 1) { *err = vu_errf("code %lld", (long long)code); return false; }
    if (code == 3) { *out = NULL; return true; }   /* success without a handle: a bug in the glue */
    return false;                                   /* failure without a message */
}
static double add_f(double a, double b) { return a + b; }
static bool not_b(bool b) { return !b; }
static uint8_t inc_byte(uint8_t b) { return (uint8_t)(b + 1); }
static vu_str echo(const vu_str *s) { return vu_str_from(s->data, s->len); }
static int64_t str_len(const vu_str *s) { return s->len; }
static bool check_pos(int64_t x, vu_str *err) {
    if (x < 0) { *err = vu_errf("negative: %lld", (long long)x); return false; }
    return true;
}
static bool cstr_ok(const vu_str *s) { char *p = vu_cstr(s); bool ok = p != NULL; free(p); return ok; }
