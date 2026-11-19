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

With no files named, vtsc reads the current folder's `tsconfig.json` (or `-p PATH`), as tsc
does: `extends` (paths and packages), `files`/`include`/`exclude`, `target`, `lib`, `types`
and `paths`. Strict mode is what vtsc models: a config that turns a strict option off (or turns
on `exactOptionalPropertyTypes` or `noUncheckedIndexedAccess`) checks no file, and says which
option. Options that only add errors (`noUnusedLocals`, `noImplicitReturns`, ...) aren't
reported yet.

Imports of packages resolve to their declarations as TypeScript's `moduleResolution: "bundler"`
finds them (`exports` conditions `types`/`import`/`default`/`node`, `typesVersions`, `types`,
`typings`, `main` with a declaration next to it, `@types/NAME`, `/// <reference path|types>`), and
without a `types` option the `@types` folders from the current directory up are loaded as tsc 5
does. A package's files are declared, never checked or reported (`VTSC_NO_PACKAGES=1` turns this
off; `VTSC_PKG_LOG=1` prints each package import and what it resolved to). `export =` (with
`import x = require(...)`), ambient modules (`declare module "fs"`, as `@types/node` has them) and
module augmentations are modeled.

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

### n8n (2026-11-14)

One thread, wall seconds on the 2-core VM, every package's own tsconfig (`perf.sh`); tsc 7.0.2
with `--checkers 1 --singleThreaded` and a fresh `--tsBuildInfoFile` each run:

| package | files checked | vtsc | tsc 7 |
|---|---|---|---|
| workflow | 251 | 1.43 | 2.52 |
| @n8n/mcp-apps | 38 | 0.29 | 0.49 |
| @n8n/task-runner | 43 | 0.32 | 0.70 |
| @n8n/backend-common | 36 | 0.28 | 0.61 |
| @n8n/config | 88 | 0.19 | 0.41 |
| @n8n/permissions | 40 | 0.14 | 0.39 |
| @n8n/utils | 97 | 0.29 | 0.47 |
| @n8n/json-schema-to-zod | 40 | 0.20 | 0.30 |
| total | | 3.13 | 5.89 |

With their default threads (2 cores): workflow 1.08 s against 2.52 s, task-runner 0.39 s against
0.83 s. The same 8 packages took vtsc 22.9 s before this work, and earlier numbers here compared
it with tsc runs that weren't checking: these packages are composite projects, and tsc reused
their `dist/typecheck.tsbuildinfo` (written by an earlier run) and checked nothing (0.63 s for
workflow, "Check time: 0.002s"). The errors are unchanged: all 1102 files of 22 packages still
checked with tsc 7's errors, the vtests and the regression set the same.

Where the time went, and what fixed it (callgrind on workflow: 11.5G instructions to 5.8G, after
22.9 s to 4.4 s over the 8 packages in the first round):
- Caches tsc has: composed mappers, mappers interned by their contents, a package's declarations
  given types only when used, each type's signatures instantiated once, scope lookups, a call's
  result when its context and the flow state are the same (with the epoch of what it read),
  conditional types by their arguments, `is_generic`, weak types, subtype reductions.
- Unions and intersections interned by Int hashes instead of strings; members read by index
  instead of copied lists; signatures read in place instead of copied.
- Linear where it was quadratic: a `&&`/`||` chain's facts found once per chain (the first
  operand of a 40-term chain was checked about 1,500 times); a type found in a large union by a
  set (containsType), not by relating it to each member; subtype reduction skips pairs that can't
  relate (tsc's key property, object literals' property names, primitives when there's no empty
  object type).
- Loops: each pass is a real one, and the pass that settles is kept as the final one.
- Vu's runtime: Int map keys hashed with a keyed multiply-mix instead of SipHash.
- The checker isn't freed piece by piece when the program exits (3% of the run).


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

`./vtest.sh VTSC` runs the checked-in cases in `vtests/` (each folder's errors made by tsc 7,
including a `node_modules` of packages laid out each way the resolver handles).

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

## Seven more repositories, default configuration (2026-11-09)

vlint and oxlint 1.90.0 with no configuration, JSON compared diagnostic by diagnostic, wall time
the best of 3 on the same 2-core VM:

| repository | files | identical | only oxlint | only vlint | oxlint | vlint |
|---|---|---|---|---|---|---|
| vuejs/core | 539 | 471 | 0 | 0 | 172 ms | 66 ms |
| excalidraw | 723 | 254 | 0 | 0 | 191 ms | 113 ms |
| hoppscotch | 1588 | 312 | 1 | 1 | 210 ms | 117 ms |
| immich | 1574 | 13 | 0 | 0 | 211 ms | 116 ms |
| nuxt | 2114 | 71 | 0 | 0 | 227 ms | 114 ms |
| nuxt/ui | 4345 | 366 | 1 | 1 | 277 ms | 216 ms |
| vscode | 15572 | 10859 | 9 | 9 | 2916 ms | 2824 ms |

