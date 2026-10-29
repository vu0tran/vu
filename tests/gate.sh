#!/bin/bash
# The full gate: the self-host check and every suite. Prints one line per suite, with its time; a suite
# that fails says FAIL or shows failures in its counts. Exit status: 0 only if all passed.
#
# How it saves time (every check still runs):
#   1. Binaries are cached by what they're made from (VU_CACHE, see `vu build`), and prebuild.sh first
#      builds, on every core, what the last gate's suites built (vu_record.sh writes that down), so a
#      suite's builds are mostly copies, and a program whose C didn't change isn't compiled again.
#   2. Suites that don't time anything, run servers or start threads of their own run side by side,
#      one per core, longest first; the others then run alone, on a quiet machine.
# GATE_JOBS=1 runs every suite alone; VU_CACHE= (empty) turns the cache off.
cd "$(dirname "$0")" || exit 1
start=$SECONDS
export VU_REAL="$PWD/../vu"
export VU_CACHE=${VU_CACHE-$HOME/.cache/vu-gate}
jobs=${GATE_JOBS:-$(nproc)}
out=$(mktemp -d); stamp="$out/stamp"; : > "$stamp"
trap 'rm -rf "$out"' EXIT
if [ -n "$VU_CACHE" ]; then
  mkdir -p "$VU_CACHE"
  # a binary also depends on the system's headers and libraries, which the cache key doesn't see: a
  # change to the installed packages empties the cache
  sys=$( (cat /var/lib/dpkg/status 2>/dev/null; ls -l /usr/lib/x86_64-linux-gnu 2>/dev/null) | sha256sum | cut -c1-16)
  if [ "$(cat "$VU_CACHE/system" 2>/dev/null)" != "$sys" ]; then
    find "$VU_CACHE" -mindepth 1 -delete; echo "$sys" > "$VU_CACHE/system"
  fi
  t=$SECONDS; r=$(VU="$VU_REAL" ./prebuild.sh 2>&1); echo "prebuild.sh: $(echo "$r" | tail -1) [$((SECONDS - t)) s]"
  export VU_RECORD="$out/builds.list" VU="$PWD/vu_record.sh"
fi

# suite NAME: runs it, keeping its output, exit status and time
suite() {
  local t=$SECONDS
  ./"$1" > "$out/$1.log" 2>&1
  echo $? > "$out/$1.rc"; echo $((SECONDS - t)) > "$out/$1.t"
}
export -f suite; export out

# side by side, longest first (times from a gate on 2 cores)
together=(run_differential.sh run_targeted.sh run_arm64.sh run_fmt.sh run_loops.sh run_selfhost.sh run_macos.sh run_json.sh
          run_zlib.sh run_debug.sh run_re.sh run_modules.sh run_tests.sh run_ffi.sh run_crypto.sh run_text.sh run_path.sh
          run_cli_std.sh run_pkg.sh run_cli.sh run_tools.sh run_wasm.sh run_sqlite.sh run_time_zones.sh run_profile.sh run_norm.sh run_mcp.sh run_mcp_time.sh run_mcp_fetch.sh run_mcp_vu.sh run_mcp_sqlite.sh run_mcp_git.sh)
# alone: servers and clients over real sockets, threads, memory and timing measurements
alone=(run_net.sh run_tls.sh run_http.sh run_web.sh run_h2.sh run_ws.sh run_pg.sh run_pg_hostile.sh run_pg_tls.sh run_http_client.sh run_web_sockets.sh run_mt.sh run_memory.sh)
printf '%s\n' "${together[@]}" | xargs -P "$jobs" -I{} bash -c 'suite {}'
for s in "${alone[@]}"; do suite "$s"; done

fail=0
for s in run_selfhost.sh run_tests.sh run_cli.sh run_targeted.sh run_json.sh run_differential.sh run_debug.sh run_modules.sh \
         run_text.sh run_net.sh run_memory.sh run_ffi.sh run_tls.sh run_http.sh run_web.sh run_mt.sh \
         run_crypto.sh run_re.sh run_path.sh run_cli_std.sh run_fmt.sh run_tools.sh run_pkg.sh run_pg.sh run_pg_hostile.sh run_pg_tls.sh run_http_client.sh run_web_sockets.sh \
         run_ws.sh run_h2.sh run_loops.sh run_zlib.sh run_arm64.sh run_macos.sh run_wasm.sh run_sqlite.sh run_time_zones.sh run_profile.sh run_norm.sh run_mcp.sh run_mcp_time.sh run_mcp_fetch.sh run_mcp_vu.sh run_mcp_sqlite.sh run_mcp_git.sh; do
  r=$(tr -d '\0' < "$out/$s.log" 2>/dev/null); rc=$(cat "$out/$s.rc" 2>/dev/null || echo 1); t=$(cat "$out/$s.t" 2>/dev/null)
  if [ $s = run_selfhost.sh ]; then
    echo "$s: $(echo "$r" | tail -1) [$t s]"; echo "$r" | grep -a '^FAIL'
    echo "$r" | tail -1 | grep -q PASS || fail=1
    continue
  fi
  echo "$s: $(echo "$r" | grep -a -E '^[0-9]+ (passed|identical)' | tr '\n' ' ') (exit $rc) [$t s]"
  [ "$rc" -eq 0 ] || { fail=1; echo "$r" | grep -a -A3 '^FAIL' | head -20; }
done
if [ -n "$VU_CACHE" ]; then
  # the next gate replays what this one built; entries this one didn't use go
  sort -u "$VU_RECORD" > "$VU_CACHE/builds.list"
  find "$VU_CACHE" -maxdepth 1 -type f ! -name builds.list ! -name system ! -newer "$stamp" -delete
  echo "cache: $(find "$VU_CACHE" -maxdepth 1 -type f | wc -l) binaries, $(du -sh "$VU_CACHE" | cut -f1)"
fi
echo "total: $((SECONDS - start)) s"
[ $fail -eq 0 ] && echo "GATE PASSED" || echo "GATE FAILED"
exit $fail
