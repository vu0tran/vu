/* Standard input by lines, for std/stdio.vu: a buffer of what read() returned past the last line
   handed out. One reader (the program's main flow) is assumed, as with any stream. */

static uint8_t *vin_buf;
static int64_t vin_len, vin_cap, vin_off;
static bool vin_eof;

/* The next line without its '\n' (a '\r' before it is kept), or an error "end of input" once
   standard input has ended (a last line without '\n' is still returned first). */
static bool vin_line(vu_str *out, vu_str *err) {
    for (;;) {
        uint8_t *nl = vin_len > vin_off ? (uint8_t *)memchr(vin_buf + vin_off, '\n', (size_t)(vin_len - vin_off)) : NULL;
        if (nl) {
            int64_t n = (int64_t)(nl - (vin_buf + vin_off));
            vu_str s = {0};
            vu_str_cat_bytes(&s, vin_buf + vin_off, n);
            vin_off += n + 1;
            *out = s;
            return true;
        }
        if (vin_eof) {
            if (vin_len > vin_off) {
                vu_str s = {0};
                vu_str_cat_bytes(&s, vin_buf + vin_off, vin_len - vin_off);
                vin_off = vin_len;
                *out = s;
                return true;
            }
            *err = vu_errf("end of input");
            return false;
        }
        if (vin_off > 0) {   /* move what's left to the front */
            memmove(vin_buf, vin_buf + vin_off, (size_t)(vin_len - vin_off));
            vin_len -= vin_off;
            vin_off = 0;
        }
        if (vin_cap - vin_len < 65536) {
            int64_t nc = vin_cap ? vin_cap * 2 : 131072;
            if (nc - vin_len < 65536) nc = vin_len + 131072;
            uint8_t *nb = (uint8_t *)vu_malloc((size_t)nc);
            if (vin_len) memcpy(nb, vin_buf, (size_t)vin_len);
            free(vin_buf);
            vin_buf = nb;
            vin_cap = nc;
        }
        ssize_t k = read(0, vin_buf + vin_len, (size_t)(vin_cap - vin_len));
        if (k < 0 && errno == EINTR) continue;
        if (k < 0) { *err = vu_errf("can't read standard input: %s", strerror(errno)); return false; }
        if (k == 0) vin_eof = true;
        vin_len += k;
    }
}

static void vin_flush(void) { fflush(stdout); }
