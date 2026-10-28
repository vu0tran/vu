#!/bin/sh
# The MCP time server (mcp/time) against the reference (mcp-server-time, Python), plain and with
# AddressSanitizer/UBSan, on three seeds (tests/run_mcp_time.py). The reference is installed with pip
# into tests/.mcp_ref_py the first time (or point MCP_TIME_PY at a Python that has it); without it
# only a smoke test runs.
d="$(cd "$(dirname "$0")" && pwd)"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
"$d/../vu" build "$d/../mcp/time/main.vu" -o "$work/plain" || exit 1
"$d/../vu" build --san "$d/../mcp/time/main.vu" -o "$work/san" || exit 1
py="${MCP_TIME_PY:-$d/.mcp_ref_py/bin/python}"
if [ ! -x "$py" ]; then
  python3 -m venv "$d/.mcp_ref_py" >/dev/null 2>&1 && "$d/.mcp_ref_py/bin/pip" install -q mcp-server-time >/dev/null 2>&1
fi
if [ -x "$py" ] && "$py" -c 'import mcp_server_time' 2>/dev/null && [ -d /usr/share/zoneinfo ]; then
  for b in plain san; do
    for s in 1 2 3; do python3 "$d/run_mcp_time.py" "$work/$b" "$py" --seed $s --rounds 1500 || exit 1; done
  done
else
  echo "run_mcp_time: no reference server (python3 -m venv and pip needed): smoke test only"
  out=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_current_time","arguments":{"timezone":"UTC"}}}' | "$work/plain" --local-timezone UTC)
  case "$out" in *'"timezone":"UTC"'*) echo "1 passed, 0 failed" ;; *) echo "FAIL: $out"; exit 1 ;; esac
fi
