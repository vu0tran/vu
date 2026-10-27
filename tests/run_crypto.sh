#!/bin/sh
# Hashing and encoding against Python (run_crypto.py).
cd "$(dirname "$0")" || exit 1
out=$(python3 run_crypto.py); rc=$?
echo "$out" | grep FAIL
n=$(echo "$out" | grep -o '^[0-9]* of [0-9]*' | awk '{s += $1; t += $3} END {print s, t}')
set -- $n
echo "$1 passed, $(($2 - $1)) failed"
exit $rc
