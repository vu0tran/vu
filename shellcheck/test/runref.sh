#!/bin/bash
# runref.sh SHELLCHECK OUTDIR [FORMAT [SECONDS [KB [ARGS...]]]] < files: run the reference per file
# (default: -f gcc, 120 s and 3 GB limits), storing its stdout, stderr and "status seconds"
SC=$1; OUT=$2; F=${3:-gcc}; T=${4:-120}; M=${5:-3000000}; shift 5 2>/dev/null
mkdir -p "$OUT"
while read -r f; do
  o="$OUT/$(echo "$f" | tr '/' '%')"
  [ -e "$o.st" ] && continue
  s=$(date +%s.%N)
  ( ulimit -v $M; timeout $T "$SC" -f $F "$@" "$f" > "$o.out" 2> "$o.err" ); st=$?
  e=$(date +%s.%N)
  echo "$st $(echo "$e - $s" | bc)" > "$o.st"
done
