#!/bin/bash
# Wall-clock benchmark: vgolint vs golangci-lint (same linters, config golangci.yml), per corpus repo.
# vgolint best of 5; golangci-lint warm (its cache filled) best of 3; golangci-lint after
# `golangci-lint cache clean` best of 2 (Go's build cache stays warm).
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
t() { local s=$(date +%s.%N); "$@" > /dev/null 2>&1; local e=$(date +%s.%N); echo "$e - $s" | bc; }
best() { local n=$1; shift; local b=999999; for i in $(seq $n); do local x=$(t "$@"); b=$(echo "if ($x < $b) $x else $b" | bc); done; echo $b; }
GL="golangci-lint run --config $S/golint/golangci.yml --max-issues-per-linter 0 --max-same-issues 0 ./..."
printf "%-14s %9s %9s %9s\n" repo vgolint gl_warm gl_clean
for d in ${@:-$(ls $S/gocorpus)}; do
  cd $S/gocorpus/$d
  v=$(best 5 $S/vgolint ./...)
  $GL > /dev/null 2>&1
  w=$(best 3 $GL)
  c=$(best 2 bash -c "golangci-lint cache clean; $GL")
  printf "%-14s %9.3f %9.3f %9.3f\n" $d $v $w $c
done
echo BENCH DONE
