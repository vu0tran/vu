#!/bin/bash
# One program, every check, one summary: tests/try.sh FILE.vu [ARGS...]
#   check (the error, if any), a quick run, an ASan/UBSan/LeakSanitizer run (same output required),
#   and the generated C audited under gcc -Wall -Wextra (the flags run_differential.sh uses).
here="$(cd "$(dirname "$0")/.." && pwd)"
VU=${VU:-"$here/vu"}
f=$1; shift
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
if ! out=$($VU check "$f" 2>&1); then echo "check: $out"; exit 1; fi
quick=$($VU run "$f" "$@" 2>"$work/qerr"); qrc=$?
echo "$quick" | head -40
head -12 "$work/qerr"
echo "-- run: exit $qrc"
$VU build "$f" --san -o "$work/san" --emit-c "$work/c.c" >/dev/null 2>&1 || { echo "-- san: build failed"; exit 1; }
san=$("$work/san" "$@" 2>"$work/serr"); src=$?
grep -m3 -A8 'ERROR\|runtime error\|LeakSanitizer' "$work/serr"
if [ "$san" = "$quick" ] && [ $src -eq $qrc ]; then echo "-- san: clean, same output"; else
  echo "-- san: exit $src, output differs:"; diff <(echo "$quick") <(echo "$san") | head -30; fi
w=$(gcc -std=gnu11 -fwrapv -fopenmp -Wall -Wextra -Wno-unused-parameter -Wno-unused-function -Wno-unused-variable \
      -Wno-unused-but-set-variable -Wno-unknown-pragmas -Wno-infinite-recursion -O2 -c "$work/c.c" -o /dev/null 2>&1 | grep -A3 'warning:')
if [ -z "$w" ]; then echo "-- C audit: no warnings"; else echo "-- C audit:"; echo "$w" | head -20; fi
