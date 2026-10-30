#!/bin/bash
# The stripe module: API calls against a fake Stripe server (what reaches it, form encoding, errors),
# and webhook signatures against what Stripe's own Python library decides (when it's installed).
# Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
PY=${STRIPE_PY:-python3}
work=$(mktemp -d)
pass=0; fail=0
$PY stripe/model.py cases "$work/hooks" "${SEED:-$RANDOM}"
for flags in "--release" "--san"; do
  if ! $VU build stripe/main.vu $flags -o "$work/main" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  rm -f "$work/port"
  python3 stripe/model.py serve "$work/port" "$work/log" & srv=$!
  for i in $(seq 100); do [ -s "$work/port" ] && break; sleep 0.05; done
  "$work/main" "$(cat "$work/port")" "$work/hooks" > "$work/out" 2> "$work/err"; rc=$?
  kill $srv; wait $srv 2>/dev/null
  if [ $rc -eq 0 ] && $PY stripe/model.py check "$work/hooks" "$work/log" < "$work/out" > "$work/res" && ! grep -q 'ERROR\|runtime error' "$work/err"; then
    pass=$((pass+1)); echo "ok    stripe $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  stripe $flags (exit $rc)"; head -20 "$work/res"; head -5 "$work/err"; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
