#!/bin/bash
# runall.sh: vsc over both corpora, then the comparison for CODES
W=${SCW:?set SCW to the work directory}
T=$(cd "$(dirname "$0")" && pwd)
cd $W/corpus && $W/vsc $(cat $W/files.txt) > $W/v1.txt 2> $W/v1.err
cd $W/corpus2 && $W/vsc $(cat $W/files2.txt) > $W/v2.txt 2> $W/v2.err
cat $W/v1.err $W/v2.err | head -5
python3 -I $T/cmp.py $W/ref $W/files.txt $W/v1.txt "$@" > $W/c1.txt
python3 -I $T/cmp.py $W/ref2 $W/files2.txt $W/v2.txt "$@" > $W/c2.txt