The remaining differences are all parse errors in deliberately broken files (test fixtures),
where vlint words the message as TypeScript does and oxlint as oxc's parser does (e.g. `';'
expected.` against `Expected a semicolon or an implicit semicolon after a statement, but found
none`; hoppscotch's is a `.d.ts`, nuxt/ui's an empty JSX attribute expression). Both report the
file as broken at the same place in most of them.

Fixed on the way (each case is a probe folder in `probes/`, checked with `./oxprobe.sh`):
no-empty-file never runs on `.vue`/`.svelte`/`.astro` sections, as in oxlint; in TypeScript an
import and a declaration of the same name are one symbol (no redeclaration error, used together,
reported where first declared and worded as oxlint words it); in JavaScript an import followed by
a function of its name is reported twice, as oxlint does; a type alias and a type alias,
interface, class or enum of its name are a redeclaration; duplicate class members (oxc's
check_duplicate_class_elements: fields, accessors and methods with bodies, public ones only in
TypeScript, and TS2804 for a private name both static and not); `@dec()` followed by a computed
member on the next line (`[X]: string`) is a decorator and a member, not an element access (the
parser is shared, so vtsc gets this too); no-setter-return's span on a parenthesized arrow body.

## The React Compiler rules (2026-11-18, latest)

oxlint's 22 rules from oxc's port of the React Compiler (`react(purity)`, `refs`,
`set-state-in-effect`, `memo-dependencies`, `exhaustive-effect-dependencies`, `immutability`,
`hooks`, `todo`, ...) all come from one compile of each file's components and hooks, each rule
reporting the diagnostics of its category. vlint now runs the same compiler, ported to Vu (`rc_*.vu`,
about 15,500 lines with its generated tables, read side by side with `oxc_react_compiler` 1.90.0): discovery of components
and hooks and the suppression comments, lowering vlint's syntax tree to the compiler's HIR, SSA,
constant propagation, type inference with oxc's shapes and globals (`rc_gdefs.vu` is generated from
`globals.rs` by `rc_gen/gen_shapes.py`), the mutation and aliasing analysis (effects, then ranges),
reactive places and scope variables, and every validation up to `ValidateStaticComponents`. 21 of
the 22 rules are on in `limpl.vu`.

Compared with oxlint 1.90.0, every React Compiler rule on, diagnostics compared with message, help,
note and every label:

| files | oxlint | vlint | identical | missing: preserve-manual-memoization | other differences |
|---|---|---|---|---|---|
| oxc's compiler fixtures (1,846 files) | 464 | 447 | 444 | 16 | 3 extra, 1 more missing (below) |
| the `.tsx`/`.jsx` of 21 repositories (5,829 files: excalidraw, tldraw, immich, next.js, supabase, outline, mantine, ...) | 780 | 771 | 771 | 9 | none |
| outline's `app/` with its own `.oxlintrc.json` | 159 | 149 | 149 | 10 | none |

Not done: `preserve-manual-memoization` (its validation runs on the reactive function, after about 15
scope passes that aren't ported) is still named on stderr as not implemented. The other fixture
differences come from those passes too: two invariants and a `todo` they throw (oxlint then
reports only that error, vlint the function's earlier ones: the 3 extra are such a file's 2 `hooks`
errors, and a `.js` file using TypeScript syntax, which oxc refuses to parse and vlint's parser
accepts). Speed: the 5,829 files take 4.4 s with these rules, as with oxlint.

## Rules a production configuration was missing (2026-11-18, earlier)

A company configuration (not public) had these rules on, where vlint reported nothing. In order of
how often oxlint reported them there:

| rule | oxc's test cases identical | fix cases identical |
|---|---|---|
| `require-await` | 36 / 37 (the other: a top-level `for await` oxc rejects and vlint's parser accepts) | 19 / 19 |
| `react-perf/jsx-no-new-function-as-prop`, `-object-`, `-array-`, `jsx-no-jsx-as-prop` | 109 / 109 | |
| `jsdoc/check-tag-names` (oxc_jsdoc's parser, `settings.jsdoc`) | 56 / 56 | |
| `promise/always-return` | 74 / 74 | |
| `react/jsx-no-constructed-context-values` | 41 / 41 | |
| `no-empty-function` | 245 / 245 (3 not run: options the harness can't read) | 19 / 19 |
| `react/jsx-no-useless-fragment` | 39 / 39 | 18 / 18 |
| `sort-imports` | 66 / 66 (2 not run, as above) | 9 / 9 |
| `oxc/no-barrel-file` (counts through the module graph, node_modules included) | 8 / 8 | |
| `promise/no-return-wrap` | 72 / 72 | |

Checked with `oxrh.py` (each pass/fail case of the rule's `.rs` file, run by oxlint 1.90.0 and by
vlint with only that rule on, outputs compared) and `oxfix.py` (each fix case, files compared after
`--fix --fix-suggestions --fix-dangerously`); both are in the session's scratch, not the repo. The
saved probe `probes/round-r9` has all of them on one project (20 diagnostics, identical). The
regression checks (n8n defaults 3,688, editor-ui 1,377, lc 308 files, oxc's cases for earlier rules,
the probes) are unchanged.

Not done then: the React Compiler rules (done since, above, except
`preserve-manual-memoization`), and the other 22 `jsdoc` rules.

**Rules vlint doesn't have are now named on stderr.** When the configuration turns on a rule vlint
doesn't implement, vlint prints, once per run, `vlint: N enabled rules aren't implemented yet and
won't report anything: ...` (stdout and the exit code are unchanged). The table is `limpl.vu`,
generated by `gen_impl.py` from the rule codes in the sources: 398 of oxlint's 872 rules (every
rule code oxlint reports on the regression repositories is in it). oxlint's default configuration
prints nothing.

