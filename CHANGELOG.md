# Vu changelog

How Vu got where it is, round by round: what each round added, what the attack rounds found, and
the numbers as they were measured at the time. Later rounds sometimes changed earlier numbers, and
notes marked **Later** say so. For an introduction to the language, see [README.md](README.md);
for the language itself, [SPEC.md](SPEC.md).

The first sections (Results through LLM tokens) are the comparison from rounds 1 and 2.

## Releases

**0.2.0** (2026-10-28): rounds 17 to 24. The language gained methods (`x.f()`), `"""` strings and
text constants, wrapping operators and list slices, `own` parameters in function types, moving what
a `match` on a call binds, `select` over channels and a connection, and generic interfaces. The
standard library: `sqlite`, PostgreSQL over TLS, time zones, an HTTP client that keeps connections
and speaks HTTP/2 (with requests multiplexed by `fetch_all`), WebSocket routes in `web`, zlib
compression, file uploads, `heap`, `sort(by:)` and `sort(key:)`, Unicode normalization and character
classes. Tools: `vu build --wasm`, `vu build --profile`, a package registry (`vu search`, `vu add`,
`vu publish`), and hover, definition and completion in `vu lsp`. Changes that can break 0.1.0 code:
`h2.serve_conn` takes an `http.Site` (`http.serve` and `web.serve` are unchanged); `ws.Socket` and
`web.App` have more fields (made with `ws.accept`/`ws.connect` and `web.app()`, as before, they're
unaffected); a `match` on a call that binds a value now owns it (code that compiled still does).

**0.1.0** (2026-10-28), the first tagged release: everything through round 16. The language
(ownership without annotations, enums, generics, interfaces, closures, typed errors, capabilities,
tasks and `par` loops, JSON, C calls), the compiler (self-hosted, compiling to C; `check`, `run`,
`build`, `fmt`, `test`, `get`, `lsp`, `new web`, and a WebAssembly build for the browser), and the
standard library (`http` with HTTP/2 and TLS, `web`, `ws`, `pg`, `re`, `zlib`, `path`, `cli`, `time`,
`log`). Linux on x86-64 and ARM64. Versions below 1.0 may change the language incompatibly; the
changelog says when they do. `vu version` prints the release.

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

## Round 12: zlib, and what it taught the compiler

`std/zlib` decompresses DEFLATE in the zlib and gzip formats or raw, with `crc32` and `adler32`:
about 436 lines of Vu (536 with comments). It's a showcase on purpose: almost everything reads compressed data, the input
is whoever sent it, and decompressors written in C have a long record of memory bugs (zlib itself:
CVE-2022-37434, a heap overflow in inflate). In Vu, damaged or hostile data can only make it fail. It
takes no capability, so the compiler guarantees it can't open a file, use the network or run a
command, whatever it's given (a compression library that did, in 2024, was xz). `gunzip_max(data, n)`
and the other `_max` forms stop at a size limit before using the memory: a 200 MB zip bomb (204 KB of
gzip) fails in 0.08 s in 13 MB.

**Correctness**: `tests/run_zlib.py` makes random data (text, random bytes, runs, repeated patterns,
mixtures; up to 400 KB), compresses it with Python's zlib at every level and strategy, every window
size and with flushes in the middle, into the zlib, gzip (with every optional header field, header
CRC included) and raw formats, damages 40% of it (bits flipped, cut short, header bytes changed, junk
appended, plain junk), and requires std/zlib to succeed exactly when `zlib.decompress` does, with the
same bytes. In the gate's run, 2,400 cases, and 800 more under ASan and UBSan, all agreed (and about
4,600 more while it was written), and every error message was zlib's (cases with a size limit aside: there std/zlib stops at the limit, before the damage zlib
reports).

**Speed**, `bench/zlib/compare.sh`: zlib-format decompression of 40 MB of Python source (text),
40 MB of /usr/bin (binary) and 8 MB of random bytes, median of 5 runs, each result checked:

| | C zlib | Rust (flate2, pure Rust) | Go | **Vu** | Vu, versioning off | Python (C zlib) |
|---|---|---|---|---|---|---|
| text, 5 times | 0.76 s, 51 MB | 1.08 s, 84 MB | 1.94 s, 133 MB | **1.60 s, 219 MB** | 2.04 s | 1.03 s |
| binary, 2 times | 0.51 s, 58 MB | 0.66 s, 91 MB | 1.11 s, 161 MB | **0.88 s, 154 MB** | 1.07 s | 0.54 s |
| random, 5 times | 0.04 s | 0.04 s | 0.17 s | **0.11 s** | 0.25 s | 0.09 s |

Vu takes 1.7–2.1x C zlib's time on data that compresses, and is ahead of Go on all three; C zlib
writes into a buffer of exactly the right size (its best case), the others grow theirs. Vu uses the
most memory: the result is built in a `[Byte]` that doubles, then copied into a `Str`.

**What the library needed from the compiler.** The first version took 2.3x C's time on text. Profiled
(callgrind), the time went to checks that the code shows can't fail, so the compiler learned to see
them (each version checked once before the loop, as in round 11):

- `t[x & 1023]`: an index masked by a constant is in range once the list has that many elements (the
  Huffman tables, CRC tables). The decoder pads its 29- and 30-entry tables to 32 and masks with 31.
- `out[k - d]` with `d` fixed in the loop (LZ77's copy): an index that is the counter plus or minus a
  variable is bounded by the first and last pass.
- `Str` indexes, like list indexes; loops with a `by` step or `..=` (with the last value the counter
  really reaches: the first version used the bound, which made `data[i + 7]` in a `by 8` loop look out
  of range, so it was never hoisted).
- Accumulators: when an Int changes only by `s += e`, with `e` of known range (a Byte, `x & c`, a
  literal, the counter, a fixed variable, another accumulator), one 128-bit check that
  `s0 + passes * (most per pass)` stays an Int lets the loop add without checks. adler32's
  `a += int(b); b += a` went from about 10 instructions a byte to 3.
- Shifts by `x & c` (c < 64) need no check of the amount.
- `xs.truncate(n)`, new: keeping the first n elements was a loop of `pop()`.
- Tried loops (round 11) now read `[Byte]` and `Str` elements, but aren't made when the loop carries an
  Int from pass to pass: those deferred checks can't be vectorized (the flag depends on every partial
  sum), and unvectorized they cost more than checks that stop. adler32 was 5 instructions per add
  slower that way.

All of it together: 2.04 s to 1.60 s on text, 0.25 s to 0.11 s on random (the "versioning off" column).
The library also does its part: CRC-32 eight bytes at a time.

Attack rounds:

1. std/zlib against Python, 600 cases, then 1,200 with sanitizers: all agreed. Found: nothing in the
   library. My mistakes: the data generator recursed forever on mixtures, and the message count
   included cases with a limit.
2. The compiler's new forms: the loop generator (`tests/loops_gen.py`) now writes `xs[i + k]`,
   `xs[e & c]`, `Str` reads, stepped and `..=` loops, accumulators and masked shifts (in 40 programs,
   53 accumulators, 44 masked or constant indexes, 16 offsets by a variable, 14 `Str` indexes): 600
   programs versioning on against off, and 179 against the compiler before this round (the other 21
   use `fma`): all the same.
3. Targeted tests 629–637: accumulators near both ends of Int and a chain that overflows, more than
   2^31 passes (never bounded, since the 128-bit products could overflow), a mask wider than the list,
   offsets by a variable that's negative or changes in the loop, a stepped loop near the largest Int,
   `truncate` (frees Str and list elements; refuses -1 and past the end), masked shifts of negative
   and wrapping values: all as the compiler before this round, which agrees on the seven that don't
   use `truncate`. My mistakes: two tests' own expected values.
4. Test 363 (a par loop in a task) failed once under TSan: a "thread leak", libomp's worker threads
   not joined at exit. The compiler before this round does the same (2 runs in 40; this one 1 in 40):
   not a Vu thread, so it's suppressed now (0 in 60).

## Round 13: bytes in bulk

std/zlib was 1.7–2.1x C zlib's time, and Rust's pure-Rust decoder (flate2 with miniz_oxide, memory-safe
like Vu) 1.4x. The difference was things Rust can say and Vu couldn't: read 8 bytes at once, copy a
range, and keep a buffer as the result. Three built-ins, each one checked operation:

- `s.read_le(at, n)` and `s.read_be(at, n)`, on a `Str` or `[Byte]`: n bytes (1 to 8) as an Int. The
  decoder refills its bit buffer from one 8-byte read instead of one byte at a time.
- `xs.copy_within(to, from, n)`: memmove, after one check that both ranges are in the list (plain
  values only). The decoder copies a long match in blocks, and a short one as a fixed 16 bytes, which
  gcc turns into two moves (the output keeps 16 bytes to spare; what lands past the match is
  overwritten later).
- `bs.take_str()`: a `[Byte]` list's bytes as a `Str`, the list left empty. A buffer over 256 bytes is
  handed over as it is (with its unused end given back with realloc); smaller ones are copied, since
  short `Str` buffers live in the allocator's size classes and need buffers of their size. The result
  isn't copied any more.

The decoder also unrolls adler32 by 8 (every add still checked once before the loop), and the Int
helpers (`vu_add` and the rest) are now always inlined: in the decoder's big function gcc had been
calling `vu_add`.

