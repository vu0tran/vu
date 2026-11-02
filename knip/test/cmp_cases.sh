#!/bin/bash
# Compares vknip with knip's saved outputs on generated projects.
#   VKNIP=path/to/vknip cmp_cases.sh GEN_DIR REF_DIR
GEN=$1; REF=$2; same=0; n=0
for d in $GEN/*/; do
  name=$(basename $d)
  [ -f $REF/$name.txt ] || continue
  n=$((n+1))
  got=$(cd $d && $VKNIP 2>&1)
  if [ "$got" == "$(cat $REF/$name.txt)" ]; then same=$((same+1)); else echo "=== DIFF $name"; diff <(echo "$got") $REF/$name.txt | head -12; fi
done
echo "identical: $same/$n"
