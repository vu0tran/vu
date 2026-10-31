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
  # the parts check pure functions: they run side by side, VU_FETCH_JOBS at a time (default one per
  # core). The four whole-server runs come after, one at a time: they time out requests, and under a
  # loaded machine the reference server's own timeout fired (CI, 4 cores) while Vu's answered.
  for part in url robots guard tok charset; do
    "$top/vu" build --san "$work/src/${part}_driver.vu" -o "$work/$part" || exit 1
  done
  jobs=${VU_FETCH_JOBS:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)}
  mkdir "$work/cmd" "$work/out"
  # one small script per run, named for it; xargs gets the names
  for part in url robots guard tok charset; do for s in 1 2; do
    printf '"%s" "%s" %s "%s" --seed %s --n 3000\n' "$py" "$d/mcp_fetch/parts.py" $part "$work/$part" $s > "$work/cmd/part-$part-$s"
  done; done
  for b in plain san; do for s in 1 2; do
    printf 'python3 "%s" "%s" "%s" --seed %s --rounds 200\n' "$d/run_mcp_fetch.py" "$work/$b" "$py" $s > "$work/cmd/server-$b-$s"
  done; done
  parts="part-url-1 part-url-2 part-robots-1 part-robots-2 part-guard-1 part-guard-2 part-tok-1 part-tok-2 part-charset-1 part-charset-2"
  servers="server-plain-1 server-plain-2 server-san-1 server-san-2"
  printf '%s\n' $parts | xargs -P "$jobs" -I{} sh -c 'sh "$1/cmd/$2" > "$1/out/$2" 2>&1; echo $? > "$1/out/$2.rc"' _ "$work" {}
  for n in $servers; do sh "$work/cmd/$n" > "$work/out/$n" 2>&1; echo $? > "$work/out/$n.rc"; done
  names="$parts $servers"
  bad=0
  for n in $names; do
    cat "$work/out/$n"
    [ "$(cat "$work/out/$n.rc" 2>/dev/null)" = 0 ] || { echo "FAIL: $n (exit $(cat "$work/out/$n.rc" 2>/dev/null))"; bad=1; }
  done
  [ $bad = 0 ] || exit 1
else
  echo "run_mcp_fetch: no reference server (python3 -m venv and pip needed): smoke test only"
  out=$(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"fetch","arguments":{"url":"x"}}}' | "$work/plain")
  case "$out" in *'relative URL without a base'*) echo "1 passed, 0 failed" ;; *) echo "FAIL: $out"; exit 1 ;; esac
fi
