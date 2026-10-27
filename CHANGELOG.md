# Vu changelog

How Vu got where it is, round by round: what each round added, what the attack rounds found, and
the numbers as they were measured at the time. Later rounds sometimes changed earlier numbers, and
notes marked **Later** say so. For an introduction to the language, see [README.md](README.md);
for the language itself, [SPEC.md](SPEC.md).

The first sections (Results through LLM tokens) are the comparison from rounds 1 and 2.

## Rounds 1–2: results

All runs: Linux cloud VM, 2 vCPUs, single-threaded, median of 5, `-O3 -march=native`.
C, C++, Rust and Go are the same programs as the earlier comparison (the upstream sources
from hanabi1224/Programming-Language-Benchmarks, plus single-threaded C and C++
binary-trees ports in `bench/`). Every program's output matches the reference output.

### Speed

| | binary-trees (depth 20) | n-body (50M steps) |
|---|---|---|
| C | 6.43 s, 130 MB | 2.36 s |
| C++ | 7.16 s, 132 MB | 2.55 s |
| Rust | 8.22 s, 130 MB | **1.71 s** |
| Go | 15.29 s, 186 MB | 2.85 s |
| **Vu** | **2.50 s, 66 MB** | 2.46 s |
| Vu `--malloc` | 5.44 s, 130 MB | — |

- **binary-trees: Vu is about 2.6x faster than C and uses half the memory.** Most of
  that comes from the default allocator: freed tree nodes go onto a per-type free list
  and are reused, and new nodes are carved from 1 MB blocks. Because the compiler
  proves no node is referenced after it's freed, this needs no checks and is always safe.
  With plain `malloc`/`free` (`--malloc`), Vu is still faster than C here. I haven't
  isolated why; likely candidates are that each tree's root lives on the stack and
  children are allocated before their parent.
- **n-body: Vu matches C but is about 45% behind Rust.** I tested where the gap comes
  from. Restructuring the Vu program the way the Rust one is written, removing bounds
  checks, and fixing the body count at 5 each changed little. A hand-written C
  translation of the Rust program, compiled with gcc or clang 18, lands at 2.2–2.7 s,
  not Rust's 1.7 s. The most likely explanation is that rustc 1.97's newer LLVM optimizes
  this loop better, but I haven't confirmed that. Building with `CC=clang` gives 2.1–2.4 s.
- **Update: Vu now uses strict floating point** (no fused multiply-add), so a program
  gives bit-identical results on every machine, as in Rust. This was required for
  mandelbrot's output to be correct, and it slows Vu's n-body to 3.10 s (C 2.42 s,
  Rust 1.82 s in the same session).
- **Later (2026-10-26): the strict-FP explanation above was wrong.** Rust also uses strict
  floating point and was the fastest, so the lack of fused multiply-add isn't what puts Vu behind.
  Re-measured with `bench/compare.sh`, Vu's n-body is 5.33 s against C 3.08 s and Rust 2.59 s:
  slower than in these rounds, and being investigated.

### Four more benchmarks

Every language runs the same algorithm, single-threaded. Sources are in `bench/`:
upstream programs where they matched (spectral-norm C/Rust/Go, nsieve all four),
straight ports otherwise. C and C++ mandelbrot are built with `-ffp-contract=off`,
because without it they print the wrong hash.

| | spectral-norm 8000 | nsieve 13 | fannkuch-redux 11 | mandelbrot 8000 |
|---|---|---|---|---|
| C | 3.14 s | 1.57 s | 2.44 s | 3.44 s |
| C++ | 3.44 s | **1.42 s** | 2.68 s | **3.33 s** |
| Rust | **3.03 s** | 1.68 s | 2.65 s | 3.39 s |
| Go | 3.21 s | 1.50 s | 2.60 s | 3.47 s |
| **Vu** | 3.18 s | 1.58 s | **2.35 s** | 3.40 s |

All five land within about 15% of each other on every one of these four, which is
expected for simple loops that the C compiler and LLVM both optimize well. Vu's one
weak spot is memory: mandelbrot used 124 MB against about 13 MB for the others, because
Vu has no byte type and stores each pixel byte as an 8-byte `Int`. **Later:** round 3 added `Byte`, and mandelbrot
now uses 18 MB.

Tokens (same method as below):

| | spectral-norm | nsieve | fannkuch-redux | mandelbrot |
|---|---|---|---|---|
| C | 491 | 194 | 379 | 426 |
| C++ | 437 | 320 | 317 | 421 |
| Rust | 450 | 173 | 316 | 367 |
| Go | 399 | 174 | 385 | 353 |
| Vu | **351** | **115** | 366 | 1520 (296 without MD5) |

Vu writes MD5 itself because it has no library yet. fannkuch-redux is longer in Vu than
in C++ or Rust because those use built-in `reverse` and `rotate`.

### Compile time (full build, optimized)

| | binary-trees | n-body |
|---|---|---|
| C | 0.20 s | 0.13 s |
| C++ | 0.61 s | 0.35 s |
| Rust | 0.20 s | 0.23 s |
| Go | 0.17 s | 0.20 s |
| Vu | 0.24 s | 0.17 s |
| Vu `--debug` | 0.11 s | 0.13 s |

Vu's own front end takes about 2 ms. The rest is gcc. These programs are too small
to show the compile-time differences that appear in large projects.

### The edit-and-test loop

What matters day to day is the time from a change to a result. `vu check` stops after
Vu's front end, which is where every compile error comes from, and `vu run` now builds
unoptimized (`-O0`) because gcc compiles that several times faster. `vu run --release` and
`vu build` still optimize. Measured with the self-hosted compiler (`compiler/vuc`):

| | before | now |
|---|---|---|
| check the JSON parser for errors (~300 lines) | 0.95 s (only a full build would tell you) | **0.008 s** (`vu check`) |
| check the compiler itself for errors (6,000 lines) | 17 s | **0.14 s** (`vu check`) |
| change the JSON parser, rebuild and run it | 0.95 s (`-O3`) | **0.26 s** (`vu run`, `-O0`) |
| `tests/run_tests.sh` (34 programs, all through `vu run`) | 13.4 s | 11.7 s (`vu.py`), 8.2 s (`vuc`) |

The trade-off: an `-O0` program runs slower, often 3–10x, so for timing or heavy tests use
`--release`. `tests/run_cli.sh` checks these rules with a stand-in C compiler that records
the flags it gets, so it would catch `check` calling gcc or `run` building optimized.

### LLM tokens

Comments stripped, each file run through its standard formatter (clang-format, rustfmt,
gofmt), then counted with the GPT-4o (o200k) tokenizer. Claude's tokenizer isn't
public, so this is a proxy.

| | binary-trees | n-body |
|---|---|---|
| C | 376 | 1413 |
| C++ | 327 | 1675 |
| Rust | 440 | 1551 |
| Go | 363 | 1362 |
| **Vu** | **255** | **1074** |

Vu needs about 22–42% fewer tokens than the other four. About 600 of the n-body tokens
in every version are the same planet constants.

## Round 3: bytes, strings, threads, overflow checks, capabilities

New in the language: `Byte`, `Str`, `write()` for raw output, `par for` loops that the
compiler proves free of data races, integer overflow that stops the program, and the `Fs`
file capability (see `SPEC.md`).

**Mandelbrot memory: 124 MB to 18 MB.** The bitmap is now `[Byte]` instead of `[Int]`.

**Cost of overflow checks: about zero, except nsieve.** Same programs, built by the
compiler before and after this round (median of 5):

| | wrapping | checked |
|---|---|---|
| binary-trees 20 | 2.78 s | 2.44 s |
| n-body 50M | 3.04 s | 3.08 s |
| nsieve 13 | 1.68 s | 1.87 s |
| fannkuch-redux 11 | 2.74 s | 2.66 s |

Differences under about 5% are within run-to-run noise here. nsieve's 11% is the one
measurable cost.

**Multithreaded, 2 vCPUs** (same algorithm everywhere; C and C++ use OpenMP, Rust scoped
threads, Go goroutines):

| | mandelbrot 8000 | spectral-norm 8000 |
|---|---|---|
| C | **1.69 s** | 1.92 s |
| C++ | 1.72 s | 1.93 s |
| Rust | 1.79 s | **1.80 s** |
| Go | 1.88 s | 2.32 s |
| Vu | 1.82 s | 2.08 s |

Both are close to a 2x speedup over one thread in every language. Vu's `par for` costs
something when it can't use more threads: spectral-norm built with `par` and run on one
thread takes 4.07 s, against 3.40 s without `par`. The loop body optimizes less well once
OpenMP moves it into a separate function. A static schedule was slower still (2.77 s on
2 threads), so Vu keeps the dynamic one.

## Round 4: enums, errors, maps, and a real program

Three features the self-hosted compiler will need, then one real program to see whether
the ownership rules are livable. Details are in `SPEC.md`.

- **Enums with `match`:** `type Token:` with variants like `Num(value: Int)` or `End`.
  `match` must cover every variant (or have `_`), and its bindings borrow like `if v = ...`.
- **Error values:** a function marked `throws` can `fail "message"`. Callers must handle
  it with `f(x)?` (pass it on), `f(x) else default`, or `match f(x):` with `ok(v)` and
  `err(e)` arms; an unhandled call doesn't compile. File operations now fail this way
  instead of panicking.
- **Maps:** `{Str: Int}`, insertion-ordered, with a random-keyed SipHash so attacker-chosen
  keys can't force collisions.

### The real program: a JSON parser

`examples/json.vu` reads a JSON file, prints a summary, and can print it back in compact
form (255 lines without comments). Malformed input gives `error: <what> at byte N` and exit
code 1. It's an enum tree (`Obj` holds a `{Str: Json}` map), a recursive-descent parser in
functions marked `throws`, and a depth limit of 1000 so hostile input can't exhaust the
stack.

**Correctness.** `tests/run_json.sh` (84 checks) does three things:
- generates random documents (all escapes, surrogate pairs, emoji, ints, floats from 1e-30
  to 1e30, nesting) and checks the parser reads exactly the values Python's `json` reads,
  with floats compared bit for bit;
- feeds 15 malformed documents, each of which must give its specific error;
- feeds 100,000 levels of nesting.

Every run is also checked under AddressSanitizer, LeakSanitizer and UBSan, with both
allocators. That includes the error paths, where `?` unwinds through recursive frames
holding half-built trees.

**Speed** on a 50 MB file of 160,000 records, parsing into a generic tree and counting the
nodes, single-threaded. Times are ranges over interleaved runs on a noisy machine:

| | time | memory |
|---|---|---|
| Rust (serde_json, insertion-ordered maps) | 0.90–1.07 s | 550 MB |
| **Vu** | **1.13–1.47 s** | 520 MB |
| Go (encoding/json) | 1.11–1.37 s | 330 MB |
| Python (json, C scanner) | 1.55–2.05 s | 424 MB |

Vu and Go trade places between runs. Vu's memory is high because every map key is its own
allocation and every object is a hash map: about 100 bytes per entry, plus an index. (The
memory follow-up below brings Vu to 392 MB.)

#### Memory follow-up: why Vu used more than Go, and two compiler fixes

Measured sizes: one Vu `Json` value took 56 bytes, Go's 16. Rust's `serde_json::Value` is
32 bytes by default and 72 with insertion-ordered maps, which is what my Rust benchmark
used. Vu's value was big because an enum is as large as its largest variant, and `Obj`
held the 48-byte map header inline, so even `null` cost 56 bytes. Each key was also copied
into the map and the original freed, and my parser copied the whole 50 MB file.

