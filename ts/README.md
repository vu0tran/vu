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

date-fns (`pkgs/core/src`, 1334 files, 2.0 MB of TypeScript), on a 2-core Intel Xeon @ 2.10GHz
VM, best of 5 runs, wall clock (`ts/bench.sh` with `ts/bench_parse.mjs`; measured
2026-11-09):

| type checking (`--noEmit --strict`) | ms |
|---|---|
| vtsc (2 workers) | 305 |
| vtsc (1 thread) | 454 |
| tsc 7.0.2 (Go) | 1009 |
| tsc 7.0.2, `--checkers 1 --singleThreaded` | 1143 |
| tsc 6.0.3 (JavaScript) | 5114 |

vtsc checks all 1334 files and reports what tsc 7 reports for them: no errors (tsc with
`--allowImportingTsExtensions`, which date-fns' imports need). That makes it 3.3x faster than
tsc 7 and 17x faster than tsc 6 on the same work. (Before 2026-11-09 it left 34 files unchecked:
spreads into overloads, a switch's flow join, `x op= y` on an auto-typed variable, infer
declarations in a conditional type's constraint and in its non-deferred resolution, a spread
replacing a written property.)

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

## Three repositories with their own configurations (2026-11-09)

Run on each repository's own oxlint configuration, vlint's JSON output was compared with
oxlint 1.90.0's, diagnostic by diagnostic (code, message, labels, help, severity), and both were
timed on the same loaded 2-core VM (wall seconds, a few runs each):

| repository | configuration | diagnostics | identical | vlint | oxlint |
|---|---|---|---|---|---|
| n8n (26,149 files) | defaults (`--disable-nested-config`: its `.mts` configs need a build) | 3688 | 3688 | 2.2-2.5 s | 2.7-2.8 s |
| n8n `packages/frontend/editor-ui` (2555 files) | its config, 107 rules, the import plugin's graph rules on, local JS plugins left out | 1377 | 1377 | 1.05-1.1 s | 1.42-1.50 s |
| vitest (1454 files) | its `.oxlintrc.jsonc`, 229 rules | 0 | 0 (and no unused-directive reports) | 0.29-0.31 s | 0.28-0.30 s |
| tldraw (2854 files) | its config, 122 rules, type-aware (tsgolint), its JS plugin left out | 82 | 82 | 2.3-2.5 s | 2.2-2.3 s (tsgolint's time) |

What it took: the rules these configurations turn on and vlint lacked (no-default-export,
no-mutable-exports, method-signature-style, prefer-arrow-callback, prefer-template,
prefer-regex-literals, no-unreachable-loop, no-template-curly-in-string, no-new-func, no-alert,
no-proto, prefer-regexp-test, no-empty-interface, no-restricted-types,
vue/no-required-prop-with-default; `rmore8.vu`), options (no-cond-assign "always", prefer-const
ignoreReadBeforeAssign), and fixes found on the way (no-use-before-define, no-useless-spread,
no-import-assign, constructor-super, no-invalid-fetch-options, no-useless-length-check, TS1038
and TS2309). `.vue` files now have module records (one per script section, as oxlint's
runtime has), so the import plugin's rules run in them. Each ported rule was checked against oxc's
own test cases through both linters: over every rule, 32,359 of 43,915 cases give the same output
(263 rules on all their cases); most of the rest are rules vlint doesn't have.

Not the same yet: oxlint's React Compiler rules (`react/refs`, `set-state-in-effect`, and the
rest of `oxc_react_compiler`, 62,657 lines of Rust) aren't in vlint, so a React project that
keeps them on gets fewer diagnostics (AFFiNE: 211 of oxlint's, all from those rules; outline:
170). vitest's config turns on rules vlint still lacks; vitest's code breaks none of them, so its
output matches, but code that did would differ. Where the speed comes from on editor-ui: the
import plugin's module graph (1.5 s of the 1.85 s before) now resolves in long-lived workers,
reads only the top level of each file and stops at what node_modules re-exports.

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
| `--print-config` | yes (`lprint.vu`; byte-identical on the 15 real projects and 8 hand-written configs; several `jsPlugins` entries can come out in another order, see below) |
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
`jsPlugins` (in the config and in overrides): run in Node as oxlint runs them (see "JS plugins"
below). Ignore files: `.gitignore` (and the folders above, up
to the repository root, and `.git/info/exclude`), `.eslintignore`/`--ignore-path`.

**JS plugins** (`ljs.vu`, `ljs_glue.c`, `jsplug/`): vlint runs ESLint-style plugins with
oxlint 1.90.0's own plugin runtime (its `dist`, MIT, embedded by `jsplug/gen_host.py` into
`lhost.vu` and written once to `~/.cache/vlint`): the same `context`, `sourceCode`, scope manager,
selectors and `:exit` visitors, CFG events, options validation, fixes and suggestions, message
ids, disable comments for plugin rules. What oxlint hands that runtime from Rust (raw transfer of
oxc's AST) vlint builds in JavaScript from its own tree: `jsplug/estree.js` turns vlint's flat
node arrays into oxc's ESTree (the same node types and fields in oxc's order, UTF-16 offsets,
`loc`, oxc's quirks: TS fields on JS nodes, `ChainExpression` around non-null chains, decorated
classes, `export import`, `sourceType` decided as oxc decides it), and `jsplug/tokens.js` makes
oxc's tokens and comments (kinds as `oxc_estree_tokens` sets them). Plugins resolve as oxc_resolver
is set up for them (`exports` conditions, extensions, realpath), with oxlint's errors for missing
packages, invalid aliases and reserved names. Each linting thread drives one long-lived `node`
process (requests on fd 3, answers on fd 4; the plugin's own `console.log` goes to vlint's
output); a JS rule's diagnostics follow the native ones as in oxlint. Checked against oxlint with
a dumping plugin: identical ASTs on about 16,000 real files, tokens and comments on 4,577 of
4,580; oxlint's JS plugin fixtures (`apps/oxlint/test/fixtures`): 81 of 94 identical (the rest:
`vite.config`/`oxlint.config.ts` configurations, a vue rule and parse-error wording); 21 real
plugins with every rule on (eslint-plugin-react, react-hooks, sonarjs, perfectionist, @stylistic,
playwright, storybook, testing-library, security, unused-imports, simple-import-sort,
@tanstack/query, @next/next, react-native, react-you-might-not-need-an-effect, no-only-tests,
oxlint-plugin-eslint, oxlint-tailwindcss, oxlint-plugin-complexity, oxlint-plugin-react-doctor,
@shadcn/lint) on excalidraw: 632 of 632 files identical. CPU with those plugins on excalidraw
(best of 3, loaded 2-core machine): one thread oxlint 93 s, vlint 102 s; two threads oxlint
92 s CPU and 71 s wall, vlint 114 s CPU and 59 s wall (oxlint runs JS on one thread, vlint on
one Node process per thread).

