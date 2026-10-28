# mcp-sqlite

The MCP SQLite server in Vu: `read_query`, `write_query`, `create_table`, `list_tables`,
`describe_table` and `append_insight`, the `mcp-demo` prompt and the `memo://insights` resource,
answering as the reference server (`mcp-server-sqlite` 2025.4.25, Python) does: the same tools,
schemas, results (rows written as Python writes a list of dicts, `[{'id': 1, 'name': 'a'}]`),
messages, transactions and notifications.

```
./vu build mcp/sqlite/main.vu -o mcp-sqlite          # needs libsqlite3 (and its headers) to build
./mcp-sqlite --db-path ./sqlite_mcp_server.db
```

The reference is archived, and it no longer starts with the current Python MCP SDK (2.x): installed
today (`pip install mcp-server-sqlite`), it stops at startup with `AttributeError: 'Server' object has
no attribute 'list_resources'`. It runs with `mcp<2`, which is what it's compared against.

## What it can reach

`main` holds `Fs` and `Os` only at startup, to find the database's path (`~` expanded) and make its
folder. The tools get the path and `Ffi` (SQLite's C library) and nothing else: no network, no
program, no other file, whatever SQL they're sent (SQLite's own `ATTACH` can still open another
database file, as in the reference).

## Measured

2-vCPU Linux VM, Python 3.13 (`mcp/bench_start.py`: median of 15 starts, then 1,000
`read_query` calls of `SELECT 1, 2.5, 'x'`):

| | Vu | Python reference |
|---|---|---|
| install | one 226 KB binary (and the system's libsqlite3) | a 70 MB virtualenv |
| start to the `initialize` answer | 2.1 ms | 443 ms |
| memory (RSS) | 3.4 MB | 57 MB |
| `read_query` calls per second | 15,683 | 457 |

## Checked

`tests/run_mcp_sqlite.sh` runs both servers, each on its own database, through random sessions:
tables of random columns, inserts of every kind of value (integers to 64 bits, floats, text with
quotes, newlines and emoji, blobs, NULL), selects of expressions, updates, deletes, `REPLACE`,
`PRAGMA`, `ALTER`, comments and spaces before the SQL, several statements at once, SQL and
constraint errors, arguments missing or of the wrong type, insights and the memo resource, the
prompt. Every message is compared as JSON (the resource-updated notification included): about
2,700 answers on six seeds, the same, plain and with AddressSanitizer.

## Where it differs

- **SQLite's own messages** come from the SQLite library each server uses (Python's bundled one,
  the system's here). Versions differ in which error they report for a statement that is wrong
  twice over (a row of the wrong length for a table that doesn't exist); the test leaves those out.
- Text that isn't UTF-8 (a blob cast to text) is an error in the reference ("Could not decode to
  UTF-8 column ..."); the message here is close, not the same.
- `INSERT ... RETURNING` through `write_query`: the reference counts the changed rows before it
  has stepped the statement to its end; this server counts them all.
- It also answers the 2026-07-28 protocol revision, which the reference's SDK (before 2.0) doesn't.
