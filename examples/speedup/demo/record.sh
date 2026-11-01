#!/bin/sh
# Records the demo for real in a scratch copy (out_*.txt), then draws demo.gif from it.
# Needs vu on PATH and Pillow. examples/speedup/demo/record.sh
set -e
here=$(cd "$(dirname "$0")" && pwd); w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
cp "$here/typos.py" "$here/did_you_mean.vu" "$here/time_it.py" "$w/"
cd "$w"
cat typos.py > out_cat.txt
python3 time_it.py > out_before.txt
vu speedup typos.py:did_you_mean --port did_you_mean.vu > out_speedup.txt 2>&1
python3 time_it.py > out_after.txt
tail -6 typos.py > out_tail.txt
python3 "$here/make_gif.py" "$here/demo.gif"
cat out_before.txt out_after.txt