`bench/zlib/compare.sh`, same inputs as round 12 (this run's C is a little faster than then):

| | C zlib | Rust (flate2, pure Rust) | Go | **Vu** | Vu, versioning off | Python (C zlib) |
|---|---|---|---|---|---|---|
| text, 5 times | 0.69 s, 51 MB | 0.76 s, 84 MB | 1.65 s, 133 MB | **0.84 s, 147 MB** | 1.04 s | 0.83 s, 140 MB |
| binary, 2 times | 0.42 s, 58 MB | 0.40 s, 91 MB | 0.93 s, 167 MB | **0.53 s, 154 MB** | 0.62 s | 0.45 s, 148 MB |
| random, 5 times | 0.04 s | 0.02 s | 0.09 s | **0.06 s** | 0.13 s | 0.07 s |

Vu is now 1.22–1.26x C zlib on data that compresses (from 2.1x), level with Python (which is C zlib
under a thin wrapper) and twice as fast as Go; Rust is still ahead, at 0.95–1.1x. Memory is about what
Python and Go use, still about 3x C's: the output grows by doubling, and while the benchmark
decompresses again, the previous result is still alive.

Testing: targeted tests 638–642 (read_le/read_be ending exactly at the end, one byte past, counts of 0 or 9;
copy_within overlapping both ways, n = 0, past the end, owned elements refused; take_str of big,
small and empty lists, the list usable after, LSan clean), and `tests/run_zlib.py`'s 3,201 cases
(800 with sanitizers, which watch the 16-byte copies): all as expected, nothing found.

## Round 14: the gate in 12 minutes

The full gate took 49 minutes (2,959 s on the 2-core VM), every suite one after another, and most of
it was building: about 4,600 programs, each built with gcc from scratch every time, one at a time,
though a small program's C is mostly the runtime and changes only when the compiler does.

- `vu build` keeps binaries when `VU_CACHE=DIR` is set: under the SHA-256 of the C, the C compiler's
  arguments (minus file names), its `--version`, and the CPU's model and flags when building for the
  native CPU. The same build again is a copy: 18 ms instead of 534 for a targeted test under the
  sanitizers, the same bytes. Programs with extern C files aren't cached (their C includes files the
  hash doesn't see), and the gate empties the cache when the system's packages change (headers and
  libraries aren't in the hash either).
- The gate runs every suite with `VU` set to `tests/vu_record.sh`, which notes each build (its folder,
  the settings that change the binary, its arguments). The next gate's `tests/prebuild.sh` replays that
  list on every core first, so the suites' own builds are copies. Builds in folders a suite made for
  itself can't be replayed; run_loops' generated programs are generated again for the purpose.
- Suites that don't run servers, threads or timing checks run side by side, one per core, longest
  first; the network, TLS, HTTP, HTTP/2, WebSocket, PostgreSQL, thread and memory suites then run alone
  as before.
- run_fmt compares the C a program makes before and after formatting and never used the binaries: it
  now builds with `CC=true`, which writes the C and compiles nothing (the compiler's own source was two
  full builds of 99,000 lines of C).
- run_cli turns the cache off: its checks watch the C compiler being called.

| | before | first gate (empty cache) | next gate |
|---|---|---|---|
| prebuild | | 79 s (600 builds) | 58 s (4,663 builds, mostly copies) |
| run_targeted | 663 s | 608 s | 122 s |
| run_differential | 728 s | 559 s | 161 s |
| run_arm64 | 272 s | 277 s | 66 s |
| run_fmt | 226 s | 143 s | 41 s |
| run_loops | 155 s | 14 s | 14 s |
| run_selfhost | 135 s | 107 s | 24 s |
| the suites that run alone | 587 s | 551 s | 418 s |
| **total** | **2,959 s** | **1,571 s** | **733 s** |

(The first gate's run_fmt was before the `CC=true` change; the next one's is after it.) Every suite
passed in all three. The next gate is the usual case: a change to the compiler leaves most programs'
C as it was, and those are copies. A change to the runtime changes every program's C, which makes the
gate a first gate again.

What's left is mostly the suites that run alone (418 s, which includes real waiting on sockets and
threads) and running the targeted programs under the sanitizers. Not done: compiling the runtime once
as its own object. It's about 80% of compiling a small program (a hello-world takes 176 ms of gcc at
-O3, a typical targeted test 212 ms), so it would make first gates and every `vu run` faster, but the
runtime changes with each program's flags and features, and its small functions must stay inlinable;
that's a change to the compiler, not the gate.

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

## Round 15: the compiler in a browser

The compiler builds to WebAssembly, so vulang.org can check and format Vu as you type, with nothing
installed and nothing sent anywhere.

- `tools/wasm.sh` compiles `vuc_seed.c` with zig for `wasm32-wasi`. The runtime needed a WASI case in a
  few places (`#ifdef __wasi__`, so native builds are unchanged): no stack-overflow handler (no signals),
  no thread for `main` (it runs on the wasm stack, 64 MB), `flockfile` as a no-op (one thread),
  `getentropy` for random bytes (as on macOS), and `fs.temp_dir`, `os.output` and `os.run` fail with
  "not available in WebAssembly". So `vuc check` and `vuc fmt` work, and `build` and `run` stop at
  the temporary folder they can't make.
- Size: 1.9 MB with `-Os` (12.5 MB at `-O2` with symbols), 477 KB gzipped. Checking a small program in
  Chrome takes 2 to 60 ms after the first load; `import http` (which reads std/http.vu and h2.vu) 0.5 s.
