#!/bin/bash
# CPU seconds (user+sys), best of 3: the previous vgolint (CLI `vgolint ./...`), this one (`vgolint run`
# with the same linters and no limits, no cache), and golangci-lint warm with the same config.
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
cpu() { local out; out=$( { TIMEFORMAT='%U %S'; time "$@" > /dev/null 2>&1; } 2>&1 ); set -- $out; echo "$1 + $2" | bc; }
best3() { local b=99999; for i in 1 2 3; do c=$(cpu "$@"); b=$(echo "if ($c < $b) $c else $b" | bc); done; printf "%7.3f" $b; }
NEW="$S/golint-work/vgolint run --no-cache -c $S/golint/golangci.yml --max-issues-per-linter 0 --max-same-issues 0 ./..."
GL="golangci-lint run --allow-parallel-runners --config $S/golint/golangci.yml --max-issues-per-linter 0 --max-same-issues 0 ./..."
printf "%-12s %8s %8s %8s\n" repo old new golangci
for d in ${@:-dns otto zap testify gin}; do
  cd $S/gocorpus/$d
  printf "%-12s " $d; best3 $S/vgolint --no-cache ./...; printf " "; best3 $NEW; printf " "; best3 $GL; echo
done
echo BENCH DONE
