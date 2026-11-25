# Working on vtsc, vlint and vknip (ts/)

A map for changing these tools without re-reading 50,000 lines. `README.md` says what they do
and how well; this file says where things are. Keep it current when you move things.

## Build and check

- `../vu check vlint.vu` (and `vtsc.vu`, `../knip/...`): milliseconds, run after every edit.
- `../vu build --release vlint.vu -o OUT` takes about 45 s. Build to a scratch path, not to
  `ts/vlint`, while you compare old and new.
- `parse.vu`, `scan.vu` and `ast.vu` are shared by vtsc, vlint and vknip. After a parser change,
  run all three tools' regressions (see "Checks" below).

## Files

| file | what |
|---|---|
| `scan.vu`, `parse.vu`, `ast.vu` | tokens, the parser, the flat tree (`nd[x].k/a/b/c/d/f/s/pos/end`; kinds `N_*`, modifiers `M_*` in ast.vu) |
| `bind.vu`, `chk.vu`, `rel.vu`, `tyops.vu`, `types.vu`, `show.vu` | vtsc: symbols, checking, assignability, type operators, the type table, printing types |
| `ctab.h` | vtsc: the flat type and symbol tables as C columns (`types.ct_at` and friends; see "Checking one program on several workers") |
| `tsconf.vu` | vtsc: tsconfig.json (`read`: options through extends, root files, `unmodeled`; `path_targets`) |
| `tsres.vu` | vtsc: where a package's types are (`resolve_types`, `auto_types`, `triple_slash`); `vtsc.run` loads them as package files (`c.pkg_files`: declared, never checked) |
| `vlint.vu` | vlint's driver: CLI, file walk, workers, tsgolint, output |
| `rules.vu` | the `L` state, the walk, oxlint's default rules, semantic errors (below) |
| `rmore.vu` … `rmore8.vu` | non-default rules ported in batches (each file's header lists its rules); `rmore.vu` has the `newr` scheme: setup says which node kinds a rule needs, `node()` runs them |
| `rmore9.vu` | more non-default rules (its header lists them); it also runs the jsdoc rules (`jsdoc_rules`) and rmore11's |
| `rjsdoc.vu` | the jsdoc plugin: oxc_jsdoc 1.94's parser (`parse_one`, a tag's parts in `tnc`), which comments are JSDoc and the token each is attached to (`leading_docs`: oxc's trivia rules), the node a function's JSDoc belongs to (`nearest_doc`), iter_all's FxHashMap order (`doc_order`, `hb_order`), settings, and its 9 rules |
| `rmore11.vu` | eslint(no-restricted-properties); promise(no-multiple-resolved) on a model of oxc_cfg's graph (`build_cfg`/`cv`: blocks and edges as SemanticBuilder adds them; `mr_check`: the rule's walk) |
| `ra11y.vu`, `ra11y2.vu` | jsx-a11y |
| `rhooks.vu` | react-hooks(exhaustive-deps) |
| `rimport.vu`, `lmod.vu`, `lresolve.vu` | import plugin rules on the module graph, module records, resolution |
| `rjest.vu` | jest/vitest rules |
| `scope.vu` | scopes, symbols, references, redeclarations (below) |
| `lconf.vu`, `lglob.vu`, `lprint.vu`, `lsupp.vu` | config, globs, `--print-config`, bulk suppressions |
| `lout.vu` | reporters (`Diag`, `Lab`, `Rec`, `make_rec`) |
| `lpart.vu` | `.vue`/`.astro`/`.svelte` script sections |
| `ltsgo.vu` | type-aware rules via tsgolint |
| `ljs.vu`, `lhost.vu`, `jsplug/` | JS plugins in node processes (`jsplug/estree.js` turns vlint's tree into oxc's ESTree) |
| `fixgen.vu` | `--fix` code printed as oxc_codegen prints it |
| `lmeta.vu` | generated rule table (`M_*` rule ids, categories, fixability) |

To find a rule: `grep -n '"eslint(no-foo)"' *.vu`. `rules.vu` holds most eslint, unicorn,
typescript, react and oxc rules; its sections start with `# ----` (`grep -n '^# ----' rules.vu`).

## Helpers in rules.vu (use these, don't write new ones)

| helper | what |
|---|---|
| `k(l, n)`, `name_of(l, n)` | a node's kind, its name or literal text |
| `parent(&l, n)`, `class_of(&l, n)` | the parent node, the enclosing class (or -1) |
| `unparen(l, n)` | skip parentheses |
| `key_name(l, key)`, `key_id(&l, key)`, `static_key(l, key)` | a property key's static name (`"\t?"`, -1 or `""` when it has none) |
| `num_value(raw)` | a numeric literal's value |
| `strip_hash(s)`, `best_match(s, cands)` | `#x` → `x`, the "did you mean" suggestion |
| `add(&l, pos, rule, msg, help)`, then `span(&l, end)` and `label(&l, end, text)` | report a diagnostic |
| `on_rule(l, lmeta.M_...)` | is a rule on for this file |
| `shown_src(l.src, l.disp)` | the source as the reporter shows it (needed for `make_rec`) |
| `err_rec`, `err_rec_code` | an error record with labels |

These names are also defined, differently, in other modules (`key_name` and `member_key` in
`rmore2.vu`, `unparen` in `rmore6.vu`, `callee_name` in `rhooks.vu` and `rjest.vu`): check the
module you're in. `../vu check --dups vlint.vu` lists every such name.

## Semantic errors (what oxc's SemanticBuilder reports)

