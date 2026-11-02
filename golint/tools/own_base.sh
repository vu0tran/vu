#!/bin/bash
# golangci-lint with each corpus repo's own config (or none), default flags: $S/golint-work/own/REPO.{out,err,rc}
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
O=$S/golint-work/own
for d in ${@:-$(ls $S/gocorpus)}; do
  (cd $S/gocorpus/$d && golangci-lint run --allow-parallel-runners > $O/$d.out 2> $O/$d.err; echo $? > $O/$d.rc)
  echo "$d rc=$(cat $O/$d.rc) $(wc -l < $O/$d.out)"
done
echo OWN DONE
