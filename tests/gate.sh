#!/bin/bash
# The full gate (about 30 minutes): the self-host check, then every suite. Prints one line per suite;
# a suite that fails says FAIL or shows failures in its counts. Exit status: 0 only if all passed.
cd "$(dirname "$0")" || exit 1
fail=0
r=$(./run_selfhost.sh 2>&1); echo "run_selfhost.sh: $(echo "$r" | tail -1)"; echo "$r" | grep -a '^FAIL'
echo "$r" | tail -1 | grep -q PASS || fail=1
for s in run_tests.sh run_cli.sh run_targeted.sh run_json.sh run_differential.sh run_debug.sh run_modules.sh \
         run_text.sh run_net.sh run_memory.sh run_ffi.sh run_tls.sh run_http.sh run_mt.sh; do
  r=$(./$s 2>&1 | tr -d "\0"; exit ${PIPESTATUS[0]}); rc=$?
  echo "$s: $(echo "$r" | grep -a -E '^[0-9]+ (passed|identical)' | tr '\n' ' ') (exit $rc)"
  [ $rc -eq 0 ] || { fail=1; echo "$r" | grep -a -A3 '^FAIL' | head -20; }
done
[ $fail -eq 0 ] && echo "GATE PASSED" || echo "GATE FAILED"
exit $fail
