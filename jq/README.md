# vjq: jq in Vu

`vjq` is a command-line JSON processor that aims to behave exactly like jq 1.7.1: the same filter
language, the same output bytes, the same error messages and exit codes. About 8,800 lines of Vu
(`jv.vu` values, parsing and printing; `lang.vu` lexer and parser; `run.vu` interpreter;
`nat.vu` built-ins; `mods.vu` modules; `vjq.vu` the command line) plus `glue.c` for libm, time
functions and Oniguruma. `builtins.vu` holds the parts of jq's own `builtin.jq` that are not native.

    jq/test.sh                       # builds jq/vjq and runs jq's test suites through it
    ../vu build --release vjq.vu -o vjq
    vjq -c 'map(select(.x > 5))' data.json

## What it does

- The whole jq 1.7.1 language: paths and assignment (`|=`, `+=`, `del`, `paths`, `getpath`,
  `setpath`, `to_entries`...), `reduce`/`foreach`/`label`/`try`/`?`, `limit`/`first`/`until`,
  `def` with filter and `$` parameters, recursion, string interpolation and `@format`s,
  `input`/`inputs`, `$__loc__`, regex built-ins (`test`, `match`, `capture`, `sub`, `gsub`,
  `splits`, `scan`, through Oniguruma), dates (`strftime`, `strptime`, `mktime`, `gmtime`...),
  `tostream`/`fromstream`/`truncate_stream`, `INDEX`/`IN`, `env`/`$ENV`, `input_line_number`,
  `halt`/`halt_error`, `getpath`, `modulemeta`, `import`/`include` of code and data modules
  (`-L`, `~/.jq`, `$ORIGIN/../lib/jq`).
- Options: `-n -s -r -j -a -c -C -M -S -e --tab --indent N --arg --argjson --slurpfile
  --rawfile --args --jsonargs -f -L --stream --seq --unbuffered --raw-output0 -R
  --run-tests`, `JQ_COLORS`, colors by default on a terminal.
- Numbers follow jq 1.7: doubles for arithmetic, but a number taken from the input or the
  program keeps its literal text until it is changed (`100000000000000000001` and `1.000` print
  as written; two literals compare exactly, as decimals). Printing uses jq's 17-digit shortest
  form rule. Object keys keep insertion order; `-S` sorts.
- jq's JSON parse errors word for word (`Unfinished JSON term at EOF at line 2, column 0`...),
  with jq's line numbering; jq's repair of invalid UTF-8 (U+FFFD); its 256-level print limit.

## How parity was checked

- jq 1.7.1's own test files, run by `vjq --run-tests` the way jq's `make check` runs them
  (`jq/test.sh`; files copied from jq's source tree under its MIT license): **jq.test 447/447,
  man.test 224/224, onig.test 40/40, base64.test 7/7, optional.test 3/3** (721/721). man.test
  needs `PAGER=less` set for 2 cases, for jq too.
- Differential fuzzing (`tools/fuzz.py VJQ JQ N SEED`): random filters (paths, assignment,
  reduce/foreach, try, regex, formats, sorting, 60 built-ins, random options) on random
  documents with jq-1.7-specific literals (`1.0`, `1E0`, big integers, `-0.0`, NUL, emoji),
  comparing stdout, stderr and exit status byte for byte with jq 1.7.1. Last run, ten seeds of
  300 cases: **2980 of 3000 identical**. The 20 that differ are listed under "Not done".

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

## Not done

- Syntax errors: jq's bison parser lists expected tokens (`unexpected X, expecting Y`) in some
  states and reports several errors in one program; vjq gives the `expecting` part only for
  object constructions and `@format` strings, and stops at the first error.
- Path expressions: jq's message for an invalid path names the operation that broke it
  (`Invalid path expression near attempt to iterate through ...`), and in a few nested cases
  (a path through `map`, `unique_by` or `$__loc__` after a non-path) jq tracks paths differently;
  vjq says `Invalid path expression with result ...` or, rarely, returns a result where jq errs.
  Most fuzz differences left are these.
- `--seq` writes jq's record separators, but input is not read as RS-separated records (jq
  reports and skips broken records); `--stream-errors` is missing; `$__prog_args` is `null`
  where jq reports it undefined; `debug` output is not colored.
- Standard input is kept whole while it is read (memory grows with input as in jq; not
  compacted between documents).
- Regex needs `libonig.so.5` at run time (loaded with `dlopen`; without it regex built-ins
  report an error).
- Additions after 1.7.1 (jq 1.8's `@base32d` fix, `ltrimstr` changes, `have_decnum`...) are left out
  on purpose: the jq 1.7.1 binary says `base32 is not a valid format`, and so does vjq.
