#!/bin/bash
# runs one scenario with both tools: scen.sh DIR ARGS...; prints DIFF/SAME
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
d=$1; shift
cd $d
golangci-lint "$@" --allow-parallel-runners > /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint-work/sw.out 2> $S/golint-work/sw.err; wr=$?
[ "$1" = linters ] && { golangci-lint "$@" > $S/golint-work/sw.out 2> $S/golint-work/sw.err; wr=$?; }
VGOLINT_QUIET=1 $S/golint-work/vgolint "$@" --no-cache > $S/golint-work/sg.out 2> $S/golint-work/sg.err; gr=$?
[ "$1" = linters ] && { VGOLINT_QUIET=1 $S/golint-work/vgolint "$@" > $S/golint-work/sg.out 2> $S/golint-work/sg.err; gr=$?; }
if cmp -s $S/golint-work/sw.out $S/golint-work/sg.out && [ $wr = $gr ] && diff -q <(sort $S/golint-work/sw.err) <(sort $S/golint-work/sg.err) >/dev/null; then echo "SAME  $*"; else echo "DIFF  $* (rc $wr/$gr)"; diff $S/golint-work/sw.out $S/golint-work/sg.out | head -8; diff <(sort $S/golint-work/sw.err) <(sort $S/golint-work/sg.err) | head -6; fi
