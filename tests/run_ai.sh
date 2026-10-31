#!/bin/bash
# std/ai against a fake Anthropic and OpenAI (tests/ai/server.py): the requests (headers, the exact
# JSON), the answers, retries after 529 with Retry-After, errors. Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d)
pass=0; fail=0
for flags in "--release" "--san"; do
  if ! $VU build ai/main.vu $flags -o "$work/main" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  if timeout 200 python3 ai/server.py "$work/main" > "$work/res" 2>&1; then pass=$((pass+1)); echo "ok    $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  $flags"; tail -30 "$work/res"; fi
  if ! $VU build ai/stream.vu $flags -o "$work/stream" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build stream $flags"; cat "$work/err"; continue; fi
  if timeout 200 python3 ai/stream_server.py "$work/stream" > "$work/res" 2>&1; then pass=$((pass+1)); echo "ok    stream $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  stream $flags"; tail -30 "$work/res"; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
