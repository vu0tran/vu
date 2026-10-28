#!/bin/sh
# The MCP SQLite server (mcp/sqlite) against the reference (mcp-server-sqlite, Python), plain and with
# AddressSanitizer/UBSan, on three seeds (tests/run_mcp_sqlite.py). The reference needs the MCP SDK
# before 2.0 (it doesn't start with 2.x): it's installed with pip into tests/.mcp_ref_sqlite the first
# time, or point MCP_SQLITE_REF at its command; without it only a smoke test runs.
d="$(cd "$(dirname "$0")" && pwd)"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
"$d/../vu" build "$d/../mcp/sqlite/main.vu" -o "$work/plain" || exit 1
"$d/../vu" build --san "$d/../mcp/sqlite/main.vu" -o "$work/san" || exit 1
ref="${MCP_SQLITE_REF:-$d/.mcp_ref_sqlite/bin/mcp-server-sqlite}"
if [ ! -x "$ref" ]; then
  python3 -m venv "$d/.mcp_ref_sqlite" >/dev/null 2>&1 && "$d/.mcp_ref_sqlite/bin/pip" install -q "mcp<2" mcp-server-sqlite >/dev/null 2>&1
fi
if [ -x "$ref" ]; then
  for b in plain san; do
    for s in 1 2 3; do python3 "$d/run_mcp_sqlite.py" "$work/$b" "$ref" --seed $s --rounds 400 || exit 1; done
  done
else
  echo "run_mcp_sqlite: no reference server (python3 -m venv and pip needed): smoke test only"
  out=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_query","arguments":{"query":"SELECT 1"}}}' | "$work/plain" --db-path "$work/x.db")
  case "$out" in *"[{'1': 1}]"*) echo "1 passed, 0 failed" ;; *) echo "FAIL: $out"; exit 1 ;; esac
fi