- `tests/run_wasm.sh` (in the gate, skipped without zig and Python's `wasmtime`) runs `check` and `fmt`
  under wasmtime on all 637 targeted programs and the examples and compares exit status, messages and
  the formatted file with the native compiler: 1,288 of 1,288 the same.
- The one difference it found: the compiler recurses as deep as the program nests, and a wasm stack is
  small (wasmtime's at most 2 MB, a browser's about 1 MB), so 52_deep_nesting traps instead of reporting
  "nested too deeply". The suite counts that trap as the error; the playground reports it as "nested too
  deeply to check in the browser". In Chrome that happens past about 500 levels of nested parentheses
  (native: 4,000).
- Node 22's built-in `wasi` module crashed (a segmentation fault in node) when the compiler exited with
  status 1; wasmtime and browser_wasi_shim (what the playground uses) don't. Not chased further.

## Round 16: web basics

What it takes to write and ship a web app, on top of `http`:

- `std/web.vu` (about 470 lines of Vu): routes with `:name` and `*rest` parameters, 404 and 405
  (with `Allow`), HEAD answered by GET routes; middleware that wraps what follows and can pass values
  on (`web.with`, `web.val`); `web.logger` and `web.same_origin` (refuses cross-site requests that
  change things, by `Sec-Fetch-Site` or `Origin`); forms; cookies with safe defaults (HttpOnly,
  Secure, SameSite=Lax), percent-encoded values, and signing (HMAC-SHA256, constant-time check);
  redirects that can't leave the site; static files; and HTML templates.
- Templates take a `const` template, the same idea as `pg`'s SQL: the markup is written in the
  program, so text from a request can only ever be a value, and values are always escaped unless
  they're `web.Html` (made by `render`, `join` or an explicit `trust`). `web.html` takes only a
  `web.Html`, so a `Str` can't be sent as a page by mistake (a compile error).
- `vu new web NAME` writes a starter (main.vu, public/style.css, a Dockerfile, .dockerignore, fly.toml,
  README.md); the files live in `compiler/rt/new_web/` and are carried in the compiler like the runtime.
  `vu build --static` passes `-static` (OpenSSL included; glibc warns that name lookups in a static
  binary need its libraries at run time, which the help and README repeat).

Attack rounds (`tests/run_web.sh`, plus targeted tests 643 to 649):

1. Reading the code before testing it: `web.redirect` set its target to `/` inside a loop over the
   target's bytes when it found a control character, so the loop went on indexing the shortened
   string and would have panicked on the next byte. Fixed before any test ran (it marks the target
   and replaces it after the loop). Then the tests: 7,500 random cases of routes, forms, escaping,
   cookies and templates against a Python model (urllib.parse, the HTML escapes), and an app against
   30 hostile requests (escaping in text and attributes, tampered signatures, redirects to
   `//host`, `https://`, `/\`, a CRLF; cross-site posts; 16 ways out of the static folder), plain,
   under ASan/UBSan and under TSan: nothing found in web.vu. My own test mistakes: the harness read
   HEAD responses as having a body (twice), one targeted test interpolated `{b}` by accident, one
   expected the wrong wording.
2. 400 random static paths built from `..`, `%2e%2e`, `%2f`, `%5c`, `%00`, hidden names and real
   files, each checked against a model of what may be served; 8 clients at once, 320 requests, each
   checking its own parameter and signed-in user: nothing.
3. Size: a 9 MB form value decodes in 0.09 s, a body of 2 million fields parses in 0.36 s, 6 MB of
   text escapes in 0.11 s, a 60 KB path against 101 routes routes in 5.4 ms (release build): nothing
   quadratic.
4. The starter: built and run as its README says (GET, a form post with its 303 and cookie, the page
   it leads to with the name escaped, the cookie remembered, /health, CSS, a cross-site post refused,
   SIGTERM). Building it showed the binary links OpenSSL dynamically (`libssl.so.3`), which the
   Dockerfile's runtime image didn't install: it does now.

5. The full gate: every suite passed except the ARM64 one, on targeted test 646, which imports `web`.
   That suite cross-compiles with no OpenSSL headers for ARM64 and already skipped programs calling
   `tls_` functions; `web` reaches TLS through `http`. It now also skips programs importing `http`,
   `web`, `ws`, `h2` or `pg` (551 passed, 0 failed after). Gate: 1,152 s.

Not done here: the Dockerfile was never built (no Docker daemon on this machine; its build commands
were run by hand, including `VU_MARCH=x86-64-v2`), and nothing was deployed to Fly.io. Not in `web`
yet: multipart forms (file uploads), sessions stored on the server, and a CSRF token (SameSite
cookies and `same_origin` cover browsers from the last several years).

## Round 17: methods

`x.f(args)` now calls `f(x, args)` for any function `f` whose first parameter takes `x`, so a model
(or a person) can write `a.dist(b)`, `st.grow(3)` and `"hi".shout().len` the way most languages read.
It's only another way to write the call: the checker sees `f(x, args)`, with `&x` when the first
parameter is `var` and a move when it's `own`, so every ownership and borrowing rule applies unchanged.

- Lookup: the function visible where the call is written, else the one in the module that defines the
  receiver's type (so `p.norm()` works on a `geo.Point` with only `import geo`). Built-in methods come
  first, then a struct field holding a function, then a function; capabilities, channels, optionals and
  function values keep only their built-in methods. A local variable of the same name doesn't hide a
  method.
- The places that look at a call's shape before checking it (whether it can fail, hoisting `?`, which
  variables an index may change) see through method calls too.

Attack rounds:

1. Tests 650 to 659: structs, enums, Int, Str, lists, generic and interface functions, chained calls;
   a var receiver inside an index (refused), on a computed value (refused, with a message that doesn't
   mention the `&` nobody wrote), an own receiver used again (refused), a failing method unhandled
   (refused) and with `?`, `else` and `match`; built-in Str and list methods not taken over by functions
   of the same name; a field holding a function winning over a function. One real bug found while
   writing them: the loop optimizer (round 7) learns that a variable changes from the `&` in `f(&k)`, and
   `k.bump()` has no `&` to see, so `xs[i + k]` in a loop that bumps `k` that way would have been checked
   once before the loop instead of on every pass. A method call's receiver is now treated as changed, and
   test 654 shows the out-of-range read stopped at the right index. (Checked: a compiler built without
   the fix runs test 654 to the end and prints 66381, a sum that includes memory past the list's end.)
2. Modules, `par` loops (a receiver changed through `pts[i]` is fine, through `pts[0]` refused), interface
   values with var methods, `for var`, read-only views, `st.merge(st)` with a var first parameter
   (refused as two uses of `&st`): nothing new; the exclusive-access message now says that `x.f()` passes
   `&x`. Test 246 expected the old "Vu has functions, not methods" message and was updated.

## Round 18: """ strings and text constants

Writing the web starter in round 16 showed two gaps: an HTML page had to be a chain of
`"...\n" +` pieces inside parentheses (a `+` can't end a line), and `const SECRET = "..."` didn't
compile (constants were numbers only).

- `"""` strings: the text on the lines between an opening `"""` (ending its line) and a closing one (on
  a line of its own); the closing `"""`'s indentation is removed from every line, and the last line
  break goes, as in Swift. Quotes need no escaping. They're turned into ordinary strings before lexing,
  on their first line, with the lines they took left blank, so every later line keeps its number and
  every string rule (escapes, interpolation, `{{ }}`) applies unchanged. `vu fmt` moves the string's
  lines with its statement and changes nothing inside them.
- Text constants: `const NAME = "text"`, or literals and text constants joined with `+`. Using one is
  using its literal (it's inlined), so it's text written into the program: `web.render(LAYOUT, ...)` and
  `pg.query(net, &db, QUERY, args)` accept it, as they accept a literal. An interpolating one is refused.
- The `vu new web` starter now keeps its page and form in `"""` constants.

Attack round (tests 660 to 668): the indentation rule, quotes, `{{ }}`, escapes, blank lines and the last
line break; a `"""` string as an argument with the call going on after the closing `"""`, and as a const
template; unclosed, under-indented, text after the opening, an interpolation over two lines (all refused
at the right line); `"""` inside an ordinary string, beside a `'"'` Byte literal and in a comment (not an
opening); text constants joined with `+` and passed to a const parameter; an interpolating constant
(refused). `vu fmt` on a file whose statement moves from 4 to 2 spaces: the string's lines move with it,
the program prints the same, and formatting again changes nothing. Nothing found in the compiler; two of
my tests were wrong (one expected `\t` as two characters, one put a `"""` string inside an interpolation,
which isn't supported: an interpolation is one line).

## Round 19: compression and file uploads

- `zlib.compress`, `zlib.gzip` and `zlib.deflate` (and `_level` forms, 0 to 9): DEFLATE as zlib makes
  it. Strings repeated within 32 KB are found through hash chains (with lazy matching from level 4:
  a match is held one byte to see whether the next position has a longer one), and each block of up to
  16,384 symbols is written with whichever costs fewest bits: Huffman codes built for the block
  (lengths capped at 15, or 7 for the code-length code, by halving the frequencies until the tree is
  shallow enough), the fixed codes, or stored as is. About 400 lines of Vu in std/zlib.vu.
- On 3 MB of C (the compiler's seed), best of 5, one core:

  | level | Vu size | C zlib 1.3.2 size | Vu time | C zlib time |
  |---|---|---|---|---|
  | 1 | 622,801 | 682,887 | 33.5 ms | 19.3 ms |
  | 6 | 530,605 | 531,273 | 118.7 ms | 72.4 ms |
  | 9 | 513,231 | 512,523 | 401.4 ms | 248.0 ms |

  (Level 1 is smaller than zlib's because zlib's level 1 uses a faster matcher than the one here.)
- `web.parts(req)` reads `multipart/form-data` bodies (file uploads), `web.file` and `web.part_value`
  pick from them, and `web.safe_filename` makes a browser's file name safe to store under.

Attack rounds:

1. `tests/run_zlib_compress.py`: every level and format on empty input, one and two bytes, 100 KB of
   zeros, random bytes, words, a run-heavy pattern, source code, 3 MB of C and mostly-two-letter data;
   Python's zlib and gzip must give back exactly the input. The first run failed 87 of 141: the last
   partial byte was never written (a stream ending mid-byte lost its end-of-block code), and the match
   search read one byte past the input when a match already reached its end (a bounds-check panic,
   not a wrong read). Both fixed; 141 of 141. Making the length and distance codes table lookups
   (they were searched, and their tables rebuilt for every symbol) took level 1 on 3 MB from 219 to
   50 ms.
2. Multipart: 400 random forms (names with `;`, `=`, quotes and backslashes, files with paths in their
   names, data holding CR, LF, dashes and almost-the-boundary, a preamble, padding after a boundary)
   compared with what made them, and 9 broken bodies (no closing boundary, a part without a name,
   headers over 8 KB, 1,001 parts, no boundary parameter, another content type, a boundary run into
   the next text, a part that isn't form-data): all right the first time.

## Round 20: a model writes Vu

The claim the site leads with, that a model writes correct Vu from the spec alone, had never been
tested. Ten tasks (word frequencies, bracket matching, Dijkstra, an LRU cache, an expression
calculator, Life on a torus, a binary search tree with deletion, topological order, Roman numerals,
CSV with quoted fields), each reading standard input, with a Python reference and 4 to 7 test inputs
(edge cases and large ones). For each of three models (Claude Opus 5.5, Sonnet 5.5, Haiku 5.5), one
agent wrote all ten in Vu with only SPEC.md, and another wrote all ten in Rust; neither could run a
compiler or anything else (one attempt each). `vu build` and `rustc -O`, then every test.

| model | Vu: compiles | Vu: passes every test | Rust: compiles | Rust: passes every test |
|---|---|---|---|---|
| Opus | 10/10 | 10/10 | 10/10 | 10/10 |
| Sonnet | 9/10 | 9/10 | 10/10 | 10/10 |
| Haiku | 8/10 | 8/10 | 10/10 | 10/10 |

All three failures were the compiler's fault rather than the programs', and are fixed:

- Two programs named a variable `par` (a tree node's parent), which was a keyword for `par for`. It's
  now a keyword only right before `for`.
- One program pushed a string onto a list inside an `if`, then used it after the `if`: "'region' may
  have been moved". The spec said a `Str` used again is copied, but only own parameters did that. Now
  every place that takes a `Str` variable (push, a map value, a field, `let`) moves it only at its last
  use in the block that declared it and copies it otherwise. Test 91, which expected `m[s] = s` to be
  refused, now expects it to work (s is copied; the sanitizers find nothing wrong).

With those fixes the same 30 programs all compile and pass. Every program was correct; no test failed
on a program that compiled.

Tokens (GPT-4o tokenizer, comments stripped, formatted): Vu took 5% more than Rust for Opus' programs,
16% more for Sonnet's, 2% more for Haiku's. That's not the 21-42% fewer of the benchmark programs, and
the differences show why: Vu's standard library has no priority queue (Dijkstra and topological order
were 200-350 tokens longer, with heaps written by hand) and no sort by key (word frequencies), and
every program spent ~30 tokens on a loop reading standard input. The agents also listed what the spec
left them unsure of: whether `and`/`or` short-circuit, whether maps have `.len`, whether a Byte literal
`'{'` interpolates.

What this shows and doesn't: on tasks of this size, models write working Vu from the spec as reliably
as Rust they've seen millions of examples of, once two sharp edges were gone. It's one run per model,
10 tasks, written blind; it doesn't measure larger programs, or repair with compiler feedback, which is
where Vu's error messages are meant to help.

## Round 21: wrapping arithmetic, list slices, `vu check --checks`, streaming zlib

Four pieces written after round 13 and left unbuilt, now built, tested and finished.

- `+% -% *%` (and `+%= -%= *%=`) wrap at 64 bits, and `>>>` (and `>>>=`) shifts right filling with
  zeros: what hashes (FNV, xxHash), checksums and random number generators need, while `+ - *` keep
  stopping on overflow. A shift amount outside 0..63 stops the program.
- `xs[a..b]` on lists: `let v = xs[a..b]` is a read-only view (no copy; the list is frozen while it
  lives), `for x in xs[a..b]` loops over the range, `var v = xs[a..b]` copies.
- `vu check --checks FILE` lists, for each loop, the checks it still makes on every pass (the ones the
  optimizer couldn't move before the loop): where to look when a hot loop is slower than C.
- `zlib.stream`, `feed`, `finish`: decompression of data that arrives in pieces, with the same results
  and errors as the whole-buffer functions.

Attack rounds:

1. Building it: the code had never been compiled. Three errors the checker caught (a borrowed `g`
   passed with `&g` in the same call, twice; a parameter named like the function `report`), and two
   uses of `x += f()?` in the streaming test driver (not allowed: `?` takes a whole value).
2. `tests/run_zlib.py`'s streamed modes (every test stream fed in random-sized pieces, with and
   without a size limit, then the input after its end): all 400 answers of every seed failed with a
   panic. When a piece arrived, the input already read was dropped, including whole bytes the bit
   buffer had read ahead, so a trailer (the checksum after the last block) that started in those bytes
   was read at a negative index. A bounds-check panic, not a wrong read. `feed` and `finish` now keep
   those bytes; 3,201 of 3,201.
3. Tests 671 to 676 (wrapping against Python's results, a plain `+` still checked next to `+%`, a shift
   by 70, a view freezing its list, a copy growing on its own, a slice past the end) and a `--checks`
   CLI test: nothing found.

## Round 22: what the experiment asked for

Round 20 left a list: programs spent tokens on things the standard library didn't have, and the agents
named what the spec didn't say. This round adds those, plus the language server's missing half.

- `os.read_stdin()` with no argument reads all of standard input.
- `xs.sort(by: fn(a, b) => ...)`: a stable sort of any element type by a comparison (whether a goes
  first), with `reverse:` too. The comparison runs while the list is rearranged, so it can't use the
  list (refused, by name or through a closure that borrows it).
- `xs.swap(i, j)`, and `std/heap.vu`: `heap.push`, `heap.pop`, `heap.heapify` on a list, ordered by
  a comparison.
- The spec now says what the agents had to guess: `and`/`or` short-circuit, maps have `.len`, a Byte
  literal `'{'` is a brace, and `'\"'` is a Byte (the spec listed `\"` as an escape for Bytes, but the
  compiler refused it: fixed).
- A last `return` (or `fail`, `break`, `continue`) that can't be reached, as after a `while true:`
  that returns from inside, is now left out instead of being an error ("unreachable code").
- `vu lsp`: hover (a function's signature and the comment above it, a variable's type, a field),
  go to definition (in the file or a module), and completion (a module's items after `mod.`, a
  variable's fields and methods after `x.`, otherwise what's in scope), from `vu check --index`, kept
  from the last version that compiled while the buffer has errors.

The experiment again, with this spec, new agents, the same tasks and the same Rust programs:

| model | Vu passes every test (round 20 → now) | Vu tokens vs Rust (round 20 → now) |
|---|---|---|
| Opus | 10/10 → 10/10 | +5% → +1% |
| Sonnet | 9/10 → 7/10 | +16% → 0% |
| Haiku | 8/10 → 10/10 | +2% → -4% |

Sonnet's three failures were again the compiler's: two `return` statements after a `while true:` loop
that returned from inside (now allowed), and a `'\"'` Byte literal (now accepted). With this round's
compiler, all 30 programs pass every test. Tokens moved from 5-16% more than Rust to between 4% fewer
and 1% more: still not the 21-42% fewer measured on the benchmark programs, which are
computation-heavy; here most of the difference left is in Dijkstra and topological order, where the
agents still packed (distance, node) pairs into one Int instead of using a struct with `heap`.

Attack rounds:

1. Tests 677 to 680: sort by comparison against Python's sorted (stable both ways), a comparison that
   reads the list (refused), the heap against Python's heapq over 2,000 random operations, swap of
   elements that own memory and out of range; `os.read_stdin()` in run_cli: nothing found.
2. `tests/run_tools.py` drives the language server: hover on a method, a variable, a module's function
   and a field, definition into a module file and within the file, completion after `x.` and `mod.`,
   all on a buffer edited to have an error after its last good version: all right the first time.

## Round 23: SQLite, PostgreSQL over TLS, programs built to WebAssembly, time zones, an HTTP client that keeps connections, WebSocket routes, a package registry, a profiler

- `std/sqlite.vu`: SQLite through the sqlite3 C library (`extern` glue in `std/sqlite_glue.c`), with
  the same rule as `pg`: the SQL is a `const` parameter and values go only as parameters.
- `pg` speaks TLS: `cfg.tls = true` asks the server for it (an SSLRequest) and then checks its
  certificate like `sslmode=verify-full`, against the system's certificates or `cfg.ca`. The new
  `net.start_tls(&conn, host, ca:, timeout:)` turns an open connection into a TLS one.
- `vu build --wasm` builds a program to a WASI module with zig's C compiler. What WASI can't do
  (threads, sockets, processes, OpenSSL, C files) is refused at build time with the reason.
- Time zones in `std/time.vu`: `time.zone(fs, "Europe/Paris")` reads the tz database's TZif file
  (versions 1 to 4, with the POSIX rule at the end for times after the table), and `local`,
  `offset`, `iso_in` and `from_local` work in it. All in Vu: about 370 lines.
- `http.Client`: `client.fetch(net, req)` keeps connections open between requests (HTTP/1.1
  keep-alive) and speaks HTTP/2 to https servers that choose it through ALPN (`std/h2.vu` gained a
  client half: HPACK both ways, flow control both ways, SETTINGS, PING, GOAWAY, RST_STREAM,
  CONTINUATION, padding, 1xx responses and trailers). For it, `net.tls_connect` takes `alpn:` and
  `net.protocol(conn)` says what was chosen.
- Fixed: `arg(i, "text")` compared with `==` or `!=` was refused ("can't compare Str with Str"):
  the checker's quick type guess said Int for every `arg`. Found writing the client's test driver.
- `own` parameters in function types: `fn(own ws.Socket, http.Request)` takes ownership of its
  first argument (a call moves it in), a closure says `fn(own s) => ...`, and a named function with
  `own` parameters is now a value. Before, a function value could only borrow, so nothing could hand
  a connection to a stored handler.
- WebSocket routes in `web`: `app.websocket("/rooms/:room", handler)`; the handshake goes through the
  middleware, the handler owns the socket, and cross-origin pages are refused unless
  `allow_origin` names them. Underneath, `http.Site` lets a handler's 101 hand the connection to a
  function (`http.serve_site`); `ws.accept_request` does the handshake for a request already read,
  and `ws.poll` waits for a message for a given time, so a handler can also send what other tasks
  queue for it. `web.serve_tls` serves an app over TLS.
- What `ok(v)` and `err(e)` bind in a `match` on a failing call now belongs to the arm, so it can be
  moved (`ok(c): spawn serve(net, c)`); before, it was a view into the result, which the error
  said to take out with `else`. Test 357 expected that refusal and now checks the move works.
- A package registry: `need clock v1.2.0 os` names a package by its registry name; the index
  (`https://vulang.org/registry/index.txt`, a text file served with the site, or `VU_REGISTRY`)
  records each version's commit and file hash, and `vu get` refuses anything else. `vu search`,
  `vu add`, `vu publish`. The index starts empty: publishing is a pull request to it.
- `vu build --profile`: a sampling CPU profiler (SIGPROF on the kernel's CPU timer, reading the
  shadow call stack the quick builds keep for backtraces), reporting by function and line at exit,
  with stacks for flame graphs.

Attack rounds:

1. `tests/run_sqlite.py` against Python's sqlite3: random inserts, updates, deletes and selects with
   quotes, semicolons and NULLs, a bad statement, a reopened file, SQL that isn't const. Found one bug:
   an empty Str has no buffer, so it was bound as NULL instead of `''` (fixed in the glue).
2. `tests/run_pg_tls.py`, a fake server: the test CA, the system's CAs (which don't include it), a
   certificate for another host, a self-signed one, `N`, an `S` followed by bytes (the buffer
   stuffing of CVE-2021-23222: they must not be read as if they came over TLS), an error message
   instead of an answer, a server that ignores the request, and one that hangs up. Found one thing:
   a server that hung up was reported as "an unexpected answer"; it now says the server closed the
   connection. Certificate errors now start with `network: tls:`.
