# vjq: jq in Vu

`vjq` is a command-line JSON processor that aims to be a drop-in replacement for jq 1.7.1: the
same command line, filter language, output bytes, error messages and exit codes. About 13,900
lines of Vu (`jv.vu` values, parsing and printing; `lang.vu` lexer and parser; `bison.vu` jq's
syntax errors; `run.vu` interpreter; `nat.vu` built-ins; `regex.vu` the regex engine; `mods.vu`
modules; `vjq.vu` the command line) plus `glue.c` for libm, time functions and file reading.
`builtins.vu` holds the parts of jq's own `builtin.jq` that are not native; `bisontab.vu` and
`unitab.vu` are tables generated from jq's parser and its Oniguruma (`tools/gen_bison.py`,
`tools/gen_unicode.py`).

    jq/test.sh                       # builds jq/vjq and runs jq's test suites through it
    ../vu build --release vjq.vu -o vjq
    vjq -c 'map(select(.x > 5))' data.json

## Install

Releases are tagged `vjq-vX.Y.Z` (vjq's own versions; every one behaves as jq 1.7.1). Linux x86-64
and ARM64 (static binaries: any distribution, glibc or musl) and macOS 12 or later (Apple silicon,
Intel). The release has bare binaries named as jq's release assets, so a line that downloads jq
changes only its URL:

```sh
curl -fsSL -o /usr/local/bin/jq https://github.com/vu0tran/vu/releases/download/vjq-v0.1.0/jq-linux-amd64
chmod +x /usr/local/bin/jq          # (jq-linux-arm64, jq-macos-amd64, jq-macos-arm64)

# or vjq and jq (a link) into ~/.local/bin, checked against the release's SHA256SUMS (-b DIR elsewhere)
curl -fsSL https://raw.githubusercontent.com/vu0tran/vu/main/packaging/tools/install.sh | sh -s -- vjq

# npm: the commands vjq and jq
npm install --save-dev @vu0tran/vjq
```

GitHub Actions, in place of `dcarbone/install-jq-action`: `- uses: vu0tran/vu/jq/action@vjq-v0.1.0`
puts `jq` (vjq) and `vjq` first on PATH. The archives `vjq-0.1.0-linux-amd64.tar.gz` (and
`linux-arm64`, `macos-amd64`, `macos-arm64`) hold `vjq` and `jq`.

The release binaries never load Oniguruma on Linux (they are static; on macOS a libonig is found
only in dyld's default paths): the few regex constructs vjq leaves to it (below, Regular expressions)
are then an error, everything else is vjq's own engine. A binary built from source
(`../vu build --release vjq.vu`, not static) still uses `libonig.so.5` when it is installed.

## What it does

- The whole jq 1.7.1 language: paths and assignment (`|=`, `+=`, `del`, `paths`, `getpath`,
  `setpath`, `to_entries`...), `reduce`/`foreach`/`label`/`try`/`?`, `limit`/`first`/`until`,
  `def` with filter and `$` parameters, recursion, string interpolation and `@format`s,
  `input`/`inputs`, `$__loc__`, regex built-ins (`test`, `match`, `capture`, `sub`, `gsub`,
  `splits`, `scan`, with vjq's own engine: see "Regular expressions"), dates (`strftime`, `strptime`, `mktime`, `gmtime`...),
  `tostream`/`fromstream`/`truncate_stream`, `INDEX`/`IN`, `env`/`$ENV`, `input_line_number`,
  `halt`/`halt_error`, `getpath`, `modulemeta`, `import`/`include` of code and data modules
  (`-L`, `~/.jq`, `$ORIGIN/../lib/jq`).
- Every option of jq 1.7.1, read by a port of jq's own option loop (see "Drop-in status").
- Numbers follow jq 1.7: doubles for arithmetic, but a number taken from the input or the
  program keeps its literal text until it is changed (`100000000000000000001` and `1.000` print
  as written; two literals compare exactly, as decimals). Printing uses jq's 17-digit shortest
  form rule. Object keys keep insertion order; `-S` sorts.
- jq's JSON parse errors word for word (`Unfinished JSON term at EOF at line 2, column 0`...),
  with jq's line numbering; jq's repair of invalid UTF-8 (U+FFFD); its 256-level print limit.
- jq's syntax errors word for word, several per program: `bison.vu` replays jq's bison parser
  (its LALR tables, taken from jq's `parser.c`) with its own port of jq's flex lexer, so the
  `unexpected X, expecting Y or Z` lists, bison's error recovery and the messages jq's grammar
  adds on the way (`May need parentheses around object key expression`, `Possibly unterminated
  'if' statement`...) come out as jq prints them. Undefined names are all reported, in jq's order
  (function by function; unused definitions dropped unchecked, as jq does).
- Path expressions as jq tracks them: jq keeps one current path and the value at it, and checks
  every path step against that value; vjq does the same (a value off the path keeps a record of
  the path still current), so `path(...)`, `|=`, `del`, `paths` give jq's results and its
  `Invalid path expression near attempt to iterate through ...` messages. Built-ins that are
  jq definitions in jq (`map`, `add`, `to_entries`, `unique_by`, `limit`...) run jq's own
  definition while a path is tracked, since jq's messages depend on their steps.
- Input is read in pieces as values are needed, file after file (files are opened when reached,
  so open errors come where jq reports them); input already used is dropped between top-level
  values, so a stream of documents runs in constant memory (13 MB for 92 MB of NDJSON, as jq).
  `--stream` events come from `input`/`inputs` too; on bad input the events before the error
  come out first, worded by a replay of jq's streaming parser. Raw input (`-R`, `-Rs`) is read
  the same way, in jq's 4095-byte `fgets` pieces (invalid UTF-8 repaired per piece, as jq does);
  the byte order mark is handled as jq's parser does (once, at the start of all input; `Malformed
  BOM`).
- Memory inside a run: `-n` with `input`/`inputs` compacts the value store as it goes (what the
  program can still reach is copied down, the rest dropped), so `reduce inputs as $x (...)` runs
  in constant memory as in jq. Accumulating programs don't copy their state at every step:
  `. + [$x]`, `.[$k] += 1`, `.[$k] += [$x]`, `.[$i] = $x` and `. + {($k): $v}` in a `reduce`
  change the state in place when nothing else can hold it (jq does this through its reference
  counts; vjq checks the reduce's body, see "Speed"), and `a + b` of a value at the end of the
  store makes a new view over it instead of a copy.
- Standard output is written where jq's glibc stdio writes it (blocks of `st_blksize` bytes, lines
  on a terminal, every output with `--unbuffered`) and standard error at once, so when both go to
  one file or pipe the messages land between the same bytes as jq's.

## Regular expressions

`regex.vu` is a backtracking engine written to behave like the Oniguruma jq 1.7.1 bundles (6.9.8,
read from its source where behavior is subtle), with jq's options: Oniguruma's Perl_NT syntax
(named groups and backreferences, `(?imsx-imsx)` and `(?i:...)` with Perl's scoping, look-ahead,
fixed-length look-behind, atomic groups, possessive and lazy quantifiers, `\Q...\E`, `\K`, `\R`,
`\N`, `\O`, `\p{...}`/`\P{...}` with all of Oniguruma's Unicode properties and scripts, POSIX
brackets), Unicode `\w \d \s \b`, case folding with Oniguruma's tables (multi-character folds such
as `ß` = `ss` unravelled as it does), jq's flags `g i x n s p l`, Oniguruma's error messages
(`Regex failure: end pattern with unmatched parenthesis`), and jq's character offsets. It follows
Oniguruma where that is not what a regex "should" do: the compiled form of each quantifier (which
decides what an empty iteration does), nested quantifiers reduced by its table, its empty checks
that compare captures, groups kept on its stack (a group entered again voids its end for
backreferences), its search optimizations that change results (a pattern that can only match
empty before `\z` tries once from the end; a leading greedy `(?s).*` or `\O*` tries only the start
and the next byte), and what a search restarted inside a character (jq does that after an empty
match) sees: a byte that only negated classes match.

The few constructs it doesn't do (absent groups `(?~...)`, callouts, subexpression calls
`\g<name>`, `\X`, `\y`, variable-length look-behind, raw `\xHH` bytes above 0x7F, nested classes
`[a[b]]` in some forms) go to Oniguruma (`libonig.so.5`, loaded with `dlopen`) when it is installed,
and are an error when it isn't. jq's test suites pass with Oniguruma unavailable (`VJQ_NO_ONIG=1`
turns the fallback off).

## How parity was checked

Every comparison runs jq 1.7.1 (the release binary) and vjq on the same input and compares stdout,
stderr and exit status byte for byte (vjq is run as `jq`, so messages name the same program).

| suite | what | result |
|---|---|---|
| jq's own tests (`jq/test.sh`) | jq.test, man.test, onig.test, base64.test, optional.test, run by `vjq --run-tests` as jq's `make check` runs them (MIT-licensed files from jq's tree; man.test needs `PAGER=less`, for jq too) | 447/447, 224/224, 40/40, 7/7, 3/3; the same with Oniguruma turned off |
| `tools/cli_test.py` | the command line (`tests/cli/cases.txt`, 130 cases: every option, stacking quirks, usage errors, files that are missing or unreadable, BOMs, raw input, `-f`, `--arg*` errors, `JQ_COLORS`, `NO_COLOR`, exit codes) | 128/130 (the 2 others: `--debug-dump-disasm`, `--debug-trace`) |
| `tools/mod_test.py` | modules (`tests/mods/`, 172 cases: search paths, `-L`, `~/.jq`, `$ORIGIN`, data modules, metadata, `modulemeta`, `get_search_list`, cycles, syntax errors in module files, missing modules, `include` and `import` forms) | 172/172 (2 more cases are commented out: jq crashes on them) |
| `tools/mix_test.py` | stdout and stderr into one pipe, and on a pty (`debug`, `stderr`, errors, `--unbuffered`, big outputs) | 28/28 |
| `tools/seq_test.py`, `tools/stream_test.py` | `--seq` input; `--stream`/`--stream-errors` on good and bad input | all identical |
| `tools/path_test.sh` | path expressions (`tests/paths.txt`, 64 programs on 5 inputs) | all identical |
| `tools/cmp_programs.py` | syntax and binding errors (`tests/syntax_errors.txt`, 127 programs) | 127/127 |
| `tools/gc_test.py` | `-n` programs over `inputs` that keep, drop and rebuild what they read, with the store compacted every few KB (`VJQ_GC_UNITS`), from a file and from a pipe | 39/39 |
| `tools/fuzz.py` | random filters (paths, assignment, reduce/foreach, try, regex, formats, sorting, 60 built-ins, random options) on random documents with jq 1.7 literals (`1.0`, `1E0`, big integers, `-0.0`, NUL, emoji) | 500/500 per seed; seeds 1, 3, 7 (1,000), 9 (300, sanitizer build) |
| `tools/synfuzz.py` | programs mutated at the token level (most no longer parse) | 500/500 (seeds 1, 3), 1000/1000 (seed 7) |
| `tools/rxfuzz.py`, `tools/rxbatch.py` | random Oniguruma patterns (classes, properties, groups, named groups, backreferences, look-around, atomic groups, every quantifier form, options, `\Q..\E`, `\K`) with random flags on random strings (ASCII, accents, CJK, `ß`, newlines), vjq without Oniguruma | rxbatch seeds 21-70: 250,000 patterns, 0 differ, 4 use a construct vjq leaves to Oniguruma |
| `tools/builtin_attack.py` | every built-in on inputs and arguments of every type, wrong ones included (81,900 calls) | 81,750 identical; the other 150: jq asserts (`strftime` on a non-string format) or neither finishes in 60 s (`repeat`, `until`) |
| `tools/misc_attack.py` | formats, dates under several `TZ`, output and input options, arguments, odd JSON (deep, big numbers, bad UTF-8, escapes) | 2416/2518; the other 102 are jq assertion failures (`strftime` of `1e300`) |
| `tools/inplace_attack.py` | random reduces and foreaches with update chains, shared and kept values (init variables, both sides of `a + b`, big objects' shared key indexes) printed after the run | 600/600 on each of seeds 2-9, 42-44; 300/300 on a sanitizer build |

Sanitizer builds (`vu build --san`: ASan and UBSan) ran the in-place attack, 3,000 regex patterns,
the compaction tests and the fuzzer with the same results and no report.

## Attack rounds

Each round wrote a new differential tool for one area and fixed what it found, until a run found
nothing; earlier rounds are in the git history.

1. Modules (`mod_test.py`): imports were processed in jq's reverse order, its search chain
   (`-L` paths through realpath, `~/.jq` loaded last, `$ORIGIN/../lib/jq`, `rel/jq/main.jq`,
   `rel/name.jq`), optional and raw metadata, per-file error counts, the "library should only have
   function definitions" message, module syntax errors through `bison.vu`; on the way the syntax
   list found constant folding for object keys and metadata (jq folds `{("a"): 1}` at parse time)
   and `$$$$name`.
2. Raw input and stdin (`cli_test.py` cases): `-R` read whole lines at once (jq reads 4095-byte
   pieces and repairs UTF-8 per piece), the BOM was dropped per file (jq: once, `Malformed BOM`
   otherwise), a file that couldn't be read didn't stop the main loop where jq does, and a big
   document on a pipe was parsed again for every piece (out of memory on `cat big.json | vjq .`).
3. Interleaving (`mix_test.py`): vjq's stdout went out in other block sizes than glibc's, so
   messages landed elsewhere in a shared pipe.
4. Memory (`gc_test.py` and the table in "Speed"): `-n` with `inputs` kept everything read and
   made until the run ended (`reduce inputs` grew with the input), and `-Rn` took 1.7 GB from
   exact-size reserves fragmenting glibc's heap.
5. Regex, first batch (`rxbatch.py`, 20,000 patterns): quantifier forms, nested quantifiers,
   look-behind position, the end-anchor search, isolated options, multi-character folds.
6. Built-ins (`builtin_attack.py`): literal numbers as distinct values for path checks, `getpath`
   through null with array keys, `delpaths` error order, `flatten`/`limit` with odd arguments,
   `range` with NaN, `exp10` as the release binary computes it, `pow10` missing from it.
7. Formats, dates and odd input (`misc_attack.py`): a number at the very end of the input read
   text already dropped (a bounds-check panic), jq's 256-place parser stack, line counts after a
   parse error, `$ENV` hidden by `--arg ENV`; and `reduce range(100000) as $i ([]; . + [$i])`
   was killed for memory (quadratic in vjq, linear in jq), which started round 8.
8. Accumulation (`inplace_attack.py` and the timings in "Speed"): `a + b`, `.[k] = v` and
   `.[k] += v` in a reduce copied the whole state at every step (and kept every copy).
9. Regex, 250,000 patterns (`rxbatch.py` seeds 21-70): a backreference to a group entered again
   moved backwards (an endless loop), errors for ranges that start or end with a class, bytes
   inside a character in classes, Oniguruma's capture-comparing empty checks and its
   `ReduceTypeTable` (a row was mistyped), `^` at the very end under `(?m)`, the leading `.*`
   search anchor.
10. Speed (callgrind, against the build before round 1): reading a big file had become 15% slower
   (round 2's end scan ran on files too); fixed, and the loops that check every byte rewritten.
11. Last round: `misc_attack.py`, `builtin_attack.py`, `inplace_attack.py` on new seeds, the
   fuzzers on new seeds, and sanitizer runs found nothing new.

## Speed

CPU time (user + system), best of 3, output checked byte-identical to jq's by sha256
(`tools/bench.py`), on 100 MB of generated records (`tools/gen_records.py`, 222,409 objects in one
array). Measured at the end of the latest round on a shared 2-core VM (load average about 1, with
a callgrind run on the other core): wall times there are noisy, CPU time was steadier.

| filter | vjq | jq | vjq memory | jq memory |
|---|---|---|---|---|
| `.` | 1.80 s | 6.76 s | 520 MB | 755 MB |
| `-c .` | 1.69 s | 6.46 s | 484 MB | 755 MB |
| `.[] \| .name` | 1.32 s | 3.55 s | 390 MB | 704 MB |
| `-c 'map(select(.x > 5)) \| length'` | 1.29 s | 3.76 s | 390 MB | 709 MB |
| `-c 'group_by(.address.city) \| map({city: .[0].address.city, n: length})'` | 1.86 s | 5.34 s | 399 MB | 729 MB |
| `reduce .[] as $r (0; . + $r.balance)` | 1.27 s | 3.68 s | 390 MB | 704 MB |
| `-c 'map(.tags \|= length) \| .[0]'` | 1.47 s | 4.87 s | 493 MB | 874 MB |
| `-c '[.[] \| {id, name, city: .address.city}] \| length'` | 1.38 s | 4.14 s | 437 MB | 792 MB |
| `-c 'reduce .[] as $r ({}; .[$r.address.city] += 1) \| length'` | 1.44 s | 4.81 s | 390 MB | 704 MB |
| `-c '[paths] \| length'` | 2.73 s | 11.40 s | 1007 MB | 1257 MB |

An earlier round measured gojq 0.12.18 and jaq 2.3.0 too (same machine, heavier load): on these
eight filters vjq took 1.2-2.3x less CPU than jaq and 2.6-3.2x less than gojq; not measured again.

Instructions (callgrind, `VU_MARCH=x86-64-v2` builds) against the build before this round's
changes (the commit before d97c802), on 3 MB of the same records, so the round's changes are
checked for regressions without the machine's noise:

| filter | before | now | change |
|---|---|---|---|
| `.` | 361 M | 355 M | -1.5% |
| `-c .` | 346 M | 339 M | -2.1% |
| `.[] \| .name` | 266 M | 260 M | -2.1% |
| `-c 'map(select(.x > 5)) \| length'` | 267 M | 262 M | -2.0% |
| `-c 'group_by(.address.city) \| map(...)'` | 297 M | 292 M | -1.8% |
| `reduce .[] as $r (0; . + $r.balance)` | 268 M | 262 M | -2.0% |
| `-c 'map(.tags \|= length) \| .[0]'` | 299 M | 290 M | -2.8% |
| `-c '[.[] \| {id, name, city: .address.city}] \| length'` | 277 M | 271 M | -1.9% |
| `-c 'reduce .[] as $r ({}; .[$r.address.city] += 1) \| length'` | 305 M | 282 M | -7.5% |
| `-c '[paths] \| length'` | 531 M | 495 M | -6.8% |
| `-c '[.[] \| tostream] \| length'` | 1204 M | 1152 M | -4.3% |
| `-c 'map(to_entries \| from_entries) \| length'` | 392 M | 367 M | -6.4% |
| `.` on one 18 MB document, a file | 1836 M | 1813 M | -1.2% |
| `.` on one 18 MB document, standard input (a file) | 3352 M | 1814 M | -46% |
| `-c .name` on 20 MB of NDJSON | 1471 M | 1473 M | +0.1% |
| `-R length` on 20 MB of NDJSON | 810 M | 912 M | +12.6% |

The one slower case, `-R`, was read whole into memory before (209 MB peak for 92 MB of input,
and without jq's per-piece UTF-8 repair); it now reads in jq's pieces in 13 MB, and its CPU time is
still below jq's (0.62-0.72 s against 0.82-0.85 s for 92 MB, the same machine).

Accumulating programs (`-n`, CPU and peak memory; jq frees by reference counts, vjq changes the
state in place where the reduce's body allows it, see "What it does"):

| program | vjq | jq |
|---|---|---|
| `reduce range(1000000) as $i ([]; . + [$i]) \| length` | 0.21 s, 110 MB | 0.86 s, 35 MB |
| `reduce range(1000000) as $i ({}; .["k\($i % 1000)"] += 1) \| length` | 0.67 s, 80 MB | 7.00 s, 12 MB |
| `reduce range(300000) as $i ({}; .["k\($i)"] = $i) \| length` | 0.52 s, 105 MB | 1.06 s, 53 MB |
| `reduce range(1000000) as $i (""; . + "ab") \| length` | 0.21 s, 34 MB | 0.40 s, 12 MB |
| `[range(1000000)] \| reduce .[] as $x ({}; .[($x % 100 \| tostring)] += [$x]) \| ...` | 0.94 s, 255 MB | 39.45 s, 41 MB |
| `reduce range(1000000) as $i ([range(1000)]; .[$i % 1000] += 1) \| add` | 0.42 s, 57 MB | 6.27 s, 12 MB |

Before round 8 the first of these took 1.5 s and 800 MB at 10,000 steps (quadratic), and the
group-by one ran out of memory.

Memory while reading (92 MB of NDJSON, or the 100 MB array; standard input from the file; peak
resident MB; outputs compared by sha256, all identical):

| options and program | vjq | jq |
|---|---|---|
| `-n 'reduce inputs as $x (0; .+1)'` | 14 | 14 |
| `-n '[inputs] \| length'` | 601 | 704 |
| `-n 'input \| .name'`, `first(inputs)`, `limit(5; inputs)` | 15 | 15 |
| `-s length` | 378 | 704 |
| `-R length` | 15 | 15 |
| `-Rs length` | 131 | 197 |
| `-Rn '[inputs] \| length'` | 147 | 186 |
| `-nR 'reduce inputs as $l (0; .+1)'` | 15 | 15 |
| `-c '.[1000]'` (the array) | 386 | 704 |
| `length` (the array) | 385 | 704 |
| `-c .name` | 18 | 15 |

Why vjq is fast: values are 16-byte handles into one store; strings are spans of the input buffer
until changed; object keys are interned; the per-input store is reset after each top-level result.

## Drop-in status

Command line (jq 1.7.1's `--help` and `main.c`), read the way jq's own option loop reads it:
options are recognized in jq's order, short options stack (`-nr`; a letter given twice, `-nn`, is
an unknown option, as in jq), `-L` takes the rest of its argument or the next one, `-f` is a flag
and the filter argument names the file, the first non-option is the filter and the rest are
input files (or `--args`/`--jsonargs` values), and messages name the program as it was run.

| option | status |
|---|---|
| `-n` `-R` `-s` `-c` `-r` `-j` `-a` `-S` `-C` `-M` `-e` `--tab` `--indent n` (-1..7) | supported |
| `--raw-output0` `--unbuffered` `--seq` (input and output) `--stream` `--stream-errors` | supported |
| `-f file` (jq's `#!` handling) `-L dir` `-Ldir` | supported |
| `--arg` `--argjson` `--slurpfile` `--rawfile` `--args` `--jsonargs` (first definition wins; jq's errors) | supported |
| `$ARGS`, `$ENV`, `$__loc__`, `$JQ_BUILD_CONFIGURATION`, `input_filename`, `input_line_number` | supported |
| `-h` `--help` (jq's text) `-V` `--version` `--build-configuration` `--run-tests file` | supported |
| `-b` (Windows only in jq: accepted, no effect) | supported |
| `--debug-dump-disasm` `--debug-trace` `--debug-trace=all` | accepted, print nothing (no bytecode) |
| `JQ_COLORS` (8 colors), `NO_COLOR`, colors by default on a terminal | supported |
| `~/.jq`, `$ORIGIN/../lib/jq`, `$ORIGIN/../lib` module search | supported |
| exit codes (0, 1/4 with `-e`, 2 usage and file errors, 3 compile errors, 5 runtime and parse errors, `halt_error` codes) | supported |

Coverage: the whole jq 1.7.1 language and its 200+ built-ins (jq's test suites pass); jq 1.8
additions are left out on purpose, since a drop-in for 1.7.1 must reject them as 1.7.1 does.

Status: on every suite and attack tool in "How parity was checked" vjq's stdout, stderr and exit
status are jq's, apart from the cases listed here; it was never seen to crash (sanitizer builds
included) where jq doesn't.

Known differences (everything else measured above is identical):

- `--debug-dump-disasm` and `--debug-trace` are accepted but print nothing. They print jq's
  bytecode and its interpreter's stack: matching them means compiling to jq's bytecode exactly as
  `compile.c` does (about 1,400 lines of C, with the parser actions and builtin binding that shape
  it) and, for the trace, running jq's VM with its reference counts as printed (`execute.c`, about
  1,350 lines more). Estimated at 3,000-5,000 lines of Vu for the dump and 10,000 or more for the
  trace; not done.
- Where jq 1.7.1 crashes, vjq reports an error instead: an import cycle (jq overflows its stack),
  `include "x" {as: 1}` (jq asserts), `strftime`/`strflocaltime` with a non-string format or on a
  time such as `1e300` (jq asserts).
- jq's "function compiled to N bytes which is too long" limit is not emulated.
- Regex: the constructs listed under "Regular expressions" need Oniguruma; in the last 250,000
  fuzzed patterns nothing else differed (rarer cases may remain).
- Memory: a `reduce` keeps its state in place only when its body is a chain of updates of `.` (or
  `. + x`) whose right sides can't keep a second reference to the state; any other accumulating
  program allocates a new state each step, and inside one run (`-n`, or one input) nothing is
  freed until the run ends, so such programs can use much more memory than jq (jq frees by
  reference counts). Reading (`-n` with `input`/`inputs`, `-s`, `-R`, `-Rs`) takes no more memory
  than jq (table in "Speed").
