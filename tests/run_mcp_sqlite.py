#!/usr/bin/env python3
"""The MCP SQLite server (mcp/sqlite) against the reference (mcp-server-sqlite, Python), each on its
own database: random sessions of tool calls (tables of random columns, inserts of every type of value,
selects of expressions, updates, deletes, REPLACE, PRAGMA, comments and spaces before the SQL, several
statements, SQL errors, constraint errors, arguments of the wrong type or missing), insights and the
memo resource, the prompt. Every message is compared as JSON, notifications included.
  tests/run_mcp_sqlite.py VU_SERVER REFERENCE_COMMAND [--seed N] [--rounds N]"""
import json, os, random, subprocess, sys, tempfile

INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}

class S:
    def __init__(self, cmd):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.n = 0
        self.init = self.ask(INIT)[-1]
        self.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    def ask(self, m):
        """Every message up to the answer (notifications first)."""
        self.p.stdin.write((json.dumps(m) + "\n").encode()); self.p.stdin.flush()
        out = []
        while True:
            l = self.p.stdout.readline()
            if not l: sys.exit("FAIL: a server closed its output after " + json.dumps(m)[:500])
            x = json.loads(l)
            out.append(x)
            if "id" in x: return out
    def req(self, method, params=None):
        self.n += 1
        m = {"jsonrpc": "2.0", "id": self.n, "method": method}
        if params is not None: m["params"] = params
        return self.ask(m)

TYPES = ["INTEGER", "REAL", "TEXT", "BLOB", "", "NUMERIC", "VARCHAR(10)", "INTEGER NOT NULL", "TEXT UNIQUE", "INTEGER PRIMARY KEY", "REAL DEFAULT 1.5", "TEXT DEFAULT 'x'"]
WORDS = ["a", "b'c", 'd"e', "f\ng", "é", "日本", "\U0001F600", "tab\there", "back\\slash", "", " ", "NULL", "0", "-1", "1e5", "\x7f", "\u00a0nbsp", "\u200b"]

def sql_value(r):
    k = r.random()
    if k < 0.2: return str(r.choice([0, 1, -1, 42, 2**31, -2**63, 2**63 - 1, 9007199254740993]))
    if k < 0.35: return r.choice(["1.5", "0.1", "-0.0", "1e20", "1e-7", "3.0", "123456789.123", "1e308", "2.5e-300"])
    if k < 0.7:
        w = r.choice(WORDS) + (r.choice(WORDS) if r.random() < 0.3 else "")
        return "'" + w.replace("'", "''") + "'"
    if k < 0.85: return "x'" + "".join(r.choice("0123456789abcdef") for _ in range(2 * r.randrange(0, 6))) + "'"
    return "NULL"

EXPRS = ["1", "1.0/3", "2/3", "typeof(1.5)", "length('日本')", "upper('abc')", "'a' || 'b'", "NULL", "x'00ff'", "1e300*1e10", "-0.0", "9223372036854775807",
         "abs(-5)", "round(2.567, 2)", "hex('é')", "char(233, 128512)", "printf('%5.2f', 3.14159)", "1 = 1", "cast('12' as integer)", "zeroblob(3)",
         "replace('aXb', 'X', '''')", "1 AS a, 2 AS a", "'x' AS \"weird name\"", "count(*)", "max(1, 2.5)", "instr('hello', 'l')", "substr('héllo', 2, 2)"]