3. `tests/wasm_programs.py` builds all 7 examples and every targeted output and panic test (371
   programs) with `--wasm`, runs them under wasmtime and compares with the expected (or native)
   output: 318 the same (313 when this round started), 56 refused at build time as they should be (tasks, the network), and 3
   known differences: `os.run` can't start programs in WASI, WASI reports an empty path as "Bad file
   descriptor", and clang turns test 465's endless recursion into a loop, so it ends with an integer
   overflow instead of a stack overflow. A too-deep recursion stops with wasmtime's trap ("call stack
   exhausted"), not the panic. One mistake of mine on the way: the first comparison didn't drop NUL
   bytes from the output as the shell's does, so test 44 looked different.
4. `tests/run_time_zones.py` against Python's zoneinfo (its own reader of the same files), over all
   498 zones: 45,688 local times (random instants from 1800 to 2200, and the second before, at and
   after changes found by bisection) and 23,061 wall-clock times around changes for `from_local`
   (gaps and repeated hours, fold=0), and the same with three more seeds; then 21 broken files (bad magic, cut short,
   counts past the end, transitions out of order, indexes out of range, an offset of a week, bad
   POSIX rules), 4 unusual valid ones (a `<+0330>` name, a rule without dates, DST all year, a
   version 1 file), and 300 randomly corrupted files, plain and under ASan/UBSan. All agreed the
   first time. Not covered: the `right/` zones' leap seconds are skipped, as Unix time has none.
