#!/bin/bash
# Vu against Python and JavaScript (Node) on the six benchmarks, every language on one core (taskset)
# and at the same size, median of 3, each program's output checked against Vu's first. Sizes are
# smaller than bench/compare.sh's where Python would take minutes per run.
# Sources: dyn/{bt,nb,sn,ns}.py and dyn/{bt,nb,sn}.js from hanabi1224/Programming-Language-Benchmarks
# (binarytrees 1, nbody 2.py and 6.js, spectral-norm 8.py and 6.js, nsieve 2.py); the rest (fk, mb,
# ns.js) are straight ports of bench/fk.c, mbt.c and ns.c.
#   bench/dyn/compare.sh
cd "$(dirname "$0")/.." || exit 1
VU=${VU:-../vu}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
export OMP_NUM_THREADS=1
echo "$(python3 --version), node $(node --version), one core"
for spec in "binarytrees 20 bt" "nbody 5000000 nb" "spectralnorm 2000 sn" "nsieve 13 ns" "fannkuch 11 fk" "mandelbrot 4000 mb"; do
  set -- $spec; b=$1; n=$2; f=$3
  $VU build ../examples/$b.vu -o "$work/$b" || exit 1
  want=$(taskset -c 0 "$work/$b" $n | md5sum)
  echo "== $b $n"
  for l in vu js py; do
    case $l in vu) cmd=("$work/$b" $n) ;; js) cmd=(node dyn/$f.js $n) ;; py) cmd=(python3 dyn/$f.py $n) ;; esac
    if [ "$(taskset -c 0 "${cmd[@]}" | md5sum)" != "$want" ]; then echo "$l: output differs from Vu's"; continue; fi
    python3 - "$l" taskset -c 0 "${cmd[@]}" <<'PY'
import os, statistics, subprocess, sys, time
name, cmd = sys.argv[1], sys.argv[2:]
ts, mems = [], []
for _ in range(3):
    t = time.perf_counter()
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
    _, _, ru = os.wait4(p.pid, 0)
    ts.append(time.perf_counter() - t); mems.append(ru.ru_maxrss / 1024)
print(f"{name:<4} {statistics.median(ts):8.3f}s  {max(mems):7.1f} MB")
PY
  done
done
