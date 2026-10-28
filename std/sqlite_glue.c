/* SQLite for std/sqlite.vu: a thin layer over the sqlite3 C API (statements, text parameters and
   results). Every value crosses as text, as with pg; NULL is reported separately. */
#include <sqlite3.h>

static void sq_close(void *p) { sqlite3_close_v2((sqlite3 *)p); }
static void sq_finalize(void *p) { sqlite3_finalize((sqlite3_stmt *)p); }

static bool sq_open(const vu_str *path, void **out, vu_str *err) {
    char *p = vu_cstr(path);
    if (!p) { *err = vu_errf("a database path can't contain a zero byte"); return false; }
    sqlite3 *db = NULL;
    int rc = sqlite3_open_v2(p, &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_NOMUTEX, NULL);
    free(p);
    if (rc != SQLITE_OK) {
        *err = vu_errf("can't open the database: %s", db ? sqlite3_errmsg(db) : sqlite3_errstr(rc));
        if (db) sqlite3_close_v2(db);
        return false;
    }
    sqlite3_busy_timeout(db, 5000);
    sqlite3_extended_result_codes(db, 1);
    *out = db;
    return true;
}

static bool sq_prepare(void *db, const vu_str *sql, void **out, vu_str *err) {
    sqlite3_stmt *st = NULL;
    const char *tail = NULL;
    if (sql->len > 1000000000) { *err = vu_errf("SQL too long"); return false; }
    int rc = sqlite3_prepare_v2((sqlite3 *)db, (const char *)sql->data, (int)sql->len, &st, &tail);
    if (rc != SQLITE_OK) { *err = vu_errf("%s", sqlite3_errmsg((sqlite3 *)db)); return false; }
    if (!st) { *err = vu_errf("the SQL holds no statement"); return false; }
    /* one statement per call: anything but spaces and ';' after it is refused */
    if (tail) {
        const char *end = (const char *)sql->data + sql->len;
        for (const char *c = tail; c < end; c++) {
            if (*c != ' ' && *c != '\n' && *c != '\t' && *c != '\r' && *c != ';') {
                sqlite3_finalize(st);
                *err = vu_errf("one statement at a time: there is more SQL after the first");
                return false;
            }
        }
    }
    *out = st;
    return true;
}

static int64_t sq_param_count(void *st) { return sqlite3_bind_parameter_count((sqlite3_stmt *)st); }

static bool sq_bind_text(void *st, int64_t i, const vu_str *v, vu_str *err) {
    /* (an empty Vu string may have no buffer, and a NULL pointer would bind NULL, not "") */
    const char *p = v->data ? (const char *)v->data : "";
    int rc = sqlite3_bind_text64((sqlite3_stmt *)st, (int)i, p, (sqlite3_uint64)v->len, SQLITE_TRANSIENT, SQLITE_UTF8);
    if (rc != SQLITE_OK) { *err = vu_errf("%s", sqlite3_errstr(rc)); return false; }
    return true;
}

static bool sq_bind_null(void *st, int64_t i, vu_str *err) {
    int rc = sqlite3_bind_null((sqlite3_stmt *)st, (int)i);
    if (rc != SQLITE_OK) { *err = vu_errf("%s", sqlite3_errstr(rc)); return false; }
    return true;
}

/* true: a row is ready; false: done */
static bool sq_step(void *db, void *st, bool *out, vu_str *err) {
    int rc = sqlite3_step((sqlite3_stmt *)st);
    if (rc == SQLITE_ROW) { *out = true; return true; }
    if (rc == SQLITE_DONE) { *out = false; return true; }
    *err = vu_errf("%s", sqlite3_errmsg((sqlite3 *)db));
    return false;
}

static int64_t sq_columns(void *st) { return sqlite3_column_count((sqlite3_stmt *)st); }

static vu_str sq_column_name(void *st, int64_t i) {
    const char *n = sqlite3_column_name((sqlite3_stmt *)st, (int)i);
    return n ? vu_str_from((const uint8_t *)n, (int64_t)strlen(n)) : vu_str_from((const uint8_t *)"", 0);
}

static bool sq_is_null(void *st, int64_t i) { return sqlite3_column_type((sqlite3_stmt *)st, (int)i) == SQLITE_NULL; }

static vu_str sq_text(void *st, int64_t i) {
    const unsigned char *t = sqlite3_column_text((sqlite3_stmt *)st, (int)i);
    int n = sqlite3_column_bytes((sqlite3_stmt *)st, (int)i);
    return vu_str_from(t ? t : (const unsigned char *)"", t ? n : 0);
}

static int64_t sq_changes(void *db) { return sqlite3_changes64((sqlite3 *)db); }
static int64_t sq_last_id(void *db) { return sqlite3_last_insert_rowid((sqlite3 *)db); }
