#!/bin/bash
# runref.sh SHELLCHECK OUTDIR < files : run reference per file (timeout 120s, 3 GB), store output and status
SC=$1; OUT=$2
mkdir -p "$OUT"
while read -r f; do
  o="$OUT/$(echo "$f" | tr '/' '%')"
  [ -e "$o.st" ] && continue
  s=$(date +%s.%N)
  ( ulimit -v 3000000; timeout 120 "$SC" -f gcc "$f" > "$o.out" 2> "$o.err" ); st=$?
  e=$(date +%s.%N)
  echo "$st $(echo "$e - $s" | bc)" > "$o.st"
done
