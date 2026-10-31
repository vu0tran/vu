#!/bin/bash
# Server-sent events (web.stream, web.event): read as EventSource reads them, with refusals, 30
# clients at once, clients that leave, and HTTP/2 (505). Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d)
pass=0; fail=0
for flags in "--release" "--san"; do
  if ! $VU build sse/server.vu $flags -o "$work/server" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  if timeout 120 python3 sse/client.py "$work/server" > "$work/res" 2>&1; then pass=$((pass+1)); echo "ok    $flags ($(tail -1 "$work/res"); $(grep -c "checked in Chromium" "$work/res") in Chromium)"
  else fail=$((fail+1)); echo "FAIL  $flags"; tail -20 "$work/res"; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