5. `tests/run_http_client.py`, 34 checks: keep-alive against Python's http.server (20 GETs on one
   connection, as the server counted; mixed methods, chunked and HEAD; `Connection: close`; a body
   read to the close; a server that hangs up after answering); HTTP/2 against Vu's own server (GETs
   up to 3 MB, POSTs up to 1 MB through its 64 KB window, HTTP/1.1 over TLS with `http2` off, an
   untrusted certificate) and against the h2 package with a 16-byte window, GOAWAY after every
   three requests, REFUSED_STREAM and a 103 before the 200; then 22 hand-built servers: push,
   DATA before HEADERS, a stream never opened, undecodable HPACK, a 20,000-byte frame, a short
   body, 33 CONTINUATION frames, bad or misplaced `:status`, uppercase names, bad padding, bad
   SETTINGS, a window past 2^31-1, RST_STREAM, a close mid-body, 65 MB, an HPACK bomb (a 4 KB
   entry referenced 100 times), GOAWAY before answering (sent again on a new connection, then
   given up), silence (the timeout), and PING, trailers and padding that must work. Found one bug:
   a GOAWAY that arrived just after a response left the connection in the pool, and the next
   request (a POST, not repeatable) failed on it; kept HTTP/2 connections now read what arrived
   before they're used. Two mistakes of mine in the test: the "refuse once" flag was per
   connection, and the HPACK bomb's length prefix was wrong (it failed for the wrong reason).
6. Tests 682 to 689 on `own` in function types: named functions, closures, a list of them, a field,
   a generic parameter, one that fails (LeakSanitizer checks the argument is freed), use after the
   move, the same variable twice, `fn(Box)` and `fn(own Box)` mixed up both ways, and a borrowing
   closure: nothing found.
7. `tests/run_web_sockets.py`, 24 checks with the websockets package over TCP and TLS: echo up to
   1.2 MB, route parameters and middleware values, middleware that refuses, origins (another
   refused, an allowed one and the app's own accepted), a WebSocket request to a plain route and to
   no route, a chat of 5 sockets fed by a hub task while one drops out without closing, a frame in
   the same packet as the handshake, four broken handshakes, plain requests meanwhile, and a clean
   stop: nothing found. What got in the way, three times while writing this: a value bound by
   `match` on a call's result couldn't be moved out (`ok(m): x = m`). Now it can: the arm owns it
   (test 690: into a variable, a list and a struct, in a loop, under the sanitizers).
8. The registry, in `tests/run_pkg.sh` (25 checks): publish from a clone (origin, commit, hash), an
   unknown tag, search, add (latest version, the capabilities granted, vu.pkg and vu.lock, run),
   add twice, an unknown name, version or a name that isn't one, an older version by
   `need NAME`, a tag moved to another commit after publishing (refused, and nothing kept), files
   whose hash differs, six broken index lines (an option as a source, a name in capitals, a short
   commit, lines before their package, unknown lines, a name twice) and an http:// index. Found:
   `vu publish` dropped `.git` from every origin, which broke `file://` sources (git found the
   folder anyway, so `vu add` had passed); now only from github.com and gitlab.com URLs. And my
   test expected `ext::sh` to be refused as a source, but it can't reach git's ext transport:
   it's read as https://ext::sh.
9. `tests/run_profile.py` (11 checks): a program with a hot, a warm and a cold function (shares
   about 85/15/0, as built), the lines named, the two files, and a program with tasks on every
   thread, a par loop, a sleep and a loopback connection run 21 times while sampled. Found two
   things, both the optimizer's: the per-line stores were sunk out of loops (every sample said
   line 0), and with the small functions inlined their frame pushes were removed as dead stores
   (all time went to main). The profiled build now keeps both with volatile stores and compiler
   barriers. Measured cost, best of 3: binarytrees 0.58 -> 1.00 s, spectralnorm 0.12 -> 0.30 s,
   nbody 1.08 -> 1.51 s, fannkuch and mandelbrot (par loops, no line stores) about the same.

## Round 24: select, generic interfaces, Unicode text, sort by key, multiplexed HTTP/2

- `select` waits for the first of several things: a value from a channel (`let v = ch.recv():`), room
  in one (`ch.send(x):`, moving `x` only if that arm runs), a channel closed and empty
  (`ch.closed():`), data on a connection (`net.readable(conn):`), or a timeout. Any arm can carry
  `if condition`. In the runtime, a select registers on each channel's list of watchers (and, with a
  connection, waits on the socket's reader slot, so the poller, the timer and the channels hand off
  the one wake-up the way they already did for a timed read); when several arms are ready one is
  picked at random. `ch.send(v, timeout:)` fails instead of waiting forever, and on a closed channel
  it fails instead of stopping the program. The WebSocket chat in `tests/web/sockets.vu` now waits on
  its socket and its inbox at once instead of polling every 20 ms.
- Generic interfaces: `interface Store[T]`, `impl Store[Int] for Ints`, bounds `[S: Store[T], T]` (T
  found from the instance S implements), and values of an instance (`[Store[Str]]`). One instance
  per type, so a call needs no annotation.
- `xs.sort(key: fn(x) => x.age)`.
- `s.normalize("NFC" / "NFD" / "NFKC" / "NFKD")`, and `is_alpha`, `is_digit`, `is_space`,
  `is_alnum`, `is_upper`, `is_lower`, `is_decimal`, with tables generated from Python's unicodedata
  (`tools/gen_norm.py`, Unicode 15.1).
- `client.fetch_all(net, requests)`: every request to an HTTP/2 server goes out at once on one
  connection, up to the server's stream limit, and the responses are read as they interleave
  (`h2.requests`, which `h2.request` now calls with one).

Attack rounds:

1. Tests 691 to 698 on `select`: two producers and closed arms that sit out once seen, a send arm on
   a full channel (the list stays) and its use after (refused: may have been moved), send timeouts
   (full, then closed, the value freed), a connection with nothing and then data, a closed
   connection, a nil `Conn?`, two connections in one select, a recv arm without `let`, every arm off
   with no timeout (stops the program), 8 producers and 4 consumers across threads passing 16,000
   numbers through three channels (each arrives exactly once; also under ThreadSanitizer), and two
   tasks bouncing a number 20,000 times through selects with no timeout (a lost wake-up would hang;
   30 runs). Found while writing them: a closed channel's arm was ready on every pass, so a loop
   over it spun and starved the producer on the same thread; that's what the `if` guard is for, and
   `closed()` now means closed and empty (it fired with a value still in the channel, which was then
   lost to the loop). The modules pass didn't resolve names inside select arms (`ws.send_text` was
   "unknown"): fixed.
2. Tests 699 to 705 and module test 47 on generic interfaces: two instances, static and method
   calls, interface values, both kinds of bound, a type of the wrong instance (refused), one type
   implementing two instances (refused), a wrong signature for the instance, an unmet bound, a
   generic interface named without arguments, two type parameters implemented by generic struct
   instances, and an interface from a module implemented in main. Found: a bound's type argument
   couldn't be worked out from the instance (`first_of[S: Store[T], T]`); now it is.
3. `tests/run_norm.py`: every assigned code point (in lines of 64) and 30,000 random mixes in all four
   forms, against `unicodedata.normalize` on four seeds, plain and under ASan/UBSan; bytes that
   aren't UTF-8 kept; and the seven class tests on 1,142,065 lines (every code point alone, and the
   mixes) against Python's `str` methods. All agreed the first time, apart from my test splitting
   on tabs that were in its input, and counting the empty line after the input's last newline.
4. Tests 706 and 707 on `sort(key:)` against Python (`reverse=True` keeps equal keys in order, as
   Python does) and a key that can't be ordered. In `tests/run_http_client.py`, 4 more checks: 30
   GETs and 2 POSTs at once on one connection to Vu's server, two servers and a bad URL mixed, and a
   server (the h2 package) that answers nothing until 8 requests are open at once, which it saw:
   nothing found.

## Limits of v0

- Strings are bytes, read as UTF-8 by the text functions. Linux on x86-64 and ARM64;
  macOS builds but hasn't been run on a Mac.
- Only new tasks move between threads: a task that has started stays on its thread, so two tasks
  that never wait on the same thread still take turns only when one waits.
- The safety rules are deliberately conservative. For example, a `var` argument blocks
  every other use of the same variable in that call, even of a different field.
- Tested once (round 20) on 10 small tasks: models wrote correct Vu from `SPEC.md` as often as Rust.

## Round 25: an MCP server, folders as capabilities

The question: can a Vu program stand in for a tool people already run? The Model Context Protocol's
filesystem server (`@modelcontextprotocol/server-filesystem` 2.0.1, Node) was rewritten as
`mcp/filesystem`, with what it needed added to the standard library:

- `dir`: `dir.open(fs, path)` gives a `Dir` that reaches only what's inside one folder. Paths are
  resolved by the kernel (`openat2` with `RESOLVE_BENEATH` on Linux; elsewhere each name is opened
  with `O_NOFOLLOW` and symlinks and `..` are refused). Only regular files are read or written.
  The server's `main` opens its folders and passes on only the Dirs, so its tools can't reach
  anything else, and have no `Net` or `Os` at all.
- `stdio` (standard input by lines, no capability), `json` (JSON of any shape, written as
  `JSON.stringify` writes it) and `mcp` (the protocol, in both of its eras).
- The compiler lets the standard library's own modules make the `Ffi` their C needs (programs and
  packages still can't).

Measured against the reference on Node 22 (2-vCPU VM, `mcp/filesystem/bench.py`): one 352 KB binary
against Node plus 25 MB of packages; 1.7 ms from start to the `initialize` answer against 203 ms;
2.1 MB of memory idle against 72 MB; 8.7x the `read_text_file` calls per second; `search_files`
over 2,000 files in 2.6 ms against 149 ms.

What the rounds found:

- **Glob matching against minimatch** (random paths and patterns): round one, 2 of 3,013 differed
  (`a/**` doesn't match `a` in minimatch); round two, 1 in 20,000 (minimatch drops `x/..` from a
  pattern); round three, adding `.`, `..` and `//` to the patterns, about 9 in 5,000 (minimatch
  squeezes runs of `/` and keeps `.`). After reading minimatch's preprocessing and matching it:
  40,000 cases, no differences.
