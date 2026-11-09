#!/bin/bash
# Wall clock, default linters (golangci.yml), no limits: vgolint without and with its result cache,
# golangci-lint with its cache warm and after `golangci-lint cache clean` (Go's build cache stays
# warm). Best of 3 (cold: 1). Usage: bench2.sh DIR...  (each a module to lint with ./...)
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
t() { local s=$(date +%s%N); "$@" > /dev/null 2>&1; echo $(( ($(date +%s%N) - s) / 1000000 )); }
best() { local n=$1; shift; local b=99999999; for i in $(seq $n); do local x=$(t "$@"); [ $x -lt $b ] && b=$x; done; echo $b; }
A="--max-issues-per-linter 0 --max-same-issues 0"
printf "%-12s %9s %9s %9s %9s\n" repo vg_nocache vg_cached gl_warm gl_cold
for d in "$@"; do
  cd $d
  v=$(best 3 $S/vgolint run -c $S/golint/golangci.yml $A --no-cache ./...)
  $S/vgolint run -c $S/golint/golangci.yml $A ./... > /dev/null 2>&1
  vc=$(best 3 $S/vgolint run -c $S/golint/golangci.yml $A ./...)
  golangci-lint run --config $S/golint/golangci.yml $A ./... > /dev/null 2>&1
  w=$(best 3 golangci-lint run --config $S/golint/golangci.yml $A ./...)
  golangci-lint cache clean
  c=$(t golangci-lint run --config $S/golint/golangci.yml $A ./...)
  printf "%-12s %9s %9s %9s %9s\n" $(basename $d) $v $vc $w $c
done
echo BENCH DONE