- **Large enum payloads go behind a pointer.** In an enum that moves (rather than being
  copied), a variant whose payload is over 24 bytes, when some other variant is smaller, is
  allocated separately from Vu's per-thread node pool. `Json` shrank from 56 to 32 bytes;
  only objects pay one extra allocation. Plain-data enums are still copied inline.
- **Map keys move on their last use.** `m[k] = v` moves `k` into the map when `k` is a
  string owned by the current block and not mentioned again in it. Otherwise it's copied.
  If the check were ever wrong, `k` is marked moved, so a later use is a compile error, not
  a memory error.
- **My program:** `parse` took the text as a borrowed parameter, so the `Parser` needed its
  own copy. `main` now moves the file contents into the `Parser`.

Interleaved runs on the same file, on a more loaded machine than the table above, so the
absolute numbers are higher:

| | time | memory |
|---|---|---|
| Rust (serde_json default: sorted maps) | 0.77–0.92 s | 370 MB |
| Rust (serde_json, insertion-ordered maps) | 1.21–1.31 s | 550 MB |
| **Vu, after** | **1.33–1.34 s** | **392 MB** |
| Vu, before | 1.54–1.89 s | 520 MB |
| Go (encoding/json) | 1.67–1.86 s | 331 MB |

Vu now matches insertion-ordered serde_json on time, is faster than Go, and is about 1.55x
behind default serde_json (it was 1.8x). Of the 128 MB saved, 81 MB came from the two
compiler changes and 47 MB from not copying the file. Two things still separate Vu from
Go's 331 MB: every short string is its own allocation of at least 32 bytes (Go has no
per-allocation header), and a map entry is 96 bytes against Go's 32. Keeping short strings
inside the string value itself, and slimming map entries, are the next steps.

#### Speed follow-up: where Rust's lead came from

Against default serde_json, all of the gap was CPU time in the program (system time was
equal). Vu made 4.4 million mallocs and 1.0 million reallocs; Rust made 2.9 million and
0.1 million. Three changes:

- **`for k, v in m:`** goes through keys and values together. The JSON walk had used
  `for k in m: m[k]`, which hashed every key a second time. `for k, var v in m:` changes
  values in place (the map is locked for the loop), which also removes the old friction
  that values couldn't be updated while looping.
- **Strings start at exactly the size needed** instead of 16 bytes, so a string built once
  (a slice, a parsed token) is one allocation; one that keeps growing doubles from there.
- **`int(s[a..b])` and `float(s[a..b])` read the slice in place** instead of copying it into
  a temporary string first: 1.5 million fewer allocations in this file.

| | time | allocator calls |
|---|---|---|
| Rust (serde_json default) | 0.78–0.87 s | 3.0 million |
| **Vu, now** | **1.04–1.23 s** | 5.2 million (2.9 M malloc, 1.3 M realloc) |
| Vu, before | 1.24–1.41 s | 6.4 million |
| Rust (insertion-ordered) | 1.27–1.42 s | — |
| Go | 1.76–2.15 s | — |

Vu is now about 1.4x behind default serde_json (it was 1.8x), and faster than both
insertion-ordered serde_json and Go. Reallocs went up: strings with escape sequences grow
piece by piece from an exact first allocation. What's left is mostly the scanner itself:
every byte read is bounds-checked, often twice through `peek()`, where serde_json's string
scanner is a tight table lookup.

#### Closing the gap: parity with serde_json

Callgrind on a 5 MB file put Vu at 460 million instructions against Rust's 304 million.
The difference was in three places: `strtod`/`strtol` (72 M), the allocator (150 M against
95 M), and the byte scanner. Five changes:

- **Number parsing without libc.** `int(s)` is a direct digit loop. `float(s)` tries
  Clinger's exact fast path, then the Eisel–Lemire algorithm (its 128-bit power-of-ten table
  is only emitted into programs that parse floats), and only falls back to `strtod` for the
  rare cases neither can decide. Checked against Python's `float()` on 3 million random
  hard cases: 0 mismatches.
- **Small maps don't hash.** A map with at most 16 entries is a plain array searched
  linearly, with no index and no hashing. Most JSON objects are small. It switches to the
  hashed index at the 17th entry.
- **Cheaper checks gcc can remove.** Adding a constant uses `a > INT64_MAX - c` instead of a
  general overflow check, and an index check is `i < 0 || i >= len`. gcc now hoists both out
  of the scanner loops: about 4 instructions per input byte.
- **Fewer reallocations.** Maps grow 4 → 12 → ×1.5, and `s.reserve(n)` / `xs.reserve(n)`
  exist. String reallocations on the file went from 255,000 to 11, and list reallocations
  now match Rust's almost exactly (97,468 against 97,472).
- **Stack canaries:** measured, made no difference, kept.

Twelve interleaved runs on the 50 MB file:

| | median | fastest | memory |
|---|---|---|---|
| Rust (serde_json default) | 0.607 s | 0.573 s | 370 MB |
| **Vu** | **0.607 s** | **0.572 s** | **370 MB** |

The six benchmarks were unchanged or slightly faster (for example binary-trees 2.78 →
2.65 s, nsieve 2.63 → 2.50 s, fannkuch 2.57 → 2.50 s; mandelbrot 3.46 → 3.51 s is noise).
The program itself changed in small ways: local indexes in the inner loops, and reserving
at the first escape sequence in a string.

**Was it livable?** Mostly yes. Building the tree was natural: children are moved into
their parents, `match` borrows, and the parser threads `var p: Parser` through every call
(25 `&p` at call sites, which is noisy but makes every mutation visible). I fought the
checker once: a helper took a `Json` parameter and tried to return it, which is moving out
of a borrow. Restructuring it made the code clearer. The rest of what I hit:

| Friction | Resolution |
|---|---|
| No `'\r'` escape | **added** `\r` to strings and Byte literals |
| Couldn't read a file path from the command line | **added** `arg(i, "default")` returning a Str |
| `fs.read` of a missing file crashed the program | **changed:** file operations are now error values |
| `{x}` printed Floats with 6 digits (1234567.891 → `1.23457e+06`) | **changed:** shortest text that reads back exactly, as in Python |
| No way to turn text into a number, so my float parsing was off in the 17th digit | **added** `float(s)` and `int(s)`, which can fail and round correctly |
| `m["k{i}"] = v` was rejected | **fixed:** computed keys work for inserting and for reading plain values |
| `out += s[a..b]` copied the slice twice | **optimized:** appends straight from the source, safe even when it's the same string |
| `items.push(value(&p)?)` isn't allowed | kept: `?` must start a statement (one extra line) |
| A variant can't be called `Bool`; a local can't be called `text` when a function is | kept: renamed to `Flag` and `lit` |
| String literals can't go inside `{...}` | kept for now; it caught me 4 times writing tests |

### Other fixes from this round

- **Stack overflow:** deep recursion (a recursive-descent parser on `[[[[...`) used to die
  with a bare SIGSEGV. It now stops with `panic: stack overflow (recursion too deep)` and
  exit 101, on `par` worker threads too. It uses an alternate signal stack, the way Rust
  does it.
- **Maps** grow by 1.5x from 4 entries instead of doubling from 8. On the JSON file that
  cut memory from 650 MB to 520 MB and time by about 10%.
- **A regression I caused and fixed:** the stack guard first ran once per `par` iteration,
  which made spectral-norm 2.2x slower (gcc stopped optimizing across the call). It now
  runs once per thread. All six benchmarks are back within noise of the previous compiler.

## Self-hosting

`compiler/vuc.vu` is a Vu compiler written in Vu: lexer, parser, type and ownership
checker, C code generator and build driver. Vu has no modules for the compiler's own source yet,
so it lives in six parts (`compiler/c1_front.vu` … `c5_build.vu`) plus the runtime, which
`compiler/build.sh` joins into one file. The C runtime and code templates are plain C files in
`compiler/rt/`; `tools/gen_runtime.vu` (a Vu program) embeds them.

```
compiler/bootstrap.sh       # cc compiler/vuc_seed.c -> compiler/vuc (what ./vu does the first time)
compiler/build.sh           # vuc builds itself, the result builds itself, and that builds itself
                            # again: the last two must give identical C. Then it's installed, and
                            # its C becomes the new seed.
tests/run_selfhost.sh       # the fixed point, the seed rebuilding the same compiler, and 67 edge cases
```

**History: two compilers.** Until 2026-10-26 the language also had a Python compiler, `vu.py`,
the original bootstrap. Every feature was written in it first and then ported, and the two had
to produce byte-identical C and error messages for every test, example, module program and
`vuc.vu` itself (the last full comparison: 665 of 665 files identical). That comparison found
real bugs early on (rounds 22 and 23 below), but later it mostly caught places where the two
copies had drifted apart, at the cost of writing every feature twice. The compiler is now only
`vuc`. The edge cases from those rounds stay as tests, with their results recorded in
`tests/selfhost/expected.tsv`. `vu.py` is in `attic/`, retired.

**Speed.** The front end (everything except gcc):

| Input | `vu.py` | `vuc` |
|---|---|---|
| `compiler/vuc.vu` (6,059 lines) | 400 ms | 167 ms |
| `examples/json.vu` | 15 ms | 7 ms |
| `examples/nbody.vu` | 4.3 ms | 1.2 ms |

Building the compiler itself takes 14 s at `-O3` and 3.4 s with `--debug`. Nearly all of
that is gcc compiling 14,600 lines of C.

### What writing a compiler in Vu was like

A compiler is the kind of program Vu was least designed for: one big mutable state, trees
everywhere, lots of strings moving between tables. It worked, and the friction was
specific enough to fix:

| Friction | Resolution |
|---|---|
| `let name = node.name` was rejected (moving a Str out of a field); 67 `+ ""` copies are still in the source from before the fix | **changed:** a Str that can't be moved is copied |
| `let kids = node.kids` was rejected for the same reason, so I copied lists or indexed in place | **added** let views: a read-only view, with the owner frozen until the block ends |
| No way to take a value out of a `var` parameter | **added** `swap(&a, &b)` |
| No `pop`, no exit codes, no stderr, no argument list, couldn't run gcc | **added** `xs.pop()`, `exit(code)`, `eprint(s)`, `args()` and the `Os` capability (`os.run`, `os.env`, `os.clock`), plus `fs.temp_dir()` |
| With the default 8 MB stack, `vuc` stopped with a stack-overflow panic on 3,500-level nesting and on a 20,000-term `+` chain, both of which `vu.py` accepts | **changed:** `main` runs on a 256 MB stack (reserved, not committed); both now compile |
| Parameters can't be owned (moved in) | kept: a `var` parameter plus `swap`, or the caller builds the value |
| A local can't share a name with a top-level function (`stmts`, `arg`) | kept: renamed |
| Literal braces in strings must be doubled (`"{{"`) | kept: 117 lines of the C generator need it, and forgetting is a compile error, not a silent bug |
| No modules | kept for now: `build.sh` joins the parts |

Writing a second compiler was also the best test of the first. Comparing the two found
real `vu.py` bugs that 23 rounds of attacks hadn't (see rounds 22 and 23):

- `0x_` crashed `vu.py`, and `vuc` accepted it as 0. Now it's an error in both.
- `vu.py` accepted Unicode digits (`٣`) as numbers and Unicode spaces as whitespace,
  because Python's regular expressions and `strip()` are Unicode-aware by default.
- Errors inside `{...}` in a string were reported on line 1.
- A long `a + a + ... + a` chain hit Python's recursion limit.

## Round 5: built for the model that writes it

