#!/bin/zsh
# tparity.sh VLINT OUTDIR [PKG]: vlint on the corpus ($VLINT_CORPUS) (or packages/PKG), cold and with static
# shards (the same output every run), compared with oxlint + tsgolint's (parity/ref.sh makes it).
# Writes OUTDIR/out.txt, err.txt, diff.txt; prints the summary and the top roots.
here=${0:A:h}
REF=${VLINT_PARITY_REF:-$HOME/.cache/vlint-parity/ref_ox194_unix.txt}
O=$2; mkdir -p $O
X=$O/xdg; rm -rf $X; mkdir -p $X
J=${VLINT_CORPUS:?set VLINT_CORPUS to the folder linted (the root of a JS monorepo)}
export PATH=/opt/homebrew/bin:$PATH   # (vlint runs JavaScript plugins with node: a recent one)
cd $J
tgt=(); [ -n "$3" ] && tgt=(packages/$3)
VTSC_SHARD_STATIC=1 VLINT_VTSC_CACHE=0 XDG_CACHE_HOME=$X VLINT_VTSC_DEBUG=2 /usr/bin/time -p $1 --disable-nested-config -A typescript/no-misused-promises -f unix $tgt > $O/out.txt 2> $O/err.txt
echo "exit $? $(grep -a '^real' $O/err.txt)"
grep -a "^panic" -A1 $O/err.txt
ref=$REF
if [ -n "$3" ]; then grep "^packages/$3/" $REF > $O/ref.txt; ref=$O/ref.txt; fi
python3 -I $here/tparity.py $ref $O/out.txt $O/err.txt $here/../trules.vu $O/diff.txt
