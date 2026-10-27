#!/bin/bash
# Every runnable program, built five ways (gcc -O3, gcc -O0, clang -O3, malloc instead of the node pool,
# and gcc -O3 again with the generated C audited under -Wall -Wextra), must print identical output.
# A difference means the generated C depends on undefined or unspecified behavior somewhere.
cd "$(dirname "$0")"
# The compiler under test: ../vu (compiler/vuc) by default, or another build of it (VU=/path/to/vuc).
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d); pass=0; fail=0; warn=0
progs=()
for f in valid/*.vu; do progs+=("$f|"); done
for f in targeted/*.vu; do
  grep -q "^# expect: output" "$f" && progs+=("$f|$(sed -n '3s/^# args: //p' "$f")")
done
progs+=("../examples/binarytrees.vu|12" "../examples/nbody.vu|10000" "../examples/spectralnorm.vu|200"
        "../examples/nsieve.vu|6" "../examples/fannkuch.vu|8" "../examples/mandelbrot.vu|200")
python3 json/gen.py 100 99 "$work/doc.json"
progs+=("../examples/json.vu|$work/doc.json 1")
for entry in "${progs[@]}"; do
  f=${entry%%|*}; args=${entry#*|}; ref=""; same=1
  for mode in "" "--debug" "CLANG" "--malloc"; do
    if [ "$mode" = CLANG ]; then CC=clang $VU build "$f" -o "$work/p" >/dev/null 2>&1 || { same=0; break; }
    else $VU build "$f" $mode -o "$work/p" >/dev/null 2>&1 || { same=0; break; }; fi
    out=$(cd "$work" && OMP_NUM_THREADS=3 timeout 60 ./p $args 2>&1 | md5sum)
    [ -z "$ref" ] && ref=$out
    [ "$out" = "$ref" ] || same=0
  done
  $VU build "$f" --emit-c "$work/c.c" -o "$work/p" >/dev/null 2>&1
  # -Wno-infinite-recursion: that warning describes the Vu program (a function that can only end
  # through exit() really never returns), not a mistake in the generated C.
  w=$(gcc -std=gnu11 -fwrapv -fopenmp -Wall -Wextra -Wno-unused-parameter -Wno-unused-function -Wno-unused-variable \
        -Wno-unused-but-set-variable -Wno-unknown-pragmas -Wno-infinite-recursion -O2 -c "$work/c.c" -o /dev/null 2>&1 | grep -c 'warning:')
  if [ "$w" -gt 0 ]; then warn=$((warn+1)); echo "WARN  $f ($w warnings)"; fi
  if [ $same -eq 1 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "DIFF  $f"; fi
done
rm -rf "$work"
echo "$pass identical across builds, $fail different, $warn with C warnings"
[ $fail -eq 0 ] && [ $warn -eq 0 ]
