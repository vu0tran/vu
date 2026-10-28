#!/bin/sh
# Targeted attacks on the checker. Each file states what it attacks and what must happen:
#   reject MSG   compilation fails with MSG
#   output TEXT  the program prints exactly TEXT, with no AddressSanitizer/LeakSanitizer/UBSan report
#   panic MSG    the program stops with exit code 101 and MSG, instead of corrupting memory
#   compile MS   Vu's front end (not the C compiler) finishes within MS milliseconds
# leak checking (LeakSanitizer) where the platform has it: not on macOS
leaks=detect_leaks=1; [ "$(uname)" = Darwin ] && leaks=detect_leaks=0
cd "$(dirname "$0")"
# The compiler under test: ../vu (compiler/vuc) by default, or another build of it (VU=/path/to/vuc).
VU=${VU:-"$PWD/../vu"}
pass=0; fail=0; work=$(mktemp -d)
ARCHER=${ARCHER:-/usr/lib/llvm-18/lib/libarcher.so}
supp="$PWD/tsan.supp"   # (an absolute path: the programs run in $work)
for f in targeted/${ONLY:-*}.vu; do   # ONLY=5[12]*_iface* runs some
  attack=$(sed -n '1s/^# attack: //p' "$f")
  kind=$(sed -n '2s/^# expect: \([a-z]*\) .*/\1/p' "$f")
  want=$(sed -n '2s/^# expect: [a-z]* //p' "$f")
  args=$(sed -n '3s/^# args: //p' "$f")
  if [ "$kind" = compile ]; then
    ms=$(timeout 120 $VU build "$f" --debug --time -o "$work/prog" 2>&1 | sed -n 's/^vu: front end \([0-9]*\).*/\1/p')
    if [ -n "$ms" ] && [ "$ms" -le "$want" ]; then pass=$((pass+1)); echo "ok    $f"; why="front end took $ms ms"
    else fail=$((fail+1)); echo "FAIL  $f"; why="front end took ${ms:-?} ms (limit $want)"; fi
    echo "      attack: $attack"; echo "      result: $why"; continue
  fi
  out=$(timeout 60 $VU build "$f" --san -o "$work/prog" 2>&1); code=$?
  if [ $code -eq 124 ]; then fail=$((fail+1)); echo "FAIL  $f"; echo "      attack: $attack"; echo "      result: COMPILER HUNG (killed after 60 s)"; continue; fi
  if [ "$kind" = panic ]; then
    if [ $code -ne 0 ]; then ok=0; why="failed to compile: $out"
    else
      got=$(cd "$work" && timeout ${VU_TARGETED_TIMEOUT:-20} ./prog $args 2>&1); rc=$?
      if [ $rc -eq 101 ] && printf '%s' "$got" | grep -qF "$want"; then ok=1; why="stopped safely: $(printf '%s' "$got" | grep -m1 panic)"
      elif [ $rc -eq 0 ]; then ok=0; why="RAN TO COMPLETION (should have stopped): $(printf '%s' "$got" | head -1)"
      else ok=0; why="exit $rc: $(printf '%s' "$got" | grep -m1 'ERROR\|panic\|runtime error' | cut -c1-150)"; fi
    fi
  elif [ "$kind" = reject ]; then
    if [ $code -eq 1 ] && printf '%s' "$out" | grep -qF "$want"; then ok=1; why="rejected: $(printf '%s' "$out" | head -1 | sed 's/^[^:]*:[0-9]*: error: //')"
    elif [ $code -eq 0 ]; then ok=0; run=$(cd "$work" && timeout 10 ./prog 2>&1 | grep -m1 'ERROR: AddressSanitizer[^ ]* [a-z-]*\|runtime error'); why="ACCEPTED (should be rejected)${run:+; at runtime: $run}"
    else ok=0; why="wrong error: $out"; fi
  else
    if [ $code -ne 0 ]; then ok=0; why="failed to compile: $out"
    else
      got=$(cd "$work" && ASAN_OPTIONS=$leaks timeout ${VU_TARGETED_TIMEOUT:-20} ./prog $args 2>"$work/err"); rc=$?
      reports=$(grep -c 'ERROR\|runtime error' "$work/err")
      if [ $rc -eq 124 ]; then ok=0; why="HUNG (killed after ${VU_TARGETED_TIMEOUT:-20} s)"
      elif [ "$got" = "$want" ] && [ $rc -eq 0 ] && [ "$reports" -eq 0 ]; then ok=1; why="ran correctly, sanitizers clean"
        # again with Vu's own node allocator (freed nodes poisoned), which --san replaces with malloc
        if $VU build "$f" --san-pool -o "$work/pprog" >/dev/null 2>&1; then
          # freed nodes are poisoned but still link the free list, so LeakSanitizer must follow pointers in them
          pgot=$(cd "$work" && LSAN_OPTIONS=use_poisoned=1 timeout 60 ./pprog $args 2>"$work/perr"); prc=$?
          if [ "$pgot" = "$want" ] && [ $prc -eq 0 ] && [ "$(grep -c 'ERROR\|runtime error' "$work/perr")" -eq 0 ]; then why="$why (malloc and pool)"
          else ok=0; why="POOL MODE: exit $prc, output [$pgot], $(grep -m1 'ERROR\|runtime error' "$work/perr" | cut -c1-120)"; fi
        else ok=0; why="failed to build with --san-pool"; fi
        # par and spawn programs also run under ThreadSanitizer (clang's OpenMP + Archer), when available
        if grep -q "par for\|spawn " "$f" && [ -f "$ARCHER" ] && command -v clang >/dev/null; then
          if CC=clang $VU build "$f" --tsan -o "$work/tprog" >/dev/null 2>&1; then
            tgot=$(cd "$work" && OMP_TOOL_LIBRARIES="$ARCHER" OMP_NUM_THREADS=2 TSAN_OPTIONS="suppressions=$supp" timeout 60 ./tprog $args 2>"$work/terr"); trc=$?
            races=$(grep -c 'WARNING: ThreadSanitizer' "$work/terr")
            if [ "$races" -eq 0 ] && [ $trc -eq 0 ] && [ "$tgot" = "$want" ]; then why="$why, no data races"
            elif [ "$races" -eq 0 ]; then ok=0; why="TSAN BUILD: exit $trc, output [$tgot], $(head -c 200 "$work/terr")"
            else ok=0; why="DATA RACES: $races: $(grep -m1 -A4 'WARNING: ThreadSanitizer' "$work/terr" | tr '\n' ' ' | cut -c1-300)"; fi
          else ok=0; why="failed to build with --tsan"; fi
        fi
      elif [ $rc -ge 128 ]; then ok=0; why="CRASHED (signal $((rc-128)))"
      else ok=0; why="exit $rc, output [$got], sanitizer reports $reports"; fi
    fi
  fi
  if [ $ok -eq 1 ]; then pass=$((pass+1)); echo "ok    $f"; else fail=$((fail+1)); echo "FAIL  $f"; fi
  echo "      attack: $attack"
  echo "      result: $why"
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
