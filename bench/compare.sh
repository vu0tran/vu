#!/bin/bash
# Vu against C, C++, Rust and Go on six benchmarks, median of 5 (bench/timeit.py), on a quiet machine.
# Four are single-threaded. Vu's mandelbrot and spectral-norm use `par for`, so those two run on 2
# threads against the threaded versions in the other languages (bench/mbt.*, snt.*, sn.c with OpenMP). Each program's output is checked against Vu's before it's timed.
#   bench/compare.sh                       # all six
#   bench/compare.sh nbody mandelbrot      # some
# Sources: bench/*.{c,cpp,rs,go} (spectral-norm, nsieve, fannkuch-redux, mandelbrot, binary-trees in
# C and C++), and hanabi1224/Programming-Language-Benchmarks for the rest ($PLB, default /root/plb):
# nbody 2.c, 1.cpp, 1.rs, 1.go and binarytrees 5.rs, 1.go.
# Flags: gcc/g++ -O3 -march=native (C/C++ mandelbrot also -ffp-contract=off, or their hash is wrong),
# rustc -C opt-level=3 -C target-cpu=native -C codegen-units=1, go build, vu build (-O3 -march=native).
cd "$(dirname "$0")" || exit 1
VU=${VU:-../vu}
PLB=${PLB:-/root/plb/bench/algorithm}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
names=("$@"); [ ${#names[@]} -eq 0 ] && names=(binarytrees nbody spectralnorm nsieve fannkuch mandelbrot)
cflags="-O3 -march=native"
rflags="-C opt-level=3 -C target-cpu=native -C codegen-units=1"
for b in "${names[@]}"; do
  threads=1
  case $b in
    binarytrees) arg=20; c=bt.c; cpp=bt.cpp; rs=$PLB/binarytrees/5.rs; go=$PLB/binarytrees/1.go; extra="" ;;
    nbody)       arg=50000000; c=$PLB/nbody/2.c; cpp=$PLB/nbody/1.cpp; rs=$PLB/nbody/1.rs; go=$PLB/nbody/1.go; extra="" ;;
    spectralnorm) arg=8000; c=sn.c; cpp=snt.cpp; rs=snt.rs; go=snt.go; extra="-fopenmp"; threads=2 ;;
    nsieve)      arg=13; c=ns.c; cpp=ns.cpp; rs=ns.rs; go=ns.go; extra="" ;;
    fannkuch)    arg=11; c=fk.c; cpp=fk.cpp; rs=fk.rs; go=fk.go; extra="" ;;
    mandelbrot)  arg=8000; c=mbt.c; cpp=mbt.cpp; rs=mbt.rs; go=mbt.go; extra="-fopenmp -ffp-contract=off"; threads=2 ;;
    *) echo "unknown benchmark $b"; exit 1 ;;
  esac
  d="$work/$b"; mkdir -p "$d"
  $VU build ../examples/$b.vu -o "$d/vu" || exit 1
  gcc $cflags $extra "$c" -o "$d/c" -lm -lcrypto 2>/dev/null || gcc $cflags $extra "$c" -o "$d/c" -lm || exit 1
  g++ $cflags $extra "$cpp" -o "$d/cpp" -lcrypto 2>/dev/null || g++ $cflags $extra "$cpp" -o "$d/cpp" || exit 1
  # mandelbrot's Rust uses the md5 crate: link the one built in $MBRS (default /root/mbrs, a cargo project)
  if [ "$b" = mandelbrot ]; then
    MBRS=${MBRS:-/root/mbrs}
    rustc $rflags --edition 2021 "$rs" -o "$d/rs" -L "$MBRS/target/release/deps" \
      --extern md5="$(ls "$MBRS"/target/release/deps/libmd5-*.rlib | head -1)" 2>/dev/null || exit 1
  else
    rustc $rflags "$rs" -o "$d/rs" 2>/dev/null || exit 1
  fi
  (mkdir -p "$d/gosrc" && cp "$go" "$d/gosrc/main.go" && cd "$d/gosrc" && go mod init b >/dev/null 2>&1 && go build -o "$d/go" .) || exit 1
  want=$("$d/vu" $arg | md5sum)
  echo "== $b $arg ($threads thread$([ $threads = 1 ] || echo s))"
  if [ $threads = 1 ]; then export OMP_NUM_THREADS=1 GOMAXPROCS=1; else export OMP_NUM_THREADS=$threads GOMAXPROCS=$threads; fi
  langs="c cpp rs go vu"
  # binary-trees also as C with Vu's allocator (a free list and big chunks): what's left is the language
  if [ "$b" = binarytrees ]; then gcc $cflags bt_pool.c -o "$d/c_pool" || exit 1; langs="c c_pool cpp rs go vu"; fi
  for l in $langs; do
    if [ "$("$d/$l" $arg | md5sum)" != "$want" ]; then echo "$l: output differs from Vu's"; continue; fi
    python3 timeit.py "$l" "$d/$l" $arg
  done
done
