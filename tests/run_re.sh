#!/bin/sh
# std/re against Python's re (run_re.py), optimized and under the sanitizers.
cd "$(dirname "$0")" || exit 1
a=$(python3 run_re.py); ra=$?
b=$(N=600 python3 run_re.py --san); rb=$?
printf '%s\n%s\n' "$a" "$b" | grep 'FAIL\|agree'
n=$(printf '%s\n%s\n' "$a" "$b" | grep -o '^[0-9]* of [0-9]*' | awk '{s += $1; t += $3} END {print s, t}')
set -- $n
echo "$1 passed, $(($2 - $1)) failed"
[ $ra -eq 0 ] && [ $rb -eq 0 ]
