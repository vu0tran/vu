#!/bin/bash
# Memory that must stay bounded: values made on par worker threads and freed on another thread,
# round after round (tests/memory/*.vu print "ok", or how much resident memory grew). Plain
# release builds: sanitizers hold freed memory in quarantine, so they can't run these.
cd "$(dirname "$0")" || exit 1
VU=${VU:-../vu}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
pass=0; fail=0
for f in memory/*.vu; do
  out=$($VU build --release "$f" -o "$work/p" 2>&1 && "$work/p" 2>&1)
  if [ "$out" = ok ]; then pass=$((pass+1)); echo "ok    $f"; else fail=$((fail+1)); echo "FAIL  $f: $out"; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