def session(r, sv, sr, rounds):
    tables = []
    n = 0
    last = [""]
    def same(method, params):
        nonlocal n
        n += 1
        x, y = sv.req(method, params), sr.req(method, params)
        if os.environ.get("SQLITE_TRACE"): print(json.dumps(params)[:300], "\n   vu ->", json.dumps(x)[-130:], "\n   ref->", json.dumps(y)[-130:])
        for a, b in zip(x, y): a.pop("id", None); b.pop("id", None)
        last[0] = json.dumps(y)
        if x != y: sys.exit("FAIL %s %s:\n  vu:  %s\n  ref: %s" % (method, json.dumps(params)[:800], json.dumps(x)[:1500], json.dumps(y)[:1500]))
    def call(name, args):
        same("tools/call", {"name": name, "arguments": args})
        if os.environ.get("SQLITE_TRACE") and name == "write_query":
            for t, _ in tables: same("tools/call", {"name": "read_query", "arguments": {"query": 'SELECT count(*) FROM "%s"' % t}})
    for _ in range(rounds):
        k = r.random()
        pre = r.choice(["", "", "", " ", "\n", "  \t", "-- c\n", "/* c */ ", "\x0c"])
        post = r.choice(["", "", ";", " ;", "; ", ";;", "; SELECT 1", " -- end", " /* x */"])
        if k < 0.12 or not tables:
            t = r.choice(["t", "u", "data", "x y", "t2"]) + str(len(tables))
            cols = ["c%d %s" % (i, r.choice(TYPES)) for i in range(r.randrange(1, 5))]
            q = 'CREATE TABLE "%s" (%s)' % (t, ", ".join(cols))
            if r.random() < 0.1: q = "create table " + r.choice(["if not exists ", ""]) + '"%s" (a)' % t
            call(r.choice(["create_table", "create_table", "write_query"]), {"query": pre + q + post})
            # (only tables that exist: SQLite versions differ in which error they report first for a
            # statement that is wrong twice over, such as a row of the wrong length for a missing table)
            if "successfully" in last[0] or "affected_rows" in last[0]: tables.append((t, len(cols)))
        elif k < 0.45:
            t, nc = r.choice(tables)
            rows = ", ".join("(" + ", ".join(sql_value(r) for _ in range(nc if r.random() < 0.95 else nc + 1)) + ")" for _ in range(r.randrange(1, 4)))
            verb = r.choice(["INSERT INTO", "INSERT INTO", "insert into", "REPLACE INTO", "INSERT OR IGNORE INTO"])
            call("write_query", {"query": pre + '%s "%s" VALUES %s' % (verb, t, rows) + post})
        elif k < 0.65:
            t, nc = r.choice(tables)
            q = r.choice(['SELECT * FROM "%s"' % t, 'SELECT * FROM "%s" ORDER BY rowid' % t, 'select c0, typeof(c0) from "%s"' % t,
                          'SELECT count(*) AS n FROM "%s"' % t, "SELECT " + r.choice(EXPRS), "SELECT " + r.choice(EXPRS) + ", " + r.choice(EXPRS),
                          'SELECT * FROM "%s" WHERE c0 IS NOT NULL LIMIT 2' % t, "SELECT * FROM nope", "SELECT", "SELEC 1", "WITH x AS (SELECT 1) SELECT * FROM x"])
            call(r.choice(["read_query"] * 4 + ["write_query"]), {"query": pre + q + post})
        elif k < 0.75:
            t, nc = r.choice(tables)
            q = r.choice(['UPDATE "%s" SET c0 = %s' % (t, sql_value(r)), 'DELETE FROM "%s" WHERE rowid %% 2 = 0' % t, 'DELETE FROM "%s"' % t,
                          'UPDATE "%s" SET c0 = c0 WHERE 0' % t, "PRAGMA user_version", "PRAGMA table_info(\"%s\")" % t, 'ALTER TABLE "%s" ADD COLUMN z' % t,
                          'DROP TABLE IF EXISTS "nope"', "VACUUM", "UPDATE nope SET a = 1"])
            call(r.choice(["write_query", "write_query", "read_query"]), {"query": pre + q + post})
        elif k < 0.82:
            t, nc = r.choice(tables)
            call("describe_table", {"table_name": r.choice([t, '"%s"' % t, "nope", "", "t); SELECT (1", t.upper()])})
            call("list_tables", {})
        elif k < 0.88:
            call("append_insight", {"insight": r.choice(WORDS) + " insight"})
            same("resources/read", {"uri": r.choice(["memo://insights", "memo://insights", "memo://other", "file:///etc/passwd", "memo://insights/"])})
        elif k < 0.95:
            name = r.choice(["read_query", "write_query", "create_table", "describe_table", "append_insight", "list_tables", "nope"])
            args = r.choice([{}, {"query": 5}, {"query": None}, {"query": ["SELECT 1"]}, {"table_name": True}, {"insight": 1.5}, {"other": "x"}, {"query": "SELECT 1", "extra": 1}])
            call(name, args)
        else:
            same(r.choice(["prompts/list", "resources/list", "tools/list", "prompts/get"]), r.choice([None, {"name": "mcp-demo", "arguments": {"topic": r.choice(WORDS)}}, {"name": "mcp-demo", "arguments": {}}, {"name": "x"}]))
    return n

def main():
    a = sys.argv[1:]
    vu, ref = a[0], a[1]
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    rounds = int(a[a.index("--rounds") + 1]) if "--rounds" in a else 400
    r = random.Random(seed)
    d = tempfile.mkdtemp()
    sv = S([vu, "--db-path", os.path.join(d, "vu", "a.db")])
    sr = S(ref.split() + ["--db-path", os.path.join(d, "ref", "a.db")])
    if sv.init != sr.init: sys.exit("FAIL initialize:\n  vu:  %s\n  ref: %s" % (sv.init, sr.init))
    n = session(r, sv, sr, rounds)
    print("run_mcp_sqlite: %d answers the same as the reference server (seed %d)" % (n, seed))

main()
