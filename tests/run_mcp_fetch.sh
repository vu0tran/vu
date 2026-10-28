#!/bin/sh
# The MCP fetch server (mcp/fetch) against the reference (mcp-server-fetch, Python): first its parts
# against the libraries the reference uses (tests/mcp_fetch/parts.py: URLs, robots.txt, the address
# guard, the HTML tokenizer, text decoding), then the whole server over stdio, plain and with
# AddressSanitizer/UBSan (tests/run_mcp_fetch.py). The reference is installed with pip into
# tests/.mcp_ref_py the first time (or point MCP_FETCH_PY at a Python that has it); without it only a
# smoke test runs.
d="$(cd "$(dirname "$0")" && pwd)"
top="$d/.."
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
"$top/vu" build "$top/mcp/fetch/main.vu" -o "$work/plain" || exit 1
"$top/vu" build --san "$top/mcp/fetch/main.vu" -o "$work/san" || exit 1
py="${MCP_FETCH_PY:-$d/.mcp_ref_py/bin/python}"
if [ ! -x "$py" ] || ! "$py" -c 'import mcp_server_fetch' 2>/dev/null; then
  python3 -m venv "$d/.mcp_ref_py" >/dev/null 2>&1 && "$d/.mcp_ref_py/bin/pip" install -q mcp-server-fetch >/dev/null 2>&1
fi
if [ -x "$py" ] && "$py" -c 'import mcp_server_fetch' 2>/dev/null; then
  mkdir "$work/src" && cp "$top"/mcp/fetch/*.vu "$d"/mcp_fetch/*_driver.vu "$work/src/" && rm "$work/src/main.vu"
  for part in url robots guard tok charset; do
    "$top/vu" build --san "$work/src/${part}_driver.vu" -o "$work/$part" || exit 1
    for s in 1 2; do "$py" "$d/mcp_fetch/parts.py" $part "$work/$part" --seed $s --n 3000 || exit 1; done
  done
  for b in plain san; do
    for s in 1 2; do python3 "$d/run_mcp_fetch.py" "$work/$b" "$py" --seed $s --rounds 200 || exit 1; done
  done
else
  echo "run_mcp_fetch: no reference server (python3 -m venv and pip needed): smoke test only"
  out=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"fetch","arguments":{"url":"x"}}}' | "$work/plain")
  case "$out" in *'relative URL without a base'*) echo "1 passed, 0 failed" ;; *) echo "FAIL: $out"; exit 1 ;; esac
fi
