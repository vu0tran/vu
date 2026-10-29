#!/bin/sh
# The MCP git server (mcp/git) against the reference (mcp-server-git, Python), plain and with
# AddressSanitizer/UBSan, on three seeds and once confined with --repository (tests/run_mcp_git.py).
# The reference is installed with pip into tests/.mcp_ref_py the first time (or point MCP_GIT_PY at
# a Python that has it); without it only a smoke test runs.
d="$(cd "$(dirname "$0")" && pwd)"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
"$d/../vu" build "$d/../mcp/git/main.vu" -o "$work/plain" || exit 1
"$d/../vu" build --san "$d/../mcp/git/main.vu" -o "$work/san" || exit 1
py="${MCP_GIT_PY:-$d/.mcp_ref_py/bin/python}"
if [ ! -x "$py" ] || ! "$py" -c 'import mcp_server_git' 2>/dev/null; then
  python3 -m venv "$d/.mcp_ref_py" >/dev/null 2>&1 && "$d/.mcp_ref_py/bin/pip" install -q mcp-server-git >/dev/null 2>&1
fi
if [ -x "$py" ] && "$py" -c 'import mcp_server_git' 2>/dev/null && command -v git >/dev/null; then
  for b in plain san; do
    for s in 1 2 3; do python3 "$d/run_mcp_git.py" "$work/$b" "$py" --seed $s --rounds 300 || exit 1; done
    python3 "$d/run_mcp_git.py" "$work/$b" "$py" --seed 4 --rounds 200 --confined || exit 1
  done
else
  echo "run_mcp_git: no reference server (python3 -m venv, pip and git needed): smoke test only"
  out=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_status","arguments":{"repo_path":"/nonexistent"}}}' | "$work/plain")
  case "$out" in *'/nonexistent'*) echo "1 passed, 0 failed" ;; *) echo "FAIL: $out"; exit 1 ;; esac
fi
