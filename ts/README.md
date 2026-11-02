# vtsc: a TypeScript type checker written in Vu

`vtsc` checks TypeScript the way `tsc --noEmit --strict` does and prints the same errors (each
error's first line, as `tsc --pretty false` prints it), with TypeScript's own lib files. It is
about 17,000 lines of Vu in this directory.

```
cd ts && ../vu build --release vtsc.vu -o vtsc
VTSC_LIB=node_modules/typescript/lib ./vtsc --target esnext src/**/*.ts
```

Flags: `--lib DIR` (TypeScript's lib files; else `VTSC_LIB`, else `node_modules/typescript/lib`),
`--target es2025|esnext|...`, `--jobs N` (workers; the default is the core count for 64 or more
files), `--time` (phase times), `--parse-only` (parse the files and report the time).

A file that uses something vtsc doesn't model yet isn't guessed at: it is listed on stderr as
`not checked`, with the construct and where it is, and so is every file that imports it. Every
file it does check gets exactly the errors tsc 7 reports for it.

## Speed

date-fns (`pkgs/core/src`, 1334 files, 2.0 MB of TypeScript), on a 2-core Intel Xeon @ 2.80GHz
VM, best of 5 runs, wall clock (`ts/bench.sh` with `ts/bench_parse.mjs`; measured
2026-11-01):

| type checking (`--noEmit --strict`) | ms |
|---|---|
| vtsc (2 workers) | 566 |
| vtsc (1 thread) | 867 |
| tsc 7.0.2 (Go) | 1660 |
| tsc 7.0.2, `--checkers 1 --singleThreaded` | 1999 |
| tsc 6.0.3 (JavaScript) | 8746 |

vtsc checks 1210 of the 1334 files; it lists the other 124 as not checked (generic call
patterns, spreads into overloads, and the like), so the comparison is close to, not exactly, the
same work. It reports no error tsc doesn't on the files it checks.

| parsing only (sources in memory) | ms |
|---|---|
| vtsc | 52 |
| Bun 1.x `Transpiler.scan` | 52.5 |
| oxc-parser (from Node) | 67 |
| TypeScript 5.9 `createSourceFile` | 227 |
| @swc/core `parseSync` (from Node) | 298 |
| esbuild `transformSync` (no parse-only API: parse, lower, print) | 1512 |

The Node and Bun numbers include their bindings' cost of handing the result to JavaScript (oxc's
native parser alone is faster than its Node binding); vtsc builds its whole AST in the same
process.

With more than one worker, each worker parses every file, checks its part of them (contiguous
parts of the import order, balanced by size), and resolves the declarations its files import
from other parts; the files not checked are merged over all workers. The output doesn't depend
on the number of workers (checked on date-fns, ky, redux, zod and remeda with 1, 2 and 3).

## What it checks

Expressions, statements and declarations with tsc's errors and messages: assignability with
elaboration (TS2322, TS2345, TS2741, TS2739/2740, TS2559, TS2353, TS2820 spelling suggestions),
calls and overloads (TS2769 at the last overload's argument, reorderCandidates), generic
inference, narrowing (typeof, instanceof, in, equality, discriminants, type predicates,
assignments, loops to a fixpoint), classes, interfaces, modules and imports, async functions and
generators, tuples with optional and rest elements, conditional, indexed access, keyof, mapped
and finite template literal types with their base constraints, comparability for type
assertions, alias variances, `@ts-expect-error`/`@ts-ignore`, and the binder's duplicate and
redeclaration errors.

## How it's tested

Against tsc 7 itself: generated programs (classes, modules, generics, spreads, instanceof, flow,
names, declarations, members, methods, async, loops, tuples, and generic programs with conditional
types, keyof, `T[K]`, assertions and overloads), each run through both checkers and compared line
for line; a set of hand-written programs; and real projects (date-fns, ky, redux, zod, remeda,
immer, zustand, jotai, p-queue, reselect), where every checked file must get tsc's errors.

The generics generator (`gen_gx.py`), added with this round, found in its rounds: generic
assertions compared by assignability instead of comparability (false TS2352 for type parameters,
unions and object types), type literals instantiated when they mention no type parameter, a
conditional's alias kept on the type it resolved to, `keyof` of a mapped type, of a type with a
string index signature alone and of numeric keys, string-index-only access, intersections inside
unions printed without parentheses, `object` printed as `Object` in TS7053, a key union split in
TS7053, TS2769's location, overload order across merged lib declarations, IntersectionState
(implicit index signatures inside an intersection source, weak type checks inside an
intersection target), the restrictive instantiation of a conditional, and subtype instead of
assignability in type-predicate narrowing. What it still finds (about 1% of lines): substitution
types in a conditional's true branch (`T & U` printed as `T`), and an assertion from a type
parameter constrained to `{}` against a union.

# vlint: an oxlint-compatible linter written in Vu

`vlint` checks JavaScript and TypeScript (`.js .mjs .cjs .jsx .ts .mts .cts .tsx`) with oxlint's
96 default rules (the correctness rules that need no type information: `eslint/*`, `typescript/*`,
`unicorn/*`, `oxc/*`) and prints each diagnostic the way `oxlint -f unix` does. It reuses vtsc's
scanner and parser, plus a scope builder (`scope.vu`), a regular-expression parser (`regex.vu`)
the rules (`rules.vu`) and, for `--fix`, a printer of expressions as oxc prints them
(`fixgen.vu`): about 7,700 lines of Vu.

```
cd ts && VU_SPLIT=off ../vu build --release vlint.vu -o vlint   # one C file: the fastest binary
./vlint [--jobs N] [--cache] [--cache-location PATH] src/   # files, or folders searched for the extensions above
./vlint --fix src/             # rewrites the files as `oxlint --fix` does (see below)
```

It honors `eslint-disable`/`oxlint-disable` comments, and reports parse errors with oxc's
messages where they're known (redeclarations, invalid characters).

## The cache

`vlint --cache` works like `eslint --cache`: it keeps each file's output in `.vlintcache` in the
current directory (ESLint's default place, `.eslintcache`), or in `--cache-location PATH` (a folder,
or a path ending in `/`, gets `PATH/.vlintcache`; ESLint names the file after a hash of the current
directory there). A later run prints the saved lines of files that haven't changed without parsing
them, lints the rest, and saves the cache again only if something changed. The output is the same
bytes in the same order as without the cache. The code is `lcache.vu` (with `lcache_glue.c` for
`stat`) and `cached_run` in `vlint.vu`; the path without `--cache` is unchanged.

- The cache as a whole is keyed by a hash of the vlint executable (`/proc/self/exe`), a version
  string and the options that change the output, so a rebuilt vlint or other rules start over. Where
  the executable can't be read, nothing is cached.
- Each file's entry holds its path (as printed), size, modification and change times (ns), inode, a
  64-bit content hash (xxHash64's word step, one lane) and the output lines. A file whose size,
  times and inode all match is a hit without being read. Otherwise it's read and hashed (in the
  workers), and a matching size and hash is still a hit (a fresh checkout, a copied tree, `touch`).
  Times less than 2 s old aren't trusted, as git does with its index ("racy" files): such a file is
  saved without them, so the next run checks its content. A file edited to the same size with its
  modification time put back is caught by its change time.
- Entries of files outside this run are kept while the file exists; deleted files' are dropped.
- The file is one header line (`vlintcache1`, the key, the record count, the body's length and its
  hash) and length-prefixed records. A truncated, corrupt or foreign file is ignored and rebuilt. It's
  written to a temporary file with a unique name and renamed, so concurrent runs each leave a whole
  cache (the last one wins). 660 KB for the 3,445-file corpus, 5 MB for vscode/src (ESLint's: 3.2 MB
  for the corpus).

Checked (`cache_verify.sh`): on that corpus, the `node_modules` JavaScript, preact, excalidraw and
vscode/src the output without a cache, with a cold one, a warm one, in a copy of the tree (new inodes
and times) and, in that copy, after appending to, truncating, deleting and adding 1% of the files each
and changing a byte of 1% more without changing their size or modification time, is identical
(first cached run and the next). Also: truncated, bit-flipped, random, empty and crafted cache files
(lengths past the end, 20-digit numbers, a folder in its place, a location in a missing folder) give
the same output and the cache is rebuilt; six runs at once on one cache, twice, give the right output
and a valid cache; the sanitizer build (ASan, UBSan) is clean on cold and warm runs.

Measured (`cache_bench.py`, copies of the trees in `/dev/shm`, CPU = user + system, best of 5 for
the corpus and of 3 for vscode/src; 1% changed = a line appended to 1% of the files before each run,
starting from the warm cache). The machine is the same loaded 2-core VM (load average 7 to 11 during
these runs), so wall times are inflated and noisy; CPU times are the comparison:

| 3,445-file corpus (11.9 MB) | 1 thread CPU s | wall s | all cores CPU s | wall s |
|---|---|---|---|---|
| vlint, no cache | 0.50 | 1.37 | 0.50 | 1.56 |
| vlint `--cache`, cold (writes it) | 0.58 | 1.51 | 0.51 | 1.57 |
| vlint `--cache`, warm | 0.030 | 0.072 | 0.028 | 0.084 |
| vlint `--cache`, warm, 1% changed | 0.041 | 0.106 | 0.037 | 0.119 |
| oxlint 1.90.0 (it has no cache) | 0.57 | 1.46 | 0.62 | 1.59 |
| ESLint 10.14 `--cache`, cold | 67.3 | 144 | | |
| ESLint `--cache`, warm | 2.69 | 4.41 | | |
| ESLint `--cache`, warm, 1% changed | 5.17 | 9.23 | | |

| vscode/src (11,260 files) | 1 thread CPU s | wall s | all cores CPU s | wall s |
|---|---|---|---|---|
| vlint, no cache | 6.99 | 17.0 | 6.71 | 14.4 |
| vlint `--cache`, cold | 7.22 | 15.9 | 6.84 | 11.5 |
| vlint `--cache`, warm | 0.087 | 0.23 | 0.086 | 0.18 |
| vlint `--cache`, warm, 1% changed | 0.160 | 0.41 | 0.154 | 0.31 |
| oxlint | 6.64 | 13.8 | 7.38 | 19.3 |

In instructions (callgrind, the corpus, one thread), which the load doesn't disturb: no cache
2,352 M (the build before the cache: 2,406 M), cold cache 2,399 M (+2%: hashing and writing), warm
cache 44 M (1.9%: hashing the executable, reading and checking the cache, a map of paths; the rest of
a warm run is `stat` and directory reading). A warm run takes 17 times less CPU than linting the
corpus and 80 times less on vscode/src, and 90 times less than ESLint's warm cache. The cold runs'
extra CPU time in the tables (up to 16%) is mostly noise from the load: the instruction count says 2%. ESLint was measured on the corpus only (its cold run on
vscode/src would take many minutes on this machine).

## Matching oxlint

`lint_diff.py` runs oxlint 1.90.0 (`-c` an empty config, `--disable-nested-config`) and vlint on
the same files and compares every diagnostic (position, rule, message, help). On date-fns, zod,
remeda, immer, jotai, ky, mitt, p-queue, redux and reselect (3,445 files), JavaScript from
`node_modules`, preact, excalidraw, vscode (11,000 diagnostics) and a set of hand-written probe
files, every warning matches: no missing ones, no extra ones. What still differs is parse errors
in a few vscode test fixtures that oxc rejects and vlint accepts (duplicate class methods,
TypeScript syntax in `.js` files).

## Speed

The TypeScript corpus above (3,445 files, 11.9 MB), user CPU time (best of 5), on a 2-core Intel
Xeon @ 2.80GHz VM that was heavily loaded by other jobs (load average 4 to 9), so wall-clock times
aren't meaningful and the CPU times are noisy (`lint_bench.sh`; measured 2026-11-01):

| linter | CPU s (run 1) | CPU s (run 2) |
|---|---|---|
| vlint, 1 thread | 0.55 | 0.65 |
| oxlint 1.90.0, `--threads 1` | 0.55 | 0.64 |
| vlint, all cores | 0.65 | 0.63 |
| oxlint, all cores | 0.56 | 0.60 |
| Biome 2.6.4 `lint` (its recommended rules), all cores | 7.3 | |
| ESLint 10.14 + typescript-eslint parser, the same 56 core rules, 1 thread | 72.3 | |

So vlint runs about as fast as oxlint (written in Rust) and does the same work: 13 times less CPU
than Biome and 130 times less than ESLint. Biome runs a different (larger) rule set, so its line
compares the cost of a lint pass, not the same checks. On vscode/src (11,260 files, single thread,
loaded machine) vlint took 7.9 to 8.6 s of CPU against oxlint's 7.2 to 7.5 s. All of this was
measured on a busy machine: it needs repeating on an idle one.

What made it fast, measured in instructions (callgrind, zod): a keyword recognizer reading the
source bytes instead of a map lookup; identifiers interned straight from the source with an FNV
table (no string per identifier); a small name table per file, which stays in the cache; arrays
instead of hash maps for node-keyed data and a name-chained scope table; the source lent to the
parser rather than copied; and an 8-bytes-at-a-time scan for irregular whitespace. Together these
cut instructions by 24% and CPU time by about 25%.

## `--fix`

`vlint --fix` rewrites each file exactly as `oxlint --fix` does and prints the diagnostics that are
left. What oxlint does, read from its source (oxc `oxlint_v1.90.0`, `crates/oxc_linter/src/fixer`,
`context/mod.rs`, `service/runtime.rs`) and checked against it:

- Each fix has a kind. `--fix` applies only plain safe fixes; `--fix-suggestions` applies only
  suggestions; `--fix-dangerously` applies everything (safe, suggestions, dangerous). vlint
  implements `--fix` only and refuses the other two.
- Of the 96 default rules, 19 produce safe fixes: `eslint/no-compare-neg-zero` (not for `===`),
  `no-extra-boolean-cast` (`Boolean(x)` calls, not `!!x`), `no-unsafe-negation`, `no-unused-labels`,
  `no-useless-escape`, `no-useless-rename`, `use-isnan` (`==`-style comparisons), `valid-typeof`
  (`undefined`), `typescript/no-extra-non-null-assertion`, `no-useless-empty-export`,
  `no-wrapper-object-types` (type references), `prefer-as-const`, `prefer-namespace-keyword`,
  `unicorn/no-single-promise-in-promise-methods`, `no-unnecessary-await`,
  `no-useless-fallback-in-spread`, `no-useless-spread` (declared "dangerous" but its fixes are made
  as safe ones, and applied), `prefer-set-size`, `prefer-string-starts-ends-with`. Many of these
  only fix some cases (oxlint's conditions are mirrored rule by rule). The others' fixes
  (`no-unused-vars`, `no-debugger`, `for-direction`, `erasing-op`, ...) are suggestions or dangerous.
- One pass: the fixes are sorted by their span and applied left to right; a fix that starts at or
  before the end of the last applied one (touching counts) is skipped. The file isn't linted
  again, so a fix that uncovers a new problem leaves it for the next run, and two adjacent escapes
  (`"\-\."`) need two runs.
- The output lists the diagnostics whose fix wasn't applied (no fix, a skipped one, or one
  disabled by a comment), at their positions in the original text. Files that don't parse are left
  alone. With an agent detected (as here) oxlint prints one line per diagnostic and no summary,
  which is what vlint prints.

Two `no-useless-spread` fixes (`{...{a: 1}}` and `[...[a], ...[b]]`) print new code with oxc's code
generator rather than copying text, so `fixgen.vu` prints expressions the way `oxc_codegen` does
(single quotes and its escapes, numbers like `1e3` and `.5`, parentheses from precedence, objects
of two or more properties on separate lines with tabs, oxc's `pife` parentheses, comments dropped).
It covers expressions, simple functions and arrow functions (return, expression and variable
statements), object methods and the simpler TypeScript types; for anything else (classes, JSX,
other statements) it gives up and that one fix is left out.

**Parity.** Each corpus copied twice to `/dev/shm`, `oxlint --fix` on one copy and `vlint --fix` on
the other (`fix-work/fixdiff.sh`), every file compared with `diff -r` and the printed lines
compared sorted:

| corpus | files | changed by oxlint | files that differ | printed lines that differ |
|---|---|---|---|---|
| date-fns, zod, ... (TypeScript) | 3,445 | 17 | 0 | 0 |
| JavaScript from `node_modules` | 730 | 22 | 0 | 0 |
| preact | 249 | 1 | 0 | 0 |
| excalidraw | 723 | 12 | 0 | 0 |
| vscode | 15,572 | 538 | 4 | 130 (all known parse-error differences) |
| probe files (`lint/p`) | 53 | 11 | 0 | 25 (a known parse-error difference) |
| fix probes (overlaps, CRLF, BOM, disable comments, parse errors, the code printer) | 17 | 14 | 0 | 9 (two error wordings, a tie, a `module A.B` warning) |
| generated files (`genfix.py`, 6 seeds of 300 JS files, 3 of 300 TS files) | 2,700 | 2,292 | 152 (149 that oxc rejects, 3 others, below) | |

2,553 fixes were applied across the real corpora: `no-useless-escape` 1,973, `no-useless-spread`
173, `prefer-string-starts-ends-with` 138, `no-useless-fallback-in-spread` 103,
`no-wrapper-object-types` 90, `prefer-as-const` 18, `no-extra-boolean-cast` 14,
`no-single-promise-in-promise-methods` 8, `no-extra-non-null-assertion` 7, `no-unnecessary-await`
6, then `prefer-namespace-keyword`, `no-useless-rename`, `no-useless-empty-export`,
`no-unused-labels`, `use-isnan`, `valid-typeof`, `no-compare-neg-zero`, `prefer-set-size` and
`no-unsafe-negation` (1 to 4 each): every one of the 19 rules was exercised.

What still differs: the 4 vscode files are fixtures oxc rejects (duplicate parameters in strict
code) and vlint lints and fixes; the generated files oxc rejects for invalid assignment targets or
`-a ** b`, which vlint's parser accepts; when two fixes have exactly the same span (`NaN == NaN`, two spreads
in one array), oxlint's unstable sort picks one of them, which vlint matches in small files but
not always in files with many diagnostics; and one oxc code-generator oddity (an identifier
statement in an arrow body printed with a label) isn't reproduced.

Running the corpora found and fixed these in the plain linter as well (its output on all corpora
is unchanged): keyword literals (`true`, `this`, ...) and `debugger`/empty statements had no
length in the exact tree; `eslint-enable` without rules ended a rule-specific `eslint-disable`
(oxc pairs them only by kind); `x!?.y` wasn't reported by `no-extra-non-null-assertion`;
`no-wrapper-object-types` missed `implements`/`extends` lists; `no-unnecessary-await` used a
different list of non-promise expressions; and a `>` glued to `=` or `>` was taken as the end of
type arguments (`a < b >= c`).

**Speed.** CPU seconds (user + sys), best of 5 (vscode: 3), fresh copies for each run, on the
2-core VM heavily loaded by other jobs (load average 10 to 17), so the numbers are noisy:

| corpus | oxlint `--fix` | vlint `--fix` | oxlint `--fix`, 1 thread | vlint `--fix`, 1 thread | oxlint (no fix) | vlint (no fix) |
|---|---|---|---|---|---|---|
| TypeScript (3,445 files) | 0.61 | 0.49 | 0.62 | 0.48 | 0.59 | 0.51 |
| JavaScript (730 files) | 5.13 | 2.69 | 4.93 | 2.58 | 4.94 | 2.59 |
| excalidraw | 0.38 | 0.32 | 0.34 | 0.32 | 0.35 | 0.32 |
| vscode (15,572 files) | 9.28 | 9.07 | 9.67 | 8.47 | 9.02 | 8.41 |

Fixing costs nothing measurable over linting for either tool. The plain path didn't get slower: on
zod (`VU_MARCH=x86-64-v2` build, callgrind) it went from 706.5M to 674.1M instructions (-4.6%),
because the unused-label report and its string building moved out of `visit`, the function called
for every node, which was paying for that branch's string temporaries on each call.

