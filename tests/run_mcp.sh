#!/bin/sh
# The MCP filesystem server (mcp/filesystem): built plainly and with AddressSanitizer/UBSan, each run
# against the reference Node server on three seeds (tests/run_mcp.py). The reference is installed with
# npm into tests/.mcp_ref the first time (or point MCP_REF at its dist/index.js); without node or npm the
# comparison is skipped and only a smoke test runs.
d="$(cd "$(dirname "$0")" && pwd)"
top="$d/.."
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
"$top/vu" build "$top/mcp/filesystem/main.vu" -o "$work/plain" || exit 1
"$top/vu" build --san "$top/mcp/filesystem/main.vu" -o "$work/san" || exit 1
ref="${MCP_REF:-$d/.mcp_ref/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js}"
if [ ! -f "$ref" ] && command -v npm >/dev/null 2>&1; then
  mkdir -p "$d/.mcp_ref" && (cd "$d/.mcp_ref" && echo '{}' > package.json && npm install --no-audit --no-fund @modelcontextprotocol/server-filesystem@2.0.1 >/dev/null 2>&1)
fi
if [ -f "$ref" ] && command -v node >/dev/null 2>&1; then
  for b in plain san; do
    for s in 1 2 3; do
      ASAN_OPTIONS=detect_leaks=1 python3 "$d/run_mcp.py" "$work/$b" "$ref" --seed $s --rounds 300 || exit 1
    done
  done
else
  echo "run_mcp: no reference server (node and npm needed): smoke test only"
  out=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | "$work/plain" "$work")
  case "$out" in *list_allowed_directories*) echo "1 passed, 0 failed" ;; *) echo "FAIL: tools/list: $out"; exit 1 ;; esac
fi
