#!/bin/bash
# Builds the compiler for WebAssembly (WASI): OUT/vuc.wasm, which runs `check` and `fmt` (the
# playground on vulang.org uses it), and OUT/std.json, the standard library it reads from /std.
# Needs zig (`pip install ziglang`, or zig on PATH). Running programs needs processes and a C
# compiler, which WASI doesn't have: `build` and `run` report that they aren't available.
#   tools/wasm.sh [OUT]   (default: out/wasm)
set -e
cd "$(dirname "$0")/.."
out=${1:-out/wasm}
mkdir -p "$out"
if command -v zig >/dev/null; then zig=(zig); else zig=(python3 -m ziglang); fi
"${zig[@]}" cc -target wasm32-wasi -std=gnu11 -fwrapv -Os -w \
  -D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS -D_WASI_EMULATED_GETPID -D_WASI_EMULATED_MMAN \
  compiler/vuc_seed.c -o "$out/vuc.wasm" \
  -lwasi-emulated-signal -lwasi-emulated-process-clocks -lwasi-emulated-getpid -lwasi-emulated-mman \
  -Wl,-z,stack-size=67108864 -Wl,--strip-all
python3 - "$out/std.json" <<'PY'
import glob, json, os, sys
json.dump({os.path.basename(p): open(p, encoding='utf-8').read() for p in sorted(glob.glob('std/*.vu'))},
          open(sys.argv[1], 'w'), ensure_ascii=False)
PY
echo "$out/vuc.wasm: $(wc -c < "$out/vuc.wasm") bytes"
