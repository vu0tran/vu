#!/bin/bash
# The fast check while developing (about a minute), instead of the full gate:
#   1. rebuild the compiler from its source (compiler/build.sh: fixed point, new seed),
#   2. run the targeted tests whose names match the patterns.
#   tests/run_quick.sh own_ sort_      # targeted tests with "own_" or "sort_" in the name
#   tests/run_quick.sh                 # step 1 only
# Before calling a feature done, run the full gate (see CLAUDE.md).
cd "$(dirname "$0")/.." || exit 1
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
compiler/build.sh || { echo "QUICK CHECK FAILED"; exit 1; }
fail=0
if [ $# -gt 0 ]; then
  mkdir -p "$work/t/targeted"
  cp tests/run_targeted.sh tests/tsan.supp "$work/t/"
  for p in "$@"; do cp tests/targeted/*"$p"*.vu "$work/t/targeted/" 2>/dev/null; done
  echo "-- $(ls "$work/t/targeted" | wc -l) targeted tests matching: $*"
  vu="$PWD/vu"
  r=$(cd "$work/t" && VU="$vu" ./run_targeted.sh 2>&1)
  echo "$r" | grep -a -A2 '^FAIL'
  echo "$r" | tail -1
  echo "$r" | tail -1 | grep -q ' 0 failed' || fail=1
fi
[ $fail -eq 0 ] && echo "QUICK CHECK PASSED" || echo "QUICK CHECK FAILED"
exit $fail
