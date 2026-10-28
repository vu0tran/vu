#!/bin/bash
# The compiler built for WebAssembly gives the same `check` and `fmt` results as the native one, on
# every targeted test and example. Skipped without zig or Python's wasmtime package.
cd "$(dirname "$0")/.." || exit 1
if ! command -v zig >/dev/null && ! python3 -c 'import ziglang' 2>/dev/null; then echo "skipped: no zig"; echo "0 passed"; exit 0; fi
if ! python3 -c 'import wasmtime' 2>/dev/null; then echo "skipped: no wasmtime (pip install wasmtime)"; echo "0 passed"; exit 0; fi
./vu check examples/json.vu >/dev/null || exit 1   # builds compiler/vuc if needed
out=$(mktemp -d); trap 'rm -rf "$out"' EXIT
tools/wasm.sh "$out" >/dev/null || { echo "FAIL: tools/wasm.sh"; exit 1; }
python3 tests/wasm_diff.py "$out/vuc.wasm" compiler/vuc std tests/targeted/*.vu examples/*.vu
