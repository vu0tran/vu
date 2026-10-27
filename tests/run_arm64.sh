#!/bin/bash
# ARM64 (Linux): every runnable targeted test and example that prints its expected output, cross-compiled
# with aarch64-linux-gnu-gcc and run under qemu-aarch64, quick (-O0) and optimized. Skipped if the
# cross compiler or qemu isn't installed. (No sanitizers or TLS: they aren't available for the target here.)
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
if ! command -v aarch64-linux-gnu-gcc >/dev/null || ! command -v qemu-aarch64 >/dev/null; then echo "0 passed, 0 failed (skipped: no ARM64 cross compiler or qemu)"; exit 0; fi
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
export CC=aarch64-linux-gnu-gcc VU_MARCH= QEMU_LD_PREFIX=/usr/aarch64-linux-gnu
pass=0; fail=0
for f in targeted/*.vu; do
  sed -n '2p' "$f" | grep -q '^# expect: output ' || continue
  grep -q 'tls_\|extern "' "$f" && continue
  # qemu-user runs posix_spawn's child as a plain fork, so a program that can't be started shows up
  # as exit status 127 instead of an error (a qemu limitation, not ARM64's)
  [ "$f" = targeted/180_os_run_bad_args.vu ] && continue
  want=$(sed -n '2s/^# expect: output //p' "$f")
  args=$(sed -n '3s/^# args: //p' "$f")
  for mode in --debug ""; do
    if ! $VU build "$f" $mode -o "$work/p" >"$work/err" 2>&1; then fail=$((fail+1)); echo "FAIL  $f $mode: build: $(head -c 300 "$work/err")"; continue; fi
    got=$(cd "$work" && timeout 120 qemu-aarch64 ./p $args 2>"$work/rerr"); rc=$?
    if [ "$got" = "$want" ] && [ $rc -eq 0 ]; then pass=$((pass+1))
    else fail=$((fail+1)); echo "FAIL  $f ${mode:-optimized}: exit $rc, [$(echo "$got" | head -c 200)] $(head -c 200 "$work/rerr")"; fi
  done
done
# the runtime as the cross compiler sees it: no attribute it ignores (GCC ignores naked on ARM64, which
# once broke task switching without a word), no implicit declarations
$VU build targeted/490_chan_closed.vu --emit-c "$work/r.c" -o "$work/r" >/dev/null 2>&1
if aarch64-linux-gnu-gcc -std=gnu11 -fwrapv -O2 -c -Werror=attributes -Werror=implicit-function-declaration "$work/r.c" -o "$work/r.o" 2>"$work/err"; then pass=$((pass+1))
else fail=$((fail+1)); echo "FAIL  the runtime has warnings on ARM64: $(head -c 400 "$work/err")"; fi
for b in "binarytrees 12" "nbody 1000" "spectralnorm 100" "nsieve 4" "fannkuch 7" "mandelbrot 200"; do
  set -- $b
  ref=$(cd ../examples && CC= VU_MARCH= $VU run $1.vu $2 | md5sum)
  $VU build ../examples/$1.vu -o "$work/e" >/dev/null 2>&1 && got=$(qemu-aarch64 "$work/e" $2 | md5sum)
  if [ "$got" = "$ref" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL  examples/$1.vu differs on ARM64"; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