**A bug found on the way:** since the JS plugins round (2026-11-06) two more entries follow the
rules' options, and three readers still counted from the end: `settings["jsx-a11y"]`
(`polymorphicPropName`, `components`) was never read (`<Image>` mapped to `img` wasn't checked by
`alt-text`), and the environments and globals turned off came from the wrong entries for the
two rules that look up globals: `no-implied-eval` (with `env.browser`, oxlint reports
`window.setTimeout("alert(1)")` and vlint didn't; it does now) and `no-shadow`'s `builtinGlobals`.
They now read their entries by position (`rmore.extra`).

**Also this round:** `react/no-unstable-nested-components` (oxc's 88 cases identical, unix and
JSON output); oxc's parser errors for `await` and `for await` outside async functions, in class
static blocks, and module syntax in `.cjs` files (`import`/`export` statements, `import.meta` also in
`.cts`): 72 of 72 placements across `.js .cjs .mjs .ts .cts .mts` identical to oxlint, where vlint
reported none before. Found with them: `is_module` took a `for (const …)` declaration's empty
modifier field for `export`, so such a file counted as a module.

**JS plugin hosts can't hang a run (issue #7).** Two ways a run could stop forever, where oxlint
finishes: a plugin that keeps Node's event loop alive (a timer, an open handle) kept its host from
exiting when its input closed, and vlint waited for it at exit without a limit (reproduced: a plugin
with `setInterval` hung the previous build until killed, and the run now ends in 2 s); and a host
that stops answering (a plugin stuck in a loop) kept the file's thread waiting. Now every read and
write on a host's pipes gives up after `VLINT_JS_TIMEOUT` seconds (default 120, 0 for no limit) and
the host is killed: that file gets `Error running JS plugin` saying so, and the rest of the run goes
on (checked: a plugin looping on one file of 400, with a 3 s limit, gives that error and the 400
files' other diagnostics, in 3.4 s). At exit a host gets 2 s. Hosts are started one at a time with
close-on-exec pipes (on macOS with `POSIX_SPAWN_CLOEXEC_DEFAULT`), so one can't inherit another's
pipe ends, and the host answers every request once, even if handling it throws. `VLINT_JS_DEBUG=1`
traces requests and answers on stderr. Not reproduced: the macOS 39k-file stall itself (this was
checked on Linux; the Mac wasn't reachable), so whether it was one of these is not confirmed.

**An old oxlint-tsgolint is named (issue #6).** When the tsgolint found is older than 7.0.2005 (what
oxlint 1.90.0's package.json requires; older ones panic with `unknown rule` on newer rule names),
vlint says so on stderr before running it. The run and its output are otherwise oxlint's (tsgolint's
stderr was already passed on).

**Issues #6 and #7, follow-up (2026-11-18).** #7 still stalled on macOS with 0.4.1, with a thread
in `write` and none in `poll`. The write path waited once for room in the pipe and then wrote the
whole request (178 KB there) with a blocking `write`, and `poll`'s "writable" only means some room,
so a host that stopped reading held that thread forever, past `VLINT_JS_TIMEOUT`. The pipe to a
host is now non-blocking: each wait for room is limited, and a host that takes nothing for the
limit is killed and the request sent again to a new one. Reproduced on Linux (one thread, 440
files of 2.4 MB, `VLINT_JS_TIMEOUT=5`): a plugin that, after answering one file, blocks its host
for 40 s at 0% CPU (`Atomics.wait`) while the next request is written. The previous build sat in
`write` for all 40 s, ignoring the limit, and said nothing (61.7 s; 20 s without the nap); now
the host is killed after 5 s and the run ends in 27.4 s with the same 440 diagnostics. Freezing
the host with `SIGSTOP` mid-write, three times: the same output as a normal run each time.
`VLINT_JS_DEBUG=1` now names the
host's pid, its fd, the request's size and file before each write, and how much was written when a
write waits more than 1 s or gives up. A host also exits when its input ends or fails. Still not
known: why the Mac's host stopped reading (it was at 0% CPU); the trace will say which file and
host. AFFiNE with its six JS plugins (no type-aware rules), two runs each: the same 322
diagnostics and stderr as the previous build, 45.5 and 46.6 s against 50.3 and 46.9 s.
#6 in a pnpm workspace: `node_modules/.bin/tsgolint` is a shell shim there, so the package.json
beside it wasn't tsgolint's. vlint now also looks for `oxlint-tsgolint/package.json` in the
`node_modules` folders above the binary and above the working folder, and in the pnpm store paths
the shim names (the version in the store folder's name if its package.json is gone). Checked in a
real pnpm workspace with oxlint-tsgolint 7.0.2001: the warning shows (it didn't before), also with
the `node_modules/oxlint-tsgolint` link removed. When no version is found and tsgolint fails with
`unknown rule`, vlint adds a line saying that's what an old oxlint-tsgolint does (checked with a
copied 7.0.2001 binary and no package.json around). The `Error running tsgolint` line itself stays
oxlint's.

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
| `--type-aware`, `--type-check`, `options.typeAware/typeCheck` | yes: runs tsgolint (`oxlint-tsgolint`) as oxlint does, with one deliberate difference: when tsgolint (7.0.2006 and earlier) panics in no-misused-promises on an object literal member with a computed name (`{ ["a"]: async () => {} }`), oxlint fails with `Error running tsgolint`; vlint runs tsgolint again with that rule left out for the files that have such a member, prints a warning naming them, and reports everything else (issue #3) |
| `--report-unused-disable-directives[-severity]` | yes |
| `--rules` | yes (the table, `-f json`) |
| `--init` | yes |
| `--print-config` | yes (`lprint.vu`; byte-identical on the 15 real projects and 8 hand-written configs; several `jsPlugins` entries can come out in another order, see below) |
| `--fix-suggestions`, `--fix-dangerously` | yes for the rules that have them in vlint (see below); not yet: `no-unused-vars`', `no-new-array`'s and `no-extra-boolean-cast`'s suggestions |
| `--lsp` | no (refused) |
| `--suppress-all`, `--prune-suppressions` (hidden), `oxlint-suppressions.json` | yes (`lsupp.vu`) |
| `--type-check-only` (hidden) | yes (tsgolint's type check only, oxlint's messages for invalid combinations) |

**The type check by vtsc (`VLINT_VTSC=1`, off by default, 2026-11-14)**: with `--type-check`,
vlint can take the type errors from vtsc, its own checker, run in the same process, for every
file vtsc fully checks in its tsconfig's program. tsgolint then type-checks only the other files
and still runs the type-aware rules (`lvtsc.vu`). The errors are tsgolint's, file for file and in
its order (each program's errors in program order, imports first, before that program's rule
diagnostics). Against oxlint 1.90.0 with n8n's tsgolint 0.21.1, default configuration, on 22 n8n
packages: no difference in either `--type-check` (every line equal) or `--type-check-only`.
vtsc checks 809 of the 1,280 linted files under a tsconfig; the rest are files that tsconfig
doesn't include, files that use something vtsc doesn't model, and every file of the 6 packages
whose tsconfig has `references`. It stays off for now: the type-aware rules still need tsgolint's
program, so tsgolint runs either way (when this was measured, vtsc itself was also slower:
`--type-check` took 0.3-4.0 s per package with vtsc against oxlint's 0.2-2.7 s, and 14.7 s on
mcp-apps, Vue's types; vtsc's speed since: "n8n" under Speed). TypeScript's lib files come from
`$VTSC_LIB`, else the nearest TypeScript 7 or 6 install; with an older one, tsgolint checks
everything.

### The type-aware rules in vtsc (2026-11-14)

The 15 type-aware rules oxlint turns on by default now also run inside vtsc (`trules.vu`), over
each file it fully checks, ported from tsgolint 0.21.1 (the version n8n uses): await-thenable,
no-array-delete, no-base-to-string, no-duplicate-type-constituents, no-floating-promises,
no-for-in-array, no-implied-eval, no-meaningless-void-operator, no-misused-spread,
no-redundant-type-constituents, no-unsafe-unary-minus, no-useless-default-assignment,
require-array-sort-compare, restrict-template-expressions, unbound-method. With `VLINT_VTSC=1`, a
file whose type check and rules are all vtsc's isn't sent to tsgolint at all; a rule that reaches
something vtsc doesn't model leaves that file's rules to tsgolint (`VLINT_VTSC_RULES=0` turns the
rules off). `vtsc --lint RULES` prints them as tsgolint's messages.

Checked two ways:
- tsgolint's own test cases (`tsgolint_parity.py`: each case's program run through the tsgolint
  0.21.1 binary and through `vtsc --lint`): 1,107 of 1,258 cases give the same diagnostics (ranges,
  message ids, messages, help, labels), 7 differ, 135 are files vtsc doesn't check or rules it
  leaves to tsgolint, 9 have options not written as JSON. The 7: unbound-method 4 (a class
  extending Array's statics, `C.prototype.m`, a for-of pattern), and one each in no-base-to-string
  (a user function named String), no-floating-promises (`yield*`'s result type) and
  restrict-template-expressions (tsgo prints an unresolved type parameter by its name).
- The 22 n8n packages, default configuration, `--type-aware --type-check`: every line equal to
  oxlint's (`hyall.sh`). 809 of 1,280 files get their type check from vtsc, and the rules of
  almost all of those. Wall time over the 22: oxlint 22.0 s, vlint with this 20.5 s, vlint with
  tsgolint for everything 20.8 s; tsgolint still starts for each package with a file vtsc doesn't
  cover, which most have, so it stays opt-in.

Found on the way (and fixed in the checker, since tsc does them): `x ?? y` is x's type when x can't
be nullish; a homomorphic mapped type over a type with an index signature keeps the declared
properties (zod's `meta()?.title` was `unknown`). Not modeled yet, so those files' rules are
tsgolint's: tsc narrows `unknown` by typeof as `{} | null | undefined`, and intersects a narrowed
type parameter with what the narrowing leaves; a pattern's contextual type keeps its
initializer's literals.

While doing this, one walker difference was fixed. Outside a git repository, oxlint's walker
applies the `.gitignore` files of every folder above the paths it lints (a package's folder
inside a monorepo copied without `.git`). vlint read them only up to a `.git`, so it linted
`node_modules` there.

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

### The type check's cache (2026-11-16)

With `VLINT_VTSC=1`, vlint keeps what the type check found, in `$XDG_CACHE_HOME/vlint/vtsc-files`
(`~/.cache/...`; `VLINT_VTSC_CACHE=0` turns it off), so a run where little changed checks little:

- Each file of a program has a key: a hash of its path, its source and what its imports resolved
  to, summed over everything it imports all the way down, with the hashes of whatever declares
  globals (lib files, scripts, `declare global`, module augmentations), the compiler options, the
  lib folder, its rule list and the vlint executable (`tsprog.file_keys`). A file whose key is in
  the cache isn't checked: vtsc still reads and binds the program (about 0.2-0.4 s for n8n's
  packages), checks the files whose keys changed and takes the rest's errors, rules' diagnostics
  and reasons for not checking from the cache. What a file's check found in another file (a
  construct vtsc doesn't model) is kept with it and applied again.
- tsgolint's results for the files vtsc leaves to it are kept by the same keys, per rule list, so
  tsgolint runs only for those whose keys changed (none: it doesn't start). A message about no file
  turns this off for the folder.
- When the options, the file list and every file and folder the last run looked at (their
  modification and change times, sizes and inodes) are as they were, the last run's result is the
  answer without reading a file. A file changed less than 2 s before the run's end isn't trusted
  that way (as git's index treats racy files); its key decides next time.
- With at most 16 changes since the last run, one worker checks instead of one per core (the
  others' parse is all they'd do).

Checked: a run with the cache prints the same as one without it after each of 155 random edits to
a copy of `@n8n/workflow-sdk` (adding type errors, widening and narrowing declared types, adding
imports, adding and removing files, touching files and doing nothing, in sequence; tsgolint left
out there, since it runs out of memory on the copy). Over the 33 n8n packages, `--type-aware
--type-check`, default configuration (`hyw.sh`): every line equal to oxlint's, the first run and
the second.

| | oxlint | first run | next run |
|---|---|---|---|
| 22 smaller packages (total) | 20.5 s | 11.2 s | 0.7 s |
| `@n8n/api-types` (608 of 704 files vtsc's) | 6.86 s | 7.30 s | 0.15 s |
| `core` (164 of 286) | 3.90 s | 6.19 s | 0.11 s |
| `@n8n/workflow-sdk` | 2.37 s | 2.85 s | 0.11 s |
| `frontend/@n8n/composables` | 2.68 s | 3.85 s | 0.03 s |
| `@n8n/node-cli`, `@n8n/eslint-config` (no TypeScript 7 lib: all tsgolint's) | 0.93, 0.91 s | 0.86, 0.74 s | 0.88, 0.86 s |

After an edit to one file of `@n8n/workflow-sdk` (the copy), the type check takes 0.4-1.0 s
against about 1.0 s without the cache (vtsc's part only; oxlint takes 2.4 s for the package each
time). A first run is still slower than oxlint where vtsc leaves files to tsgolint: both run, and
tsgolint's cost is mostly its program, not the files. On this two-core machine, starting tsgolint
beside vtsc (`VLINT_VTSC_SPECULATE=1`) is slower again (`core` 6.7 s, `@n8n/api-types` 10.6 s).

Also: a statement past 400,000 type instantiations (was 1,000,000) leaves its file to tsgolint; the
most n8n's checked statements need is 390,000, and reaching the limit took up to 1.6 s
(`core`'s `supply-data-context.ts`, lodash's `get`), so `core`'s check went from 2.8 s to 1.5 s.

### Twice as fast as oxlint on every package (2026-11-18, latest)

The same 33 n8n packages, the same comparison (best of 3 interleaved runs, cache cleared before
each, 2-core VM, load average 1-1.8, `hyw3.sh`): every line equal to oxlint's in all 33, no file
left to tsgolint, and vlint at least 2x faster on each:

| | oxlint | vlint | |
|---|---|---|---|
| `@n8n/api-types` (704 files) | 7.28 s | 3.47 s | 2.10x |
| `core` | 4.08 s | 1.75 s | 2.33x |
| `workflow` | 3.23 s | 1.26 s | 2.57x |
| `frontend/@n8n/composables` | 3.22 s | 1.27 s | 2.53x |
| `@n8n/workflow-sdk` | 2.55 s | 1.10 s | 2.32x |
| `@n8n/ai-utilities` | 2.45 s | 0.96 s | 2.55x |
| `@n8n/telemetry` | 2.20 s | 0.74 s | 2.97x |
| `@n8n/decorators` | 1.92 s | 0.56 s | 3.45x |
| `frontend/@n8n/stores` | 1.32 s | 0.58 s | 2.28x |
| `@n8n/task-runner` | 0.94 s | 0.40 s | 2.34x |
| `@n8n/eslint-config` | 0.83 s | 0.36 s | 2.30x |
| `frontend/@n8n/chat` | 0.96 s | 0.42 s | 2.31x |
| 21 other packages | 0.26-1.56 s | 0.07-0.44 s | 2.40-4.60x |

What changed (each measured on the package it was found in; instruction counts from callgrind
on a build for plain x86-64):
- **Conditional and mapped types keep only the outer type parameters they mention**
  (getConditionalTypeInstantiation's outer type parameters; one with a `typeof` query keeps them
  all). A deferred conditional type carried every type parameter in scope, about 19, and composing
  it with the next mapper instantiated each one. eslint-config's `base.ts` (type-fest's `KebabCase`
  under eslint-import-context's `WithPluginName`): 94 -> 55 ms, 81,691 -> 66,096 instantiations,
  mapper entries 180,724 -> 58,844. Also memoized: `inter_of` of two types, `cond_key` and
  `strip_infers` by node and mapper.
- **Subtype reduction** of a union of more than 10 members skips the pairs whose key properties
  differ (removeSubtypes does so for any object type, not only object literals): a rule file whose
  conditional expression joins two of TSESTree's `Node` unions, 31 -> 12 ms.
- **The type-aware rules**: their visitor compared every rule's name, copied, at every node (5.5
  million string copies on workflow-sdk); rule numbers, a table of the node kinds some rule visits,
  and the children walked without lists built: 6.79 -> 5.46 G instructions for workflow-sdk's
  program with its 15 rules (4.87 G without them).
- **The cache keys** (vlint): each file's import closure walked file indexes, not paths looked up in
  a map at every step: workflow-sdk's 128 -> 36 ms per worker.
- **Cores**: the largest program gets one worker fewer than the cores when the others are a third
  of its size or more (each worker parses the whole program): eslint-config 0.40 -> 0.38 s, best
  of 5; workflow-sdk and task-runner keep a worker per core (one fewer was slower for them).
- List copies are slices (one allocation), and the lib files' reference directives are read from
  their heads only: 2.5% of workflow-sdk's instructions.
- New vtest `typeof-param-cond` (vue-i18n's `createI18n`, which the first version of the mapper
  cut got wrong in `@n8n/mcp-apps`: found by the n8n parity run, fixed before commit).

### No file left to tsgolint (2026-11-18)

Over the 33 n8n packages (`--type-aware --type-check`, default configuration, cache cleared
before each run; oxlint 1.90.0 with tsgolint against vlint with `VLINT_VTSC=1`): every line equal
to oxlint's in all 33, and vtsc checks every file of every program, tsgolint's inferred program
included (`inv.sh`: none left). vlint then doesn't look for tsgolint at all: run without
`OXLINT_TSGOLINT_PATH` and with no tsgolint installed, `frontend/@n8n/chat` prints what oxlint
prints. (tsgolint is still looked for, and its missing-executable error printed, the moment a file
would be left to it.)

Best of 3 runs each, interleaved, same 2-core VM (`hyw3.sh`, load average about 1):

| | oxlint | vlint | |
|---|---|---|---|
| `@n8n/api-types` (704 files) | 7.70 s | 3.85 s | 2.00x |
| `core` | 4.43 s | 2.12 s | 2.09x |
| `workflow` | 3.08 s | 1.47 s | 2.10x |
| `frontend/@n8n/composables` | 3.00 s | 1.41 s | 2.13x |
| `@n8n/workflow-sdk` | 2.75 s | 1.42 s | 1.94x |
| `@n8n/ai-utilities` | 2.59 s | 1.05 s | 2.46x |
| `@n8n/telemetry` | 2.38 s | 0.83 s | 2.88x |
| `@n8n/decorators` | 1.95 s | 0.68 s | 2.89x |
| `@n8n/engine` | 1.65 s | 0.50 s | 3.30x |
| `frontend/@n8n/stores` | 1.33 s | 0.64 s | 2.09x |
| `@n8n/node-cli` | 1.05 s | 0.50 s | 2.09x |
| `frontend/@n8n/chat` | 1.00 s | 0.47 s | 2.10x |
| `@n8n/task-runner` | 0.99 s | 0.51 s | 1.93x |
| `@n8n/eslint-config` | 0.84 s | 0.46 s | 1.82x |
| 19 other packages | 0.29-1.30 s | 0.08-0.52 s | 2.25-3.79x |

Below 2x: `eslint-config` (three programs, two of them a few files each, every one parsing the
lib and `@types` again: 0.07-0.13 s each), `task-runner` and `workflow-sdk`, within the runs'
spread of 2x (single runs vary by about 10%).

What changed:
- **The last fallbacks**: `templates[type][name]` (`N extends keyof M[T]`: the read stays
  `M[T]`, and `M[T][N]` has no constraint where a union member lacks the key); a `in`-narrowed
  union-constrained parameter read in a closure; a union of one declaration's generic methods
  (their constraints compared through the instantiation); `Omit<O, K>` against a union; zod and
  langchain inference stopped at `isDeeplyNestedType` (it ran to millions of instantiations); each
  side's own `this` in inference; `flatten<T> = identity<{ ... }>` printed without the alias; a const
  type parameter as an object literal property's contextual type; `pkg/` as the package itself;
  `for await` over an iterable whose iterator is `this`; the permissive and restrictive
  instantiations of a conditional type with free type variables.
- **TypeScript 7's default is strict** (a `{}` tsconfig is strict; vtsc read it as loose). A strict
  flag set off checks only files it can't matter in (enums, constants of literals).
- **JavaScript** (decorators' 118 stale tsc outputs): tsc's CommonJS output (`exports.x = ...`,
  top-level `this && this.__decorate`, `Object.defineProperty(exports, ...)`), a class's
  `this.x = v` declarations (the constructor's widened types, `[]` as `any[]`, `| undefined` when
  only methods assign), inference without candidates giving any, `extends` a generic expression
  filled with defaults, destructured parameters without types, and errors that don't change types
  allowed (no checkJs: none reported). A TypeScript file the inferred program only imports doesn't
  need its TC39 decorators modeled.
- **Speed**: vlint checks its programs in-process (no worker process and JSON;
  `VLINT_VTSC_ISOLATE=1` keeps them); vtsc's workers take files from a shared queue; a file a worker
  only declares gets its declarations' types as importers ask for them, and a one-signature call
  there isn't checked against its arguments; programs at once share the cores; a worker per core
  from 16 files; a conditional type's free type variables found without resolving object
  literals' members (chat's check 508 -> 230 ms).
- TS2695 and TS2776 (`(0, f)(x)` assertion calls), vtsc printing duplicates of different spans as
  tsc does, `export { a as b }` in a namespace (events' `EventEmitter.EventEmitter`).

### Fewer files left to tsgolint (2026-11-18, later)

Same setup (`hyw.sh` over the 33 packages, oxlint 1.90.0 with tsgolint against `vlint` with
`VLINT_VTSC=1`, cache cleared for the first run): every line equal to oxlint's in all 33
packages, first run and second. Packages that used to send files to tsgolint and now don't:
`frontend/@n8n/chat` (53 of 53 files, was 41), `frontend/@n8n/stores` (39 of 39, was 29),
`@n8n/api-types` (700 of 700, was 697), `@n8n/eslint-config`'s main program (73 of 73, was 68).
Fewer in `@n8n/node-cli` (45 of 59 in its main program, was 20) and `@n8n/ai-utilities` (164 of
183, was 152).

| | oxlint | first run | next run |
|---|---|---|---|
| `core` | 4.93 s | 2.57 s | 0.12 s |
| `@n8n/api-types` | 8.35 s | 4.46 s | 0.25 s |
| `workflow` | 3.13 s | 1.52 s | 0.11 s |
| `frontend/@n8n/chat` | 1.03 s | 0.51 s | 0.03 s |
| `frontend/@n8n/stores` | 1.39 s | 0.75 s | 0.03 s |
| `@n8n/engine` | 1.66 s | 0.65 s | 0.07 s |
| `@n8n/workflow-sdk` | 2.74 s | 2.25 s | 0.15 s |
| `@n8n/ai-utilities` | 2.42 s | 3.06 s | 0.08 s |
| `frontend/@n8n/composables` | 3.69 s | 4.39 s | 0.03 s |
| `@n8n/node-cli` | 1.15 s | 1.05 s | 0.04 s |
| `@n8n/eslint-config` | 0.92 s | 0.76 s | 0.16 s |
| `@n8n/decorators` | 2.55 s | 2.43 s | 0.07 s |
| 21 other packages | 0.3-2.4 s each | 1.8-4 times less | 0.02-0.07 s |

Not yet twice as fast: the packages where tsgolint still starts for a few files (its start costs
about two seconds: composables 1 file, ai-utilities 20, node-cli 25 of its templates' programs,
eslint-config 8, decorators 118 stale `.js` outputs), and `api-types` and `workflow-sdk`, whose
zod schemas vtsc checks in 6 s of CPU on two cores.

What changed (each checked against tsc 7, 25 new vtests):
- **Errors vtsc got wrong, silently, now right**: a function inside another function that an
  overload candidate checked and dropped was never checked again (pinia's `defineStore` setup
  functions: no errors in their nested functions); `Partial<X>` and conditional types of an
  unresolved `X` (tsgo's unresolvedType is any in a conditional type, the error type isn't);
  same-generic type arguments compared covariantly whatever the interface's measured variance
  (`B<'a'>` assignable to `B<string>` with `f: (x: T) => void`); inference through a type alias's
  type arguments (oclif's `Args.string()`); a union member that's an instantiation of the same alias
  as the source takes the inference (`Flag<T>`); single-quoted property names print with single
  quotes; parameters of immediately invoked functions typed by their arguments (they were
  implicitly any, TS7006).
- **Modeled now**: destructured discriminants (`const { done, value } = await reader.read()`;
  `if (done)` narrows `value`); computed names of a union of literals in destructuring patterns;
  a computed key beside a spread (the spread drops the index signature); `{} | undefined` and
  `T | undefined` spreads (tsc's partial of the constraint); `NoInfer<T>` parameters; mixin
  constructor intersections as class bases (ts-morph); `this is T` predicates of union
  signatures; type guards on `Awaited<T>`; async generators with a return type; `#private`
  names; properties assigned in loops (the loop's fixpoint, as for variables); `import()` in a
  CommonJS file (the `import` condition); TypeScript's package deduplication (two pnpm copies of
  one package version are one: vitest's matchers reach the tests' `Assertion`); a side-effect
  import of a package's JavaScript; interface heritage in variance; variance of recursive aliases
  (a reference inside is related, as tsc's in-progress variance); callback parameters of methods
  compared strictly (`Promise<T>` stays covariant); Lowercase and the like of template literals
  and deferred conditional types; an ambient module's `export =` of a global namespace
  (handlebars); `NoInfer<T>` in a conditional type (type-fest's `IsAny`); a unique symbol key
  missing from an instantiated type with only a string index (unknown, Vue's slots).
- **Printing**: an alias of an interface or class reference keeps its name, `type H<T> = I<T>`
  prints `H<number>` (tsgo does; tsc 6 printed `I<number>`).

### All of n8n core checked, twice as fast as oxlint (2026-11-18)

Same machine and setup (`hyw.sh`, every line equal to oxlint's in all 33 packages, first run and
second):

| | oxlint | first run | next run |
|---|---|---|---|
| `core` (all 275 files vtsc's, was 255 of 264 plus 9 of 11 inferred) | 3.92-4.34 s | 1.83-2.10 s | 0.11-0.14 s |
| `@n8n/engine` (135 of 135, was 117) | 1.51 s | 0.53 s | 0.05 s |
| `@n8n/api-types` | 7.47 s | 5.14 s | 0.17 s |
| `workflow` | 3.92 s | 2.24 s | 0.08 s |
| 20 other smaller packages | 0.3-2.7 s each | 2-4 times less | 0.01-0.05 s |
| `@n8n/decorators` | 2.09 s | 1.97 s | 0.07 s |

Still slower than oxlint on a first run: `frontend/@n8n/composables` (one Vue test file vtsc leaves
to tsgolint: inference to a mapped type with an `as` clause), `stores` and `ai-utilities` (11 and
35 files left), `@n8n/decorators` (121 stale `.js` build outputs in `src`, tsc's CommonJS).

What changed:
- **Long types in messages print as tsc 7 prints them.** Past 160 characters tsc elides members
  (`... 31 more ...`) and union or argument lists, by an approximate length it counts as it
  builds the type, and cuts the text at 320 characters. Each form's count was measured against
  tsc 7 (a property's name plus one, a named type's name twice, two per list member, a
  parameter's name after its type, `readonly` after the property's type). Such a message used to
  leave its file unchecked. 750 generated types compared with tsc 7: the differences left are
  union orders and reductions vtsc already got wrong in short messages. Printing also stops after
  4000 types (one mock's message took 614 ms, now 49 ms).
- **TC39 decorators** (no `experimentalDecorators`): method and getter decorators are checked
  (TS1241, TS1270); class decorators of type `Function` or `any` are untyped calls; any other
  decorator leaves its file unchecked (before, none were checked).
- **CommonJS in JavaScript**: `require("x")` is the module (a relative file or a CommonJS module
  isn't modeled); `module.exports = ...` at the top level; a JavaScript file no type-aware rule
  runs on only has to parse.
- **Coverage**: an augmentation's interface is the merged one inside the augmentation (vitest's
  `expect.soft`); classes extending or implementing an import of a module not found; `typeof a.b`
  through intersections; array destructuring of unions of tuples; object destructuring
  assignments; JSON files in packages; `Awaited<T>` against an object type.
- **Errors vtsc got wrong, silently**: the subtype reduction let `{ a; b }` absorb a fresh
  `{ a }` literal (an `it.each` table failed with TS2769); a missing property on `this` named the
  type `this` instead of the class; a mapped array of the error type wasn't the error type; a
  call with explicit type arguments whose arguments fail now returns the defaults as written
  (`mock<T>({...})` is `_MockProxy<T> & T` in tsc).

### More of n8n checked, and the second run everywhere (2026-11-17)

Measured on the same two-core machine, oxlint 1.90.0 with tsgolint against `vlint` with
`VLINT_VTSC=1`, `--type-aware --type-check`, default configuration (`hyw.sh`): every line equal to
oxlint's in all 33 packages, the first run (cache cleared) and the second.

| | oxlint | first run | next run |
|---|---|---|---|
| 22 smaller packages (total) | 20.96 s | 11.20 s | 0.67 s |
| `core` (255 of 264 files vtsc's, was 164 of 286) | 4.24 s | 5.79 s | 0.13 s |
| `@n8n/api-types` | 7.43 s | 5.71 s | 0.21 s |
| `@n8n/workflow-sdk` | 2.51 s | 2.19 s | 0.12 s |
| `@n8n/engine` (117 of 135, was 110) | 1.68 s | 1.35 s | 0.07 s |
| `frontend/@n8n/composables` | 3.34 s | 4.58 s | 0.03 s |
| `@n8n/ai-utilities` | 2.73 s | 2.87 s | 0.07 s |
| `frontend/@n8n/stores`, `chat` | 1.39, 1.00 s | 1.82, 1.36 s | 0.03, 0.03 s |
| `@n8n/node-cli`, `@n8n/eslint-config` (no TypeScript 6 or 7 lib) | 1.07, 0.81 s | 1.56, 1.01 s | 0.06, 0.15 s (were 0.88, 0.86 s) |
| `frontend/@n8n/rest-api-client` | 1.08 s | 0.52 s | 0.03 s |

A first run is still slower than oxlint where a package keeps files vtsc leaves to tsgolint
(`core`'s 9 test files, `composables`' 2): tsgolint then loads the whole program as oxlint does,
after vtsc's check. Every next run takes 0.03-0.21 s, 20-140 times less than oxlint.

What changed:
- **tsgolint's cache without a TypeScript 6 or 7 lib**: vtsc still finds such a program's files
  and their keys (nothing checked), its own and the inferred program's, so tsgolint's results
  are cached there too. Messages tsgolint reports outside the requested files (a template's
  `tsconfig.json`) are kept for the whole set of files, under all their keys and those files'
  contents, instead of turning the cache off. Checked on a copy of `node-cli`: after editing a
  template's tsconfig, restoring it, editing a source file and editing an inferred-program file,
  each run printed what oxlint printed.
- **Instantiations cached by mapper** (a union, intersection, conditional type, indexed access,
  keyof or template by the same interned mapper is the same instantiation): `core`'s check 2.2 s
  to 1.5 s; inference into a recursive conditional type stops where tsc's `invokeOnce` does
  (lodash's `get` with a contextual type went past the instantiation limit), 1.2 s.
- **Errors vtsc missed, silently**: a `catch (e)` variable was `any` whatever
  `useUnknownInCatchVariables` said; `get(o, ['a', 'b'])` (a literal in a tuple contextually
  typed by type parameters constrained to `keyof`) picked lodash's `any` overload;
  `[1] extends [infer A extends string]` took the true branch; `instanceof` never reported a
  primitive left side (TS2358); `k in x` with `k` a constant didn't narrow; `[a] = anyValue`
  kept `a`'s narrowing.
- **Errors vtsc reported that tsc doesn't** (in files checked for the first time): the right side
  of `&&` without the contextual type; object-literal methods with a `this` parameter (every
  parameter implicitly `any`); `this` in an arrow function in a derived class's constructor
  (TS17009); `x!` where `x` is only `null` by flow (tsc takes the declared type); a property
  narrowed before its object was narrowed to an intersection; `break label` out of a labeled
  block (now left unmodeled).
- **Coverage**: assignments in conditional and logical expressions joined; `this as T` through a
  mapped type; labeled `break`/`continue` to loops; for-of over existing variables in a pattern;
  a union's generic methods (`(A[] | B[]).flatMap`); `instanceof` with an unresolved import or
  generic construct signatures; a method call's `this` in an optional chain; properties
  assigned in loops; package-declared iterators; `as const` with shorthand properties;
  destructuring intersected tuples; `Exclude` over a union with a named member prints by it.

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

