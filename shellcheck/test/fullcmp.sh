#!/bin/bash
# fullcmp.sh VSC [JOBS]: vsc over each whole corpus in one invocation per format, against
# ShellCheck's run of the same command (full/run.sh made them): stdout, stderr and exit status.
# The files ShellCheck can't finish are left out (bench1.txt is corpus 1 without acme.sh and
# nvm.sh, files3_ok.txt corpus 3 without 7 configure scripts). gcc: corpus 1 and 2 against the
# per-file reference outputs concatenated, corpus 3 against one run.
W=${SCW:?set SCW to the work directory}
V=$1; J=${2:-1}
for spec in "tty:" "checkstyle:" "diff:" "json:" "json1:-o all" "gcc:"; do
  f=${spec%%:*}; extra=${spec#*:}; tag=$f; [ -n "$extra" ] && tag=${f}_all
  for c in 1 2 3; do
    [ $c = 1 ] && { d=corpus; l=bench1.txt; }
    [ $c = 2 ] && { d=corpus2; l=files2.txt; }
    [ $c = 3 ] && { d=corpus3; l=files3_ok.txt; }
    [ $f = gcc ] && [ $c != 3 ] && continue
    o=$W/full/sc_${tag}_$c
    [ -e $o.st ] || { echo "$tag corpus$c: no reference"; continue; }
    cd $W/$d
    "$V" --jobs $J -f $f $extra $(cat $W/$l) > $W/full/v.out 2> $W/full/v.err; echo $? > $W/full/v.st
    if cmp -s $W/full/v.out $o.out && cmp -s $W/full/v.err $o.err && cmp -s $W/full/v.st $o.st; then
      echo "$tag corpus$c: identical ($(wc -c < $o.out) bytes, exit $(cat $o.st))"
    else echo "$tag corpus$c: DIFFERENT"; fi
  done
done
# gcc: the per-file reference outputs, concatenated
for c in 1 2; do
  [ $c = 1 ] && { d=corpus; l=bench1.txt; r=ref; } || { d=corpus2; l=files2.txt; r=ref2; }
  cd $W/$d
  while read -r f; do cat "$W/$r/$(echo "$f" | tr '/' '%').out"; done < $W/$l > $W/full/g.ref
  "$V" --jobs $J -f gcc $(cat $W/$l) > $W/full/v.out 2> $W/full/v.err
  if cmp -s $W/full/v.out $W/full/g.ref && [ ! -s $W/full/v.err ]; then echo "gcc corpus$c: identical"; else echo "gcc corpus$c: DIFFERENT"; fi
done
rm -f $W/full/v.out $W/full/v.err $W/full/v.st $W/full/g.ref