A model doesn't mind typing; what costs it is a wasted compile-and-fix round, an unfamiliar
name, or a bug it can't see. This round goes after those.

### Debugging: errors and panics a model can act on

- **Panics name the line and the chain of calls.** In quick builds (`vu run`, `--debug`)
  each function keeps a frame on a per-thread shadow stack, so a panic prints
  `at deep.vu:5 in third`, then `called from deep.vu:9 in second`, and so on. Deep recursion
  is collapsed into one line with a count, and a panic in a `par` worker leads back to the loop.
  Optimized builds compile the frames away and report the panic's own line.
- **`--json`** turns compile errors and panics into one JSON object per line on stderr, with
  file, line, message, the source line, and the backtrace. `VU_PANIC=json` does the same for
  any binary at run time.
- **gdb, sanitizers and core dumps point at Vu lines**: the generated C carries a `#line`
  directive before every line. That grew the C for the compiler from 14,600 to 37,700 lines
  and `-O0` builds by about 8%.

Rounds 25–31 attacked this. They found, and I fixed:

| Round | Found |
|---|---|
| 25 | a panic in a `par` worker didn't show where the loop was; a file over 16.7 million lines could make the reporter read past its file table (the line is kept in 24 bits; such files are now an error); an off-by-one in my own new limit |
| 26 | JSON with invalid UTF-8 in a message wasn't valid JSON; `vu.py` crashed on a source file that wasn't UTF-8 while `vuc` accepted it; `vu.py` crashed on a missing file; a lone `\r` and raw carriage returns in strings meant different things to the two compilers |
| 27 | **a data race in the new reporter:** several `par` workers panicking at once shared its buffer, which could garble the report or overflow the buffer. Reports now take a lock, and exactly one is printed |
| 28 | my round-27 fix cleared the buffer in the stack-overflow handler before taking the lock, so a second overflowing thread could wipe the first one's report |
| 29 | `exit(3)` in one worker racing a panic in another could print a panic report but exit with 3. `exit` takes the same lock now |
| 30 | `panic()` cut its message at the first zero byte (an old bug: it went through `printf`'s `%s`) |
| 31 | **0** |

### Python's helpers, with Python's names

`s.split()`, `s.split(sep)`, `sep.join(items)`, `s.strip()` (and `lstrip`, `rstrip`, with an
optional set of characters), `s.startswith(p)`, `s.endswith(p)`, `sorted(xs)`,
`sorted(xs, reverse: true)`, `xs.sort()`, `min(xs)`, `max(xs)`, and `min`/`max` of more than
two numbers. They behave as in Python, including the edge cases: `"".split(",")` is `[""]`,
`"aaa".split("aa")` is `["", "a"]`, an empty separator is an error, sorting is stable even
reversed, and strings sort by code point. A call to a Python method Vu doesn't have yet, like
`s.lower()`, gets a message listing what `Str` does have.

Rounds 32–33 attacked them with 38 programs: every edge case above checked against Python,
20,000 random Ints, NaN and negative zero, zero bytes, sorting while a loop borrows the list,
sorting inside `par`, temporaries under AddressSanitizer, and a million-piece split to rule out
quadratic time. Round 32 found that Vu printed a NaN with its sign bit set as `-nan` (Python
prints `nan`), and that the unknown-method message talked about lists when the value was a
string. Round 33 found nothing.

### Owned parameters

`fn add(var lx: Lexer, own tok: Token)` takes ownership of `tok`: the function can store it,
return it or change it, and frees it otherwise. The argument is moved, exactly as by `let`.
Three details make it hard to trip over:

- A `Str` variable that is used again is copied instead of moved, so `shout(name)` followed
  by `print(name)` just works; a string used for the last time is moved, with no copy.
- The move happens after the other arguments are evaluated, so the very common
  `consume(items, items.len)` works. Borrowing the same list in another argument is still an
  error, since the callee would hold a pointer into a list it owns.
- Moving a borrowed parameter now says how to fix it: "declare the parameter
  'own xs: [Int]' to take ownership".

The self-hosted compiler uses an owned parameter itself, where it used to need a workaround.

### Modules

`import geo` reads `geo.vu` next to the importing file; `from geo import area, Point` brings
names in bare. Inside the compiler, everything module `geo` defines becomes `geo__name`, so
the checker and code generator see one program and nothing clashes, and a single-file
program compiles to exactly the C it did before. Errors, panics, backtraces, JSON reports and
gdb all name the right file: a line number carries its file's index in its top bits, the
same encoding the runtime uses. Modules may import each other in cycles; `match` arms name
variants bare (or `geo.Circle(r):`, as models used to Rust's `Shape::Circle` write them); and
constants are evaluated in the order they use each other, across files. `tests/run_modules.sh`
runs 37 multi-file programs and 6 generated cases (up to the 127-module limit).

### Small frictions, gone

- **`?` anywhere in an expression.** `items.push(parse(&p)?)` and `add(num(a)?, num(b)?)`
  now compile. Each `?` becomes a hidden `let` just before its statement, in the order
  written. Where that would change what runs, it's an error that says so: after a call to
  its left, on the right of `and`/`or`, in an `else` fallback, or in a `while` condition. An
  `elif` condition's `?` runs only when the earlier conditions were false.
- **Locals can shadow functions, constants and built-ins** (`let text`, `let max`). This
  rule cost me four compile errors while writing this round's changes to the compiler.
  Calling the shadowed function says exactly that.
- **String literals inside `{...}`**, as in Python 3.12: `"{m["k"]} {", ".join(xs)}"`.

### Rounds 34–44

| Round | Focus | Found |
|---|---|---|
| 34 | owned parameters (16 attacks) | a string passed to two owned parameters of one call was "moved twice"; moving a `let` view gave a message about borrowing |
| 35 | owned arguments moved last (7) | **an accepted double move:** `take(items, take(items, 0))`. Memory-safe only because moves zero their source; the deferred move now re-checks |
| 36 | owned arguments with `?`, `else`, `match` (5) | **0** |
| 37 | modules (25) | a module defining `print` would silently replace the built-in inside it; constants from imported modules weren't known yet; a module used but not imported gave "unknown name" |
| 38 | module ordering, qualified arms (6) | constants across modules depended on import order |
| 39 | constants across cycles (5) | ordering by file can't be right for cycles: constants are now ordered by what they use |
| 40 | names with underscores (4) | `geo.__helper` was shown as `geo..helper` |
| 41 | module types, gdb across files (3) | **0** |
| 42 | the frictions (21) | a `?` in an assignment's target would have run before the value, which Vu computes first |
| 43 | `?` with `elif`, `&` arguments, nested strings (5) | `?` in an `elif` wasn't supported; a hoisted call was still counted as changing a borrowed argument |
| 44 | `?` in chains, matches, nested strings, owned parameters (5) | **0** |

As before, my own test mistakes are not counted. There were several: wrong line numbers
after the test header, and `else` used inside an expression, where it has never been allowed.

## Round 6: networking and an HTTP benchmark

Vu had no networking, so a web server needed a new capability. `Net` (`fn main(net: Net)`) is
a TCP server as an event loop: `net.listen(port)`, `net.wait()` returns a connection with data,
`net.recv(c)`, `net.send(c, data)`, `net.close(c)` (see SPEC.md). The runtime uses epoll; the
Vu program does the HTTP. It follows the other capabilities: a function can only reach the
network if it's handed the `Net`. Connections are Int ids, so the runtime checks every id it's
given: a made-up or closed id stops the program instead of reading another file.

`bench/http/server.vu` is a 40-line HTTP/1.1 server (keep-alive, pipelining, requests split
across reads) that answers "Hello, World!".

### The benchmark

One test for every language: 50 keep-alive connections requesting `/` for 10 seconds, measured
with wrk. This machine has 2 cores, so the server is pinned to one and wrk to the other.
`bench/http/run.sh` runs each server 3 times and reports the median run.

The comparison that's fair to the languages is "raw": the same minimal server (find the
blank line, send the canned reply) written over plain TCP in Go and TypeScript. The standard
HTTP servers (Go's `net/http`, Node's `http`, `Bun.serve`) parse every header and add their
own, so they do more work per request; they're listed for reference.

| Server | Requests/s | p50 | p99 | Server CPU | Requests per CPU-second |
|---|---|---|---|---|---|
| **Vu** (`server.vu`) | **96,360** | **0.28 ms** | **1.41 ms** | 79% | **121,974** |
| Go, raw TCP, 1 thread (`goraw/`) | 85,373 | 0.41 ms | 2.40 ms | 91% | 93,816 |
| TypeScript on Bun, raw TCP (`server_raw.ts`) | 66,633 | 0.57 ms | 3.41 ms | 94% | 70,886 |
| TypeScript on Node 22, raw TCP (`server_raw.ts`) | 54,085 | 0.73 ms | 2.80 ms | 96% | 56,338 |
| TypeScript on Bun, `Bun.serve` | 58,014 | 0.70 ms | 2.47 ms | 95% | 61,067 |
| Go `net/http`, `GOMAXPROCS=1` | 26,587 | 1.82 ms | 5.41 ms | 97% | 27,409 |
| TypeScript on Node 22, `http` | 18,334 | 2.80 ms | 10.13 ms | 98% | 18,708 |

How to read it:
- At this speed, the load generator is part of the limit: wrk used 94% of its core while
  driving the Vu server, and Vu's server used 79% of its own. So the requests/second column
  understates the gap at the top, and the last column (requests divided by the server's CPU
  time) is the better measure of the work each server needs per request.
- Runs vary by about 10% on this machine (Vu's three runs: 99,709, 80,442 and 96,360). Vu
  against raw Go is within that noise on requests/second; it isn't on CPU per request or p99.
- Raw Go starts a goroutine per connection and the Go scheduler multiplexes them; Vu's loop
  is a single thread calling epoll directly. That's most of the difference, and it's a
  difference of design as much as of language.

### Rounds 45–47

| Round | Focus | Found |
|---|---|---|
| 45 | `Net` in the checker, and runtime basics (16 targeted programs, a new suite of 18 checks with Python clients: 3000 connections, 3 MB echoes, 8 MB replies to a slow reader, resets, pipelining, requests sent one byte at a time) | net calls inside a `par` loop were refused with a misleading message about half the time, when the loop's iteration ran on the main thread; the check now asks OpenMP whether it's inside a parallel region. My first test for closing connections with events still queued **passed even with the fix removed**, because epoll happened to deliver events in a harmless order; it now stops the server and orders the events so that, without the fix, it fails every time |
| 46 | running out of file descriptors, modules, all checks under AddressSanitizer/UBSan | **at the descriptor limit, `wait` spun at 100% CPU** on a listener it couldn't accept from; the listener now pauses until a connection closes (measured: 97 ticks of CPU per second before, 0 after) |
| 47 | half-closed connections, both compilers again | **0** |

`tests/run_net.sh` runs 21 checks, on plain builds and again under AddressSanitizer/UBSan,
with either compiler.

### The JSON benchmark

The second test makes each language do real work per request: `POST /order` with a 5.8 KB
order (`bench/http/order.json`, 30 items, escapes and non-ASCII text). The server parses it,
totals it, and replies with a JSON summary that must match `expected.json` byte for byte
(`check.py` verifies every server before it's timed). Each language uses its standard JSON:
Vu's `json` module (written in Vu, from `examples/json.vu`), Go's `encoding/json`, and
JavaScript's built-in `JSON.parse`/`JSON.stringify`. `TEST=json bench/http/run.sh`. Every
server here used 97–99% of its core, so these numbers measure the servers, not wrk.

| Server | Requests/s | p50 | p99 |
|---|---|---|---|
| **Vu** | **15,679** | **2.74 ms** | **6.15 ms** |
| TypeScript on Bun, `Bun.serve` | 12,258 | 4.14 ms | 6.71 ms |
| TypeScript on Bun, raw TCP | 10,903 | 4.41 ms | 9.33 ms |
| TypeScript on Node 22, raw TCP | 9,543 | 4.81 ms | 9.25 ms |
| Go, raw TCP | 8,409 | 6.03 ms | 15.77 ms |
| TypeScript on Node 22, `http` | 7,328 | 6.44 ms | 23.36 ms |
| Go `net/http` | 6,025 | 8.34 ms | 20.14 ms |

What this does and doesn't show:
- Go's `encoding/json` decodes through reflection and is known to be slow; faster Go JSON
  libraries exist and weren't tried. Rust (serde_json) isn't in the table yet, and on the
  50 MB file earlier it was as fast as Vu.
- Vu's HTTP handling is about 100 lines: no chunked bodies, timeouts, header limits or TLS.
  The raw-TCP servers in Go and TypeScript do the same minimal handling.
- Everything ran on one core, which suits single-threaded event loops.

**Short strings were the cost.** Before this round Vu served 11,316 requests/s. Callgrind on
the parse showed about half the instructions in malloc and free: some 400 calls per order,
mostly short strings (keys, values). Strings of up to 256 bytes now take their buffers from
per-thread free lists by size class (16 to 256 bytes): parsing the order went from 43 to
27 µs, and the server from 11,316 to 15,679 requests/s (+39%). On the 50 MB file nothing
changed: 369 MB both ways, and the same time within noise.

### Memory

`bench/http/mem.sh`: resident memory idle, at the peak of 5 seconds of the JSON test, and
the extra per connection with 5,000 idle keep-alive connections open.

| Server | Idle | JSON peak | Per idle connection |
|---|---|---|---|
| **Vu** | **1.7 MB** | **1.8 MB** | **~0 KB** |
| Go, raw TCP | 6.5 MB | 16.9 MB | 14.4 KB |
| Go `net/http` | 7.1 MB | 13.2 MB | 18.7 KB |
| TypeScript on Bun, `Bun.serve` | 26.6 MB | 39.3 MB | 0.1 KB |
| TypeScript on Bun, raw TCP | 30.9 MB | 49.8 MB | 1.7 KB |
| TypeScript on Node 22, raw TCP | 69.1 MB | 83.1 MB | 2.2 KB |
| TypeScript on Node 22, `http` | 72.1 MB | 91.0 MB | 7.4 KB |

Vu has no runtime beyond a small C library and no garbage collector (values are freed when
their owner goes out of scope), so peak memory stays near the live data. Its server keeps
nothing per connection unless a request is half-received. Go's ~15 KB per connection is
mostly the goroutine's stack. Kernel socket buffers aren't in any of these numbers.

### A memory leak in the node free lists

Checking the new string free lists against `par` loops found an older bug. Each type of
tree node has a free list per thread. When `par` workers built trees and the main thread
freed them, the main thread's list kept growing while the workers carved new nodes: a test
went from 6 MB to 250 MB over 360 rounds, without end. The new string lists had the same
flaw.

- **Nodes:** at the start of every `par` loop each thread hands its free lists to a shared
  pool, and a thread that runs out takes up to 1,024 nodes from it before carving new ones.
  The same test now stays at 4.3 MB. A first version counted nodes on every allocation and
  free; that cost 30% on a parallel tree benchmark and about 20% on binary-trees, so it was
  replaced. The final version costs nothing per operation: binary-trees and the parallel
  tree benchmark run at their old speed.
- **Strings:** in a program with `par` loops, each list keeps at most 4,096 buffers and
  returns the rest to `free`.

`tests/run_memory.sh` runs both cases and fails with either fix disabled. ThreadSanitizer
reports no races in the shared pool, and reports 8 when its lock is removed.

### Rounds 48–49

| Round | Focus | Found |
|---|---|---|
| 48 | the JSON server: bodies by `Content-Length`, pipelined POSTs, requests in 1 KB pieces, mixed-case headers, malformed and oversized lengths, a JSON error followed by a good request; seven servers checked byte for byte against a Python reference | **0** in Vu. One friction for a model that knows Python: a format spec is `{x:.1}`, and Python's `{x:.1f}` is a parse error |
| 49 | the string free lists: every size class, growth across classes, `s += s` at boundaries, reuse across lengths, strings and nodes moving between `par` threads | **the unbounded node free list above** (a bug from an earlier round), and the same flaw in the new string lists |

My own test mistakes this time: a made-up expected hash, a wrong sum, and an attack line
that wrapped onto a second line, which the runner then read as the expectation.

## Round 7: what a production backend needs

Asked what Vu would need to run a real backend service, I listed five things and built them in
this order: calling C, lightweight tasks, outbound connections with timeouts and TLS, types for
errors and data (optionals of any type, typed errors, JSON), and a standard library (time,
logging, an HTTP server and client).

### Calling C

```
extern "sqlite_glue.c":
  link "sqlite3"
  type Db drop vu_db_close
  fn db_open(ffi: Ffi, path: Str) -> Db throws
```

C functions are declared in Vu and their glue is compiled with the program. Calling one needs
the `Ffi` capability, which only `main` can hand out, so a function's signature still shows
everything it can reach. Opaque handles get a destructor and follow the same ownership rules
as other values. `tests/run_ffi.sh` runs 33 checks.

### Tasks

`spawn f(args)` starts a task: a coroutine with its own 8 MB stack (reserved, not touched until
used, with a guard page), scheduled on the main thread (since round 8, on one thread per core:
see "Tasks on every core"). Network calls, `os.sleep` and channel
operations wait without blocking other tasks, so a server is written one connection at a time
in plain blocking style. Channels (`chan(n)`) carry values between tasks; a deadlock is
reported with the line where each task waits. The benchmark server now uses one task per
connection, and serves as fast as the event-loop version it replaced (101.7k vs 96k
requests/s on the hello test).

### Outbound connections and timeouts

`net.connect(host, port)` (DNS runs on a helper thread so other tasks keep going), and every
`accept`, `connect`, `recv` and `send` takes `timeout:` in seconds.

### TLS

`net.tls_connect(host, port, ca:, timeout:)` and `net.tls_listen(port, cert:, key:)` give the
same `Conn` and `Listener` as plain TCP, so `recv`, `send` and `accept` don't change. It's
OpenSSL, linked only into programs that use TLS. Certificates and keys are PEM text, so reading
them from disk still needs `Fs`. The client always checks the certificate and the host name;
there is no switch to turn that off. A server's handshake happens in the connection's own task,
so a slow client can't stall `accept`. OpenSSL's socket layer writes with `write()`, which raises
SIGPIPE when the peer is gone, so Vu gives it a small BIO that sends with `MSG_NOSIGNAL`, as
plain `send` does.

`tests/run_tls.sh` (30 checks, plain and under ASan) uses Python's `ssl` module as the other
side: interop both ways, chains through an intermediate CA, ECDSA keys, SNI, wrong or untrusted
certificates, plain HTTP sent to the TLS port, a silent client, a handshake cut off halfway, a
reset while the server is sending 2 MB, 200 connections at once, and 100 Vu client tasks.

Memory, measured with `bench/http/tls.sh` (1000 idle TLS connections, after one request each):

| Server | Idle | Per idle TLS connection |
|---|---|---|
| **Vu** | **6.6 MB** | **26.2 KB** |
| Go, `crypto/tls` | 7.4 MB | 43.7 KB |

Vu's figure is with `SSL_MODE_RELEASE_BUFFERS`, which hands OpenSSL's buffers back while a
connection is idle (36.6 KB without it), at a cost within run-to-run noise.

Speed, from the same script: `GET /` over HTTPS with keep-alive (50 connections, one core
each, median of three 10 s runs) on a quiet machine: **Vu 80,897 requests/s, Go 76,108**. An
earlier run while the test gate was using the same cores gave 43k and 44k, so this is the
number taken alone. One fix came from looking at it: after each TLS record, `recv` read again
and found the socket empty, one wasted system call per request; it now stops after a short
record with nothing left to decrypt (in the numbers above; its effect alone wasn't measured).

### Types for errors and data

- **Optionals of any type:** `Int?`, `Str?`, `[T]?`... (before, only structs and enums).
- **Typed errors:** `throws E` with an enum `E`, `fail Bad(...)`, and `match` on the value
  (see SPEC, Typed errors).
- **JSON for any type:** `from_json(text, Order)` and `to_json(x)`, with the decoder and
  encoder for each type generated at compile time (see SPEC, JSON).

The JSON benchmark's server now reads the order with `from_json` into four small types and
writes the reply with `to_json`, in 44 lines instead of 65, types included (`bench/http/server.vu`; the
version that walks a tree of JSON values is `server_tree.vu`). Same machine and settings as
before (one core, 50 connections, 3 runs of 10 s, median):

| Server | Requests/s | p50 | p99 |
|---|---|---|---|
| **Vu, `from_json`/`to_json`** | **25,792** | **1.89 ms** | **3.94 ms** |
| Vu, tree of JSON values | 17,858 | 2.60 ms | 6.11 ms |
| TypeScript on Bun, raw TCP | 15,559 | 2.92 ms | 6.89 ms |
| Go, raw TCP | 9,932 | 5.05 ms | 11.85 ms |

The typed decoder is 44% faster than the tree because it builds no intermediate values:
fields go straight into the struct, and fields the type doesn't have are skipped without
being stored. Go and Bun still use their standard JSON (`encoding/json`, `JSON.parse`), which
is how most code in those languages is written; Go has faster libraries that weren't tried.

### The standard library

`std/` holds modules written in Vu, found by `import` when there's no file of that name next to
the importing one (see SPEC, The standard library):

- `time`: UTC dates from `os.time()`, ISO 8601 and HTTP dates, and RFC 3339 parsing. It was
  checked against Python's `datetime` on 20,000 random times from year 1 to 9999.
- `log`: timestamped lines on standard error, or one JSON object per line.
- `http`: an HTTP/1.1 server (request by request, without closures) and client, over TCP or
  TLS. `tests/run_http.sh` runs 64 checks, plain and under ASan. curl works with it too: a
  3 MB upload, a chunked upload, HTTP/1.0, HEAD, and query decoding.

`bench/http/server_std.vu` is the benchmark server written on `http`. The cost of the library,
in instructions per request counted with callgrind (one connection, 2000 requests, so the
counts don't depend on machine load):

| | Hello | JSON order |
|---|---|---|
| `server.vu` (its own minimal HTTP code) | 3,732 | 165,465 |
| `server_std.vu` (`http` module) | 8,700 | 174,802 |

The library does more per request: it checks every header line, lowercases names, enforces the
limits, and builds a `Request` value. Against the JSON work that's 6%. Through wrk on one core (quiet machine, median of three runs):

| Server | Hello req/s | Hello req per CPU-second | JSON req/s |
|---|---|---|---|
| Vu, own HTTP code (`server.vu`) | 121,467 | 148,130 | 25,506 |
| Vu, `http` module (`server_std.vu`) | 132,421 | 147,134 | 23,986 |
| Go, raw TCP | 112,124 | 118,025 | 9,488 |

The hello test is limited by wrk (the servers use 82–95% of their core), so its requests per
CPU-second are the fairer figure: the two Vu servers are the same there. The JSON test, where
each server uses its whole core, shows the library's 6%.

**Interpolating an Int no longer calls printf.** The profile showed `vfprintf` as the biggest
single cost in the std server. A plain `{n}` (an Int or Byte with no format spec) now appends
its digits directly, and other conversions format into a stack buffer in one pass instead of
two. That takes the raw server's hello from 4,771 to 3,732 instructions per request (−22%),
and helps every program that builds strings with numbers.

### Attack rounds since round 49

As before, each feature got targeted attacks until a whole round found nothing. My detailed
notes of the earlier rounds were lost when the session's context was reset, so this table
lists findings by feature rather than by round number.

| Feature | Found |
|---|---|
| Calling C | a forged handle (an integer passed where a handle goes) gave an unclear message; a C function named like a C keyword or with Vu's reserved prefixes (`vu_`, `fn_`, `drop_`) broke the generated C. Both are now compile errors that say why |
| Tasks | **a deadlock report showed one task's line with another task's backtrace**; LeakSanitizer reported false leaks when `main` exited with tasks still waiting (their stacks are now registered as root regions); in pool mode, ASan's fake stacks hid task locals from the leak checker |
| Optionals | list and map literals didn't work where an optional was expected (`let xs: [Int]? = [1]`) |
| Ownership | a value bound by `if`/`match` couldn't be moved out, and the message ("this function only borrows it") was wrong for match bindings; the message now says what happened and `else return` / `else break` / `else continue` were added so the usual fix reads naturally |
| JSON, round 1 | **a module's enum variants were written as `"geo.B"`** instead of `"B"`; `from_json(s, Int?)` didn't parse (the second argument is now parsed as a type, so `Int?`, `[T?]` and `{Str: [geo.Point]}` all work); messages for enums listed the wrong variants; an error deep in nested data built a 15 KB path (now cut to the innermost 200 bytes); a type with no JSON form deep inside a struct didn't say which field |
| JSON, round 2 | **0**: boxed enum variants, places and slices as arguments, `?` hoisted out of `push`, a loop that fails halfway, a `par` loop (clean under ASan, pool mode and TSan) |
| JSON, found by the gate | **two problems both rounds missed**, caught by the gate's audit of the generated C with `-Wall -Wextra`: encoders took `const T *`, which for an optional `T` is an incompatible pointer type (a warning in gcc 13, an error in gcc 14); and a program that used `to_json` but no `from_json` called the float parser without declaring it (also an error in gcc 14). Both fixed, and the audit is now part of every attack round |
| TLS, round 1 | an unhandled `net.tls_connect(...)` said "Net has no .tls_connect()" instead of "can fail, so handle its error" (a second list of net functions didn't have the new names) |
| TLS, round 2 | **0**: chains, ECDSA, SNI, 100 concurrent Vu clients, ASan and pool-mode builds |
| `http`, round 1 | **a header section over 64 KB was accepted when it arrived in one read** (the limit was only checked while waiting for more); HTTP/1.0 keep-alive replies didn't say `Connection: keep-alive`, and HEAD replies carried a body (`reply` now takes the request) |
| `http`, round 2 | **a pipelined request could hang its connection**: after a read moved the buffer, the server waited for a byte count measured from the old start; **reading a request piece by piece rescanned everything each time** (a 60 KB header section sent one byte per read: 2.32 s of CPU before, 0.81 s after); a second `Transfer-Encoding` header was ignored (request smuggling) |
| `http`, round 3 | `Expect: 100-continue` wasn't answered, so curl paused a second before every upload over 1 MB; a request with two `Host` headers was accepted; a connection kept the buffer of its last request while idle (20 connections after 5 MB uploads: 181 MB, now 25 MB) |
| `http`, round 4 | **0** in the module; the round used the new `else fail` in the library itself |

The JSON work is also checked by a differential fuzzer in `tests/run_json.sh`: 12,000
generated documents (byte-level mutations, and well-formed documents with wrong types,
missing, extra and repeated fields) decoded by Vu and by a Python model of the same types,
which must agree on every document, in plain, ASan and pool-mode builds.

`else fail value` was added because I reached for it twice while writing `std/http`: after a
call that can fail, `else` can now also fail the enclosing function, like `else return`.

Frictions noticed while writing the library, not yet changed: `x += f()?` is refused for a Str
`x` but accepted for an Int; a `var` argument needs the whole variable, so `&r.rs` next to
`r.buf` in one call is refused (a `swap` around the call works); a call that returns nothing
can't be written `return f()`.

My own mistakes in these rounds, none counted as findings: a fuzz harness run without the
LeakSanitizer option the suites use, which reported the string free lists as leaks; a model
that accepted numbers too large for a Float; a checker comparing `3e10` with `30000000000` as
text; TSan run with gcc instead of clang and Archer, which reports libgomp's barriers as
races; several expected strings typed by hand instead of computed; test certificates without
the key-usage extensions Python 3.13 requires; a test whose client and server timeouts were
equal, so either could fire first; `else` inside an argument and an interpolation; a
Content-Length overflow I introduced while restructuring (caught before it was tested); and
measuring HTTPS speed while the gate was using the same cores.

## Round 8: generics, closures, tasks on every core, shared values, and one compiler

### One compiler

Every feature used to be written twice, in `vu.py` and in `vuc`, which had to make byte-identical
C. Most of my turns went to the second copy and to keeping the two in step, so the Python
compiler is retired (to `attic/`) and `compiler/*.vu` is the only compiler. It is bootstrapped
from `compiler/vuc_seed.c`, the C it makes of itself (65,000 lines, 3.7 MB), so a C compiler is
all that's needed. `compiler/build.sh` rebuilds it in about 40 s and only installs the result if
it reaches a fixed point. Before closures were added, the full gate passed on the single compiler
(every suite; the one failure was a test written for closures).

`tests/try.sh FILE.vu` now runs the steps every attack test needs (check, a quick run, an
ASan/UBSan/LeakSanitizer run that must print the same, and the C audited with the gate's
warning flags) and prints one summary.

### Generics

`fn largest[T](xs: [T], better: fn(T, T) -> Bool) -> T?` and `type Pair[A, B]:` (see SPEC.md).
Type arguments are inferred from arguments and from the expected type, and each use makes a
separate copy of the function or type, checked on its own. The generic parts of
`tests/targeted/` (410–427), `tests/modules/42_generics` and `43_generic_layout` cover them.

| Round | Found |
|---|---|
| 1 | `match` arms in a generic enum's copies used the wrong name prefix; passing `Fs` or a call that returns nothing gave a misleading inference message; the hint named the wrong type parameter; **a function calling itself with ever bigger types (`f[[T]]` from `f[T]`) took 91 s to be refused** (now: nesting is limited to 32, copies to 2,000) |
| 2 | the expected type didn't reach a generic call through `?` and `else` (`let xs: [Int] = load()?`) |
| 3 | **0** |

### Closures

`fn(x) => x * k` borrows what it captures and can't outlive it; `own fn(x) => x + n` owns
copies and is an ordinary value (fields, lists, maps, channels, `spawn`). Named functions are
values too, and nested `fn name(...):` statements are closures with a block body (SPEC.md has
the rules). A function value is three words (the C function, the captured variables, and the
function that frees them); a call through one is an indirect C call. On a 200-million-step
loop of a dependent multiply and modulo, calling the step function directly, through a named
function value, and through a closure capturing a local all took 0.87 s. gcc can see which
function is called there, so this shows the calls add nothing when it can, not the cost of a
call it can't resolve.

| Round | Found |
|---|---|
| 1 | **a closure that returned a borrowing closure (`fn() => fn() => k`) returned a pointer into its own stack frame**: its result type was inferred as the borrowing type, so nothing refused it; **a list or map literal of borrowing closures made a list that could outlive them** (it was only refused later, by a mismatch reading "expected [fn() -> Int], found [fn() -> Int]"); a generic call couldn't infer `T` from a closure passed for a plain `T` parameter; copies of generics made for function types were shown by their C names (`ident.G12_FP1_3_IntInt`); a closure as a `const` was accepted and then reported as an unknown function. Messages: a closure's arguments were named `'#1'`, `?` in a closure said "a function marked throws", and a closure for `fn()` whose body is a value said "this line computes a value" |
| 2 | **`spawn f(x)`, where `f` is a local closure, would have spawned the top-level function named `f`** instead (found reading the code; the test only showed a misleading message). Now an error that says how to run a closure in a task |
| 3 | a borrowing closure given an optional type got a type-mismatch message instead of the one that explains borrowing |
| 4 | **0**: closures in generic structs and maps, typed errors passed on through a closure field, function values of functions taking capabilities, extern signatures |

47 targeted tests cover closures (428–474), each run under ASan, UBSan and LeakSanitizer and
audited with `-Wall -Wextra`. One rule is stricter than it needs to be: a closure inside a
`par` loop can't capture the list the loop splits, even if it reads only its own element.

Frictions from writing the closure code in Vu itself, not yet changed: `throws` is a keyword,
so it can't be a field name; `m.get(k, default)` refuses Str values; and passing a Str
variable to a struct literal moves it, so `oty + ""` is needed to keep using it.

### Tasks on every core

Tasks used to share the main thread. Now there is one task thread per core the program may use
(it follows `taskset`; `VU_THREADS=n` overrides it), each with its own scheduler, poller and
timers. New tasks go to the threads in turn and stay on theirs, so a task's thread-local state
(its call stack for backtraces, its allocator free lists, OpenSSL's error queue) never changes
under it, and the code generated for tasks didn't change. What threads share is locked or atomic:

- channels have a lock, and waking a task on another thread puts it on that thread's queue and
  signals the thread's eventfd if it's asleep in `epoll_wait`;
- a socket is watched by the poller of the thread whose task last waited on it, and moves when a
  task on another thread uses it; the waiting task and the pollers hand off through atomics, so
  readiness that arrives just before a task starts waiting isn't lost;
- a socket freed while another thread's poller might still hold an event for it is freed only
  after every poller has finished the batch of events it was handling;
- deadlock detection counts the tasks that can still run, across all threads;
- `print` and `eprint` write each line in one piece.

| Measured (2 vCPUs, quiet machine) | 1 thread | 2 threads |
|---|---|---|
| 8 tasks, each 50 M steps of an LCG, results over a channel | 1.14 s | 0.57 s (2.0x) |
| HTTP hello, `bench/http/mc.sh` (median of 3 × 10 s, wrk -t2 -c50 on the same 2 cores) | 125,747 req/s | 147,173 req/s |
| HTTP JSON (5.8 KB order parsed, totalled, answered) | 25,934 req/s | 59,335 req/s |

Go on the same runs: raw TCP hello 121,664 (GOMAXPROCS=1) and 125,786 (2); JSON 10,167 and
21,393; `net/http` with GOMAXPROCS=2: 53,771 hello and 14,966 JSON. On two cores wrk competes with
the server for the same cores, so these show how each scales, not its peak; the JSON gain past
2x for Vu is likely an artifact of how the two wrk threads and the server's threads share the
cores, not something to expect elsewhere. The single-core numbers above (Results) are unchanged:
`bench/http/run.sh` pins each server to one core, and Vu then starts one task thread.

| Round | Found |
|---|---|
| 1 | **values freed on a thread whose task never waits piled up**: a task receiving boxed values from another thread kept their nodes on its own free list while the sender carved new ones (158 MB after 200,000 messages; now a list past 4,096 nodes goes back to the shared pool: bounded, and `tests/memory/tasks_cross_thread.vu` checks it); the thread count ignored `taskset`, so a server pinned to one core ran two task threads on it; **the DNS helper thread could write to its eventfd after the task had closed it and freed the lookup** (a race that predates multi-core: the helper was always a real thread), and my first fix of it lost the wake-up instead (lookups timed out); a socket made from a dup'ed eventfd stayed in the epoll set after it was closed, so a later event could name freed memory (found reading the code; sockets now leave the epoll set explicitly); the remote queue's head was read atomically but written plainly (reported by ThreadSanitizer, harmless on x86-64, fixed). **And the test suite's ThreadSanitizer checks had never run**: `run_targeted.sh` passed the suppressions file by a relative path after changing directory, so every TSan run exited at startup and counted as clean. Fixed; all 38 par and spawn programs with output now pass under TSan for real |
| 2 | **0**: tasks spawning tasks from every thread (a 4,095-task tree), a deadlock reached by the last sender exiting, a listener accepting on a worker thread, `eprint` from 16 tasks, under ASan and TSan 5 times each |
| 3 | **0**: a sender blocked on a full channel while the only receiver sleeps on another thread, and 40 runs each of the producer, ping-pong, close, timeout and sleep tests in optimized builds looking for a false deadlock or a hang |

`tests/run_mt.sh` runs every task program with output 10 times under ThreadSanitizer and 10 times
optimized, and checks that 16,000 lines printed by 8 tasks at once all arrive whole. The network
suites (`run_net.sh`, `run_tls.sh`, `run_http.sh`) now also run under ThreadSanitizer.

### Shared values, signals, and stopping gracefully

`share(v)` makes a `Shared[T]`: one value that tasks on every thread read at once, with no locks,
because nothing can change it (writes, `push`, `&`, `var` bindings and moves out of it are compile
errors). It's freed with its last handle. That's what a server needs for its configuration and,
with closures, for its handler: `http.serve(net, os, port, handler, grace)` is now in the standard
library. It runs one task per connection on every core, and on SIGTERM or SIGINT stops accepting,
lets requests in progress finish, closes idle connections, and returns. Under that, `os.signals()`
delivers SIGTERM, SIGINT and SIGHUP on a channel instead of ending the program, and `ch.closed()`
lets one closed channel tell many tasks to stop.

`run_http.py` checks the graceful stop with both signals: a request in progress gets its whole
answer, an idle keep-alive connection is closed, new connections are refused, and the server returns
(exit 0); a request that never finishes is given up after the grace period. Stopping a server
built on `http.serve` under wrk load (50 connections) took 0.08 s from SIGTERM to exit. The hello
benchmark's `server_std.vu` rewritten on `http.serve` (pinned to one core, 3 runs of 5 s each) did
155k, 177k and 116k requests/s against 167k, 115k and 144k for its own accept loop: no difference
this machine can measure (runs vary by about 25%).

| Round | Found |
|---|---|
| 1 | **watching for signals turned deadlock detection off for the whole program** (my first design counted the signal thread as a task that could always wake someone, so a task stuck on any other channel hung silently). Now only a task waiting on the signal channel itself counts as wakeable; the message for a borrowing closure in a `Shared` value talked about connections |
| 2 | **0**: `if var`, `for var`, `match var`, `swap` and a generic function reaching into a `Shared` value (all refused), a channel kept in a `Shared` value used from every thread, a tree of `Shared` nodes sharing a leaf read by 10 tasks, optional and generic `Shared` fields, 40 signals at once, a stop under load |

My own mistakes in these rounds, not counted: a test of `closed()` whose tasks never waited, so it
hung (a task that never waits keeps its thread, as SPEC.md says); and, worse, a change I made to
`tests/gate.sh` that read the suites' exit codes wrongly, so a failing suite could still print
GATE PASSED. One `run_debug.sh` check failed once in that run, while my hung test was using both
cores; it passed in 3 reruns. The gate now fails on any suite's failure again.

## Round 9: what was missing for real services

The list after round 8, in order: the slowdowns, interfaces, Unicode text, packages, a PostgreSQL
client; then ARM64 and macOS, `vu fmt`/`vu test`/`vu lsp`, tasks that move between threads, hashing,
regular expressions, paths, argument parsing, WebSockets and HTTP/2.

### Language

- **Interfaces** (`interface Shape:` / `impl Shape for Circle:`): calls are resolved at compile time
  when the type is known, through a table of functions when it isn't (`[Shape]`), and generic
  bounds (`[T: Shape]`) check that a type implements one.
- **Text as UTF-8**: `upper`/`lower` with Python's full case mapping (Unicode 15.1 tables),
  `chars`, `char_count`, `ord`, `chr`, `find`, `count`, `replace`, `sub in s`, `is_utf8`, each
  checked against Python on random text.
- **`opt else default`** reads an optional the way `else` already handled a failing call, with the
  same ways to leave (`else return`, `continue`, `fail`, `panic`); and `else` now works inside
  arguments, parentheses, list and map literals and interpolations. I added it because I kept
  writing it while building the standard library in this round (four times before it existed),
  which is the best evidence I have that an agent will too.
- **`x in xs`** for lists of numbers, Bools and strings.
- **`const` parameters**: the argument must be text written in the program. `pg.query` takes its
  SQL this way, so SQL built from input doesn't compile.
- Hashing and encoding built-ins (SHA-256, SHA-1, HMAC, PBKDF2, random bytes, base64, hex), `fs.list`,
  `mkdir`, `exists`, `remove`, `rename`, `os.output`, `os.read_stdin`, and `assert`.

### Tools and packages

- **Packages**: `vu.pkg` lists sources (any git URL or a folder) and versions; `vu get` fetches them
  and writes `vu.lock` with each package's commit and a SHA-256 of its files, which every build
  checks. A package only gets the capabilities its line grants (`fs net os ffi`), and an `extern`
  block needs `ffi`, so a dependency that starts reading files stops the build until you allow it.
- **`vu fmt`**, **`vu test`** (each `fn test_...` in its own process), **`vu lsp`** (diagnostics
  and formatting for editors).
- **Machines**: Linux on ARM64 (the whole targeted suite under qemu) and macOS on ARM64 and x86-64
  (built with zig's cross compiler, linked except for TLS; not run on a Mac yet).

### Standard library

`pg` (PostgreSQL: SCRAM sign-in, parameters only), `re` (Python's syntax and results in linear
time), `path`, `cli`, `ws` (WebSockets), and HTTP/2 in `http` (prior knowledge, and ALPN over TLS).
`re` is slower than Python's C engine on ordinary patterns: `findall` over 870 KB of text took
0.18 s for `[a-z]+` (Python 0.07 s) and 0.20 s for `\w+@\w+\.com` (0.055 s), and 0.028 s for
`(\d+)` (0.051 s); skipping to bytes a match can start with made it 1.4–8x faster than it first was.

### Tasks that move

A thread with nothing to do now takes new tasks (ones that haven't started) from a busy thread.
Measured with 200 short tasks queued behind one that computes for 0.9 s on a 2-core VM: they all
finish after 0.28 s with this, and after 1.03 s without (`tests/mt/steal.vu`, which checks the
order in `run_mt.sh`). Only tasks that haven't started move: a C compiler may keep the address of a
thread-local variable in a register across a call, so a task stopped partway through a function
must resume on its own thread. ARM64 showed this; x86-64 had hidden it.

### The slowdowns

`bench/compare.sh` again, same 2-vCPU VM (about 10% slower than in round 8 for every language), median
of 5, seconds:

| | binary-trees 20 | n-body 50M | fannkuch-redux 11 | nsieve 13 | mandelbrot 8000 (2 threads) | spectral-norm 8000 (2 threads) |
|---|---|---|---|---|---|---|
| C | 12.32 s, 130 MB | 3.47 s | 2.90 s | 4.95 s | 2.90 s | 2.38 s |
| C++ | 12.62 s, 132 MB | 4.89 s | 3.52 s | 2.06 s | 2.87 s | 2.04 s |
| Rust | 13.84 s, 130 MB | 2.78 s | 3.30 s | 4.92 s | 2.89 s | 2.53 s |
| Go | 24.94 s, 223 MB | 5.48 s | 3.28 s | 4.80 s | 2.94 s | 3.46 s |
| Vu | 4.06 s, 66 MB | 4.84 s | 3.50 s | 4.75 s | 2.84 s | 3.69 s |

Against C, n-body went from 1.73x to 1.39x, fannkuch-redux from 1.35x to 1.21x and spectral-norm
from 1.77x to 1.55x: a list index check had grown from one unsigned comparison into two, and gcc
couldn't tell that lengths are far below 2^63 (now it's told). What's left, measured by building
Vu's generated C with one thing taken out (3 runs each):

| | as built | without | C |
|---|---|---|---|
| spectral-norm, without overflow checks | 3.29 s | 2.30 s | 2.38 s |
| fannkuch-redux, without bounds checks | 3.50 s | 2.86 s | 2.90 s |
| n-body, with fused multiply-add | 4.6–4.8 s | 3.9 s | 3.47 s (4.49 s without) |

So each remaining gap is one of Vu's choices: checked integers (they keep gcc from vectorizing
spectral-norm's inner loop; round 3's measurement of their cost didn't include spectral-norm),
checked indexing, and no fused multiply-add, so a program gives the same results on every machine.
Taking the overflow checks out of fannkuch-redux saves 3%, and neither check matters to n-body.
A way to keep the checks and still vectorize would be to check a loop's arithmetic once at its end
when the loop has no other effects (the program stops either way); that's not done yet.

### What the attack rounds found

My own mistakes in tests aren't counted here; these are bugs in Vu.

1. **`std/h2` didn't compile, so no HTTP program did** in the working copy, from when HTTP/2 was
   added until the first build of this batch (an unreachable `return`). The gate would have caught
   it; nothing shipped with it.
2. **ARM64 task switching was broken**: GCC ignores the `naked` attribute on ARM64 (with a warning
   that `-w` hid), so the switch function got a prologue that corrupted the stack. Every program
   that spawned a task crashed there. Now it's a plain assembly function, and `run_arm64.sh`
   compiles the runtime with ignored attributes as errors.
3. **Moving started tasks between threads was unsafe** (above): five multi-threaded tests crashed
   on ARM64 (a double free among them).
4. **Work stealing missed most of the work**: tasks spawned from another thread wait in the busy
   thread's inbox, which it never reads while busy, and the stealing code skipped a thread whose own
   queue was empty. Measured before the fix: no difference at all with and without stealing.
5. **Every `vu build` and `vu run` left a folder in `/tmp`** with the generated C (and, for `run`,
   the binary), since the first version: about 97,000 of them on the test machine. Now removed on
   every way out. (`vu test` left one too.)
6. **HPACK bomb**: a 16 KB HTTP/2 header block of references to one 4 KB header would have decoded
   to 64 MB before the size check; now decoding stops at 64 KB.
7. **HTTP/2 request bodies**: 100 open streams could each buffer 10 MB (1 GB per connection); now
   20 MB in all. Also: stream window overflows weren't errors, request trailers closed the
   connection, empty CONTINUATION frames could arrive forever, and a response with a line break in
   a header closed the whole connection instead of resetting its stream.
8. **The ALPN list of a TLS listener leaked** (14 bytes per listener, and on error paths).
9. **macOS didn't compile**, though SPEC said it did: a Linux-only call, a `pipe2` that newer SDKs
   declare, and a weak OpenMP symbol Mach-O can't leave undefined.
10. **`re`**: a pattern starting with `\b` gave up after the first position; loops whose body can
    match nothing gave different groups from Python (now the same on 10,000 random patterns);
    `a{1,2}{3}` was accepted (Python refuses it) and possessive repeats were read as nested ones.
11. **The WebSocket test's "server hangs"** turned out to be the Python client: `websockets`'
    threaded client loses its handshake over TLS now and then, against its own server too. The Vu
    server handled 6,000 TLS upgrades in a row with the asyncio client. Not a Vu bug, but it took
    a while to show that, and my extra logging created a second, fake hang (a full stderr pipe).
12. **Two races in the new scheduler code** (ThreadSanitizer, in the gate): the `started` flag was
    read by other threads without atomics, and after handing a task to another thread, the waker
    read the task's fields, by which time that thread could have run it and freed it.
13. **`vu get` would have run commands from a dependency**: a source like `git+--upload-pack=...`
    in any package's `vu.pkg` reached `git clone` as an option. Now only https, http, ssh, git and
    file URLs are accepted, after `--`, with git's `ext::` transport off.
14. **A version could lead outside the package cache**: `v1/../../somewhere` passed the version
    check and named the folder `vu get` cloned into, deleted (`rm -rf`) and renamed onto. Versions
    are now `v` with digits and dots and an optional `-suffix`, also when read back from vu.lock.
15. **Symbolic links in a package** made the hash walk recurse forever (a link to its own folder)
    or read files outside it; `vu get` now refuses packages that contain any.
16. **`pg` against a hostile server**: a short data or row-description message crashed the client
    program (an index out of range) instead of failing the query; after a protocol error the
    connection stayed usable, so the next query could read the previous one's leftovers as its
    results; a server could skip proving it knows the password once SCRAM had started; and any
    server could ask for the password in clear text and get it (now only with `allow_plain`).
    `tests/run_pg_hostile.py` is a fake server that tries each.

The last round (optional elements of lists and maps, `else` in `par` loops, `const` through
interfaces, generics and interpolation, `re` patterns that match nothing, compared before and
after its speed-up on text that isn't UTF-8) found nothing.

## Round 10: regular expressions as fast as Python's

`std/re` was 2.6 to 7 times slower than Python's `re` on ordinary patterns. Python's is a
backtracking engine in C; Vu's ran every match through a Pike VM written in Vu, which is what keeps
matching linear in the text (a pattern like `(a|a)*b` takes Python exponential time, and Vu 0.03 s on
30,000 characters). Now it works as RE2 does, still linear:

- **Two DFAs and a reverse one, built by `re.compile`.** The forward DFA's states are the VM's
  ordered thread lists, so it finds where the leftmost-first match ends, as the VM would; the
  reversed pattern, run backwards from there, finds the leftmost position the match can start at,
  which is where it starts. Assertions (`^ $ \b \B \A \Z`) are part of the states: each carries
  what's on the side already read (the text's start, a word character or not; backwards, the text's
  end or a final newline), and the next symbol includes "a newline that ends the text" for `$`. After
  an empty match, Python's rule (no second empty match there, and the threads after it not cut off)
  has its own transitions for the first step.
- **Groups**: none (`\w+`) or groups around the whole pattern (`(\d+)`): nothing more to do;
  groups at fixed places (`(\d{3})-(\d{4})`): counted off in characters; others: a backtracking
  search over the match alone that never visits an (instruction, position) twice (RE2's bit state).
- **Skipping ahead**: to the next place the text every match starts with occurs (`memmem`, through a
  new `s.find(sub, start)`), or else the next byte a match can start with.
- Loops whose body can match nothing (`(a*)*`), and patterns whose DFAs would pass 50,000 table cells
  (`(a|b)*a(a|b){12}`), keep the VM. Building the DFAs takes up to about 50 ms (that worst case:
  when the limit is reached); ordinary patterns compile in 0–5 ms.

Same 870 KB of text, best of 3, seconds (Python 3.13, `re.ASCII`):

| | `findall` Vu | Python | | `search`, no match in 3.5 MB | Vu | Python |
|---|---|---|---|---|---|---|
| `[a-z]+` | 0.038 | 0.040 | | `qqq` | 0.0016 | 0.0018 |
| `\w+@\w+\.com` | 0.009 | 0.027 | | `\d{5}` | 0.0095 | 0.0709 |
| `(\d+)` | 0.008 | 0.048 | | `x\w+y` | 0.0029 | 0.0042 |
| `(\w+)@(\w+)\.com` | 0.029 | 0.043 | | `(alpha\|beta)\s+zz` | 0.0214 | 0.0447 |
| `\b\w+\b` | 0.025 | 0.038 | | `\bzeta\b` | 0.0025 | 0.0501 |
| `[a-z]*` | 0.066 | 0.077 | | `[A-Z]{3}` | 0.0054 | 0.0663 |
| `\d{1,3}` | 0.006 | 0.021 | | `é` | 0.0037 | 0.0011 |
| `(?:alpha\|beta\|gamma)\w*` | 0.011 | 0.016 | | | | |
| `[^ \n]+` | 0.021 | 0.030 | | | | |
| `.` | 0.117 | 0.079 | | | | |
| `(a)(l)(p)(h)(a)` | 0.014 | 0.007 | | | | |
| `^\w+`, `a$`, `e-?mail`, `x1\|delta` | 0.000–0.006 | 0.000–0.008 | | | | |

Before: `[a-z]+` 0.18 s, `\w+@\w+\.com` 0.20 s. Vu is behind on `.` and `(a)(l)(p)(h)(a)`, where
each match is one or a few characters and CPython hands back the same cached string objects for
one-character strings while Vu makes new ones, and on the two-byte literal `é`.

What the testing found, in my new code: the backward search started without knowing it was just
before a final newline, so `$` there failed and `(.)*$` found no start; the capture pass's fallback
didn't apply the after-an-empty-match rule, which made `finditer` loop forever on `\b(\.*?)`; and the
first version's transitions always cut threads at a match, wrong right after an empty one (72 random
patterns disagreed with Python). All three were caught by the comparison with Python, which now
agrees on all 17,507 random patterns and texts of 7 seeds (on two more seeds, the 4,997 cases Python
could finish agreed; on 3, Python's backtracking ran past 2 seconds), and the new code gives the same
results as the VM-only version on 5,260 cases over text that isn't UTF-8. `finditer` now also refuses a match that doesn't move on,
so a disagreement can't turn into a loop again.

## Round 11: the checks stay, the loops get fast

Vu checks every list index and every Int operation, and those checks were what kept three
benchmarks 1.2–1.6x behind C (README.md, before this round): spectral-norm's overflow checks kept gcc
from vectorizing its inner loop, fannkuch-redux paid for bounds checks, and C's n-body used fused
multiply-add, which Vu leaves out. This round keeps every check and makes them cheap where it matters:

- **Hoisted index checks.** When a range loop's counter indexes a list the loop can't resize
  (`xs[i]`, `ys[i + 1]`), or any loop uses a constant index (`xs[0]`) or the two sides of
  `while lo < hi` that only move toward each other by one, one comparison before the loop checks
  every such index for every pass (in 128 bits, so bounds near the largest Int are exact). If it
  holds, a copy of the loop runs with those elements read and written directly; if not, the checked
  copy runs and stops where it always did.
- **Tried loops.** A range loop that only computes numbers (it assigns scalar variables, reads
  lists, and calls only functions that do the same) first runs as a copy whose checks record
  failures in a flag instead of stopping (`vu_vf_add` and the rest in the runtime): they don't
  branch, so gcc vectorizes the loop. If the flag is set at the end, the variables the loop assigned
  are put back and the checked copy runs from the start, so the program stops at the same check with
  the same message and line. A product of two operands over 2^31 counts as a failure in the tried
  copy (vectorized code can't check it exactly), so the checked rerun decides; a loop whose try
  failed once isn't tried again. Functions such loops call get tried copies too (`fn_a__vf`), never
  for recursion. A tried copy whose C does anything but the deferred checks, math and other tried
  copies is thrown away when it's generated, and an inner loop doesn't start once the flag is set,
  so a wrapped value can't make it run for ages.
- **`fma(a, b, c)`**: `a * b + c` rounded once, the same on every machine. Float math is still never
  fused unless a program asks; the n-body example now asks where C's compiler fuses by itself.
- `VU_NO_VERSIONING=1` turns the copies off, and `tests/run_loops.sh` uses it: 300 random programs
  (loops with overflowing arithmetic, out-of-range offsets, division by zero, shifts, calls,
  two-pointer loops, break and continue), built both ways, must print the same and stop the same
  way. It's in the gate.

The same programs, the build before this round against this one, run back to back (median of 5):

| | before | after | C (`bench/compare.sh`) |
|---|---|---|---|
| spectral-norm 8000, 2 threads | 3.23–3.30 s | 2.39–2.45 s | 2.45 s |
| n-body 50M | 4.47–4.58 s | 3.55–3.69 s | 3.16 s |
| fannkuch-redux 11 | 3.40–3.43 s | 3.10–3.26 s | 2.85 s |

mandelbrot's hot function compiles to the same C as before (2.91 s before and 2.93–2.97 s after,
which is noise), and binary-trees and nsieve have no loops these apply to. The compiler's own C grew
from 88,327 to 95,913 lines, and its release build takes 67.8 s instead of 64.0 s (one run each);
`vu check` didn't change measurably (0.42–0.48 s both).

What's left: fannkuch-redux's flips index the list by values read from it (`perm[0]`), which no check
before the loop can cover. Unchecked by hand, the flip loop with that read gives 2.75–2.9 s, but a
precheck before each flip costs as much as it saves (flips are a few swaps each). Rust (3.26 s) pays
the same. n-body's remaining gap to C (3.56 s against 3.16 s in the comparison) wasn't investigated.

Attack rounds, each against the compiler before this round (same output, stderr and exit status) or
against this one with `VU_NO_VERSIONING=1`:

1. 15 programs aimed at the tried copies (overflow, a false failure that must not double a total,
   division by zero, an index the counter doesn't bound, a negative offset, a list resized in the
   loop, bounds near the largest Int, break, a wrapped inner-loop bound, calls, var parameters,
   int() of NaN, shifts by 64, par loops): all the same. Found: a tried copy using an `INT64_C`
   literal was thrown away (a missed speedup, not a wrong result). My own mistake: an inner loop
   bound of 2^62 that doesn't overflow (it would take as long without the change).
2. 15 more (views, lists passed to functions, nested lists, Str and struct elements, maps, par loops
   with split lists, four nested loops, continue, `..=` and `by`, mutual recursion, early returns,
   big bodies, generics and `?`, Bytes, NaN): all the same. Found: a list indexed by anything other
   than the counter wasn't hoisted at all (a missed speedup). My own mistakes: a `swap` the checker
   refuses, and two expected values.
3. 400 random programs against the old compiler, with about 2.4 tried and 1.5 hoisted loops each:
   all the same.
4. Modules, nested functions, a generic function, tasks on several threads, and clang's warnings on
   the new C: nothing found.
5. 420 random programs, versioning on against off: nothing found.
6. Two-pointer loops added to the generator: 103 of them hoisted in 150 programs, the same as the
   old compiler on the 129 it can build (the others use `fma`), and 600 more versioning on against
   off: nothing found.

The full gate then found two more. In my code: the tried-read helper declared its zero element as
`const T *`, which for a list of pointers made the pointed-to values const instead of the element, a
C warning in 11 programs (gcc -Wall). Not in this change: a task's panic could end the program with
status 0 when `main` returned at the same moment, because `main` returning didn't wait for a panic
report in progress the way `exit()` does (test 347 failed once, under load). Both fixed.

Targeted tests 610–628 keep these cases.

## Memory safety evidence

- `tests/reject/`: 21 programs, each containing a bug Vu must refuse: use after move, a
  value moved on only some paths, a move inside a loop, iterator invalidation, aliased
  mutation, returning a borrowed value, freeing a node while it's borrowed, nil
  dereference, uninitialized variable, hidden mutation, writing to an immutable value,
  mixed number types, missing return, four data races in `par` loops, a forged and a
  missing file capability, an out-of-range Byte, and changing a string in place. Each
  fails to compile with a specific message.
- `tests/panic/`: out-of-bounds indexing and slicing, division by zero, Int overflow and
  Byte overflow stop the program with a message and exit code 101.
- `tests/valid/`: four programs with exact expected output, covering ownership, strings
  and files, `par` loops, and the formatting features.
- AddressSanitizer, LeakSanitizer and UBSan (`--san`) report nothing for the valid tests,
  binary-trees, spectral-norm and mandelbrot. To check that LeakSanitizer would catch a
  mistake, I deleted one generated `drop` by hand and it reported the exact 32-byte leak.
- ThreadSanitizer (`--tsan`) reports no data races for the threaded programs, in three
  runs each. Making it trustworthy took three adjustments:
  - It needs clang's OpenMP library with its Archer add-on (`OMP_TOOL_LIBRARIES=.../libarcher.so`).
    With gcc's library, a correct program and a racy one both showed 2 "races".
  - `tests/tsan.supp` silences reports raised inside the OpenMP library's own
    uninstrumented memory allocator.
  - `--tsan` builds use a static schedule, because the dynamic schedule's chunk hand-off
    looks like synchronization to TSan and can hide real races.

  With all three, a race I injected into generated code (every iteration writing
  `out[0]`) was reported in all three runs, pointing at the exact line.

### Targeted attacks on the checker

`tests/targeted/` holds 70 programs, each aimed at a specific place where I suspected the
checker or code generator could be wrong. Each states what it attacks and what must
happen: rejected at compile time, or run with exactly the expected output and no sanitizer
report. Run them with `tests/run_targeted.sh`.

Run against the compiler as it was, 6 were blocked and 2 got through:

1. **Real memory bug, now fixed:** `show(xs[0], grow(&xs))` compiled. The generated code
   computed a pointer to `xs[0]` before evaluating `grow`, which enlarged the list and
   moved its storage, so `show` read freed memory (AddressSanitizer: heap-use-after-free).
   The aliasing rule only compared a call's arguments directly with each other. Now a call
   is rejected if any argument changes (through `&x` or `.push`) a variable that another
   argument is passed by reference.
2. **Infinite loop, now fixed:** a loop counter stepping past the largest Int wrapped
   around and the loop never ended. Range loops that could step past the end now stop
   instead; the common `0..n` form can't overflow and keeps its fast code. `par` loops
   count their iterations up front instead.

After the fixes all 8 pass, the 30 earlier tests still pass, ThreadSanitizer still reports
no races, and benchmark times are unchanged within noise.

**Second round: 21 more attacks (09–29).** First I went through the code generator for the
same bug pattern as #1: a pointer computed, then other code run before it's used. That
predicted two holes. Then I ran the attacks against the unfixed compiler:

| Attack | Before the fix | Now |
|---|---|---|
| 12 An index expression grows the list (`names[0] += names[g(&names)]`) | accepted | rejected: indexes can't change variables |
| 25 A function returns an `Fs` it was never given | accepted | rejected: only a function given a capability can return one |
| 27 `[0] * n` where n × 8 bytes wraps to a tiny size | **wrote past the end of the buffer** (UBSan) | stops: "too large" |
| 28 Freeing a 3-million-node chain | **crashed: stack overflow** | frees with a loop; works |
| 29 Borrow a value in one argument, move it in another | (found by the code review) | rejected |

The other 16 were already blocked or ran correctly: moves in `and`, `while` conditions and
`if v = ...` subjects, moving out of a field, returning a binding into a temporary,
`break` with live bindings, changing a bound value through a function, order of
evaluation in constructors, list literals and interpolation, `par` with the same element
passed twice, nested lists, strings, the `.len` shortcut under a lock, capabilities
stored in structs, and `INT64_MIN / -1`. Three of those initially failed because my tests
were wrong (one moved a field instead of a whole value, one had a miscalculated expected
output, one used `Int`, which is copied and so can't alias); I corrected them.

Freeing chains with a loop costs nothing measurable: binary-trees 2.66 s against 2.60 s.

| Attack | Result |
|---|---|
| Borrow `xs[0]` while another argument grows `xs` | rejected (was accepted: use-after-free) |
| Move a value, then `continue` into the next iteration | rejected |
| Hold a binding into a list element, then empty the list | rejected |
| `s += s`, `xs.push(xs[0])`, grow a list while appending to its element | runs correctly, sanitizers clean |
| `par` loop reads the whole list its iterations write | rejected |
| `par` loop writes a list an enclosing loop is reading | rejected |
| Fake file access with a look-alike type | rejected |
| Loop counters stepping past the largest Int | stops correctly (was an infinite loop) |

### Rounds until a round finds nothing

I kept going in rounds, fixing what each found, until a whole round found no real
problem. Each round mixed a review of the code (to predict where bugs were) with attacks
run against the unfixed compiler. Mistakes in my own tests are not counted.

| Round | Focus | Real problems found |
|---|---|---|
| 1 | checker rules | 2: use-after-free through a borrowed argument; infinite loop on counter overflow |
| 2 | evaluation order, moves, capabilities, limits | 5: index that grows its list; capability from nowhere; `[v] * n` heap overflow; stack overflow freeing long chains; borrowed value moved in the same call |
| 3 | runtime library, deep nesting | 4: null pointer passed to `memchr` for an empty path; stack overflow for chains alternating between two types and for structs nested through lists; command-line number silently clamped |
| 4 | double evaluation, printing | 3: NUL byte cut `print` short; side effects ran twice in `write()` arguments and in `if v = ...` subjects |
| 5 | compiler edges, generated names | 5: format width/precision overflow; compiler crash on deep nesting; colliding C field names; struct named `Cap` colliding with generated names |
| 6 | compiler robustness (50 malformed programs), names | 2: `_` variable's C name could collide with a user name; float literal silently became infinity |
| 7 | compiler performance, identifiers | 3: exponential compile time on long `+` chains; long expressions hit Python's recursion limit; non-ASCII names (look-alike "homoglyph" risk) |
| 8 | sanitizer coverage | 1: `panic()` with a message over 2 GB could overflow `printf`'s length argument. Also closed a test gap: Vu's own node allocator had never run under AddressSanitizer. Freed nodes are now poisoned and every program also runs in that mode (`--san-pool`). No bugs found there. |
| 9 | warnings audit, differential testing, `par` combinations | **0** |
| 10 | new: enums, errors, maps (25 attacks) | 1: recursion with input-controlled depth died from a signal |
| 11 | maps in `par`, `match` in `par`, self-moves, compaction (12) | **0** (one usability fix) |
| 12 | features added for the JSON parser (9) | 1: the shortest-float printer was wrong for subnormal numbers (`5e-324`) |
| 13 | map lifetimes, deep trees through maps, errors in fallbacks (7) | 1 (usability): reading `m[s[0..2]]` was rejected |
| 14 | attacking the round-13 fix (5) | 1: **double free.** Reading an owned value through a computed key handed out the map's own list as a copy. Found before it shipped; owned values now need the key in a variable |
| 15 | computed keys, capabilities in maps and enums, map typing (7) | **0** |
| 16 | the memory changes: key moves, boxed payloads (11) | 1: the last-use check rescanned the rest of the block at every insert, so 4,000 inserts took 2 minutes to compile. Now it makes one pass (0.4 s), and attack 146 checks the front-end time |
| 17 | borrowed keys, key moves in `par`, boxed payloads through optionals and error results (4) | **0** |
| 18 | `for k, var v in m`, slice parsing, exact-size strings (11) | **0** |
| 19 | the JSON-gap changes: small maps, float parsing, reserve, cheaper checks (10) | **0** |
| 20–21 | features added for self-hosting: `pop`, `exit`, `args`, `eprint`, `Os`, `swap`, the Str copy rule, let views (attacks 172–198) | counts weren't kept in my notes; every attack passes |
| 22 | `vu.py` against `vuc`: lexer and parser edges, 25 files written to make the two disagree | 5: `0x_` crash; Unicode digits and spaces accepted; interpolation errors on line 1; recursion limit on long chains |
| 23 | `vu.py` against `vuc`: literals at their limits, escapes, C-name collisions, deep types (33) | **0** |
| 24 | let views, `swap`, `pop` and `exit` together (20) | **0** memory bugs; 1 usability fix: writing through a view suggested `var v`, which is itself an error. It now explains what a view is |

Round 9 checked:
- **Warnings audit:** gcc and clang with full warnings, including the evaluation-order
  checks, over the generated C for 38 programs. Nothing beyond harmless style warnings.
- **Differential testing:** the same 38 programs built 5 ways (gcc -O0, gcc -O3,
  clang -O3, and two malloc builds), with identical output from every build.
- **5 new attacks** on `par` loops with bindings, `continue` and panics, and deep
  freeing inside threads.

All 70 attacks (`tests/run_targeted.sh`) and 30 tests (`tests/run_tests.sh`) pass. The
tests that run programs do so under AddressSanitizer, LeakSanitizer and UBSan, with both
malloc and Vu's allocator; `par` programs also run under ThreadSanitizer.

Rounds 10–15 covered the round-4 features. Round 14 is the reason to keep attacking
fixes: my round-13 usability fix introduced a double free, and only a deliberate attack on
that fix found it. Current totals, all passing:

| Suite | Checks |
|---|---|
| `tests/run_tests.sh`: reject, panic and exact-output tests (including every example in SPEC.md) | 34 |
| `tests/run_targeted.sh`: targeted attacks (sanitizers in both allocator modes, TSan for `par`, front-end time limits) | 218 |
| `tests/run_json.sh`: the JSON parser against Python, malformed input, deep nesting | 84 |
| `tests/run_differential.sh`: 116 programs built 5 ways with identical output, generated C warning-free under `-Wall -Wextra` | 116 |
| `tests/run_selfhost.sh`: bootstrap, fixed point, and identical output from `vu.py` and `vuc` | 319 files |
| `tests/run_cli.sh`: `check`, `run` and `build` modes, and argument passing | 8 |

Every suite passes with both compilers (`VU=compiler/vuc tests/run_targeted.sh`).

**What this does and doesn't show.** It's strong evidence, not proof. The hit rate fell
from 4–5 real problems per round to zero, which suggests the bugs I know how to look for
are mostly gone. A round finding nothing doesn't rule out bugs nobody has thought of. The
next step up would be random program generation (fuzzing) to search for those, and a
written formal definition of the ownership rules to check the checker against.

Run the tests with `tests/run_tests.sh`. For the thread check:

```
export OMP_TOOL_LIBRARIES=/usr/lib/llvm-18/lib/libarcher.so TSAN_OPTIONS=suppressions=$PWD/tests/tsan.supp
CC=clang python3 vu.py build examples/mandelbrot.vu --tsan -o mb && ./mb 500
```

## Limits of v0

- No methods. Strings are bytes, read as UTF-8 by the text functions. Linux on x86-64 and ARM64;
  macOS builds but hasn't been run on a Mac.
- Only new tasks move between threads: a task that has started stays on its thread, so two tasks
  that never wait on the same thread still take turns only when one waits.
- The safety rules are deliberately conservative. For example, a `var` argument blocks
  every other use of the same variable in that call, even of a different field.
- Not yet tested: whether an LLM actually writes correct Vu more often than Rust when
  given only `SPEC.md`. That's the natural next experiment.
