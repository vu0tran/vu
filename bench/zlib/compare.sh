#!/bin/bash
# std/zlib against C zlib, Rust (flate2 with its pure-Rust backend, miniz_oxide), Go (compress/zlib) and
# Python (zlib.decompress, which is C zlib): zlib-format decompression of the corpus.py inputs, median
# of 5 runs (bench/timeit.py), each program's output (length and CRC-32) checked against the others.
# C zlib is given an output buffer of exactly the right size (its best case); the others grow theirs.
#   bench/zlib/compare.sh        (needs zlib.h, cargo with network access for flate2, go)
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
python3 corpus.py "$work" || exit 1
gcc -O3 -march=native zb.c -o "$work/c" -lz || exit 1
(cp -r rs "$work/rs" && cd "$work/rs" && RUSTFLAGS="-C target-cpu=native" cargo build --release --quiet && cp target/release/zbrs "$work/rs_bin") || exit 1
(mkdir -p "$work/go" && cp zb.go "$work/go/main.go" && cd "$work/go" && go mod init zb >/dev/null 2>&1 && go build -o "$work/go_bin" .) || exit 1
$VU build zb.vu -o "$work/vu" || exit 1
VU_NO_VERSIONING=1 $VU build zb.vu -o "$work/vu_plain" || exit 1
for f in text binary random; do
  n=5; [ $f = binary ] && n=2
  echo "== $f ($n decompressions)"
  want=$("$work/c" "$work/$f.z" 1)
  for l in c rs_bin go_bin vu vu_plain py; do
    cmd=("$work/$l"); [ $l = py ] && cmd=(python3 zb.py)
    [ "$("${cmd[@]}" "$work/$f.z" 1)" = "$want" ] || { echo "$l: output differs"; continue; }
    python3 ../timeit.py "${l%_bin}" "${cmd[@]}" "$work/$f.z" $n
  done
done