Speed on AFFiNE (2026-11-08; oxlint's own config there: six JS plugins including the React
Compiler's react-hooks rules, type-aware rules on; 2-core machine, two runs each, wall time):
oxlint 70.1 and 73.8 s, vlint 63.7 and 68.6 s (79.1 and 90.5 s before this change); without
type-aware rules, oxlint 57.7 and 67.4 s, vlint 58.2 and 59.9 s. The change: oxlint's
`NodeProto` has `loc` as an enumerable getter, so vlint's `for-in` walks over the tree read it on
every node (computing every node's position and giving each node an own property, a slow shape);
they now skip it. And the node literals in `estree.js` carry `start`, `end`, `range` and `parent`
themselves, so each node is allocated once in its final shape. Building the ESTree went from
22.2 s to 3.5 s of CPU on one thread; a 6 MB file (TypeScript's `_tsc.js`) no longer runs Node out
of memory. The node processes also use Node's compile cache (Node 22.1 and later) in
`~/.cache/vlint/node-compile-cache`, unless `NODE_COMPILE_CACHE` or `NODE_DISABLE_COMPILE_CACHE` is
set: a one-file run with those plugins, 2.0 s before, takes 1.5 s from the second run on. Checked:
the same diagnostics on AFFiNE, lc 308 of 308, and a dumping plugin's ASTs and scopes byte-identical
to the previous build's on 18,196 dumps. Not measured on a machine with more cores.

CPU, the same day: vlint used about 30% more CPU than oxlint there (104-111 s against 79 s), and
nearly all of it was in the node processes. A busy node process keeps about one and a half cores
busy (V8's garbage collector and optimizing compiler run beside it), so with a process per core on
2 cores the processes mostly took turns: the React Compiler's rules alone cost 79 s of CPU in two
processes and 56 s in one, in the same wall time. Now: one node process for each two cores (at
most one per linting thread; `VLINT_JS_PROCS` sets it), shared by the linting threads, which send
their requests without waiting for each other's answers (answers come back in order, by ticket),
so the process isn't left waiting for the next file (11 s of a 58 s run before); each process gets
`--v8-pool-size` of the cores left over per process, at least 1, instead of Node's 4 (unless
`NODE_OPTIONS` sets it); and `setParents` walks each node type's fields from a list made once per
type. AFFiNE, oxlint's config, three runs each alternating: oxlint 57.8, 58.0, 59.0 s wall and
81.9, 82.4, 83.2 s CPU; vlint 56.6, 58.4, 61.7 s wall and 80.5, 83.9, 88.9 s CPU, 1.0-1.2 GB
against oxlint's 2.4 GB; the same diagnostics. A request queued behind one whose plugin made node
exit is sent again to a new process (the one that did gets the error, as before); and
`process.exit()` in a plugin no longer leaves node hung (fd 3 is read as a socket now, not a file
stream with a blocking read in libuv's thread pool). Checked: lc 308 of 308; 8 threads on 1 and 3
processes, the same AFFiNE diagnostics; plugins that make node exit on one file and on every fifth
file, 150 runs with 1 to 8 threads and 1 or 2 processes, every other file linted and only those
files reported; `VLINT_JS_CHECK=1` (no node missed by the per-type field lists) on AFFiNE, lc and
blocksuite.

On GitHub's standard runner (4 vCPUs: 2 AMD EPYC 7763 cores with 2 hardware threads each;
`bench/vlint_affine.sh` on the `bench-vlint` branch, run 42561461521), the same config, three
runs each alternating: oxlint 48.0, 48.9, 49.4 s wall and 94-95 s CPU; vlint (2 node processes)
41.1, 41.9, 40.9 s wall (1.19 times as fast) and 132-135 s CPU. With 1, 3 and 4 processes: 53.0,
44.7, 48.8 s wall, 97, 166, 187 s CPU. Most of the time is the plugins' own JavaScript (the React
Compiler and Babel, run the same way in both), which oxlint runs on one thread; vlint can only
spread it over processes, and on these machines a second node process gains less than half a
process (hardware threads, V8's own threads), a third nothing. So not 2 times as fast here; not
measured on a machine with more physical cores.

Built-in rules only (AFFiNE's config without its JS plugins and type-aware rules, 2026-11-08, 2
cores, four runs each alternating): oxlint 2.32-2.41 s wall and 4.2-4.3 s CPU; vlint 1.45-1.52 s
and 2.1-2.2 s (1.76-1.90 s and 2.7-2.8 s before); on one thread, oxlint 4.49 s, vlint 2.25 s. Found
with `vu build --profile` and a count of the C runtime's string copies (3.3 GB copied for 25 MB of
source): `let src = p.sc.src` in three JSX parsing functions copied the whole file for every JSX
name and element (3.19 GB of it; the source is now read in place); react-hooks' `additionalHooks`
pattern was tried at every byte of every call's name, with two lists allocated at each (lmatch now
skips places where no match can start: the bytes a match can begin with are worked out when the
pattern is compiled; the old and new matcher agree on 60,000 random patterns and texts); and
`fast_match` copied a gitignore pattern for each of 1.6 million paths checked. Checked: the same
diagnostics on AFFiNE with the built-in, no-JS-plugin and full configs; lc 308 of 308; vtsc's and
vknip's regressions (the parser is theirs too) unchanged.

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
spans, labels, fixes (and their kinds) and order. Added in the latest round: the import
plugin's rules that read the module graph (`import/namespace`, `default`, `named`,
`no-self-import`, `no-named-as-default`, `no-named-as-default-member`, `extensions`,
`no-duplicates`, `no-cycle`; see "The module graph" below); 21 jest/vitest rules that run on test
calls (`rjest.vu`: `no-focused-tests`, `no-disabled-tests`, `valid-describe-callback`,
`valid-expect`, `no-standalone-expect`, `expect-expect`, `valid-title`, `no-conditional-expect`,
`require-to-throw-message`, `prefer-snapshot-hint`, `no-identical-title`,
`no-commented-out-tests`, `valid-expect-in-promise`, and vitest's `warn-todo`,
`no-conditional-tests`, `require-local-test-context-for-concurrent-snapshots`,
`require-awaited-expect-poll`, `hoisted-apis-on-top`, `require-mock-type-parameters`), with
oxc's `parse_jest_fn_call` and its list of possible jest calls; 18 more jsx-a11y rules
(`ra11y2.vu`: all but `lang` and `anchor-ambiguous-text`); and `no-implied-eval` (with oxlint's
env globals, `lglobals.vu`, generated from the `javascript-globals` crate), `no-useless-call`,
`no-await-in-loop`, `preserve-caught-error`, `block-scoped-var`, `no-throw-literal`,
`no-new-wrappers`; `promise/valid-params`, `no-new-statics`; `unicorn/` `prefer-add-event-listener`,
`prefer-array-flat-map`, `no-confusing-array-with`, `no-instanceof-array`, `prefer-string-slice`,
`prefer-date-now`; `import/` `no-absolute-path`, `no-empty-named-blocks`, `no-unassigned-import`;
`react/` `jsx-no-script-url`, `no-namespace`, `iframe-missing-sandbox`, `style-prop-object`;
`node/no-exports-assign`; `oxc/no-async-endpoint-handlers` (`rmore3.vu`, `rmore4.vu`). Added this
round (`rmore5.vu`, `rmore6.vu`, kimi-code's most frequent missing ones): `unicorn/`
`prefer-single-call`, `explicit-length-check`, `prefer-top-level-await`, `prefer-string-replace-all`,
`no-typeof-undefined`, `prefer-math-min-max`, `new-for-builtins`, `prefer-type-error`,
`no-unnecessary-array-splice-count`, `consistent-assert`, `prefer-array-find`,
`prefer-import-meta-properties`, `prefer-at`; `no-promise-executor-return`, `no-lonely-if`,
`prefer-promise-reject-errors`, `no-inner-declarations`; `promise/` `no-promise-in-callback`,
`no-callback-in-promise`. Added in round 7 (`rmore7.vu`, by how often configurations enable them,
then kimi-code's last missing ones): `no-unmodified-loop-condition`, `no-shadow` (every option),
`unicorn/consistent-function-scoping`, `unicorn/prefer-set-has` (with its dangerous fix),
`oxc/no-accumulating-spread`, `typescript/consistent-type-imports` (its fixes in both fix styles,
and `prefer: no-type-imports`), `no-fallthrough` (oxc's control-flow notion of a case that can
complete: loops always can, a `do`-`while` only through its body), `jsx-a11y/lang` (the IANA subtag
registry of the `language-tags` crate oxc uses, `llang.vu`: identical to the crate on 115,000
generated tags), `no-loop-func`, `unicorn/no-immediate-mutation`, `unicorn/prefer-query-selector`,
`unicorn/prefer-native-coercion-functions`, `unicorn/prefer-dom-node-dataset`, `no-else-return`
(their fixes, with oxc's automatic fix messages as help where the rule gives none). All 61
type-aware rules through tsgolint. A rule
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
(12,227 enables, type-aware ones counted as covered), vlint now has 73.8% (71.7% at the start of
round 7, 64.3% three rounds ago); counting the rules their categories and plugins turn on as
well (233,108 enables, type-aware excluded), 85.5% (84.6%). The largest missing share is the React
Compiler rules (about 1,030 enables each, 12,300 together), then `oxc/no-map-spread` (130),
`no-regex-spaces` (126), `react/no-unstable-nested-components` (123) and the vue plugin (about 35
rules enabled by about 119 configs each); by name, `no-regex-spaces` (48), `typescript/array-type`
(33), `prefer-template` (30), `no-restricted-globals` (26).

**The module graph** (`lmod.vu`, `lresolve.vu`, `rimport.vu`): when a rule that reads it is on,
vlint builds the graph oxlint builds before linting: every linted file's module record (as oxc's
`ModuleRecordBuilder` makes it: requested modules, import entries, local, indirect and star
exports, exported bindings, `export default`, module syntax), each request resolved as oxlint
configures `oxc_resolver` (extensions `.js .mjs .cjs .jsx .ts .mts .cts .tsx`, main fields
`module` and `main`, the `module`/`import`/`default` conditions, extension aliases, and the
tsconfig that includes the importing file: `paths`, `baseUrl`, `extends` including packages,
`references`; an `extends` that can't be found makes every request of the files it covers
unresolved, as `oxc_resolver` does), and the records of what they load, transitively and in
parallel. The rules that iterate oxc's `FxHashMap` of requested modules emulate its order (two
maps: the parser's, then the collected one). `no-cycle` finds the components with a cycle once per
run (Tarjan's algorithm), so files outside one cost nothing, and then walks the graph as oxc's
`ModuleGraphVisitor` does (sorted keys, one traversed set, `maxDepth`), so the path in the note is
oxc's.

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
- The other ~540 non-default rules: missing (the vue plugin, nextjs, the rest of import's
  syntactic rules, jest/vitest style rules, most of unicorn's and eslint's pedantic and style
  rules). kimi-code (which turns on pedantic, perf, vitest, import) is now complete: all 10,599 of
  oxlint's diagnostics, all 1,679 files identical (10,558 at the start of round 7, 435 five rounds
  ago).
- `jsx-a11y/anchor-ambiguous-text` (13 enables): missing.
- `prefer-snapshot-hint`'s diagnostics in two excalidraw files come out in another order: oxc groups
  snapshot calls in an `FxHashMap` keyed by its own node ids, which vlint doesn't number the same.
- The module graph covers files whose whole text is JavaScript or TypeScript (`.vue`, `.svelte` and
  `.astro` sections are not read as records), and a lone surrogate in an import name (`\uD800`)
  is shown as U+FFFD where oxc shows the escape.
- Fixes not yet ported: the suggestions of `no-unused-vars`, `no-new-array` and
  `no-extra-boolean-cast` (so `--fix-suggestions`/`--fix-dangerously` leave those), and the fix of
  `no-negated-condition` (`--fix` leaves it).
- JS plugins: `--print-config` prints several `jsPlugins` entries in oxlint's `FxHashSet` order,
  which hashes each entry's folder as Rust's `Path` hashes it; vlint's emulation of that hash is
  wrong (a single entry prints identically; an 11-entry config prints in another order: checked
  with a Rust program, whose order is oxlint's). JavaScript configuration files (`oxlint.config.ts`,
  Vite+'s `vite.config.ts` `lint` field) are still refused, so the fixtures that use them differ.
  A stack trace printed for a crashing plugin shows the host file's path and line where oxlint
  shows `lint.js`'s. Node must be on `PATH`.
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
  a conditional type inside a mapped type inside a conditional type's `extends` clause. Added in
  round 7: duplicate parameters where oxc forbids them (arrows, methods, lists that aren't simple,
  strict code: JavaScript modules, `"use strict"`, classes) as oxc's redeclaration errors (vscode's
  4 Conway fixtures now match, and vscode with defaults is 2,769 of 2,783 files identical); a static
  block's `var` no longer leaks into the enclosing scope, and a function or class expression's own
  name no longer clashes with a declaration in its body (`(function a() { let a; })` was reported
  as a redeclaration). Counted with one oxlint and one vlint run over the fixtures folder (files
  with no diagnostics on both count as identical), 89 of 369 are identical before and after this
  round; the earlier figure of 109 was counted another way.
- `-f sarif` puts the suppression file's errors into oxlint's `notifications`; vlint doesn't.
  `-f checkstyle` groups files in oxlint's hash order (unchanged).

**Parity** (`ljson_diff.py`: every diagnostic's rule, message, help, severity, labels and order):

| corpus | config | files with diagnostics identical |
|---|---|---|
| lc: date-fns, zod, remeda, ... + node_modules JS | defaults | 308 / 308 |
| lc | the previous round's added rules on | 1570 / 1570 vlint files (oxlint's 3 more: React Compiler) |
| preact, excalidraw | defaults | 230 / 230 |
| preact, excalidraw | the previous round's added rules + react plugin | 488 / 574 (the rest: React Compiler, exhaustive-deps, now added) |
| vscode | defaults | 2769 / 2783 (the rest: files oxc rejects with errors vlint words differently or doesn't make) |
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
| kimi-code | its own configuration | 10,599 / 10,599 diagnostics, 1,679 / 1,679 files identical (10,558 at the start of round 7) |
| oxc's test cases of round 7's 14 rules | defaults, and each case with its options (`opt.sh`) | identical except parse-error wording and early errors vlint doesn't make; `--fix`/`--fix-dangerously` output identical |
| lc, preact, excalidraw, vscode, the 15 real projects | each of round 7's rules on its own | all identical (7,179 `no-shadow` and 40,269 `consistent-type-imports` on lc2, 5,664 `consistent-function-scoping`, 1,784 `no-else-return`, 843 `no-loop-func`, 446 `no-immediate-mutation`, ...), except files with early errors vlint doesn't make; `consistent-type-imports`' and `no-else-return`'s `--fix` output identical on OpenFrontIO |
| oxc's test cases of this round's 19 rules | defaults (1,773 cases), and each case with its own options (655 cases, `optcases.py`: one folder and config each) | identical: all 751 and 358 files with diagnostics, and the files `--fix`, `--fix-suggestions`, `--fix-dangerously` write |
| lc, preact, excalidraw, vscode, kimi-code, the 15 real projects | this round's rules, each batch on its own and all together | all identical (about 15,000 diagnostics: 3,449 `explicit-length-check`, 2,725 `prefer-single-call`, 2,091 `no-lonely-if`, 1,416 `no-inner-declarations` with "both", 1,293 `prefer-at` and 45,618 with `checkAllIndexAccess`, ...); the only differences are files oxlint rejects with early errors vlint doesn't make |
| JS plugins: oxlint's fixtures | as the fixtures run them | 81 / 94 |
| JS plugins: 21 real plugins, every rule on | excalidraw | 632 / 632 files identical |
| JS plugins: ESTree | a dumping plugin, every file of lc, preact, excalidraw, kimi-code, the 15 projects | ASTs identical on about 16,000 files; tokens and comments on 4,577 of 4,580 |
| oxc's own test cases of the rules added in the latest round | defaults and every option configuration in the tests | jest/vitest 2,357, jsx-a11y 3,875, the others about 700: identical except parse-error wording, with `--fix`, `--fix-suggestions`, `--fix-dangerously` |
| oxc's import fixtures (`tasks/coverage` import plugin fixtures) | the graph rules | 72 / 74 files (a lone surrogate, a parse error) |
| lc, preact, excalidraw, mantine, the 15 real projects | each rule added in the latest round on its own | all identical (2,922 `block-scoped-var` on lc, 526 `no-cycle` in excalidraw and 145 in OpenFrontIO with their notes, 568 `import/extensions` and 61 `no-duplicates` in kimi-code; `no-duplicates` fixes identical) except `prefer-snapshot-hint`'s order in 2 excalidraw files |
| `--print-config` | 15 real projects, 8 configs, 3 jsPlugins configs | 23 / 23 identical (evolu newly: with `extends`, oxlint prints the root file's own categories and rule options only, and prints even when an override names an unknown plugin); jsPlugins: 1 / 3 (one entry identical, 10 and 11 entries in another order) |
| suppressions | a 21-step scenario, all output formats | identical except `-f sarif` |
| zod, `--type-aware`, 5 typed rules | | 1282 / 1285 diagnostics (tsgolint prints 3 types differently run to run) |

Real projects with their own `.oxlintrc.json` (15 cloned from GitHub; JS plugins removed from
their configs where the plugin isn't installed): identical on agents, leaflet-geoman, logtape,
mcp, OpenFrontIO (type-aware), react-element-to-jsx-string, react-starter-kit,
typescript-nextjs-starter, yak and (since round 7) kimi-code; FigmaToCode, Tracearr, difit and
next-shadcn-dashboard-starter differ only by React Compiler diagnostics and
`react/no-unstable-nested-components` (next-shadcn-dashboard-starter). (OpenFrontIO needs tsgolint
and evolu's configuration needs oxlint's JavaScript config support to run oxlint at all; they were
compared with the rule configurations above.)

**Speed in round 7** (callgrind, x86-64-v2 builds, one thread): with the default rules zod takes
543.5M instructions against 541.2M before the round (+0.4%: the larger per-file rule tables and
the scope events' extra bookkeeping), vscode/src/vs/editor/common 333.4M against 333.5M.
kimi-code's agent-core-v2 package with kimi-code's configuration, which turns on 10 of this
round's rules: 9,804M against 9,477M (+3.5%, for the new rules' work; their first version cost
+9%: `prefer-set-has` scanned every reference event and every export for each candidate, now
one per-file index of each symbol's reference events and one table of exported names, and maps
keyed by position became an open-addressing table). Whole kimi-code, CPU best of 3 on a loaded
2-core machine: vlint 2.94 s against 2.80 s before the round, oxlint 2.15 s; the import graph's
second parse (planned) was not taken on this round.

**Speed in the previous round**: with the default rules nothing changed (callgrind, x86-64-v2 builds, one
thread: zod 542.6M instructions against 542.9M at the round's start, vscode/src/vs/editor/common
334.1M against 334.7M). kimi-code with its own configuration, which turns on 19 of this round's
rules: 2.73 s and 2.41 s of CPU against 2.53 s and 2.50 s for the round's start (best of 5, two
runs each alternating, load average about 0.9: the difference is within the noise; callgrind on
its agent-core-v2 package: +5.5% instructions; oxlint 2.02 s), for 373 more diagnostics. The rules' first
version cost +18% there; most of it was copying names to compare them (`rules.name_is` compares
in place), the comment list rebuilt for each `prefer-single-call` candidate, and `rjest.refs_of`'s
map of reference lists (now two arrays).

**Speed** (lc corpus, defaults, 1 thread, user+sys CPU, best of 5, 2-core VM, load average
about 0.6): vlint 0.99 s, oxlint 3.83 s; the previous round's vlint takes 2.42 s on the same run.
The difference is `scope.vu`: it kept each name's declarations in one chain across all scopes, so
resolving a reference walked the chain once per enclosing scope, quadratic in minified bundles
(one-letter names declared in thousands of scopes); it's now one hash table keyed by (name,
scope, meaning), with the same answers (a 4 MB bundle in kimi-code: 4.3 s before, 0.46 s now,
oxlint 0.28 s). kimi-code with its own configuration (import graph with `no-cycle`, vitest,
pedantic): vlint 2.34 s CPU, oxlint 2.02 s (1.68 s against 1.61 s without the import plugin: the
graph parses every file a second time, and the jest rules on its large test suite are the other
big share). The previous round measured 2.28 s against 4.54 s for lc. Instructions (callgrind, x86-64-v2 builds, one thread) in the latest round: zod 543.8M against
the round's start 550.9M (-1.3%), vscode/src/vs/editor/common 335.0M against 337.9M (-0.9%): the
new rules' per-file tables are made only when one of them is on, and the scope table is sized
once. The round before: zod 550.9M against 545.4M (+1.0%: the semantic checks for private names, exports and
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

