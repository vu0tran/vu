# vu speedup: slow Python, ported to Vu, checked, swapped in

```
vu speedup suggest.py:close_matches --port close_matches.vu
```

```
close_matches(word: str, possibilities: list[str], n: int, cutoff: float) -> list[str]  [direct call]
3000 inputs; the original raises on 703
same answers as the original on all 2982 inputs; 18 more ran the original (the Vu version can't take them, or hands them back)
speed on the 3000 test inputs: Python 99.7 ms, Vu 20.5 ms: 4.9x
speed on 34 bigger inputs (lists of 500 to 2,000): Python 142.4 ms, Vu 20.9 ms: 6.8x
suggest.py: close_matches now runs the Vu version (the lines after it say so; delete them to undo)
```

`vu speedup FILE.py:FUNC` takes a Python function with type hints and:

1. **Makes inputs.** Thousands, from the hints: edge cases, Unicode (accents, CJK, emoji, combining
   marks, capital sigma), empty and long lists, ints past 64 bits, infinities and NaN; plus real
   calls recorded from your code (`--record script.py args`) or a JSON file (`--inputs-file`). It
   runs your function on each and keeps what it returns or raises. A function that changes its
   arguments is refused.
2. **Gets the Vu version.** From `--port FILE.vu` (written by you or a coding agent), or from a
   model (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`) in a loop that feeds back the compiler's errors
   and every answer that differs. With neither, it writes the prompt for an agent (`llms.txt`, the
   function and the module code it uses, the exact Vu signature, the rules) and stops; `--prompt`
   prints it.
3. **Checks it.** The Vu version runs on every input in a separate process; each answer must equal
   the original's: same types, same values (floats to the last bit), the same exception class where
   it raises.
4. **Measures it,** on the test inputs and on bigger ones, and swaps it in only if it's faster
   (1.2x or more): two lines after your function, saying so. Delete them to undo.

The swapped-in function never changes what your program does. Anything the Vu version can't take
runs your Python instead: an int over 64 bits, a string Python can't encode as UTF-8, an argument of
another type (a bool where an int was hinted), a panic (an overflow inside the Vu version), or a call
the port hands back on purpose (`fail "vu-speedup: fallback"`, for a rare case that's hard to get
exactly right).

## The examples here

Each folder has a Python module, its Vu ports and a `bench.py`. Ports in agent mode (written by
Claude from the prompt `vu speedup` gives); every one gave the same answers as the Python on every
generated input, and the numbers below are `bench.py` on realistic data (a 2-core Linux x86-64
machine, Python 3.13, best of 3):

| | Python | Vu | |
|---|---|---|---|
| `difflib.get_close_matches`, 1,000 words (closematch) | 1.71 ms | 0.205 ms | 8.4x |
| `difflib.get_close_matches`, 10,000 words | 16.5 ms | 2.07 ms | 8.0x |
| jellyfish `jaro_winkler_similarity`, a pair of names (names) | 3.72 us | 0.55 us | 6.7x |
| jellyfish `damerau_levenshtein_distance`, a pair | 15.9 us | 1.21 us | 13.2x |
| the closest of 5,000 names (Jaro-Winkler) | 22.6 ms | 2.37 ms | 9.6x |
| a GPS track's length, 100,000 points (geo) | 77.4 ms | 12.8 ms | 6.1x |
| the nearest of 5,000 points, 200 queries | 688 ms | 99.2 ms | 6.9x |

jellyfish also ships a Rust extension for those two functions: 0.74 us and 1.84 us a pair on the
same machine, so the Vu ports are faster per call than the hand-written Rust (5.0x and 8.7x over
Python). `difflib` is Python's standard library; the jellyfish code is its pure-Python
implementation (`_jellyfish.py`, MIT license), as it is.

## Where it helps, and where it doesn't

- A function that does its own work in Python loops (string algorithms, numeric loops, scoring a
  list): 5 to 13x here.
- A function whose time is already in Python's C code (`re`, `Counter`, `sorted`, `min` and `max`,
  `str` methods) or that does little per call: the Vu version is slower, because its arguments still
  have to be passed. `vu speedup` measures that and leaves the function alone (`--force` overrides).
- Arguments pass straight through for `int`, `float`, `bool`, `str`, `bytes` and lists of numbers
  or strings (a CPython extension it builds, or ctypes without Python's headers); dicts, nested
  lists, tuples and optionals pass as JSON, which costs microseconds a call.
- The function must be pure: its result from its arguments, its arguments left alone, no global
  state. Results are new objects (a list it returns isn't one it was given).

## Writing a port

The prompt `vu speedup` writes has the rules; the ones that matter most:

- Python's `len(s)` and `s[i]` count characters; Vu's `s.len` and `s[i]` are bytes. Use
  `s.codes()` (code points as `[Int]`) or `s.chars()`. `upper()`, `lower()` and `is_alpha()` and
  friends match Python's, except that Vu's `lower()` doesn't make a final capital sigma "ς":
  `fail "vu-speedup: fallback"` when the text holds "Σ".
- Python's exceptions are `fail "ValueError: message"`; a class of your module works too.
- Python's math functions are Float methods calling the same C functions (`x.sin()`, `y.atan2(x)`,
  `x.pow(y)` for `x ** y`), so the results are the same bits. Python raises `ValueError: math domain
  error` where C returns NaN: check, as `examples/speedup/geo/geo_common.vu` does.
- Do float operations in Python's order, so they round the same.

`tests/run_speedup.sh` checks every port here, the model loop (against a fake API), the swap, the
fallbacks, threads, and Float methods against Python's math module.
