#!/bin/sh
# Rejected programs must fail to compile with the expected message;
# panic programs must compile, then stop at runtime with exit code 101 and the expected message.
cd "$(dirname "$0")"
# The compiler under test: ../vu (compiler/vuc) by default, or another build of it (VU=/path/to/vuc).
VU=${VU:-"$PWD/../vu"}
pass=0; fail=0
for f in reject/*.vu; do
  want=$(sed -n '1s/^# expect: //p' "$f")
  out=$($VU build "$f" -o /dev/null 2>&1)
  if [ $? -eq 1 ] && printf '%s' "$out" | grep -qF "$want"; then pass=$((pass+1)); echo "ok    $f"
  else fail=$((fail+1)); echo "FAIL  $f"; echo "$out" | sed 's/^/      /'; fi
done
for f in panic/*.vu; do
  want=$(sed -n '1s/^# expect: //p' "$f")
  out=$($VU run "$f" 2>&1); code=$?
  if [ $code -eq 101 ] && printf '%s' "$out" | grep -qF "$want"; then pass=$((pass+1)); echo "ok    $f"
  else fail=$((fail+1)); echo "FAIL  $f (exit $code)"; echo "$out" | sed 's/^/      /'; fi
done
# Valid programs must print exactly their .expected output; they run in a scratch folder
# because some write files.
work=$(mktemp -d)
for f in valid/*.vu; do
  exp="${f%.vu}.expected"
  [ -f "$exp" ] || continue
  out=$(cd "$work" && $VU run "$OLDPWD/$f" 2>&1); code=$?
  pout=$(cd "$work" && $VU build "$OLDPWD/$f" --san-pool -o "$work/pool" 2>&1 && LSAN_OPTIONS=use_poisoned=1 ./pool 2>&1); pcode=$?
  if [ $code -eq 0 ] && [ "$out" = "$(cat "$exp")" ] && [ $pcode -eq 0 ] && [ "$pout" = "$(cat "$exp")" ]; then pass=$((pass+1)); echo "ok    $f"
  else fail=$((fail+1)); echo "FAIL  $f (exit $code)"; printf '%s\n' "$out" | diff - "$exp" | sed 's/^/      /'; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
