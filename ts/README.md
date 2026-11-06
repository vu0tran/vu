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

`vlint` is meant as a drop-in replacement for oxlint 1.90.0: the same command line, the same
configuration files, the same output bytes and exit codes. It checks `.js .mjs .cjs .jsx .ts .mts
.cts .tsx` and the script sections of `.vue`, `.astro` and `.svelte` files. It reuses vtsc's
scanner and parser, plus a scope builder (`scope.vu`), a regular-expression parser (`regex.vu`),
the rules (`rules.vu`), configuration (`lconf.vu`, `lglob.vu`, `lmatch.vu`), output (`lout.vu`),
the rule table (`lmeta.vu`, `lrules.vu`), partial files (`lpart.vu`), tsgolint (`ltsgo.vu`) and,
for `--fix`, a printer of expressions as oxc prints them (`fixgen.vu`).

```
cd ts && VU_SPLIT=off ../vu build --release vlint.vu -o vlint   # one C file: the fastest binary
./vlint [options] [paths]      # as oxlint; plus --jobs N, --cache, --cache-location PATH
```

## Drop-in status (checked against oxlint 1.90.0)

**Command line** (every flag of `oxlint --help`, plus its hidden ones):

| flag | status |
|---|---|
| `-c/--config`, `--disable-nested-config`, `--tsconfig` (accepted) | yes |
| `-A/-W/-D` (rules, categories, `all`), `--*-plugin`, `--disable-{unicorn,oxc,typescript}-plugin` | yes |
| `--deny-warnings`, `--max-warnings`, `--quiet`, `--silent`, `--no-error-on-unmatched-pattern` | yes |
| `-f default/agent/json/unix/github/gitlab/junit/checkstyle/stylish/sarif` | yes (checkstyle/stylish group files in oxlint's hash order: file order can differ) |
| `--ignore-path`, `--ignore-pattern`, `--no-ignore` | yes |
| `--threads`, `-h`, `-V`, `--debug files` | yes (`--debug timings` accepted, prints no table) |
| `--fix` | yes (oxlint's safe fixes, for the rules vlint has) |
| `--type-aware`, `--type-check`, `options.typeAware/typeCheck` | yes: runs tsgolint (`oxlint-tsgolint`) as oxlint does |
| `--report-unused-disable-directives[-severity]` | yes |
| `--rules` | yes (the table, `-f json`) |
| `--init` | yes |
| `--print-config` | yes (`lprint.vu`; byte-identical on 14 of the 15 real projects and 8 hand-written configs, the 15th uses a JS plugin) |
| `--fix-suggestions`, `--fix-dangerously` | yes for the rules that have them in vlint (see below); not yet: `no-unused-vars`', `no-new-array`'s and `no-extra-boolean-cast`'s suggestions |
| `--lsp` | no (refused) |
| `--suppress-all`, `--prune-suppressions` (hidden), `oxlint-suppressions.json` | yes (`lsupp.vu`) |
| `--type-check-only` (hidden) | yes (tsgolint's type check only, oxlint's messages for invalid combinations) |

**Configuration**: `.oxlintrc.json`/`.jsonc` discovery and `-c`, nested configs, `extends`
(with oxlint's error messages for missing files, named configs and cycles), `overrides`, rules
with severities and options, `categories`, `plugins`, `env`/`globals` (globals read by
`jsx-no-undef`), `settings` (parsed), `ignorePatterns`, `options` (`typeAware`, `typeCheck`,
`denyWarnings`, `maxWarnings`, `reportUnusedDisableDirectives`, `respectEslintDisableDirectives`),
JSON errors as serde words them. `oxlint.config.ts` is reported as needing a JavaScript runtime.
`jsPlugins`: a missing package gets oxlint's "Failed to load JS plugin" error; an installed one
is refused (vlint can't run JavaScript). Ignore files: `.gitignore` (and the folders above, up
to the repository root, and `.git/info/exclude`), `.eslintignore`/`--ignore-path`.

**Output**: oxlint's graphical report (themes, links, summary lines), the agent format, and all
`-f` formats, byte-identical in the cases checked.

**Rules**: oxlint's default rules (all of them since this round: `oxc/uninvoked-array-callback`
was the one missing), plus, chosen by how often real configurations enable them: `prefer-const`,
`no-restricted-imports`, `no-console`, `no-var`, `eqeqeq`, `prefer-rest-params`, `no-empty`,
`no-array-constructor`, `no-case-declarations`, `no-prototype-builtins`, `prefer-spread`, `curly`,
`no-new`, `no-unneeded-ternary`, `no-useless-concat`, `no-redeclare`, `no-self-compare`,
`no-nested-ternary`, `no-negated-condition`, `require-unicode-regexp`, `no-underscore-dangle`,
`no-extra-bind`; `typescript/` `no-explicit-any`, `no-require-imports`,
`no-unnecessary-type-constraint`, `no-namespace`, `no-unsafe-function-type`,
`no-non-null-assertion`, `ban-ts-comment`, `no-empty-object-type`, `no-confusing-non-null-assertion`,
`no-extraneous-class`; `unicorn/` `prefer-node-protocol`, `require-module-specifiers`,
`no-array-sort`, `no-array-reverse`, `no-negated-condition`, `catch-error-name`;
`oxc/misrefactored-assign-op`; `import/first`; `react/` `jsx-key`, `no-this-in-sfc`,
`no-children-prop`, `no-find-dom-node`, `jsx-no-duplicate-props`, `jsx-no-undef`,
`jsx-props-no-spread-multi`, `no-danger-with-children`, `no-did-mount-set-state`,
`no-did-update-set-state`, `no-will-update-set-state`, `no-direct-mutation-state`, `no-is-mounted`,
`no-render-return-value`, `no-string-refs`, `no-unsafe`, `void-dom-elements-no-children`,
`forward-ref-uses-ref`, `jsx-no-comment-textnodes`, `no-unescaped-entities`,
`react-hooks/rules-of-hooks`, `react-hooks/exhaustive-deps`, `react/only-export-components`;
and in the restart round: `no-useless-constructor`, `no-unexpected-multiline`, `no-extend-native`;
`unicorn/` `no-instanceof-builtins`, `prefer-math-trunc`, `prefer-code-point`,
`no-object-as-default-parameter`, `prefer-number-coercion`, `escape-case`, `no-hex-escape`,
`no-array-fill-with-reference-type`, `no-accessor-recursion`,
`require-post-message-target-origin`; `oxc/` `approx-constant`, `no-this-in-exported-function`;
`jest/` and `vitest/no-conditional-in-test`; `jsx-a11y/` `aria-props`,
`aria-unsupported-elements`, `aria-role`, `alt-text`, `html-has-lang`, `iframe-has-title`,
`no-access-key`, `tabindex-no-positive`, `no-distracting-elements`, `scope`, `no-autofocus`,
`role-has-required-aria-props`, `role-supports-aria-props`, `heading-has-content`,
`anchor-has-content`, `mouse-events-have-key-events` (with the plugin's `polymorphicPropName` and
`components` settings, and oxc's role and ARIA tables). Each comes with its options, oxc's messages,
spans, labels, fixes (and their kinds) and order. All 61 type-aware rules through tsgolint. A rule
vlint doesn't have is accepted in the configuration and reports nothing. The rules added in these
rounds are in `rhooks.vu` (exhaustive-deps), `rmore.vu`, `rmore2.vu` and `ra11y.vu`; each runs only
when the configuration turns it on.

**Rule order when an override applies** (`lfx.vu`, `lconf.rule_rank`): oxlint then runs a file's
rules in the iteration order of an `FxHashMap` keyed by rule id (`Config::apply_overrides`: the
base rules inserted in id order, the categories of plugins an override adds, each override's rules
removed and inserted again), so diagnostics that two rules report on one node come out in that
order, not by rule id. `lfx.vu` emulates the map (inserts, `entry().or_insert`, removes with
tombstones, growth, rehashing in place; identical to Rust's on 15,000 random operation sequences),
and the same table with oxc's `IdentHasher` gives the order of the root scope's unresolved
references, which `no-extend-native` reports in (identical to Rust's on 400 random name sets).
Checking this order on three override configurations found four rules reporting from a different
node than oxc's (`no-func-assign`, `no-useless-spread`, `no-extra-boolean-cast`, and nodes with the
same span sorted inner first); all fixed.

**Coverage of real configurations** (the 1,830 `.oxlintrc.json` files collected from GitHub in an
earlier round, `vlint4-work/cov.py` and `cov2.py`): of the rules those files turn on by name
(12,227 enables, type-aware ones counted as covered), vlint now has 64.3% (58.4% at the start of
the previous round); counting the rules their categories and plugins turn on as well (233,108
enables, type-aware excluded), 79.3% (74.8%). The largest missing share is the React Compiler
rules (about 1,030 enables each, 12,300 together), then `import/namespace` and `import/default`
(which need the module graph), the rest of jsx-a11y (20 rules, about 2,800), the jest/vitest rules
that run on test calls (`expect-expect`, `valid-expect`, ...; about 2,400), and eslint's
`preserve-caught-error`, `block-scoped-var`, `no-implied-eval`, `no-unmodified-loop-condition`
and `no-shadow` (about 320 each).

`react-hooks/exhaustive-deps` follows oxc's port closely, including the order of the names in
"missing dependencies: 'a', 'b', and 'c'" and of the diagnostics of one call: oxc keeps
dependencies in an `FxHashSet`, so vlint emulates rustc-hash 2's FxHasher and std's hashbrown table
(insertion, growth, probing; checked against a Rust program on 400 random sets) and hashes with
oxc's symbol ids (oxc numbers symbols as it declares them: a declarator's or parameter's names when
it starts; parameters of type signatures are symbols in oxc and are counted in). The dependency
visitor follows oxc's `VisitJs` (no types). The same emulation orders `--print-config`'s
categories, env, globals and settings maps.

**Not at 100%**:
- The React Compiler rules that oxlint 1.90.0 turns on with the react plugin's `correctness`
  category (`react/globals`, `immutability`, `refs`, `purity`, `set-state-in-effect`,
  `set-state-in-render`, `static-components`, `preserve-manual-memoization`, `use-memo`,
  `void-use-memo`, `incompatible-library`, `error-boundaries`, plus `exhaustive-effect-dependencies`
  and `no-deriving-state-in-effects`): missing. They come from `oxc_react_compiler`, 61,109 lines
  of Rust: lowering to HIR (build_hir alone is 6,837 lines), SSA, type inference,
  mutation/aliasing inference, reactive scopes and 14 validation passes; the validations read the
  inferred types and effects (`set-state-in-effect` follows setState functions through local
  functions and skips ref-controlled branches with post-dominator frontiers), and a function the
  compiler bails out on (unsupported syntax, an `eslint-disable` of the hooks rules, `"use no
  memo"`) reports nothing. A port is roughly 35,000 to 45,000 lines of Vu. A syntactic
  approximation was considered and not shipped: it would trade missing diagnostics for wrong ones.
- The other ~620 non-default rules: missing (jsx-a11y, the rest of import, jest/vitest, most of
  unicorn's and eslint's pedantic and style rules). On kimi-code (which turns on pedantic, perf,
  vitest, import) vlint now finds 9,021 of oxlint's 10,599 diagnostics (435 two rounds ago), with
  none extra and the order identical; the rest are mostly `import/extensions` (568), the vitest
  rules that run on test calls (`no-conditional-expect` 190, `require-to-throw-message` 185,
  `expect-expect` 153) and `unicorn/prefer-single-call` (169).
- Fixes not yet ported: the suggestions of `no-unused-vars`, `no-new-array` and
  `no-extra-boolean-cast` (so `--fix-suggestions`/`--fix-dangerously` leave those), and the fix of
  `no-negated-condition` (`--fix` leaves it).
- `--print-config` with a config that uses `jsPlugins`; JS plugins themselves (see below).
- JS plugins (`jsPlugins`): a missing package gets oxlint's "Failed to load JS plugin" error, an
  installed one is refused. Running them needs an ESTree view of vlint's tree (every node type with
  ranges and `loc`, tokens and comments), oxlint's plugin context (`report` with messages, message
  ids, data, fixes and suggestions; `sourceCode` with its scope manager), selectors and `:exit`
  visitors, run in a Node process as vknip runs JavaScript configs: not done.
- Parse errors: on oxc's own fixtures (`tasks/coverage/misc`, 257 failing and 112 passing files)
  vlint's output is identical for 109 of 369 (102 before this round). vlint reports only the first
  syntax error, in TypeScript's wording under the code `vlint(parse)` where it doesn't know oxc's
  ("Expected `)` but found `;`" with its "Opened here" label is the commonest), and it doesn't make
  many of oxc's early errors (escaped keywords, mixed `??` and `||`, `await`/`yield` contexts,
  modifiers in the wrong place, jumps across functions, and others: 142 of those fixtures get no
  error from vlint). Added this round: redeclaration errors now carry oxc's two labels (vlint gave
  one, empty: `-f json` differed), private names not declared in an enclosing class (with oxc's
  "Did you mean" suggestion) or used outside a class, duplicated exports and multiple default
  exports in JavaScript files, and tagged templates in optional chains; a crash on `<!--` in a
  module (`index -1 out of bounds` in `parse.vu`) is fixed (oxc's "HTML comments are not allowed in
  modules" is still not reported). Fixed in the previous round: vlint rejected valid TypeScript with
  a conditional type inside a mapped type inside a conditional type's `extends` clause.
- `-f sarif` puts the suppression file's errors into oxlint's `notifications`; vlint doesn't.
  `-f checkstyle` groups files in oxlint's hash order (unchanged).

**Parity** (`ljson_diff.py`: every diagnostic's rule, message, help, severity, labels and order):

| corpus | config | files with diagnostics identical |
|---|---|---|
| lc: date-fns, zod, remeda, ... + node_modules JS | defaults | 308 / 308 |
| lc | the previous round's added rules on | 1570 / 1570 vlint files (oxlint's 3 more: React Compiler) |
| preact, excalidraw | defaults | 230 / 230 |
| preact, excalidraw | the previous round's added rules + react plugin | 488 / 574 (the rest: React Compiler, exhaustive-deps, now added) |
| vscode | defaults | 2764 / 2783 (the rest: files oxc can't parse) |
| config cases (`cfgtest`, 54 cases, as an agent and as a person) | | 108 / 108 |
| mantine (+ preact, Tracearr, next-shadcn-dashboard-starter, difit) | `react-hooks/exhaustive-deps` | 237 + 41 + 5 + 2 diagnostics, all identical |
| 900 generated components (`gen_hooks.py`, 3 seeds) | exhaustive-deps with `additionalHooks` | 4,101 / 4,101 diagnostics; `--fix` and `--fix-dangerously` files identical |
| lc and kimi-code | the 7 rules of `rmore.vu`'s first batch | 48,000 diagnostics identical |
| lc and kimi-code | `no-redeclare` | 756 + 708 identical |
| lc, kimi-code, preact, excalidraw, mantine, vscode | the second batch, `import/first` (both options) | all identical (1,338 `import/first` on kimi-code) |
| lc, kimi-code, vscode, mantine, excalidraw | `no-useless-constructor`, `no-instanceof-builtins`, `no-conditional-in-test` | all identical (78 + 9 + 7 useless constructors; 3,230 conditionals in kimi-code's tests) |
| lc, kimi-code, excalidraw, mantine, preact | `rmore2.vu`'s unicorn and oxc rules, `no-unexpected-multiline`, `no-extend-native` | all identical (about 9,000 diagnostics), and an attack file for each identical with `--fix`, `--fix-suggestions`, `--fix-dangerously` |
| excalidraw, mantine, kimi-code, preact | `react/only-export-components`, defaults and every option | 3,059 and 958 diagnostics, all identical; 7 attack files identical |
| excalidraw, mantine, preact, Tracearr, kimi-code, next-shadcn-dashboard-starter | the 16 jsx-a11y rules | 145 diagnostics, all identical; attack files with and without options and settings identical, fixes included |
| lc, kimi-code | three configurations whose overrides add plugins and rules | every file's order identical for every rule whose diagnostics match |
| kimi-code | its own configuration | 9,021 of oxlint's 10,599 diagnostics, none extra, order identical |
| `--print-config` | 15 real projects, 8 configs | 22 / 23 identical (the 23rd uses a JS plugin) |
| suppressions | a 21-step scenario, all output formats | identical except `-f sarif` |
| zod, `--type-aware`, 5 typed rules | | 1282 / 1285 diagnostics (tsgolint prints 3 types differently run to run) |

Real projects with their own `.oxlintrc.json` (15 cloned from GitHub; JS plugins removed from
their configs where the plugin isn't installed): identical on agents, leaflet-geoman, logtape,
mcp, OpenFrontIO (type-aware), react-element-to-jsx-string, react-starter-kit,
typescript-nextjs-starter, yak; FigmaToCode, Tracearr, difit and next-shadcn-dashboard-starter
differ only by React Compiler diagnostics, jsx-a11y (Tracearr) and `react/no-unstable-nested-components`
(next-shadcn-dashboard-starter); their `react-hooks/exhaustive-deps` diagnostics are now identical;
kimi-code by rules vlint doesn't have (5,667 of 10,599 found, none extra).

**Speed** (lc corpus, 1 thread, user+sys CPU, best of 5, loaded 2-core VM, load average 2 to 3):
vlint 2.28 s, oxlint 3.40 s (the previous round measured 2.28 s against 4.54 s). Instructions
(callgrind, x86-64-v2 builds, one thread, against a build of the round's starting commit made the
same way): zod 550.9M against 545.4M (+1.0%: the semantic checks for private names, exports and
tagged templates, which first cost +4.7% while they walked every node and copied the text, and
now use lists the walk fills; the per-file tables of the new rules; the `new Array(n).map` check
on calls), vscode/src/vs/editor/common 338.0M against 335.1M (+0.9%). With only exhaustive-deps on, mantine
takes 0.31 s of CPU (0.27 s with no rules) against oxlint's 0.25 s (0.23 s).

## Install

```sh
npm install --save-dev @vu0tran/vlint      # the vlint and oxlint commands
```

or, to replace oxlint in a project without touching its scripts, one line in `package.json`:
`"oxlint": "npm:@vu0tran/vlint@^0.2.0"`. The npm packages are laid out as oxlint's are (a Node
launcher and one optional dependency per platform with the binary: Linux x64/ARM64, static; macOS
12+ on Apple silicon and Intel; no Windows). What works and what doesn't as a drop-in:
`packaging/npm/vlint/README.md`, which is also the
package's README. Each `vlint-vX.Y.Z` tag also puts the bare binaries on the GitHub release
(`vlint-X.Y.Z-<platform>.tar.gz`). Releasing: `RELEASING.md`.

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

### Cold runs, later (2026-11-01)

A second round cut instructions by 25% (callgrind, zod, one C file: 678.4M -> 508.0M;
vscode/src/vs/editor/common 393.9M -> 305.3M), output byte-identical throughout:

- The scope walk is gone: the parser records scopes, declarations and references as it reads
  (`ast.Sev`, "scope events" in `parse.vu`), and `scope.vu` replays them (-7%). The rules' walk is
  the only walk over the tree; it dispatches on a per-kind table and skips absent children (-10%).
- Index checks: hot loops on a local index bounded by the string's own length, entries and events
  as lists of structs, a node read once per visit (-4%). Of the checks left, removing all of them
  (in a copy of the C, to measure) would save 8%: they index lists by values read from other lists
  (node, symbol and slot ids), which only a language feature could prove in range.
- Scanner: literal values as source ranges instead of copies, names of up to 7 bytes interned as
  one word, one-character punctuators by table (-8%); no-dupe-keys by name id (-2%).

CPU, best of 9 interleaved runs on the same loaded 2-core VM (load average 4 to 9); oxlint is
started through node (`node -e 0` alone takes 0.04 s):

| | lc/ts, 1 thread | lc/ts, all cores | vscode/src, 1 thread | vscode/src, all cores |
|---|---|---|---|---|
| vlint before | 0.49 | 0.50 | 6.39 | 6.70 |
| vlint now | 0.37 | 0.40 | 5.19 | 5.23 |
| oxlint 1.90.0 | 0.55 | 0.62 | 6.23 | 6.74 |

Measured but not done: a node list with 32-bit fields would need an integer type Vu doesn't have
(node writes cause 0.7M of zod's 3.9M first-level cache misses: at most 1 to 2% of CPU); building
without gcc's default stack protector (`-fno-stack-protector`, a Vu compiler flag) saves 5% of the
instructions.

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

