#!/bin/bash
# The edit loop: append a comment line to one file of the module (a new cache key for its
# package), then lint the module with each tool, both caches otherwise warm. Best of 3 per tool.
# Usage: bench_edit.sh DIR FILE...   (FILE relative to DIR; the file is restored afterwards)
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
d=$1; shift
cd $d
A="--max-issues-per-linter 0 --max-same-issues 0"
for f in "$@"; do
  cp $f /tmp/bench_edit.bak
  $S/vgolint run -c $S/golint/golangci.yml $A ./... > /dev/null 2>&1
  golangci-lint run --config $S/golint/golangci.yml $A ./... > /dev/null 2>&1
  bv=999999; bg=999999
  for i in 1 2 3; do
    echo "// edit $RANDOM$i" >> $f
    s=$(date +%s%N); $S/vgolint run -c $S/golint/golangci.yml $A ./... > /dev/null 2>&1; e=$(( ($(date +%s%N) - s) / 1000000 )); [ $e -lt $bv ] && bv=$e
    echo "// edit $RANDOM$i" >> $f
    s=$(date +%s%N); golangci-lint run --config $S/golint/golangci.yml $A ./... > /dev/null 2>&1; e=$(( ($(date +%s%N) - s) / 1000000 )); [ $e -lt $bg ] && bg=$e
  done
  cp /tmp/bench_edit.bak $f
  printf "%-12s %-40s vgolint %6s ms  golangci-lint %6s ms\n" $(basename $d) $f $bv $bg
done
