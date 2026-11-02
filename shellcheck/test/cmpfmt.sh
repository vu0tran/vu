#!/bin/bash
# cmpfmt.sh VSC FORMAT : vsc vs the reference outputs of one format on the samples (per file:
# stdout, stderr and exit status), printing the files that differ
W=${SCW:?set SCW to the work directory}
V=$1; F=$2
same=0; diff=0
for c in 1 2; do
  [ $c = 1 ] && d=corpus || d=corpus2
  cd $W/$d
  while read -r f; do
    o="$W/reff${c}_$F/$(echo "$f" | tr '/' '%')"
    [ -e "$o.st" ] || continue
    st=$(cat "$o.st")
    [ "$st" -gt 4 ] && continue
    "$V" -f "$F" "$f" > $W/cmp_out 2> $W/cmp_err; vst=$?
    if cmp -s $W/cmp_out "$o.out" && cmp -s $W/cmp_err "$o.err" && [ "$st" = "$vst" ]; then same=$((same+1)); else diff=$((diff+1)); echo "DIFF $d/$f ($st $vst)"; fi
  done < $W/sample$c.txt
done
echo "$F: same $same, differ $diff"