- **The server against the reference** (every tool, errors, argument errors, both protocol eras,
  random edits, names and globs, each server on its own copy of the files): the first run failed on
  modern requests on a connection that had sent `initialize`: the reference picks one era per
  connection, this server answers each request by its own `_meta`. That's kept (the 2026-07-28
  revision is stateless) and documented; the test uses a connection per era. The next failure was
  the test's (random file sizes drawn separately for the two copies). Then nine seeds, about 12,600
  answers, all the same, plain and under AddressSanitizer.
- **A compiler bug**: `to_json` of a lone `Str` or `Float`, in a program with no struct to encode,
  didn't link (the JSON runtime was included only for types with codecs of their own). Fixed;
  `tests/targeted/710`.
- **The brace footgun from round 24**: `"{"` silently starts an interpolation, so
  `s.startswith("{") and s.endswith("}")` is one string. A string that is nothing but one
  interpolation of a string literal is now an error that says to double the brace (`708`, `709`).
  It caught one in this round's own code (`"{~"` in the glob classes). The first version refused
  any interpolated string literal, and the full gate failed on two older tests that use one on
  purpose (`[{"lit"}]` in `302`, `"é{"\0"}x"` in the C tests): narrowed to the whole-string case.
- The gate also failed once in the MCP comparison: `get_file_info`'s `accessed` time differed by a
  second, because the other server's read had moved it. It's no longer compared.
- Not found by a test, but met while writing: there's no statement that does nothing (an arm that
  needs none had to be restructured), and `write` and `fail` can't name functions even in a module.

Not done this round: an attack suite against `Dir` itself. Its guarantee rests on `openat2`'s
`RESOLVE_BENEATH` (and the walk elsewhere); the tests here check that it behaves as the reference
does on ordinary trees, including symlinks that stay inside.

## Round 26: the time and fetch servers, three platforms in CI

Two more of the reference MCP servers, both Python, rewritten in Vu and checked against them:
`mcp/time` (`mcp-server-time`) and `mcp/fetch` (`mcp-server-fetch` 2026.10.28). For them:

- `net.resolve(host) -> [Str]`: a name's addresses as text, looked up off the task's thread, in the
  order `connect` tries them (`tests/targeted/715`, `716`). The fetch server checks those
  addresses and connects to the same ones.
- `mcp` serves prompts (`set_prompts`, `PromptGet`, `prompt_result`, `error_reply`).

The fetch server is built from parts that each answer as a library the reference uses, each with a
generator and a comparison (`tests/mcp_fetch/parts.py`): URLs as pydantic's `AnyUrl` rewrites them
(the WHATWG parser of the Rust url crate, with a UTS #46 table made by asking pydantic about every
code point: `tools/gen_idna.py`), robots.txt as Protego reads it, the address guard as the
reference's `_is_public_address`, HTML tokens as Python's `html.parser` makes them, text as httpx and
the reference's `decode_page` decode it (Python's codec names and single-byte tables:
`tools/gen_fetch_tables.py`). Measured (2-vCPU VM, local HTTP server): 3.6 ms to start against 730,
5 MB against 83, 1,020 fetches of a text file a second against 49, 107 of an HTML page against 8
(pure Python) or one every 881 ms (Readability.js under Node). The time server: 1.8 ms against 683,
1.9 MB against 69, 12,212 `convert_time` calls a second against 773.

What the rounds found:

- **URLs against pydantic** (5,000 generated URLs a round): round one, 71 differed: a combining
  mark can't start a label, a punycode label must decode to something valid, the host is checked
  before the port, an empty URL has its own message, `file:` drops extra slashes. Round two, 22:
  combining marks were dropped instead of kept (the table's probe composed them with the letter
  beside them; it now probes beside `q`, which composes with nothing), and Windows drive letters
  in `file:` hosts. Round three, 2, both quirks of the crate (it never pops a drive-letter segment
  with `..`, in any scheme; it takes `foo://:@` with nothing after it). Then 40,000 the same.
- **robots.txt against Protego**: none differed from the first run (20,000 cases; the generator was
  then biased so about 13% are refusals).
- **The guard against `_is_public_address`**: none differed (40,000 addresses, half near the edges
  of the special ranges).
- **The tokenizer against `html.parser`**: round one, 187 of 3,000: `<plaintext>` makes the rest of
  the input text. Round two, 79: `html.parser` holds back trailing text that might end in a cut-off
  reference. Then 12,000 the same.
- **Decoding against `decode_page`**: RFC 2231 charsets (`charset*=utf-8''latin1`) are read by
  Python's email parser; and in Python 3.13 a UTF-16 or UTF-32 charset in the header with no byte
  order mark raises instead of decoding, so the reference fails on such a page (matched). Then
  about 9,000 the same.
- **The whole server against the reference** (requests to a local server: pages, charsets, gzip,
  chunked, redirects, robots files and statuses, hang-ups, cut-off bodies, bad arguments, the
  prompt, the guard): the prompt's URL is httpx's, not pydantic's, so `0x7f.1` and
  `[::ffff:127.0.0.1]` stay as written in its messages; a body cut short reports the bytes received
  and expected; a redirect to `mailto:` makes the reference fail with an exception its SDK shows as
  "Error executing tool fetch" and nothing more. Then eight seeds, about 2,500 answers, the same
  (the Markdown of HTML pages compared by words: median F1 0.98–0.99).
- **A difference kept on purpose**: the reference resolves a name to check it and again to
  connect, so a name can answer differently the second time; this server connects to what it
  checked. Bodies are limited to 64 MB, gzip included.

CI now runs on Linux x86-64 and ARM64 and on macOS ARM64. What macOS found: there is no
LeakSanitizer there (the scripts now ask for leak checking only where it exists); Apple's clang has
no OpenMP (par loops use Homebrew's libomp when installed, and otherwise run on one thread) and
OpenSSL isn't where the compiler looked (it now looks in Homebrew's); and one targeted test of
unbounded recursion ran until its counter overflowed, because clang turned the tail call into a loop
(the test now recurses without a tail call). The time server's comparison found that the reference's
answers depend on the Python it runs on: on 3.12, `strptime` doesn't take `" 9:59"`, and with the
`tzdata` package installed a folder name fails with that package's path in the message; CI now uses
Python 3.13, and the test skips those names when `tzdata` is installed. On ARM64 two targeted tests
(a million-piece split and map churn) ran past the 20-second limit; why is being measured in CI.

Also this round: `mcp/vu`, Vu's checker as an MCP server for a model writing Vu (`vu_check` on one
file or several, `vu_docs` with `llms.txt`); `tests/run_mcp_vu.sh`. Releases now carry `llms.txt`
and the time, fetch and vu servers.

