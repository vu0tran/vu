#!/bin/bash
# The JSON parser example as a test of the whole language: random documents must come back with
# exactly the values Python's json module reads, malformed input must give the expected error
# (exit 1), and every run must be clean under ASan/LSan/UBSan with both allocators.
cd "$(dirname "$0")"
# The compiler under test: ../vu (compiler/vuc) by default, or another build of it (VU=/path/to/vuc).
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d); pass=0; fail=0
$VU build ../examples/json.vu -o "$work/fast" || exit 1
$VU build ../examples/json.vu --san -o "$work/san" || exit 1
$VU build ../examples/json.vu --san-pool -o "$work/pool" || exit 1
check() {  # check NAME COMMAND...   (the command must exit 0 and leave no sanitizer report)
  local name=$1; shift
  if "$@" 2>"$work/err" && ! grep -q 'ERROR\|runtime error' "$work/err"; then pass=$((pass+1))
  else fail=$((fail+1)); echo "FAIL  $name"; head -5 "$work/err" | sed 's/^/      /'; fi
}
export ASAN_OPTIONS=detect_leaks=1 LSAN_OPTIONS=use_poisoned=1
for seed in $(seq 1 12); do
  python3 json/gen.py 200 "$seed" "$work/c.json"
  for b in fast san pool; do
    check "corpus $seed ($b)" sh -c "'$work/$b' '$work/c.json' 1 > '$work/out' && python3 json/same.py '$work/out' '$work/c.json.expect'"
  done
done
while IFS=$'\t' read -r doc want; do
  printf '%s' "$doc" > "$work/bad.json"
  for b in fast san pool; do
    got=$("$work/$b" "$work/bad.json" 2>"$work/err"); code=$?
    if [ $code -eq 1 ] && grep -qF "error: $want" "$work/err" && ! grep -q 'ERROR: \|runtime error' "$work/err"; then pass=$((pass+1))
    else fail=$((fail+1)); echo "FAIL  $doc ($b): exit $code, $(head -1 "$work/err")"; fi
  done
done < json/errors.txt
python3 -c "print('[' * 100000 + ']' * 100000)" > "$work/deep.json"
for b in fast san pool; do
  check "deep nesting ($b)" sh -c "'$work/$b' '$work/deep.json'; [ \$? -eq 1 ]"
done
# Typed JSON: from_json/to_json on generated types, against json/typed_model.py
$VU build json/typed.vu -o "$work/tfast" && $VU build json/typed.vu --san -o "$work/tsan" &&
  $VU build json/typed.vu --san-pool -o "$work/tpool" || exit 1
T=$PWD/json
for run in "1 3000" "2 3000" "3 0 3000" "4 0 3000"; do
  (cd "$work" && python3 "$T/typed_model.py" $run) || exit 1
  for b in tfast tsan tpool; do
    check "typed $run ($b)" sh -c "cd '$work' && ./$b in.txt > tout && python3 '$T/typed_check.py' tout | tail -1 | grep -q ' 0 mismatches'"
  done
done
$VU build json/typed_deep.vu --san -o "$work/tdeep" || exit 1
python3 json/typed_deep_gen.py "$work/tdeep.txt"
check "typed deep nesting" sh -c "'$work/tdeep' '$work/tdeep.txt' | cut -c1-90 | diff - json/typed_deep.expect"
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
