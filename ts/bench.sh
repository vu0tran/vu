#!/bin/bash
# tsbench/run.sh: type checking and parsing on date-fns (pkgs/core/src, 1334 files, 2.0 MB).
# Each time is the best of N runs (wall clock), on this machine.
S=/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad
N=${1:-7}
cd $S/real/date-fns/pkgs/core
F=$(cat $S/dfiles.txt)
LIB=$S/tsref/node_modules/@typescript/typescript-linux-x64/lib
best() {  # best wall time in ms of N runs of the command
  local b=999999
  for i in $(seq 1 $N); do
    local s=$(date +%s%N); "$@" > /dev/null 2>&1; local e=$(date +%s%N)
    local t=$(( (e - s) / 1000000 )); [ $t -lt $b ] && b=$t
  done
  echo $b
}
echo "machine: $(nproc) cores, $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)"
echo "== type checking (--noEmit --strict), wall ms, best of $N"
echo "vtsc (all cores)   $(best env VTSC_LIB=$LIB $S/vtsc --target esnext $F)"
echo "vtsc (1 thread)    $(best env VTSC_LIB=$LIB $S/vtsc --jobs 1 --target esnext $F)"
echo "tsc 7 (Go)         $(best $S/tsref/node_modules/ts7/bin/tsc --noEmit --strict --ignoreConfig --target esnext $F)"
echo "tsc 7 (1 checker)  $(best $S/tsref/node_modules/ts7/bin/tsc --noEmit --strict --ignoreConfig --target esnext --checkers 1 --singleThreaded $F)"
echo "tsc 6 (JS)         $(best node $S/tsref/node_modules/ts6/lib/tsc.js --noEmit --strict --ignoreConfig --target esnext $F)"
echo "== parsing only (sources already in memory), ms, best of $N"
for i in $(seq 1 $N); do $S/vtsc --parse-only $F; done | awk '{print $(NF-1)}' | sort -n | head -1 | sed 's/^/vtsc               /'
for w in oxc swc ts esbuild; do node $S/tsbench/parse.mjs $w $S/dfiles.txt $N | awk -v w=$w '{printf "%-18s %s\n", w" (node)", $(NF-1)}'; done
bun $S/tsbench/parse.mjs bun $S/dfiles.txt $N | awk '{printf "%-18s %s\n", "bun (scan)", $(NF-1)}'