And `mcp/sqlite` (`mcp-server-sqlite` 2025.4.25): 2.1 ms to start against 443, 3.4 MB against 57,
15,683 `read_query` calls a second against 457. The reference is archived and no longer starts with
the current Python MCP SDK (2.x); it's compared on `mcp<2`. For it: `sqlite.run_sql` (SQL given as
text, values with their types; it refuses several statements in Python's words) and
`sqlite.in_transaction`; `mcp` lets a program answer other methods (`s.extra`, `Request`, `reply`,
`notify`) and unknown tools itself; `pyrepr` became a local package shared by the fetch and SQLite
servers (`need ../pyrepr`). What the comparison found (random sessions of tool calls, about 450
answers a seed): Python's sqlite3 opens a transaction before an INSERT, UPDATE, DELETE or REPLACE
even after a comment, so `/* c */ INSERT ...` through `write_query` (which commits only SQL that
starts with INSERT) is rolled back there, and here too now; the SDK answers a request without the
params it needs with its own -32602; and the two SQLite libraries (Python's bundled 3.53, the
system's) report different errors first for a statement that is wrong twice over, which the test
now avoids. Then six seeds, about 2,700 answers, the same, plain and with AddressSanitizer.

And `mcp/git` (`mcp-server-git` 2026.10.28): 2.7 ms to start against 649–702, 2.2 MB against 73, and
157 `git_status` calls a second against 123 (both run the git program for the work). The reference
leans on GitPython, so its revision parser, commit writer, patch reader and ref-name rules are
ported, the rest done with git. The first version answered *more slowly* than the reference, 66
`git_status` calls a second against 193: it ran a program for every file test and every commit it
read; reading files directly and fetching commits in one `git cat-file --batch` made it 302 (on a
two-commit repository). What the comparison found (random sessions on two copies of one repository):
GitPython rejects the ISO dates with a colon in the zone that git takes in `GIT_COMMITTER_DATE`
("Unsupported date format"); opening a `.git` folder gives the folder above it as the working tree;
GitPython makes a branch from an annotated tag by writing the tag object's sha into the branch,
which `git update-ref` refuses (so this server writes the file as GitPython does); and the test's
own paths had to be the same text for both (pydantic shows long argument values cut in the middle).
Then about 3,300 answers on twelve seeds, two of them confined, the same, plain and with
AddressSanitizer.

CI, all three platforms: the run after the round's CI fixes passed on Linux x86-64, Linux ARM64 and
macOS ARM64 (the ARM runner's slow AddressSanitizer given 120 seconds a test).

Scripts: `vu run` now keeps each program's binary, under a hash of its path and options, with a key
made from the options, the C compiler and the program's C. Running the same program again skips the
C compiler, so a script with `#!/usr/bin/env -S vu run` as its first line starts in 9 ms instead of
234 ms (the median of 20 runs on Linux x86-64; the front end still runs every time, to see whether
the program changed). Before committing, a review found that the first version kept a binary for
every program ever run, including ones run from temporary folders (as the tests do). Now it keeps
the 64 programs used last and drops one whose file is gone. `tests/run_cli.sh` checks these cases:
a second run calls no C compiler; an edit rebuilds; other options keep their own binary;
`VU_RUN_CACHE=off`; the pruning. `VU_CACHE` (the build cache the gate uses) turns it off.

Lists to C: an extern function can take a `[Byte]`, `[Int]` or `[Float]`, which C gets as a pointer
to the elements and their count (no copy), and a `var` one, whose elements C may change in place.
That is what wrapping most C libraries needs (a checksum over bytes, a numeric routine over an
array, a buffer for C to fill). The ownership checks cover these calls as they do Vu calls: a list
passed both read and `var` in one call, or changed by C while a view of it lives, is rejected
(`tests/ffi/32`, `34`). `tests/ffi/31` and `35` pass lists from every kind of place (a literal, a
call's result, parameters, a map value, an optional, an enum field, a closure, a slice, a list
element, an empty list, whose pointer may be NULL) with AddressSanitizer and UBSan, and the C is
clean under the gate's warning flags with gcc and clang. The SPEC's zlib example (`crc32` over a
`[Byte]`) gives the same checksum as Python's `zlib.crc32`. Results stay scalars, `Str` or handles:
a list doesn't come back from C.

Libraries: `export fn` makes a function a plain C function too, and `vu build --lib` builds a file's
exported functions into a shared library (`.so`, `.dylib` on macOS) with a C header. Strings and
lists of numbers go in as a pointer and a length, read in place; strings and lists come out as
`malloc`'d copies; a failing function hands back its message. An exported function gets no
capabilities, so a library can't reach files, the network or programs. `tests/run_lib.sh` builds
`tests/lib/words.vu` (every kind of parameter and result) and calls it from C, from one thread and
eight at once (57,625 checks, clean under AddressSanitizer, LeakSanitizer, UBSan and
ThreadSanitizer), and from Python through ctypes against the same functions written in Python (about
26,700 answers a seed, three seeds, also with AddressSanitizer preloaded into Python). Only the
exported names are visible in the library.

What attacking it found:
- ThreadSanitizer: the task runtime starts itself on the first task operation, assuming that's the
  program's main thread. Called from eight threads of a C program, they all started it at once.
  Making tasks work in a library is a larger change, so `--lib` refuses a program that uses tasks or
  channels, and says why.
- An exported function with type parameters was quietly left out of the library (generic functions
  are kept apart until used). It's now an error.
- The wrapper's own locals (`r`, `p`) could clash with a parameter of the same name, and a parameter
  named `size_t` or `NULL` broke the header. The wrapper's names now start with `vu_`, and such
  parameter names get a `_` in C.
- A parameter `s_len` next to a `Str` named `s` would have collided with the length C passes for
  `s`. It's an error now, with the reason.
- An export named like a C library function (`puts`) failed with "internal error". It now says the
  name is already the C library's and should be renamed.
- My own test mistakes, not findings: a `Byte` that went past 255 (Vu checks), Python's `sum()` of
  floats (it compensates, and Vu's loop doesn't), and an overflowing `Int` sum in the model.

Tracing CI's AddressSanitizer crashes: the MCP time server crashed under AddressSanitizer on the
Linux x86-64 runner a second time. The crash was a segmentation fault at its first request, and
neither crash happens locally (800 starts). Vu's own handler had reported both as "segmentation
fault", hiding where they happened. In AddressSanitizer builds, a fault that isn't a stack overflow
now goes on to AddressSanitizer's handler, which prints the stack. The cause is still unknown.

A Python package template (`packaging/python`): `pip install .` runs `vu build --lib` while it
builds the wheel, and the package calls the library through ctypes. The example is edit distance:
11 times faster than the same code in pure Python for single calls (half of that time is ctypes
calling), and 25 times faster for `closest()` over 5,000 words (`tests/bench.py`, Python 3.13, 2
cores). Its test matches pure Python on 6,001 answers with accents, CJK and emoji. `run_lib.sh`
installs it into a fresh venv with pip and runs the test. The first version decoded UTF-8 with
`.chars()`, which makes a Str per character; decoding the bytes by hand made `closest()` 1.7 times
faster (56.5 ms to 32.6).

Rebuild times against Rust (`bench/rebuild`): `gen.py` writes the same program in Vu and Rust, N
functions in M modules, and `run.sh` times a clean build and a rebuild after a one-line edit (the
median of 3, on 2 cores, with gcc 13.3, clang 18.1 and rustc 1.97). At 2,000 functions (20,000 lines
of Vu, 24,000 of Rust), Vu lost badly at first. An edit and a quick build took 12.97 s, against 0.85 s
for `cargo build`: Vu compiles the whole program as one C file, and Rust compiles incrementally. Three
changes:

- Quick builds use clang when it's there. On this program's 131,000 lines of C, clang -O0 takes
  3.4 s and gcc -O0 10.2 s. `vu run` also stopped passing `-g`, which cost clang another 4 s: its
  binary is deleted after the run, and panics get their backtraces from the shadow call stack.
  `vu build --debug` keeps `-g`. An edit and `vu run` then took 4.48 s.
- Split builds. A quick build of a program with more than about 6,000 lines of C in its functions
  compiles them as separate C files, grouped by source file into parts of about 6,000 lines, as
  many at once as there are cores. It keeps each part's object file under the hash of its C, so a
  rebuild compiles only the parts that changed. This needed two changes. The runtime's state
  (61 globals, among them the node pools' free lists) is now written `VU_G`: static in a one-file
  build, defined in part 0 and declared `extern` in the others. And temporaries are numbered within
  each function, not across the program, so an edit leaves the other functions' C as it was.
- After both: an edit and `vu run` takes 0.83 s, against 0.74 s for `cargo run`. The first build
  takes 4.66 s for both. `vu check` takes 0.30 s against `cargo check`'s 0.45 s. Optimized builds
  are unchanged and still lose: 9.4 s against 7.1 s.

`tests/run_split.sh` checks split builds. It builds every targeted test that runs, and every
example (about 400 programs), both split (`VU_SPLIT=always`) and as one file, and compares their
output, exit code and stderr. It also builds the compiler split (5 to 7 s), checks that no part
defines writable data of its own, checks that the split-built compiler writes the same C as the
installed one, and checks that an edit rebuilds the compiler in about 1.1 s. `compiler/build.sh` now
builds stage 1 split, so every rebuild of the compiler goes through a split build.

What testing split builds found:
- The split markers first appeared in the compiler's own string literals (it writes them), and a
  split of the compiler's C broke a string in half. They are now whole lines, which a C string
  can't be.
- `vu_files` (the names panics print) was declared `static const char *const *`, so the rewrite to
  `VU_G` skipped it as a constant. The duplicate-data check found it. The first comparison had looked
  only at the first line of stderr, so it missed the wrong file names that only part 0 could print;
  it now compares all of stderr.
- The compiler that has split builds builds itself, so a bug in them stops the next build. The first
  version declared `vu_main` twice (`VU_FN` and `static`). `VU_SPLIT=off compiler/build.sh` got past
  it.

Capabilities, shown: `vu check --caps FILE` prints what a program can reach, meaning the
capabilities `main` asks for, since nothing else can make one. For example, `mcp/fetch` can use
only the network, and `mcp/git` only files and programs. An agent skill (`packaging/skill/vu`) uses
it: write the tool, `vu check` it, show the person what `--caps` prints, then `vu run` it (kept
binary, about 10 ms a start after the first). The skill hasn't been tried in an agent session yet.

What the full gate found after the clang change:
- clang refuses brackets nested more than 256 deep. Vu writes that much nesting for a long chain of
  operators (`tests/selfhost/r22_13`, a sum of 20,000 terms). Past a few thousand levels, even
  `-fbracket-depth` doesn't help: clang's parser runs out of stack and crashes. Quick builds now
  measure how deep the C nests and use clang only below 200 levels. Scanning the 131,000-line
  program takes no measurable time. A clang build (macOS's `cc`, or `CC=clang`) also gets
  `-fbracket-depth`.
- Split and whole builds of the stack-overflow tests stop at different depths, because their
  frames differ in size. The comparison now checks only the first line of a stack overflow's
  report.

What CI found on the ARM64 runners (macOS and Linux), which the x86-64 gate couldn't:
- Split builds of programs that use tasks failed to link: the ARM64 context switch is a top-level
  `asm` function, which every part defined. It's now defined in part 0 only. (Checked here by
  building the network tests split for ARM64 with a cross compiler and running them in qemu.)
- On macOS a `--lib` library recorded its own name as where to load it from, so a program linked
  against it found it only in the current folder. It's now `@rpath/libNAME.dylib`, as on Linux,
  where the loader searches the program's rpath.
- On macOS, split builds of programs that use TLS didn't find OpenSSL's headers. Homebrew's `-I`
  folder is given with the libraries, after the C file, and the parts were compiled with only the
  options before it. Each part now gets the `-I` options too.

## Round 27: where Vu still lost to Rust

The question was where Vu still loses to Rust, and the aim was to fix each case. The first finding
was about the measurement itself.

**The rebuild benchmark was wrong.** `bench/rebuild/gen.py` says each function calls another "on a
path the run never takes, so nothing is dead code". But `main` passed constants, so gcc's
interprocedural constant propagation proved those paths dead and deleted them in a whole-program
build. The optimized-build numbers published last round (9.4 s against Rust's 7.1 s) measured
that. `main` now passes a number read from the command line. With that, a whole-program optimized
build took 44 s against `cargo build --release`'s 14.3 s, and the README and SPEC numbers are
replaced.

What changed:
- **Optimized builds are split too**, as quick builds were: parts of about 6,000 lines compiled in
  parallel and kept. Calls across parts aren't inlined, as with Rust's default 16 codegen units.
  The tried copies of functions (`VU_FNI`) go in the header, so every part can still inline them
  into its loops. The compiler built this way checks its own source 6% slower (median of 5, 489 ms
  against 451). On the 20,000-line program, the first optimized build takes 29.6 s (Rust: 14.3 s),
  and a rebuild after an edit takes 3.2 s (Rust: 14.1 s, since its release builds aren't
  incremental).
- **Quick builds' parts are 3,000 lines** (optimized ones keep 6,000), and the header and options
  are hashed once instead of once per part.
- **A precompiled header with clang.** Every part but part 0 uses one header compiled once and kept
  with the parts. On the 20,000-line program, an edit and `vu run` went from 0.92 s to 0.68 s
  (Rust: 0.79 s), and the first `vu run` from 4.99 s to 4.32 s (Rust: 5.16 s).
- **`vu build --debug` with clang adds `-fno-standalone-debug`**, which writes type information
  only where it's used, a third less time per part. An edit then takes 0.78 s against Rust's
  0.76 s, and the first build 6.39 s against 5.67 s, still a loss.
- **The front end makes fewer strings.** A chain `a + b + c + ...` of `Str` builds one string,
  with its length reserved once, instead of a string per `+`. `s + ""` of static text shares the
  text instead of copying it. Together they cut 13% of the instructions the front end runs on the
  20,000-line program (1.73 billion to 1.51 billion, callgrind). The wall time went from a minimum
  of 303 ms to 289 ms over 15 runs.

Where Vu still loses, and why:
- **The first optimized build**, by about 2x. gcc takes 20 to 30 ms a function at -O3 on Vu's C,
  spread over all its passes. No flag tried that keeps the code fast (less inlining, no
  vectorization, no unrolling, -O2) saved more than 15%; turning inlining off saved 39%. clang -O3 is slower still on this C, 97 s for the whole program. Leaner
  generated C is the likely fix, and it hasn't been tried.
- **n-body**, by 29% (`bench/compare.sh`, re-run today with every language on this VM). The Rust
  program's bodies are a fixed-size array, which LLVM unrolls fully and vectorizes in pairs. gcc
  doesn't do that even for C with a fixed-size array (2.53 s). clang does for Vu's C once the count
  is a constant and an unroll hint is added by hand (1.76 s), but clang makes binary-trees 40% and
  spectral-norm twice as slow (callgrind: clang's binary-trees runs 1.6 times the instructions,
  without gcc's partial inlining of the base case; for spectral-norm, clang reports that it can't
  vectorize the sum's loop without reordering the additions, and gcc's build runs twice as fast). So optimized builds stay with gcc.
- The others are now ties or wins on this VM. Spectral-norm (1.63 s against 1.78 s) and
  binary-trees are Vu's. fannkuch-redux (3%), nsieve (1%) and mandelbrot (1%) are close.

### Leaner C for faster optimized builds

The goal was to bring down the first optimized build (29.6 s, against Rust's 14.3 s on
`bench/rebuild`'s 20,000-line program). The method: measure what gcc spends its time on, in parts
of 50 to 200 of the program's functions and in programs of 100 functions of one kind each (the
minimum of 5 compiles).

- **What costs.** A function with an 8-pass loop of arithmetic costs gcc about the same as the same
  loop written by hand in C (9 ms a function at -O3): the arithmetic Vu writes isn't the problem.
  The costs are gcc's own: copying out short loops (complete peeling), and inlining the runtime's
  string helpers at every use. One `s + "a"` cost 9 ms a function, mostly from `vu_sfree_` (the
  small-string free list) inlined at every drop of a string.
- **`vu_sfree_` and `vu_str_concat` are no longer inlined.** `drop_Str` stays inline and checks
  for a buffer before calling. A string-building function compiled in half the time. The compiler's
  own front end, which frees strings constantly, wasn't slower (a minimum of 398 ms against 416 over
  9 runs).
- **`--param=max-completely-peeled-insns=100` for gcc** (the default is 200): 16% less time on
  functions with short loops. It didn't change five of the six benchmarks' binaries at all, and
  mandelbrot's ran in the same time.
- **Optimized split builds use parts of about 12,000 lines**, so the header is parsed half as many
  times: 10% less time than 6,000.

Together: the first optimized build went from 29.6 s to 21.2 s (Rust: 13.8 s). A rebuild after an
edit went from 3.2 s to 2.4 s (Rust: 14.0 s).

Tried, and not kept:
- A precompiled header with gcc: no faster (it loads a 15 MB file per part).
- Checking a whole arithmetic statement's overflow once instead of each operation (the tried
  loops' `vu_vf_*`): no faster.
- `-O2`, no vectorization, less GVN: 3 to 10% each.
- Limiting inlining of `inline` functions (`max-inline-insns-single=40`): 14% faster to compile, but
  spectral-norm ran 2.8 times as long.
- `noinline` on lists' growth and freeing: no change.

What's left is the measured gap: gcc does 1.8 times the CPU work on Vu's C that rustc does on the
Rust (42 s of CPU against 24 s, measured with `time`). Vu checks every Int operation and Rust's release builds don't,
which is about a fifth of gcc's time on arithmetic-heavy functions (19% on the program's typical
function when the checks are taken out).

### A benchmark on Railway

Railway is where people who build with AI deploy their backends, so the next measurement is there.
`bench/railway` has the same URL shortener on PostgreSQL twice: in Vu (`web`, `pg`) and in Node
(Express and node-postgres, the stack an agent usually picks). A load generator runs inside the
Railway project, and a workflow (`bench-railway`, run by hand) deploys all three and reports
requests/s, latency, memory, CPU and the monthly cost at Railway's prices. It needs the project's
token as the `RAILWAY_TOKEN` secret. On this machine first (`local.sh`, 2 cores shared with
PostgreSQL and wrk), Vu answered 7,093 requests/s in 5 MB and Node 3,689 in 138 MB, with Node using
3.4 times the CPU.

Building it found one gap: `net.listen` took IPv4 only, and Railway's private network reaches a
service over IPv6. A listener now takes both on one socket where the system has IPv6, and IPv4
alone where it doesn't. The http, net, web and WebSocket suites pass.

### Kept binaries and a new CPU

This machine's VM moved to a different CPU, and `vu run --release` began failing with "Illegal
instruction". Optimized builds use `-march=native`, but the keys of what Vu keeps (the `vu run`
binary cache, `VU_CACHE` and the split build's objects) didn't include the CPU, so a binary made for
the old CPU's AVX-512 instructions was reused on the new one. Those keys now include the CPU's model
and feature flags when a build uses `-march=native` (`/proc/cpuinfo` on Linux, `sysctl` on macOS).
The installed compiler had the same problem, being an optimized build itself; `compiler/build.sh`
recovers from that only by bootstrapping again from the seed (move `compiler/vuc` away first).

## Round 28: accounts for backend apps

The goal: an app with accounts on PostgreSQL, from `vu new api NAME` to Railway, with nothing
security-sensitive left for the person (or the model) writing it to get right.

**`std/auth`.** Password hashes are PBKDF2-HMAC-SHA256 with 600,000 iterations in Django's format
(`pbkdf2_sha256$600000$SALT$HASH`), so users can move between a Django app and a Vu app with their
passwords. Checking compares in constant time and refuses malformed hashes and ones asking for more
than 10 million iterations. Sessions are 32 random bytes; PostgreSQL keeps only their SHA-256.
`current_user` reads a Bearer token or the session cookie (HttpOnly, Secure, SameSite=Lax). CSRF
tokens are an HMAC of the session token. `tests/run_auth.sh` checks hashes both ways against Django
6.1 (60 random passwords per run, including Unicode, empty, 1,000-byte and invalid UTF-8 ones, and 14
malformed hashes), and sessions against PostgreSQL 16, plain and under the sanitizers.

**A hash no longer stalls a server.** A task runs until it waits, and a password hash takes 0.4 s
of CPU, so every connection on the same thread waited for it. `pbkdf2_sha256` now lets the other
tasks run every 16,384 iterations. Measured with one task thread: a task ticking every 2 ms saw a
longest gap of 14 ms during a 600,000-iteration hash, instead of the hash's 390 ms. (Targeted test
728 checks this with 64 tasks, so some share the hashing thread whatever the number of cores.)

**`pg.from_url`, `pg.pool`, `pg.give_back`.** Platforms give `DATABASE_URL`; parsing it was 40
lines in every app. The Railway benchmark's own parser had a bug the new tests found in the first
version of `from_url` too: a `%` two bytes from the end read past the string. `give_back` replaces a
connection that broke, so a database restart doesn't leave a pool of dead connections.

**`Shared` values can hold channels of anything.** The checker refused a `Shared` struct holding a
`Chan[pg.Db]`, because a `pg.Db` holds a connection. But a task takes a value out of a channel to own
it, so no two tasks use a connection at once. Targeted test 730 runs a pool of connections in a
`Shared` value from 10 tasks.

**`vu new api NAME`** writes a JSON API with sign-up, sign-in, sign-out, `/me` and per-user notes,
plus a Dockerfile and `railway.json` (`vu new web` gets a `railway.json` too). It hashes passwords
before taking a database connection, so a burst of sign-ins doesn't hold the pool. `run_auth.sh`
drives it over HTTP with 32 checks: cookies and Bearer tokens, wrong passwords, unknown emails,
another user's notes, a cross-site POST (403), logout, and a stored hash with 1,000 iterations
being upgraded at sign-in. CI runs `run_pg.sh` and `run_auth.sh` on Linux now (with Django).

A language gap showed up: a function value can't take a `var` parameter (by design: a closure could
hold the same variable), so handlers can't be `fn(var pg.Db, ...)` values. The template names its
routes in an enum and calls each handler with `&db` from one function.

Attack rounds: (1) malformed hashes, iteration limits, a 1 MB password (2,000 iterations in 6 ms:
the key is hashed once), tokens' alphabet and uniqueness over 2,000, CSRF with the wrong token,
session, secret or none: no findings. (2) `pg.from_url` on 13 URLs: found the `%` read past the end.
(3) the API template over HTTP: no findings beyond my test harness (it expected JSON from a 403).
