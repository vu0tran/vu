#!/bin/bash
# The compiler builds itself:
#   1. compiler/vuc builds compiler/vuc.vu (stage 1), stage 1 builds it (stage 2), stage 2 builds it
#      again: the C must equal stage 2's (a fixed point);
#   2. the seed: C built from compiler/vuc_seed.c alone (no Vu compiler at all) builds the same vuc;
#   3. the edge cases in tests/selfhost/ (lexer and parser limits, escapes, C-name collisions...) give the
#      results recorded in tests/selfhost/expected.tsv: the first line of `vu check`, and for programs
#      that compile, a checksum of what `vu run` prints ('-': none).
cd "$(dirname "$0")/.." || exit 1
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
export VU_STD="$PWD/std"
fail=0
cd compiler   # (built as build.sh does, so the #line paths in the C match the seed's)
./vuc build vuc.vu --debug -o "$work/s1" || exit 1
"$work/s1" build vuc.vu -o "$work/s2" --emit-c "$work/2.c" || exit 1
"$work/s2" build vuc.vu --debug -o "$work/s3" --emit-c "$work/3.c" || exit 1
if cmp -s "$work/2.c" "$work/3.c"; then echo "ok   fixed point ($(wc -l <"$work/2.c") lines of C)"; else echo "FAIL no fixed point"; fail=1; fi
if cmp -s "$work/2.c" vuc_seed.c; then echo "ok   compiler/vuc_seed.c is up to date"; else echo "FAIL compiler/vuc_seed.c is stale: run compiler/build.sh"; fail=1; fi
${CC:-cc} -std=gnu11 -fwrapv -fno-math-errno -fno-trapping-math -ffp-contract=off -w -O1 vuc_seed.c -o "$work/seed" -lm
"$work/seed" build vuc.vu --debug -o "$work/s4" --emit-c "$work/4.c" >/dev/null 2>&1
if cmp -s "$work/2.c" "$work/4.c"; then echo "ok   the seed alone builds the same compiler"; else echo "FAIL the seed doesn't rebuild the compiler"; fail=1; fi
pass=0; bad=0
cd ../tests/selfhost
while IFS=$'\t' read -r f want sum; do
  got=$("$work/s2" check "$f" 2>&1 | head -1)
  gsum=-
  [ -z "$got" ] && got=- && gsum=$("$work/s2" run "$f" 2>&1 | md5sum | cut -c1-12)
  if [ "$got" = "$want" ] && [ "$gsum" = "$sum" ]; then pass=$((pass+1)); else bad=$((bad+1)); echo "FAIL $f: [$got] $gsum, expected [$want] $sum"; fi
done < expected.tsv
echo "     $pass edge cases as expected, $bad not"
[ $bad -eq 0 ] || fail=1
[ $fail -eq 0 ] && echo "PASS" || echo "FAIL"
exit $fail
