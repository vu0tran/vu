#!/bin/sh
# Text functions against Python (run_text.py), optimized and under the sanitizers.
cd "$(dirname "$0")" || exit 1
a=$(python3 run_text.py); ra=$?
b=$(python3 run_text.py --san); rb=$?
echo "$a" | grep FAIL; echo "$b" | grep FAIL
n=$(printf '%s\n%s\n' "$a" "$b" | grep -o '^[0-9]* of [0-9]*' | awk '{s += $1; t += $3} END {print s, t}')
set -- $n
echo "$1 passed, $(($2 - $1)) failed"
[ $ra -eq 0 ] && [ $rb -eq 0 ]
