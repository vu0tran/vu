#!/bin/bash
# macOS (not run, only built): programs using tasks, channels, sockets and HTTP compiled for ARM64 and
# x86-64 macOS with zig's cross compiler, and linked where they don't need OpenSSL (zig has no macOS
# OpenSSL: TLS code is compiled against OpenSSL's headers only). Skipped without zig (pip install ziglang).
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
python3 -c 'import ziglang' 2>/dev/null || { echo "0 passed, 0 failed (skipped: no zig)"; exit 0; }
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
mkdir -p "$work/inc"; cp -r /usr/include/openssl "$work/inc/" 2>/dev/null; cp /usr/include/*-linux-gnu/openssl/*.h "$work/inc/openssl/" 2>/dev/null
pass=0; fail=0
for f in net/echo.vu targeted/490_chan_closed.vu targeted/488_shared_tasks.vu ../examples/binarytrees.vu ../examples/nbody.vu net/http_std.vu net/ws_echo.vu net/h2_serve.vu; do
  b=$(basename "$f" .vu)
  $VU build "$f" --emit-c "$work/$b.c" -o "$work/$b" >/dev/null 2>&1 || { fail=$((fail+1)); echo "FAIL  $f: doesn't build here"; continue; }
  for t in aarch64-macos x86_64-macos; do
    if grep -q 'openssl/ssl.h' "$work/$b.c"; then mode="-c -I$work/inc"; else mode="-lm"; fi
    if python3 -m ziglang cc -target $t -std=gnu11 -fwrapv -O2 -Werror=implicit-function-declaration -Wno-everything $mode "$work/$b.c" -o "$work/$b.$t" 2>"$work/err"; then pass=$((pass+1))
    else fail=$((fail+1)); echo "FAIL  $f for $t: $(head -c 400 "$work/err")"; fi
  done
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