In `lint_l` (rules.vu, after the walk): `scope.vu` records redeclarations in `sc.redecl_pos`
(the first declaration), `sc.redecl_name` and `sc.redecl_at` (the second). These, plus
`private_errors`, `class_elem_dups` and `ts_ambient_errors`, push records onto `sem` with a sort
key on `skey` (where oxc's walk finds them; things oxc checks when the program ends get keys past
`src.len`). If `sem` isn't empty, the file reports those errors and no lint rules, as oxlint does.
Parser errors that oxc adds after parsing are `parser_late_errors`.

## Scopes: how `declare` merges (scope.vu)

There are two tables per scope, values and types (`tab_get(sc, s, name, is_type)`). `declare`
finds `existing` in the table its kind belongs to, then:
- `lexical(a, b)` decides whether two kinds clash (let/const/class/import against anything,
  except TypeScript's merges: interface, namespace, type, import type).
- A type alias against a type alias, interface, class or enum is reported either way round.
- In TypeScript (`sc.ts`), an import and a declaration of the same name (in either table) are one
  symbol: `sc.mk[sym]` holds the second kind. no-unused-vars words it from both kinds.
- In JavaScript, an import followed by a function of the same name is reported twice (oxc does
  this).
- Merging interface+class, var+var, function overloads and namespaces returns the existing symbol.

## The oxlint parity loop

1. Make a probe folder with a few small files, one case each (`a.ts`, `b.js`, `c.vue`...).
2. `OXLINT=/path/to/oxlint ./oxprobe.sh --vlint NEW_BUILD DIR` prints only the differences,
   grouped by rule. Add `-- -A all -D rule` to look at one rule.
3. Read the oxc source for the rule or check (`crates/oxc_linter/src/rules/...`,
   `crates/oxc_semantic/src/checker/...`) before guessing at its conditions.
4. When it matches, keep the folder: `mkdir probes/NAME`, copy the files in, and run
   `./oxprobe.sh --save probes/NAME` (writes `.oxlint.txt`). `./oxprobe.sh --saved probes/*` then
   checks every probe without oxlint.

## Finding why vtsc differs from tsc

- `VTSC_ORDER=1`: the program's files in the order globals are merged (tsprog.tsc_order, tsc's
  --listFiles order: references, then imports, depth first; the types option's packages last).
- `VTSC_TRACE_REL=1`: where vtsc reports an assignability error, the failed relations under it,
  innermost first, each with the check that failed (`structural: property 'c' type`,
  `rel0: excess property 'nope' against an intersection`, `weak_fails: ...`). The labels come
  from `rfail` at each failing return in `rel.vu`. Off, it costs nothing.
- `VTSC_TRACE_REL=1 VTSC_ALL_REASONS=1`: where a relation of generic types isn't modeled (the
  file isn't checked), the relations being decided around it (`VSTACK`, outermost first), and for
  the first pair that prints the same but is two types, where they first differ (`TDIFF`: members,
  alias arguments, type arguments, mappers). Two copies of one type usually mean an instantiation
  tsc's caches make once: the copies are then compared structurally and reach what isn't modeled.
- `VLINT_VTSC_DEBUG=2` says `NOLINT f` for a file vtsc checked but whose type-aware rules
  didn't all run (a rule reached something not modeled, `unsup_here`): `VTSC_RULE_WHY=1` prints
  what (`RULEWHY f: ...`). Such a file reports no type-aware diagnostics, so every directive in it
  for a type-aware rule comes out as unused.
- `base_sig` (getBaseSignature, used when inferring from a generic signature, `Parameters<F>` of
  a generic F) keeps a constraint that names the signature's own type parameters (`E extends
  Ev<C>`) and resolves it through the others' constraints as tsc does; `VTSC_BASE_OWN=0` turns
  that back into unknown (what it was before; about 1% fewer instructions on one package).
- vlint's output must not depend on scheduling: the dynamic work queue (the default) hands
  files to whichever worker is free, so each worker's caches see a different order, and the
  per-statement instantiation budget or an alias's display name can differ between runs (one
  package measured from 43% to 52% with the same build). Measure with `VTSC_SHARD_STATIC=1
  VLINT_VTSC_CACHE=0`: identical output run to run.
- Warm runs: three caches. `--cache` (`.vlintcache`, lcache) is the plain lint's; the vtsc file
  cache (`$XDG_CACHE_HOME/vlint/vtsc-files`, one JSON a program, `tsprog.check_conf`) keeps each
  program's results, checked by the stat of every path its check read or looked for; the tsconfig
  cache (`vlint/tsconfig`, `tsprog.read_tsconfig`) keeps each tsconfig's read (its include walk)
  with what it asked the file system (`lprobe`: files read, paths looked for, folders listed),
  checked by stat (a folder's changes with its names) and not kept when a path changed in the
  2 s before the read. A program the file cache answers whole is answered in vlint's process
  (`check_conf` with jobs -1), not a worker's. `parity/exact.sh` edits a small project step by
  step and checks warm output against cold. `VLINT_VTSC_CACHE=0` turns the last two off,
  `VLINT_TSCONFIG_CACHE=0` the tsconfig one, `VLINT_TSCONFIG_DEBUG=1` says what it did.

## Function bodies checked deferred (chk.function_expr)

tsc checks function bodies after the types around them; vtsc imitates it for a function inside the
initializer of a variable whose type is being found (`defer_var`, `defer_var_outer`): its body
waits in `c.defer_bodies[var]` and `run_deferred` checks it once the variable (the outermost one
on `c.lazy_sym`) has its type (`deferred_body`: its errors go to `c.kept`, flushed at the end of
the file, so a dropped overload candidate around it can't lose them). A function whose return
type must be inferred from its body is inferred first with `c.spec > 0` (nothing reported, no
nested body checked; declarations outside it typed normally, their errors in `c.spec_keep`), and
`spec_reset` forgets what that pass found inside it before the real check. A destructuring
pattern whose initializer is being checked is in `c.pat_busy`: a sibling binding read meanwhile
is any without that being kept (`c.pat_circ`).

## Speed (a large JS monorepo, the corpus, measured 2026-11-22)

How to measure: `parity/bench.sh VLINT TAG [PKG] [ENV=...]` (cold; prints tree cpu, user + sys of every
process, and main-process instructions), two alternating A/B pairs per change, `cmp` of the .out files,
full `parity/tparity.sh` before committing. While the machine is loaded, compare cpu and
instructions, not wall. The deterministic figure is the serial type-aware run (`VLINT_PHASE=0
VLINT_VTSC_SERIAL=1 VTSC_JOBS=1`, main-process instructions, within 1%). Warm: `--cache` plus the
vtsc and tsconfig caches; `parity/exact.sh` checks warm output against cold edit after edit.

Where it stands: cold about 280 cpu-s and 32 s wall (from 317 cpu-s and 41 s), peak 3.7 GB (from
6). Warm 2.6 s, 7.6 cpu-s. The type-aware part is about 220 of the cold cpu-s, the plain lint about 63.

What paid (each byte-identical):
- the plan reads each tsconfig once (warm 4.7 -> 3.8 s); a tsconfig cache checked by stat (lprobe,
  tsprog.read_tsconfig); programs the file cache answers whole stay in vlint's process (warm -> 3.0 s)
- React Compiler: rc_imae's abstract state dense (clone_state had been 24% of the React Compiler),
  rc_sem only for files with a function to compile (plain lint main-process instructions -5.1%, -3.1%)
- the module graph's workers share kind_of's table, in 16 memos (plain lint cpu 67 -> 63 s)
- every program but the largest on one worker, each in a worker process (cpu 296 -> 284 s, peak
  6 -> 3 GB): splitting a program re-types the lib and its imports in each worker. In vlint's
  own process instead (VLINT_VTSC_SUB=0) it's 267 cpu-s, but 10.5 GB.
- the largest program's forked shards warmed with half its work (VTSC_WARM_PERMILLE 500): cpu -1.3%.

What didn't (measured, reverted; output identical every time):
- free lists in the Vu runtime: malloc, free, realloc, memmove and memset are 6% of busy samples. The
  sys time (about 50 s, 5.0M page reclaims) is memory each process touches for the first time:
  MallocXzoneEnabled=0, which keeps freed blocks, changed neither faults nor cpu
- a pool of long-lived worker processes keeping the texts and kind_of's table between programs: no
  cpu gain, wall worse. The in-process variant's gain comes from memos shared by all programs at once
- reserving the checker's lists (types, symbols, objects, mappers, signatures) by node count: page
  reclaims -5%, cpu unchanged; an Obj 288 bytes larger: +0.4% cpu. So `--profile`'s shares on push
  lines (new_obj 16%, parse.n 12% in a serial run) are an artifact of where the ticks land, and
  shrinking Node or Obj won't pay
- memoizing files' real paths (lcache.realpath_memo): no change; a folder-listing memo shared by a
  plan's tsconfigs: no change; a shared stat memo for check_conf: lost time to memo locks
- sharing the parsed and bound lib across programs: at most 7-8% of the serial type-aware time
  (lib and node_modules parsing is 5.7 of 115 s, bind 1.5 s). Sharing checker types for .d.ts files
  (about 15% of the types made) would change type ids, so union order and printed types: not done.

Profile (serial type-aware, 99 programs, 115 s): read and parse 13% (parse 6.7 s, of it lib and
node_modules 5.7 s), bind 1.3%, check 86%. Inclusive: chk.check_file 36%, call resolution
(chk.call, choose) 18-20%, bind.instantiate 13%, the type-aware rules 18%, of them
unsafe_enum_assignment's rt_enum 12% (already memoized across calls: the rest is typing each
property the first time, as tsgolint's rule does; pruning it changes which types are made). Self time
is spread: get_prop, new_mapper, rel.assignable, scope_names and declare_in are 1.5-2.5% each.
Counts over the 99 programs: 112M AST nodes, 12.1M types, 8.2M object types, 22M symbols, 8.3M
mappers, 2.6M signatures.

Profiling: `vu build --profile` (VU_PROF_OUT=prefix; a reservoir of 65,536 samples, stacks cut at 40
frames) gives honest Vu frames. macOS `sample` misattributes frames through deep recursion (rc_ssa).
For a run that sees every program in one process: `VLINT_VTSC_SUB=0 VTSC_FORK=0` (contended: page
faults on many threads inflate push lines); the serial run is cleaner. 5x cold (8.5 s) would need
the checker itself about 3x faster: about 200 cpu-s of checking without duplication is at least 20 s
wall on 10 cores.

## Speed linted a package at a time (a CI job's pattern, measured 2026-11-24)

A monorepo's CI lints each package in its own vlint process, two at a time, `--threads=4
--type-aware`, with the package's config (88 invocations). Reproduce it with a plan of the argv
lists and a runner that keeps two going (the session's scratch `job.py`); compare wall and the cpu
of every child (getrusage), and check that every output is unchanged.

What was wrong in 0.5.0 (99.5 s and 840 cpu-s, against oxlint 1.79's 74 s and 466 on 10 cores):
- a program alone in a package was checked in vlint's own process, which runs other threads, so it
  couldn't fork: its workers were threads that each read, parsed and bound the whole program
  again (a 211-file program: 29.8 cpu-s and 4.4 s on 8 workers, 11.6 cpu-s and 3.0 s on one)
- workers came from `/proc/cpuinfo`, every core of a CI node whatever the pod's quota
- forked shards were warmed with half the work first (VTSC_WARM_PERMILLE 500), serial when the
  program is the package's only one
- `/// <reference lib>` in @types/node made every program read and parse its files twice

Now (`lvtsc.run_jobs`, `shards_for`, `tsprog.cpu_count`, `lcache.cpu_budget`): a program gets a
worker per 200 files (VLINT_VTSC_SHARD_FILES), at most 8 and the budget (VLINT_CPUS, else the CPUs
the process may use: on Linux its affinity and cgroup quota); a program with more than one is
checked in a worker process that forks them cold after parsing; the programs take CPU tokens; the
types packages' lib references are read first; a single-worker program's files are read ahead by
four tasks. The job: 73.7 and 76.7 s, 453 and 449 cpu-s (oxlint 74.1 and 73.5 s, 470 and 462),
outputs identical; a package's largest process 2.7 GB where it was 13.3.

With 200 files a worker (the default since): 71.2 and 71.2 s, 478 and 475 cpu-s, against oxlint's
74.4 and 74.3 s alternated (4% under). Tried and not kept: a warm-up of 5-12% of the work (less cpu
on single packages, the job no faster: 74.4 and 72.8 s); 120 files a worker (74.5 and 72.6 s);
read-ahead as plain C threads so that forking programs get it too (their read+parse 2.0 -> 0.57 s on
one, but the job 73.9 and 76.3 s with 14 s more sys time).

Where the wall goes now: in 66 of the 88 invocations the type-aware check is the critical path (the
plain lint is done in a third of the time). In four mid-sized and large programs measured, the
files nothing lints take 4-12 ms of a check of 1.0-4.8 s; before the check, reading, resolving and
parsing 3,000-6,500 declaration files takes 0.45-0.7 s (parse 0.17-0.20 s, bind 0.03), the most a
cross-process cache of parsed declarations could save (about 13 s of the job's 71 if it went to
zero). On the job the plain lint costs 228 cpu-s against oxlint's 129 (the React Compiler is about
40% of a large package's; most of the rest the module graph no-barrel-file needs), the type-aware
part about 250 against tsgolint's 340. More shards barely help there
(each types the shared declarations again: a 79-file program reads 6,500 declaration files to check
its own). JavaScript plugins are where vlint wins (a plugin-heavy package 7-8 s against 14.7).
VLINT_VTSC_DEBUG=3 shows a worker's stderr; VTSC_PHASES times read+parse, bind, check per shard,
the worker, run_all and the fork.

Later the same day (the module record cache, lmod: `PkgC`, `parse_cached`, `save_cache`): the job
70.4-71.3 s and 451-455 cpu-s against oxlint's 74.8 (475 before it). What was measured on the way:
- the plain lint, package by package alone: 202 cpu-s against oxlint's 116. no-barrel-file makes
  the module graph follow all of node_modules (11,800 files, 32 MB for a 1,062-file package); the
  record cache leaves its resolution (stat and realpath calls, about 19% of a package's main-process
  cpu) and reading the cached records. The React Compiler is 40% of the largest package's
  main-process cpu (9.5 s; infer_mutation_aliasing_effects 17%, enter_ssa 5%), spread over passes
  with no single hot spot. A JavaScript plugin's own work (one runs React's compiler from
  eslint-plugin-react-hooks on Babel's tree) is most of the node processes' cpu, the same for
  both linters; vlint's host is 9% of it.
- the checker against tsgo on one 221-file program (tsgo 7.0.2, single-threaded, a scratch
  tsconfig extending the package's with noEmit): tsgo 791,000 instantiations and 1.22 s of check,
  vtsc 554,000 (cache hits counted) and 1.29 s. No missing cache: vtsc checks a file as fast as
  tsgo on one thread; tsgolint is faster by running four checkers over one parsed program.
- a cache of parsed declaration files (built, measured, not kept): entries made relocatable by
  parsing each file twice into trees whose node, list and name tables start at different offsets
  (a field that moves by an offset is that kind of reference), loaded by appending and interning the
  names in parse order. Outputs were identical cold and warm, but on a 79-file program with 5,268
  package declaration files the parse went from 170 ms to 155 ms warm (interning the names and
  relocating 2.1 million nodes cost about what parsing them does: the parser is already about
  180 MB/s), the cold run cost 2.6 s more (two parses each) and the cache took 124 MB for that one
  package. The code is kept in the session's scratch (dcache_attempt/), not in the repo.
- warming the resolver's stat answers in the read-ahead tasks (resolving each file's rough
  specifiers there): read+parse 470-485 ms -> 606-672 ms, the reads arriving later. Not kept.
- the measurement harness must give absolute paths for XDG_CACHE_HOME: one run from the linted
  folder with a relative one wrote its caches there.

## Checking one program on several workers (design notes, measured 2026-11-24)

tsgolint checks a program on several checkers over one parsed and bound program, the files split
between them: the parse and bind shared, each checker's type caches its own. vtsc's forked shards
are the same model, the parse and bind shared copy-on-write. What a shard spends re-typing what
the others type too (shard check times summed against one shard's, `VTSC_JOBS=1,2,4`):

| program | 1 shard | 2 shards: sum, slowest | 4 shards: sum, slowest | re-typed by each extra shard |
|---|---|---|---|---|
| 79 files | 1,102 ms | 1,965, 1,092 | 2,395, 1,025 | about 430 ms (40%) |
| 221 files | 1,217 | 1,821, 953 | 2,562, 713 | about 450 ms (37%) |
| 1,127 files | 4,621 | 6,699, 3,419 | 9,133, 2,726 | about 1,500 ms (33%) |

So a third or more of a shard's check is the lib's and packages' types the other shards type too.
Threads instead of forks (the same model) would save only the fork's copy-on-write faults, not
that. Sharing the type tables between threads isn't possible as the checker stands: every pass
mutates one checker state (`var c: C`: its type, symbol and relation tables, and the bound tree's
cached declared types), and Vu's tasks share only what a Memo or a channel carries, frozen. It
would take splitting the checker into frozen bound data and per-thread overlays over a shared,
deterministic type table: a redesign.

Tried within the forked model, outputs identical each time, none kept:
- declaring the program's own files once before forking (VTSC_PREDECLARE): 0-3 ms, the shards'
  check sums 2-8% lower, the slowest shard no faster: the shared work isn't the own files'
  declarations but the packages' types their bodies make.
- a warm-up of the files that import the most packages' modules (5-20% of the work) before forking:
  slower than forking cold (a 1,127-file program 3.6 s cold, 4.2-4.6 s warmed).
- the read-ahead as joined C threads where the shards fork, with 200 or 100 files a worker: the job
  76.9 and 73.3 s against 74.1 s without, within the run-to-run spread (about 3 s).

A shared type table (the redesign this would take), as scoped on 2026-11-24, not started:
- The state: `types.C` has 476 fields; 1,222 functions take `var c: C`; the type tables are read
  in about 8,000 places (`c.tk[` 2,800, `c.objs[` 1,721, `c.ta[` 1,299, `c.sigs[` 774), and
  binding's tables (`c.sdecl`, `c.sk`, `c.stype`, `c.sdtype`...) are written lazily during checking,
  so "frozen bound data" doesn't exist yet: binding finishes while checking.
- Vu's tasks share only frozen values (Memo, channels). A table several threads add types to
  would live in C (FFI): every one of those reads becomes an extern call, in the checker's
  hottest loops, unless the language gains shared, growable, lock-protected or append-only
  tables (a runtime and compiler change, with the gate).
- Determinism: union members are ordered by TypeScript 7's compareTypes (types.cmp_types: kind,
  value, declaration), with the type id as the last tie-break; an id given by whichever worker
  makes a type first would reach that tie-break, and every cache keyed by ids (relations,
  instantiations by mapper id) would differ run to run. Ids would have to be canonical (structural
  keys) or the tie-breaks removed, checked against tsgolint's text.
- The most it could save: the re-typing a shard does (33-40% of a shard's check, table above),
  so a mid-sized program's check on four workers from about 0.7-1.0 s to 0.3-0.4 s; read, resolve
  and parse (0.45-0.7 s a program) stay serial. Over the 66 invocations whose critical path is the
  type-aware check, that is perhaps 10-15 s of the job's 71-75 s: about the 20% asked for at best,
  for a rewrite of most of vtsc's checker.

The single-thread check, profiled (VLINT_PHASE=0 VLINT_VTSC_SERIAL=1 VTSC_JOBS=1, `vu build
--profile`, instructions from `/usr/bin/time -l`) on a 79-, a 221- and a 1,127-file program
(18.5, 16.8 and 55.1 G instructions): the self time is flat. The largest items are the push of a
new object type (types.new_obj, 5-9%), interning a mapper (types.new_mapper, 5-8%), reading files
(read_fsrc, 5-19%, the read-ahead tasks), the parser's node push (3-8%), bind.get_prop (4-5%),
rel.assignable (2-4%); nothing else reaches 3%. The work is tsc's own: per 221-file program
554,000 instantiations against tsgo's 791,000 (tsgo 7.0.2 on one thread checks it in 1.22 s, vtsc
in 1.29). Tried, not kept:
- one C file instead of the split build (VU_SPLIT=off; `--emit-c`): instructions within 0.5%
- profile-guided optimization (clang -fprofile-instr-generate on 12 of the job's invocations, then
  -fprofile-instr-use, through a CC wrapper): instructions -5 to -6%, cpu about -5%. Not in the
  release build: that is built per platform in CI (packaging/tools/build.sh), with a profile to
  train on each.

Scheduling and output: the six largest invocations, each run 10 times cold with the default
(dynamic) sharding, gave one output each.

The shared-type-table rewrite, milestones (started 2026-11-24; the old path stays the default):
- M1, bind first (measured; `VTSC_EAGER_BIND=1`, off by default): naming every file's scopes
  before checking (each module root, block and namespace body: bind.scope_names) takes 18-29 ms a
  program and makes 51,000-93,000 symbols where lazy naming had made 5,700-8,900 by then; outputs
  identical, check time within noise. But a program ends with 390,000-1,016,000 symbols: nearly
  all are made while checking, by type operations (instantiated and mapped properties, spreads,
  widening, object literals: get_prop, mapped_over1, spread_into, widen_*, about 40 call sites),
  not by binding. Those belong with the types, in the shared tables, not in a frozen bound part.
- M2, order independence (`VTSC_SHUFFLE=SEED`: the files visited, so checked, in a seeded random
  order that still has each file's imports first): the probes under seeds 1-5 and all 88 of the CI
  job's invocations under seeds 1-20 give output identical to the unshuffled run. Union members are
  ordered by TypeScript 7's compareTypes, and nothing printed turned out to depend on which file
  made a type first.
- M3, shared tables, measured so far: an append-only Int table in C, one reserved region (mmap,
  never moved, the length published with a release store), read from Vu through an extern
  function: 548-672 ms for 60 million dependent random reads against 598-681 ms for a Vu list
  (chunked, with an extra indirection: 693-720 ms). So the struct-of-arrays tables (`tk`, `tf`,
  `ta`, `tb`, `tl`, the symbols' `sk`, `sname`, `sdecl`, `stype`, `sdtype`, `sflags`) can move to
  C at no read cost. What can't as they are: `objs` and `sigs` are lists of structs with maps and
  lists inside, filled in place after they're made (about 250 sites: `objs[o].args`/`.eflags` 40
  each, `.sidx`/`.nidx`/`.resolved` 20 each, `sigs[s].tparams` 23, `.ret` 17 ...), and `stype` (61
  writes), `nsym` (32), `ntype` (22) are written lazily from everywhere. Each such fill would have to
  become compute-once (as a Memo is) and every checker function take a shared and a per-worker
  state instead of `var c: C` (1,222 functions). That is the rest of M3.
- M3 step 1, the flat tables in C (landed 2026-11-24, the only path now): `tk tf ta tb tl` and the
  symbols' `sk sname sdecl stype sdtype sflags sparent` are C columns (`ctab.h`: one reserved mmap
  region each, 2^28 entries, the length before the first entry, published with a release store),
  held as `types.Tab` handles `c.htk`... in `C`, with `c.ffi` beside them. Every use goes through
  `ct_at`/`ct_set`/`ct_push`/`ct_len` (`types.ct_at(c.ffi, c.htk, t)` for `c.tk[t]`); the sites were
  rewritten by a script (the session's scratch `m3w/conv.py FIELD...`: reads, writes and compound
  writes, `.len`, `.push`, `.reserve`; `m3w/hoist.py` moves a written value that changes `c` into a
  `let` first, 7 sites). The benchmark above was wrong for vlint: it was one small C file. In the
  split release build an extern call was a call to part 0 plus `omp_in_parallel()` (the par-loop
  check) and a stack protector: tk alone through it cost +23-35% instructions. Two compiler changes
  made it free: a glue file named `.h` is included in every part and its wrappers are `static
  inline` (always_inline), and the par-loop check asks OpenMP only while a par loop runs
  (`vu_par_live`, counted around each one), once per function (`VU_FFI_ENTRY`), not per call. With
  both, all twelve columns: 79 files 18.48 -> 18.86-18.93 G instructions (+2.1-2.4%), 221 files
  16.77 -> 17.21-17.44 (+2.6-4.0%), 1,127 files 55.20 -> 56.45 (+2.3%) (no par check at all would be
  +0.4%: the rest is the check at each function's start, which makes small leaf functions keep a
  frame). Probes 133/133, vtest the same 3 failures, the CI job's 88 outputs byte-identical.
- M3 step 2a, signatures as columns (landed 2026-11-24): `Sig`'s Int fields (`ret min node this_t
  pred_i pred_t`) are ctab columns `c.hs_*`; its lists (`tparams pnames ptypes pflags`) are list
  columns (`types.Lst`, `cl_*` in ctab.h: each row an (offset, length) into an append-only pool of
  Ints; a row is changed by writing its list again at the pool's end, or by appending when it ends
  the pool already, so an entry once written never moves or changes under another row). A list read
  whole is a copy (`types.cl_ints`); `types.Sig` stays as a value (`sig_copy`, changed, then
  `sig_push`/`sig_put`). Rewritten by the session's scratch `m3s/sconv.py DIR TABLE HPFX SCALARS LISTS
  [BOOLS]` (reads, writes, a list's `[i]`, `.len`, `.push`, `.pop`, `= list`, `ints(...)`,
  `has_int(...)`) and `m3s/hoist2.py` (a write whose value changes `c`, 7 sites). With it, the
  par-loop check made free (vu: `ffi_reach`, the functions no par loop can reach get `VU_FFI_OFF`; all
  1,009 of vlint's functions that call C): 79 files 18.62 G instructions, 221 files 16.90, 1,127 files
  55.19 (+0.8, +0.8, 0.0% on the pre-M3 base; 18.85, 17.24, 56.40 at step 1). Probes 133/133, vtest
  the same 3 failures byte for byte, the CI job's 88 outputs byte-identical.
- M3 step 2b, object types as columns (landed 2026-11-24): `Obj`'s Int and Bool fields (`kind sym
  node sidx nidx target mapper display sname nname mcons`, `resolved fresh ro`: a Bool is 0/1,
  written through `types.b2i`, read as `!= 0`) are ctab columns `c.ho_*`, its lists (`calls ctors
  tparams args eflags`) list columns; `c.objs` keeps only `props` (a map, iterated in insertion order
  in bind.vu's class/function merging) and `order` (`sconv.py . objs ho_ SCALARS LISTS BOOLS`, then
  `hoist2.py`, 52 sites). A side effect of the scripts: code quoted inside a few `rfail` trace
  messages (rel.vu, shown only with relation tracing) was rewritten with the code. 79 files 18.61 G
  instructions, 221 files 16.85, 1,127 files 55.11 (+0.7, +0.5, -0.2% on the pre-M3 base). Probes
  133/133, vtest the same 3 failures byte for byte, the CI job's 88 outputs byte-identical.
- Next (M3 step 2c): `props`/`order` in C (a list column of names and one of symbols in the same
  order, plus a lookup by (object, name): an open-addressed table in C, append-only, keyed by both),
  keeping iteration in insertion order. Then the compute-once slots: today a column entry is written
  in place (`ct_set`, `cl_set`/`cl_add` on a row); once rows are shared, a row is filled by one
  thread before its index is published (a new object or signature), and the lazily filled fields
  (`resolved` with `calls ctors sidx nidx sname nname`, `args`/`eflags` of a deferred tuple or
  reference, `sigs.ret`, `tparams`) need a set-once protocol (a state word per row: empty, being
  filled by worker N, filled; a second filler waits or computes the same value).
- Step 3 measured, not started (2026-11-24): how often a lazy write replaces a different value, over
  vtests' 834 cases (each write counted by a throwaway instrumentation, the session's scratch
  `m3s/soinst.py`): `stype` never goes from one type to another; it goes back to -1/-2 28 times in 12
  cases (circular and deferred inferred returns, `this` literals), so it is set-once but for those
  resets. `nsym` is rewritten 1,231 times, nearly all (1,206) in bind.vu's interface merging across
  namespace blocks (`types.add_decl(&c, prev, d)`: a declaration moved to the symbol it merges
  into), 25 per case that loads the lib: binding-time, so set-once once merging runs before checking
  (M1's eager binding). `ntype` is rewritten 2,041 times, 1,882 at check_expr's own write
  (`c.ntype[n] = t`): an expression checked again under another context gets another type (and
  `nt_log` already rolls some back). So `ntype` isn't a compute-once cache but the last check's
  answer: making it shared needs the speculative checks (a context, an inference pass) to write a
  per-worker overlay and only the final check to write the shared slot. That, the resets of
  `stype`, and the namespace merge's `nsym` are what step 3 has to settle before a set-once slot with
  a debug check can replace those writes.
- Step 3, decided (2026-11-24), next to do in this order, each landing with the same gates (probes
  133/133, vtest's 3 failures byte for byte, the 88 cold invocations byte-identical, ins.sh within
  about 5% of the pre-M3 base: now 18.61 / 16.85 / 55.11 G):
  1. `ntype` is per-worker state, as tsgo keeps node links per checker: it stays a Vu map in the
     per-worker part, with every other context-dependent per-node cache (flow and narrowing caches,
     `resolved_sig`/`call_sig` and the like). Nothing to convert now; it decides which side of the
     step 4 split those fields go.
  2. `nsym`: finish interface and namespace merging in bind before checking starts (where
     `VTSC_EAGER_BIND`'s `scope_names` pass runs: the merge in bind.vu that calls
     `types.add_decl(&c, prev, d)` across namespace blocks, 1,206 of the 1,231 rewrites), then make
     `nsym` set-once and shared. Check it with a set-once assertion in a debug build over vtests and
     the probes (`m3s/soinst.py` in the session's scratch shows how to count the rewrites by site).
  3. `stype`: the -1/-2 values are in-progress markers (circular and deferred returns): keep them in
     a per-worker map, and publish only the final type to the shared column, once, with a
     compare-and-swap in ctab.h (a `ct_publish`: CAS from "unset" to the value; a second publish must
     give the same value, asserted in debug builds). The 61 writes of `hstype` are the sites.
  4. `props`/`order` to C: a per-object property list in insertion order (names and symbols, list
     columns) with a lookup by name (a per-object open-addressed index, or what measures best);
     iteration must stay exactly insertion order (bind.vu's class/function merging iterates it).
- Step 3.2, `nsym` set once (landed 2026-11-24): every write goes through `types.nsym_put`, and
  `VTSC_SO_CHECK=1` panics when one changes a declaration's symbol after checking starts, except a
  move by the `scope_names` call that has just declared it (`c.naming`, `c.so_fresh`: the interface
  and namespace merges, whose old value nothing has read). So the merges are part of binding a scope,
  wherever it's bound. The one change while checking it found (vtests' global-this-ns): a `namespace
  globalThis` in `declare global`, its members declared as globals by declare_global, then given
  symbols of their own when check_stmt named its body; its body is now named as a global block's is
  (`bind.global_this_body`). With the check on: vtests the same 3 failures byte for byte, probes
  133/133, the CI job's 88 outputs byte-identical, no panic; 18.64 / 16.85 / 55.18 G instructions
  (+0.9, +0.5, 0.0% on the pre-M3 base). For M4, binding must still be finished before the threads
  start (VTSC_EAGER_BIND's pass), or two workers naming one scope would make two symbols for it.
- Step 3.3, `stype` set once (landed 2026-11-24): the column holds only final types, each
  published once by `ct_publish` (ctab.h: a compare-and-swap from -1; it returns what was there).
  What isn't final is the worker's own, in `c.st_tmp` (read first by `types.sty`, the only reader of
  the column): the in-progress marker -2, the resets to -1 (types made while an alias is made,
  `cyc_taint`; a deferred function's speculative declarations, `spec_reset`; a pattern's circular
  binding, `pat_circ`), the early types set over a -2 (`as_early`, `fn_var_hook`), and any type made
  while `c.spec > 0` or an alias is being made (`c.alias_busy`), since those are what the resets undo.
  Writes: `sty_init` (a new symbol's type: published), `sty_put` (a lazily made one: published unless
  it may be made again), `sty_tmp`. VTSC_SO_CHECK=1 panics when a published type would change or be
  reset. Its first run found republishing of the same type inside a speculative check (now allowed);
  after that, with the check on: vtests the same 3 failures byte for byte, probes 133/133, the CI
  job's 88 outputs byte-identical with no panic (and again with the check off). 18.59 / 16.90 /
  55.73 G instructions (+0.6, +0.8, +1.0% on the pre-M3 base): the markers are map entries now.
- Step 3.4, properties in C (landed 2026-11-24): `types.Obj` and `c.objs` are gone. An object's
  property names in insertion order are a list column (`c.ho_order`, one row per object: `new_obj`
  takes its index from `cl_row`), and each property's symbol is found by (object, name) in one
  open-addressed table for all objects (`c.hph`, ctab.h `ph_get`/`ph_put`: key object << 32 | name,
  linear probing, doubled at half full). `add_prop` appends the name only when `ph_put` says it's
  new, so the order is the old map's insertion order exactly; `sort_props` writes the row again; the
  merges that iterated the map (bind.vu's function and class merged with a namespace) read the row,
  then sort as before. Rewritten by the session's scratch `m4/pconv.py`. Probes 133/133, vtests the
  same 3 failures byte for byte, the CI job's 88 outputs byte-identical; 18.51 / 16.50 / 54.73 G
  instructions (+0.2, -1.6, -0.9% on the pre-M3 base: no map and list allocated per object). Not
  yet safe for threads: `ph_grow` moves the slots, so M4 needs a resize readers can't see torn (a
  new table published by pointer, the old one kept until no reader can hold it) or one reserved
  region sized from the program; and a row's `cl_add` must happen before the object is published.
- Then step 4: `var c: C` split into the shared tables and a per-worker state, and M4: N checker
  threads over the shared tables behind a switch, off by default. M4's gates: 1, 2, 4 and 8 threads,
  20 runs each, byte-identical on the 88 invocations and the probes; TSan with CC=clang and Archer as
  tests/run_mt.sh runs it (a TSan run that fails to start is a failure); the cold job.py table, two
  runs alternated with oxlint 1.79, the switch on and off.

With the caches kept between runs (`$XDG_CACHE_HOME/vlint`: the vtsc file cache, the tsconfig
cache, the module records; 261 MB for the job), the CI job's pattern takes 33.9 s and 214 cpu-s
against oxlint's 74-76 s, outputs identical; the run that fills them 81.6 s.

## Keeping the caches in CI

What a CI job can keep between runs is one folder: `$XDG_CACHE_HOME/vlint` (`~/.cache/vlint`
without XDG_CACHE_HOME). In it:
- `vtsc-files/`: each program's type-aware results, used again for a file while every path its
  check read or looked for has the same state (tsprog.check_conf); a program with a few changed
  files is checked on one worker, the rest of its results read
- `tsconfig/`: each tsconfig's reading, with what it asked the file system (lprobe)
- `modrec-BUILD/`: dependencies' module records (lmod)
- `tslib-HASH/`, `host-HASH.mjs`, `node-compile-cache/`: the TypeScript lib vlint carries, its
  JavaScript plugin host and node's compiled copy of it (all keyed by their content)

BUILD, and the build part of the other keys, is VLINT_BUILD_ID: a hash of vlint's executable bytes,
set by vlint for itself and its worker processes. A job that installs vlint afresh each run gets a
new file (new times and inode) with the same bytes, and its caches still apply; another vlint
gets new keys, its old entries unused. (Before, the keys were the executable's times and inode:
a reinstall missed every entry.) So a CI cache key needs no vlint version for correctness;
`vlint-<version>-<lockfile hash>` with `vlint-<version>-` as the fallback prefix keeps old builds'
entries from piling up. VLINT_VTSC_CACHE=0, VLINT_TSCONFIG_CACHE=0 and VLINT_MODREC_CACHE=0 turn
the parts off.

Size: 282 MB after the 88 invocations of the CI job's pattern (vtsc-files most of it). Nothing
prunes old entries: start from an empty cache when the key's version changes.

Measured on a scratch copy of the monorepo (the job's pattern, two at a time, `--threads=4`),
starting from the cache a full run left, vlint reinstalled (copied to a new file) before the
measured run:

| change | vlint, cache warm | vlint, cold | oxlint 1.79 | warm against cold, every output |
|---|---|---|---|---|
| none | 33.9 s, 214 cpu-s | 71-74 s | 74-76 s | identical |
| 1 file, 1 package | 35.1 s, 221 cpu-s | 75.2 s | 77.6 s | identical |
| 10 files, 3 packages | 36.8 s, 226 cpu-s | 76.3 s | 79.1 s | identical |
| 50 files, 10 packages (one module of a shared package imported in 29 places) | 47.2 s, 284 cpu-s | 76.5 s | 79.1 s | identical |
The run that fills an empty cache: 78.8-81.6 s.

## Checks before committing

- vtsc: `VTSC_LIB=.../typescript/lib ./vtest.sh NEW_BUILD` (the cases in `vtests/`); a slow run:
  `VTSC_FILE_TIME=1` prints each file's check time (2: also before each), `VTSC_DEBUG=1` each
  generic call's inferences. Against tsc on a real project: the session's scratch `cmpts.py DIR`
  (vtsc and tsc 6 with the folder's tsconfig; the errors only one reports, in the files vtsc
  checks; `-r` the reasons files aren't checked).
- `./oxprobe.sh --saved probes/*`: every probe still matches.
- vlint's regression scripts against saved oxlint output (the session's scratch `prof/vreg.sh`;
  it covers lc, editor-ui, n8n, vitest, tldraw, AFFiNE and oxc's own rule test cases).
- A parser change: vtsc's corpus regression (`prof/regress.sh`; it also covers vknip).
- On real repositories: run oxlint and vlint with `-f json` and compare diagnostic by diagnostic
  (README's tables). Wall time: best of 3.

## Vu habits that save a build

- Slices: `s[a..b]` (there's no `.slice`).
- A struct with many fields: give the fields defaults (`ts: Bool = false`) and construct with
  named arguments (`Scopes(ts: true)`), so adding a field doesn't mean editing every call.
- `let x = s.field` of a list or struct freezes `s`: copy what you need first.
