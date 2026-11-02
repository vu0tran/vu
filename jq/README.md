# vjq: jq in Vu

`vjq` is a command-line JSON processor that aims to be a drop-in replacement for jq 1.7.1: the
same command line, filter language, output bytes, error messages and exit codes. About 11,900
lines of Vu (`jv.vu` values, parsing and printing; `lang.vu` lexer and parser; `bison.vu` jq's
syntax errors; `run.vu` interpreter; `nat.vu` built-ins; `regex.vu` the regex engine; `mods.vu`
modules; `vjq.vu` the command line) plus `glue.c` for libm, time functions and file reading.
`builtins.vu` holds the parts of jq's own `builtin.jq` that are not native; `bisontab.vu` and
`unitab.vu` are tables generated from jq's parser and its Oniguruma (`tools/gen_bison.py`,
`tools/gen_unicode.py`).

    jq/test.sh                       # builds jq/vjq and runs jq's test suites through it
    ../vu build --release vjq.vu -o vjq
    vjq -c 'map(select(.x > 5))' data.json

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
  come out first, worded by a replay of jq's streaming parser.

## Regular expressions

`regex.vu` is a backtracking engine written to behave like the Oniguruma jq 1.7.1 bundles, with
jq's options: Oniguruma's Perl_NT syntax (named groups and backreferences, `(?imsx-imsx)` and
`(?i:...)` with Perl's scoping, look-ahead, fixed-length look-behind, atomic groups, possessive
and lazy quantifiers, `\Q...\E`, `\K`, `\R`, `\N`, `\O`, `\p{...}`/`\P{...}` with all of
Oniguruma's Unicode properties and scripts, POSIX brackets), Unicode `\w \d \s \b`, simple case
folding (Oniguruma's tables), jq's flags `g i x n s p l`, Oniguruma's error messages
(`Regex failure: end pattern with unmatched parenthesis`), and jq's character offsets (including
its counting when an empty match lands inside a character). The few constructs it doesn't do
(absent groups `(?~...)`, callouts, subexpression calls `\g<name>`, `\X`, `\y`, variable-length
look-behind, raw `\xHH` bytes above 0x7F, multi-character case folds such as `ß` = `ss`) go to
Oniguruma (`libonig.so.5`, loaded with `dlopen`) when it is installed, and are an error when it
isn't. jq's test suites pass with Oniguruma unavailable (`VJQ_NO_ONIG=1` turns the fallback off).

## How parity was checked

- jq 1.7.1's own test files, run by `vjq --run-tests` the way jq's `make check` runs them
  (`jq/test.sh`; files copied from jq's source tree under its MIT license): **jq.test 447/447,
  man.test 224/224, onig.test 40/40, base64.test 7/7, optional.test 3/3** (721/721). man.test
  needs `PAGER=less` set for 2 cases, for jq too. The same 721/721 with Oniguruma turned off.
- Differential fuzzing (`tools/fuzz.py VJQ JQ N SEED`): random filters (paths, assignment,
  reduce/foreach, try, regex, formats, sorting, 60 built-ins, random options) on random
  documents with jq-1.7-specific literals (`1.0`, `1E0`, big integers, `-0.0`, NUL, emoji),
  comparing stdout, stderr and exit status byte for byte with jq 1.7.1. FUZZ_MAIN
- Syntax fuzzing (`tools/synfuzz.py JQ VJQ N SEED`): jq programs mutated at the token level
  (tokens deleted, duplicated, inserted, swapped; most no longer parse). FUZZ_SYN
- Regex fuzzing (`tools/rxfuzz.py JQ VJQ N SEED`): random Oniguruma patterns (classes,
  properties, groups, named groups, backreferences, look-around, atomic groups, every quantifier
  form, options, `\Q..\E`, `\K`) with random flags on random strings (ASCII, accents, CJK, `ß`,
  newlines), `[match(re; flags)]` compared, vjq run without Oniguruma. FUZZ_RX
- Targeted lists, each run against jq 1.7.1 (stdout, stderr, status): the command line
  (`tools/cli_test.py`, 101 cases: every option, option stacking quirks, usage errors, files,
  `-f`, `--arg*` errors, `JQ_COLORS`, `NO_COLOR`, exit codes; 99 identical, the 2 others are
  `--debug-dump-disasm` and `--debug-trace`, which print jq's bytecode); `--seq` input
  (`tools/seq_test.py`, 186 runs, all identical); `--stream`/`--stream-errors` on bad input
  (`tools/stream_test.py`, 108 runs, all identical); path expressions (`tools/path_test.sh` on
  `tests/paths.txt`, 64 programs on 5 inputs, all identical); syntax and binding errors
  (`tools/cmp_programs.py` on `tests/syntax_errors.txt`, 127 programs, all identical).

## Speed

CPU time (user + system), best of 3, output checked byte-identical to jq's by sha256
(`tools/bench.py`; `*`: gojq's output differs because it sorts object keys). Measured on a shared
2-core VM with load average around 8, so wall times were noisy; CPU time was steadier.
jq 1.7.1, gojq 0.12.18 and jaq 2.3.0 are the release binaries from GitHub.

100 MB of generated records (`tools/gen_records.py`, 222,409 objects in one array):

| filter | vjq | jq | gojq | jaq |
|---|---|---|---|---|
| `.` | 1.74 s | 7.47 s | 4.69 s* | 4.00 s |
| `-c .` | 1.63 s | 7.42 s | 4.93 s* | 3.20 s |
| `.[] \| .name` | 1.34 s | 4.08 s | 4.31 s | 1.99 s |
| `-c 'map(select(.x > 5)) \| length'` | 1.41 s | 4.46 s | 3.73 s | 1.85 s |
| `-c 'group_by(.address.city) \| map({city: .[0].address.city, n: length})'` | 1.86 s | 6.59 s | 4.77 s | 2.68 s |
| `reduce .[] as $r (0; . + $r.balance)` | 1.32 s | 4.19 s | 4.06 s | 1.97 s |
| `-c 'map(.tags \|= length) \| .[0]'` | 1.59 s | 5.36 s | 4.56 s* | 1.91 s |
| `-c '[.[] \| {id, name, city: .address.city}] \| length'` | 1.30 s | 4.49 s | 3.69 s | 2.65 s |

Peak resident memory on these: vjq 400-590 MB, jq 704-874 MB, gojq 560-930 MB, jaq 803-834 MB.

26 MB of GitHub events (`large-file.json` from github.com/json-iterator/test-data):

| filter | vjq | jq | gojq | jaq |
|---|---|---|---|---|
| `.` | 0.31 s | 1.62 s | 0.96 s* | 0.67 s |
| `-c .` | 0.30 s | 1.46 s | 0.81 s* | 0.50 s |
| `-c '.[] \| {id, type, repo}'` | 0.23 s | 0.74 s | 0.63 s | 0.33 s |
| `-c 'group_by(.type) \| map([.[0].type, length])'` | 0.26 s | 0.74 s | 0.62 s | 0.29 s |
| `-c '.[] \| select(.payload.size > 1)'` | 0.22 s | 0.74 s | 0.53 s | 0.31 s |
| `-r '.[].actor.login'` | 0.23 s | 0.75 s | 0.57 s | 0.30 s |

Why: values are 16-byte handles into one store; strings are spans of the input buffer until
changed; object keys are interned; the per-input store is reset after each top-level result.

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

Known differences:

- `--debug-dump-disasm` and `--debug-trace` print nothing (vjq has no bytecode to show).
- Regex: the constructs listed under "Regular expressions" need Oniguruma; quantified groups that
  can only match empty in Oniguruma's own optimized ways (e.g. `(\z(?<!\d)){2,}?`) and searches
  restarting inside a multi-byte character after an empty match (`"日" | [match("\\W*"; "g")]`)
  can differ; the regex fuzz finds these about once in 300 patterns.
- `-n` with `input`/`inputs`, `-s` and `-R` hold the input they read (values may point into it);
  only the main loop over top-level values runs in constant memory.
- Module files: their syntax errors are reported vjq's way (not replayed through `bison.vu`).
- jq's quirk of starting a regex search in the middle of a character after an empty match is
  followed for offsets but not always for what the next match is.
