#!/bin/bash
# Path expressions differential test: path_test.sh JQ VJQ < ../tests/paths.txt (each program on a
# few inputs; prints the differences).
while IFS= read -r p; do for inp in '[1,[2]]' '"ab"' '{"a":{"b":1},"b":2}' 'null' '[3,{"a":1}]'; do a=$(echo "$inp" | timeout 5 $1 -c "$p" 2>&1|paste -sd' '); b=$(echo "$inp" | timeout 5 $2 -c "$p" 2>&1|paste -sd' '); [ "$a" == "$b" ] || echo "DIFF $p <<< $inp
 jq:  $a
 vjq: $b"; done; done
