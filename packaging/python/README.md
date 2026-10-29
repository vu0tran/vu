# A Python package written in Vu

A template: copy this folder, rename `fuzzy`, and replace `fuzzy.vu` with your own functions.
`pip install .` builds the Vu code into a shared library inside the package (`vu build --lib`,
with `vu` on PATH or `$VU` naming it), and `__init__.py` calls it through ctypes. Nothing else is
needed: no C compiler headers for Python, no extension-module API.

```
pip install .          # or: pip wheel . (a wheel for this platform)
python -c "import fuzzy; print(fuzzy.distance('kitten', 'sitting'))"   # 3
```

The example is edit distance (Levenshtein, on code points), which pure Python does slowly:

| | pure Python | Vu | |
|---|---|---|---|
| `distance()`, 2,000 pairs of 12-letter words | 29.8 ms | 2.6 ms | 11x |
| `closest()`, 20 words among 5,000 | 800 ms | 32.6 ms | 25x |

(`python tests/bench.py`: the median of 5 runs, on a 2-core Linux x86-64 machine,
Python 3.13. Half of the first row is the cost of calling through ctypes: 2,000 calls with
empty strings take 1.3 ms.) `python tests/test_fuzzy.py` checks the answers against the same code in
pure Python (`tests/pure.py`) on random strings with accents, CJK and emoji.

How the pieces fit:

- `src/fuzzy/fuzzy.vu`: the functions, marked `export fn`. They take and return `Int`, `Float`,
  `Bool`, `Str` and lists of numbers or bytes (see "Libraries for C and Python" in SPEC.md), and
  get no capabilities: the library can't open files, connect anywhere or run programs.
- `src/fuzzy/__init__.py`: loads `libfuzzy.so`, declares each function's C types for ctypes, and
  turns Python values into them (a `str` is passed as its UTF-8 bytes and their length).
- `setup.py`: runs `vu build --lib` while the package is built, so the wheel holds the library.

A Vu function that `throws` takes a `char **` last. Pass `ctypes.byref(err)` for an
`err = ctypes.c_char_p()`: when it's set after the call, raise it as an exception. Free a returned
`Str` or list with libc's `free` after copying it out (`ctypes.string_at(p, n)`).
