#!/bin/bash
# CPU time (user+sys, best of 3) and wall (best of 3): vgolint without its cache, vgolint with a
# filled cache, golangci-lint warm. Columns: wall then cpu, in seconds.
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
export XDG_CACHE_HOME=$S/vcache
m() { # prints "wall cpu" for one run
  local out; out=$( { TIMEFORMAT='%R %U %S'; time "$@" > /dev/null 2>&1; } 2>&1 ); set -- $out; echo "$1 $(echo "$2 + $3" | bc)"
}
best() { local n=$1; shift; local bw=99999 bc=99999; for i in $(seq $n); do set -- $(m "${@}") ; done; }
run3() { local bw=99999 bcpu=99999; for i in 1 2 3; do read w c <<< "$(m "$@")"; bw=$(echo "if ($w < $bw) $w else $bw" | bc); bcpu=$(echo "if ($c < $bcpu) $c else $bcpu" | bc); done; printf "%7.3f %7.3f" $bw $bcpu; }
GL="golangci-lint run --config $S/golint/golangci.yml --max-issues-per-linter 0 --max-same-issues 0 ./..."
printf "%-12s %15s %15s %15s\n" repo "vgolint-nocache" "vgolint-cached" "golangci-warm"
for d in ${@:-$(ls $S/gocorpus)}; do
  cd $S/gocorpus/$d
  $S/vgolint ./... > /dev/null; $GL > /dev/null 2>&1
  printf "%-12s " $d; run3 $S/vgolint --no-cache ./...; printf " "; run3 $S/vgolint ./...; printf " "; run3 $GL; echo
done
echo BENCH DONE
