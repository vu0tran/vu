#!/bin/bash
# Tasks on several threads, run many times, since a race shows up only sometimes:
#   - every targeted test of tasks (targeted/*mt_*, and the others that spawn) that expects output,
#     ROUNDS times each under ThreadSanitizer and ROUNDS times in an optimized build: same output,
#     no race reported;
#   - mt/print_lines.vu: 8 tasks printing 2,000 lines each at once; every line must arrive whole.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
ROUNDS=${ROUNDS:-3}
ARCHER=${ARCHER:-/usr/lib/llvm-18/lib/libarcher.so}   # (for par loops inside tasks)
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
supp="$PWD/tsan.supp"   # (an absolute path: the programs run in $work)
pass=0; fail=0
check() {  # name, ok (0/1), detail
  if [ "$2" -eq 0 ]; then pass=$((pass+1)); echo "ok    $1"; else fail=$((fail+1)); echo "FAIL  $1: $3"; fi
}
for f in $(grep -l "^spawn \|  spawn " targeted/*.vu); do
  kind=$(sed -n '2s/^# expect: \([a-z]*\) .*/\1/p' "$f")
  [ "$kind" = output ] || continue
  want=$(sed -n '2s/^# expect: [a-z]* //p' "$f")
  b=$(basename "$f" .vu)
  if ! CC=clang $VU build "$f" --tsan -o "$work/t" >/dev/null 2>&1 || ! $VU build "$f" -o "$work/o" >/dev/null 2>&1; then
    check "$b" 1 "doesn't build"; continue
  fi
  bad=""
  for i in $(seq "$ROUNDS"); do
    got=$(cd "$work" && OMP_TOOL_LIBRARIES="$ARCHER" OMP_NUM_THREADS=2 TSAN_OPTIONS="suppressions=$supp" timeout 120 ./t 2>"$work/err"); rc=$?
    if [ $rc -ne 0 ] || [ "$got" != "$want" ] || grep -q "WARNING: ThreadSanitizer" "$work/err"; then
      bad="tsan run $i: exit $rc, [$got], $(grep -m1 -A3 'WARNING: ThreadSanitizer' "$work/err" | tr '\n' ' ' | cut -c1-300)$(head -c 200 "$work/err")"; break
    fi
    got=$(cd "$work" && timeout 60 ./o 2>&1); rc=$?
    if [ $rc -ne 0 ] || [ "$got" != "$want" ]; then bad="run $i: exit $rc, [$got]"; break; fi
  done
  check "$b ($ROUNDS rounds, TSan and optimized)" $([ -z "$bad" ] && echo 0 || echo 1) "$bad"
done
$VU build mt/print_lines.vu -o "$work/p" >/dev/null 2>&1
for i in 1 2 3; do
  r=$("$work/p" | python3 -c "
import re, sys
ls = sys.stdin.read().split('\n')[:-1]
bad = [l for l in ls if not re.fullmatch(r'line \d \d+ abcdefghijklmnopqrstuvwxyz0123456789', l)]
print(len(ls), len(bad))")
  check "print_lines run $i: 16000 whole lines" $([ "$r" = "16000 0" ] && echo 0 || echo 1) "$r"
done
# idle threads take new tasks from a busy thread (two cores or more needed to see it)
if [ "$(nproc)" -ge 2 ]; then
  $VU build mt/steal.vu -o "$work/steal" >/dev/null 2>&1
  r=$("$work/steal")
  check "new tasks queued behind a task that never waits are taken by an idle thread" $([ "$r" = "short tasks first" ] && echo 0 || echo 1) "$r"
fi
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
