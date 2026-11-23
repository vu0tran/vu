#!/bin/zsh
# bench.sh VLINT TAG [PKG] [ENV=...]: one cold run (static shards) on the corpus ($VLINT_CORPUS) or packages/PKG;
# wall, user, instructions retired (the measure to compare by while the machine is loaded) and
# peak memory; the output in ~/.cache/vlint-parity/bench/TAG.out for cmp.
V=$1; T=$2; P=$3; shift 2; [ $# -gt 0 ] && shift
D=$HOME/.cache/vlint-parity/bench; mkdir -p $D
X=$D/xdg_$T; rm -rf $X; mkdir -p $X/vlint; cp -R $HOME/.cache/vlint-parity/tslib $X/vlint/tslib-b82676463eea69ca
export PATH=/opt/homebrew/bin:$PATH
cd "${VLINT_CORPUS:?set VLINT_CORPUS to the folder linted (the root of a JS monorepo)}"
tgt=(); [ -n "$P" ] && tgt=(packages/$P)
env "$@" VTSC_SHARD_STATIC=1 VLINT_VTSC_CACHE=0 XDG_CACHE_HOME=$X /usr/bin/time -l $V --disable-nested-config -A typescript/no-misused-promises -f unix $tgt > $D/$T.out 2> $D/$T.err
L=$(grep -a ' real ' $D/$T.err | tr -s ' ')
ins=$(grep -a 'instructions retired' $D/$T.err | awk '{printf "%.1f", $1/1e9}')
# (user + sys: every process of the run, the waited children's included; the instructions are
# the main process's only, without vtsc's worker processes and node)
cpu=$(grep -a ' real ' $D/$T.err | tr -s ' ' | awk '{printf "%.1f", $3+$5}')
mem=$(grep -a 'maximum resident' $D/$T.err | awk '{printf "%.1f", $1/1e9}')
echo "$T ${P:-all}: $L cpu $cpu s, main-process Ginstr $ins maxGB $mem lines $(wc -l < $D/$T.out)"
# (its cache folder, a copy of the TypeScript lib and vtsc's files: gone, the disk fills otherwise)
rm -rf $X
