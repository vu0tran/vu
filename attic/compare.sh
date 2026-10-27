#!/bin/bash
# Compares the C (or the error report) produced by vu.py and by a Vu-built compiler for each file.
#   compare.sh VUC FILE...        (EXTRA="--json" compare.sh ... passes extra options to both)
vuc=$1; shift
same=0; diff_n=0; work=$(mktemp -d)
for f in "$@"; do
  CC=true timeout 120 python3 vu.py build $EXTRA "$f" --emit-c "$work/py.c" -o "$work/py.bin" >"$work/py.out" 2>&1; pyc=$?
  CC=true timeout 120 "$vuc" build $EXTRA "$f" --emit-c "$work/vu.c" -o "$work/vu.bin" >"$work/vu.out" 2>&1; vuc_rc=$?
  ok=1
  [ $pyc -eq $vuc_rc ] || ok=0
  cmp -s "$work/py.out" "$work/vu.out" || ok=0
  if [ $pyc -eq 0 ]; then cmp -s "$work/py.c" "$work/vu.c" || ok=0; fi
  if [ $ok -eq 1 ]; then same=$((same+1)); else
    diff_n=$((diff_n+1)); echo "DIFF $f (exit py $pyc, vu $vuc_rc)"
    if [ $pyc -ne 0 ] || [ $vuc_rc -ne 0 ]; then diff "$work/py.out" "$work/vu.out" | head -4; else diff "$work/py.c" "$work/vu.c" | head -6; fi
  fi
  rm -f "$work/py.c" "$work/vu.c"
done
rm -rf "$work"
echo "$same same, $diff_n different"
