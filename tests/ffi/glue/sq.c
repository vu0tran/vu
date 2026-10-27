#include <sqlite3.h>
static void db_close(void *p) { sqlite3_close((sqlite3 *)p); }
static bool db_open(const vu_str *path, void **out, vu_str *err) {
    char *p = vu_cstr(path);
    if (!p) { *err = vu_errf("path contains a zero byte"); return false; }
    sqlite3 *db = NULL;
    int rc = sqlite3_open(p, &db);
    free(p);
    if (rc != SQLITE_OK) { *err = vu_errf("can't open: %s", db ? sqlite3_errmsg(db) : "out of memory"); sqlite3_close(db); return false; }
    *out = db;
    return true;
}
static bool db_exec(void *db, const vu_str *sql, vu_str *err) {
    char *s = vu_cstr(sql);
    char *msg = NULL;
    int rc = sqlite3_exec((sqlite3 *)db, s, NULL, NULL, &msg);
    free(s);
    if (rc != SQLITE_OK) { *err = vu_errf("%s", msg ? msg : "error"); sqlite3_free(msg); return false; }
    return true;
}
static void stmt_free(void *p) { sqlite3_finalize((sqlite3_stmt *)p); }
static bool db_prepare(void *db, const vu_str *sql, void **out, vu_str *err) {
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2((sqlite3 *)db, (const char *)sql->data, (int)sql->len, &st, NULL) != SQLITE_OK) {
        *err = vu_errf("%s", sqlite3_errmsg((sqlite3 *)db)); return false;
    }
    *out = st;
    return true;
}
static bool stmt_step(void *st, bool *out, vu_str *err) {
    int rc = sqlite3_step((sqlite3_stmt *)st);
    if (rc == SQLITE_ROW) { *out = true; return true; }
    if (rc == SQLITE_DONE) { *out = false; return true; }
    *err = vu_errf("%s", sqlite3_errmsg(sqlite3_db_handle((sqlite3_stmt *)st)));
    return false;
}
static int64_t stmt_int(void *st, int64_t col) { return sqlite3_column_int64((sqlite3_stmt *)st, (int)col); }
static vu_str stmt_text(void *st, int64_t col) {
    const unsigned char *p = sqlite3_column_text((sqlite3_stmt *)st, (int)col);
    return vu_str_from(p, sqlite3_column_bytes((sqlite3_stmt *)st, (int)col));
}
static vu_str sqlite_version(void) { return vu_str_from(sqlite3_libversion(), (int64_t)strlen(sqlite3_libversion())); }
