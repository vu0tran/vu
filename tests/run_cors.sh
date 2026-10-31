#!/bin/bash
# web.cors in a real browser (tests/cors): skipped (and says so) without Playwright.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d)
pass=0; fail=0
for flags in "--release" "--san"; do
  if ! $VU build cors/server.vu $flags -o "$work/server" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  if timeout 120 python3 cors/client.py "$work/server" "$PWD/.." > "$work/res" 2>&1; then pass=$((pass+1)); echo "ok    $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  $flags"; tail -20 "$work/res"; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
