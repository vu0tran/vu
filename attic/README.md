# attic

Retired, kept for reference. Nothing here is built or tested.

- `vu.py`: the Python bootstrap compiler. Until 2026-10-26 every feature was written twice, here and in
  `compiler/`, and the two had to produce byte-identical C. The compiler is now only `compiler/vuc`,
  bootstrapped from `compiler/vuc_seed.c`. This copy also holds the first implementation of closures
  (`g_lambda`, `call_value`, `fn_value`), which `compiler/` was ported from.
- `gen_selfhost_runtime.py`: generated `compiler/runtime_gen.vu` from `vu.py`'s runtime strings; the
  runtime now lives in `compiler/rt/` and `tools/gen_runtime.vu` does this.
- `compare.sh`, `test_front.py`, `test_front_main.vu`: compared `vu.py` and `vuc` file by file.
