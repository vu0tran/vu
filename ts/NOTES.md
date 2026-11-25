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

## The plain lint on the CI job's pattern (measured 2026-11-24, later)

Measured with the plain-only job (the 88 invocations with VLINT_TYPE_AWARE=0) and a `node` wrapper
on PATH that logs each node process's cpu (the session's scratch `m6/pj.sh`); oxlint's plain cost is
its job's cpu less tsgolint's (an OXLINT_TSGOLINT_PATH wrapper logging tsgolint's own). Before:
vlint 240-241 cpu-s (41 s), of it node 130 cpu-s in 341 processes and vlint's own processes about
111; oxlint about 147 cpu-s (its JS plugins run in its own node process).

Where vlint's own cpu goes, by VLINT_PHASE (0 startup, 1 read + parse + the module graph, 2 + scopes,
9 everything), vlint's process alone: the largest package (12,400 files) 0.9 / 3.6 / 3.7 / 22.0 s, so
the rules are 18 s (1.5 ms a file); a 1,100-file package 0.2 / 1.4 / 1.5 / 3.6; the plugin-heavy one
(eslint-plugin-react-hooks as a JS plugin) 0.2 / 1.5 / 1.5 / 4.1 with node at 30.8 cpu-s.
`--profile` puts the React Compiler at about 60% of the rules' samples on the largest package.
Beware `--profile` on macOS: SIGPROF goes to any thread, so a thread blocked in ljs.call gets about a
quarter of the samples, and the samples on stat calls (lresolve's `closure`, realpath_memo) overstate
them: answering 34,000 of a package's 34,400 kind_of questions from folder listings shared by the
process (C, no stat) changed neither instructions nor cpu, and integer keys for rc_imae's cached_vid
(string formatting was 4% of the RC samples) took 0.4% off the instructions. Measure by ablation and
instructions, not by profile shares.

What oxlint does: its JS plugins run in its one node process (the plugin and host load once, the
AST read lazily from a raw buffer); vlint ran one node process per two cores whatever the package,
each costing about 0.2 cpu-s to start (node, the 26,000-line host from the compile cache, the plugin's
.mts stripped by amaro): 341 starts, about 70 cpu-s, most of them for packages of a few dozen files.
A JS lint request on a light plugin is mostly vlint's own transfer: on the largest package the main
JS threads were busy 6.2 s, of which the plugin's rules 0.28 s, JSON.parse of the request about
0.8 s, and building the ESTree and setting parents most of the rest. oxlint 1.79's `--debug=timings`
printed nothing on these invocations (exit 0), so its per-rule costs weren't measured.

What landed:
- node processes as the work needs them (ljs_glue.c: vl_node_expect, vl_pick): told how many lint
  requests the run sends, calls go to the least loaded of the processes in use, and once 16 answers
  have come another is added only when the requests left, at the time the answers so far took, are
  more than 1.0 s for each process in use. Small packages keep one process; the largest still get
  four within the first few hundred files. 341 -> 134 processes, node 130 -> 96 cpu-s. (With 0.5 s
  and 4 answers: 170 processes, the plain job 190 cpu-s.)
- no-barrel-file's module graph scoped to what it counts (lmod: fullv, nb_seeds, mark_full): a
  dependency is followed whole only when it is reachable from what a linted file re-exports whole
  (`export * from`, `export * as ns from`, an exported namespace import); every other dependency
  only through its re-exports, as with the rule off (no-cycle doesn't go through node_modules). The
  counts are the same; most packages have no such file (the job reports two barrel files).
Together: the plain-only job 180.9 and 181.7 cpu-s, 33.2 and 34.1 s (from 240.3 and 241.1, 41.0
and 40.0; oxlint 146.4 and 148.7 cpu-s); the full cold job 74.8 and 74.8 s, 451.5 and 449.0 cpu-s
(before 78.4 and 79.1 s, 501 and 497; oxlint, alternated, 74.6 and 73.9 s, 473 and 468), every
output identical. So the plain lint is down a quarter, not the half aimed at; the job's wall is
the type-aware part's.
The plain numbers include the node wrapper (a python process per node process).

What's left, by size (job-wide, vlint's own about 85 cpu-s, node about 96):
- node: about 27 cpu-s of the 96 is still process starts (134; 88 is the floor with one each); the rest is per-file work, on light
  plugins mostly the transfer (JSON.parse, buildEstree, setParents). A binary transfer read lazily,
  as oxlint's raw transfer, would cut most of it. A plugin that runs React's compiler itself is
  heavy in both linters; four processes warm its JIT four times.
- the React Compiler: about 60% of the rules' cpu on large packages, spread over passes
  (infer_mutation_aliasing_effects about 37% of it: apply_effect, compute_signature, clone_state;
  enter_ssa 9%; lowering 9%; rc_shapes.base, the registry built again for every file, 7%: one built
  once and shared read-only, with each file's additions in an overlay, is the next small step).
  Done since: see "vlint's own process on the largest plain invocation" below.
- the module graph: 1.2-2.7 s of read, parse and resolve per large package even with the record
  cache; dependencies' re-exports are what import/named and friends need.

## The node processes on the CI job's pattern (measured 2026-11-25)

Which JS plugins run: every invocation has the monorepo's own local plugin (a `.mts` of about 30
rules on CallExpression, MemberExpression, JSX and import nodes; company-specific, so it can't be
ported into this repo), four packages add eslint-plugin-react-hooks' compiler rules, two add
eslint-plugin-n and eslint-plugin-jsx-a11y. Node cpu by invocation (a `node` wrapper logging each
process's cpu and the invocation): the react-hooks packages are about half (the largest 32 cpu-s in
4 processes, three more 3-8 each), the other 83 invocations the rest at 0.1-8 each.

Where it goes (`node --cpu-prof` on every process of the plain job, main threads only, 71 s
sampled of 98 by rusage; the rest is V8's GC and compiler threads): process start-up to the first
lint request about 110 ms a process (node's own internal modules compiled, 33 ms; the host module;
ajv's meta schema, 13 ms, mostly uri-js's IPv6 regex), 14.6 s over 133 processes; building the
ESTree 13.0 s; the plugin's work (React's compiler and Babel, 17.7 s; the local plugin 3 s);
oxlint's walker and context 9.7 s; JSON.parse of the requests 3.2 s; GC 4.7 s.

Not portable to Vu with identical output: eslint-plugin-react-hooks 7.1.1's compiler rules. vlint's
native React Compiler (rc_*.vu) is oxc's port of a later compiler, and they disagree on this very
monorepo: the native react(purity) reports `new Date()` in render at six places in one package
where react-hooks-js/purity (on as an error) reports nothing. The JS rules also print Babel code
frames with absolute paths. Its cost is the plugin's own: one package's 1,430 files take 21.1
cpu-s in one process and 29.0 in four (the JIT warmed four times), against 6.8 s of wall instead of
about 25. No V8 flag tried changed that by more than 4% (semi-space 32/64 MB, single-threaded GC,
pool size 0/1; the pool is already 1 on the job). The plugin skips files with no top-level
component or hook itself (`mayContainReactCode`), so skipping node for them saves nothing while the
local plugin needs every file.

What landed:
- estree.js's node literals made with constructors (gen_host.py `with_ctors`, at host generation):
  V8 builds `{ __proto__: NodeProto, ... }` about 8.5 times slower than `new Nd(...)` with the same
  prototype and keys in the same order (100,000 Identifiers: 1,170 ms against 137), and reads
  them about 1.8 times slower. buildEstree on 13,863 captured requests 2,353 -> 882 ms; the trees
  dumped (keys in order, values, prototypes, property attributes, parent links) identical. oxlint's
  own deserializer makes its nodes the same slow way.
- lint requests as frames (ljs.lint_frame, ljs_glue.c vl_send, main.js): the JSON line without the
  text and the node and list arrays, then those as bytes (int32 arrays read in place by estree.js;
  the text's bytes given as they are when they're valid UTF-8). No readline: fd 3 is split by hand,
  a frame's bytes copied into a fresh aligned buffer. vlint no longer formats 64 million numbers
  per 14,000 files, node no longer parses them. A number that doesn't fit an int32 falls back to the
  JSON request. Checked: the trees from typed arrays dump identical on 8,220 requests; a scratch
  plugin reporting every Identifier's span, parent and loc, every Literal and the token and comment
  counts gives the same 80,090 lines with the old and new build on a BOM file, a .vue section,
  invalid UTF-8, U+2028, an emoji, an empty file and a 20,000-line file.
- `gen_host.py --from-lhost` regenerates the host from the current lhost.vu (oxlint 1.90's dist
  isn't needed to change jsplug/).

Measured: with the constructors alone, one plain-only job on a quiet machine: node 97.8 -> 91.8
cpu-s, the job 183.4 -> 177.5 cpu-s (one run each, outputs identical); the profiled ESTree share
13.0 -> 7.6 s. With frames too, the job wasn't measured: the machine then had a load average of
15-27 from other work and a 99%-full disk, every job's cpu was about doubled (oxlint's plain job
971 cpu-s, its usual 476) and invocations of the old build, the new one and oxlint alike stalled
for 4-50 minutes with their processes idle (not reproduced alone in 30 runs of one invocation). So
the frames' saving is measured only offline: JSON.parse was 0.8 of the 3.2 s (JSON.parse + build)
on 13,863 requests, and 3.2 s of the 71 sampled job-wide. Measure it again on a quiet machine.

What's left in node: start-up (about 0.1 cpu-s a process, 0.05 of it node's own; a user-land V8
snapshot of the host could save part of the rest, but the plugins are ESM loaded with import());
oxlint's walker (9.7 s sampled); the ajv meta schema at start (13 ms a process: uri-js's IPv6
regex on hosts without a colon, a guard would skip it); setParents (a fifth of the remaining build).

## vlint's own process on the largest plain invocation (measured 2026-11-25)

How it was measured (the machine had a load average of 10-30 and every wall and cpu time was off):
instructions retired of vlint's process alone. `/usr/bin/time -l`'s count is the process's own, not
its children's (`sh -c 'python3 -c ...; true'` reports 24 M against the child's 7.0 G), so the node
processes don't count, and one.py execs vlint in its place. To isolate the React Compiler, the same
invocation (the largest package, 12,400 files) with a config that turns on only its rules: 139.8 G,
of which read, parse and scopes 9.7 G (VLINT_PHASE=2), so the compiler was about 130 G. The plain
invocation itself was 192.3 G: VLINT_PHASE 0 / 1 / 2 / 9 = 6.4 / 28.3 / 29.1 / 149.4 G after the
changes below (phases 0-2 don't change with them). The run-to-run noise is about 0.3 G.

Profiles: `vu --profile` puts 21-25% of the samples on lint_one's `fs.read` line and 20% on
ljs.call; both are threads blocked (VLINT_PHASE=0, which reads every file, is 4.8 G). macOS's
`/usr/bin/sample PID 2 -file OUT` on the running process shows the C level the Vu profile hides:
of the busy samples in the compiler, malloc, free and realloc about 25%, memmove/memset 8-12%,
hash-map operations 12-14% (`vu_mget_M3_IntS_rc_hir__BasicBlock` alone 4%: every pass looks up
`f.body.blocks[bid]` in a map). Scripts in the session's scratch `m8/` (samp.py: a sample's
allocation samples charged to the Vu function that called; incl.py: inclusive samples).

What landed (the compiler-only invocation, G instructions, cumulative; every output identical):
| change | G |
|---|---|
| before | 139.8 |
| rc_shapes: the built-in shapes and globals built once per process (`shared_base`, a Shared `Base` in `rules.Cx.rcb`); a file's Registry holds only the module types it adds, looked up first | 137.0 |
| rc_imae: an identifier's one value read without making a list (kind_sp, merge_vars, define, assign, freeze); the never-read `initialized` set no longer written; rc_ssa: definitions in one map keyed `block << 32 \| id`, the predecessors not copied on every lookup | 100.3 |
| rc_imae: the state indexed by `local_order` (the identifiers the function names first, a gap for the ones the pass makes, the rest after) instead of by identifier: an inner function's state was as long as the file's identifiers (one package: 27,620 calls, 179,000 clones copying 570 M ints); rmore10's rule list built once per setup | 94.5 |
| rc_build.is_always_reserved: a length and first-letter test before the 36 comparisons; rc_imae: phis and freezes of one value without lists, local_order's list made by repetition | 92.4 |
| rc_imar: the nodes in a list with an identifier -> index map (mutate looked a node up a dozen times a visit); rc_lower: a nested function's builder is lent the parent's bindings and names instead of copying them in and back | 89.6 |
| rc_vref: the checks and lookup read the environment in place instead of through a copied one-element list; shapes compared without copying | 87.1 |
| rmore10: comments, module kind and the source copy only for files with a function to compile | 86.7 |

The plain invocations, vlint's own process, before -> after (G; the build before rmore10's
change): the largest package 192.3 -> 142.9; the next three by the job's time 31.8 -> 27.2, 20.6 -> 20.2 and 29.0 -> 28.1 (outputs
identical to the old build's).

Reverted (within the noise): eliminate_redundant_phi skipping rewrites while nothing is mapped
(0.16 G), imae's signature cache as a list plus `reserve` on its output (0.15 G).

What's left, by size:
- allocation: lists grow with malloc/realloc and every `[x]` or `[]`-returned option, every
  `value_operands` list and every copied AliasingEffect (224 bytes, pushed again each time a block
  is re-applied) is a malloc. Short strings already have per-thread free lists in the runtime; the
  same for small list buffers would be a runtime change for the whole language (every free of a
  list's data goes through generated drops), not tried here.
- the HIR's blocks are a map `{Int: BasicBlock}`; block ids are the file's (shared by nested
  functions), so a list by id would be sparse; a per-function index would touch every pass.
- the module graph: 18,377 records on the largest package (12,428 of them the linted files, parsed
  again for their records; 4,023 in node_modules), about 18 G of the 28 G of phase 1, mostly
  open/read/stat (`sample` shows the graph workers in `__open_nocancel`, `read` and `stat`).
- the React Compiler is still about 77 G of the largest package's 143 G.

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
- Step 4, scoped (2026-11-24, not started; what the split has to settle, in order):
  - How tasks reach the shared tables (tried in the session's scratch `m4/share/`): Vu tasks may
    call C (only par loops may not), and `Ffi` passes to a task. A handle can't be shared, but the
    owner can pass the table's address as an Int and each task make a view of it (an extern type
    whose drop does nothing); four tasks appending by fetch-add and reading back ran clean under
    TSan (CC=clang `vu build --tsan`, three runs; Archer isn't installed on this Mac, and is only
    needed for par loops). So in `C`, every `Tab`/`Lst`/`Ph` field becomes a view, and the owners
    live in a struct the main task keeps until every worker is done. Appends from several workers
    need a row index taken once per table (one fetch-add for `tk tf ta tb tl` together, the row
    written, then published), not one `ct_push` per column.
  - What `C`'s 506 fields are (a regex count over the checker's files: reads and writes of `c.F`,
    the session's scratch `m4/fields.tsv`): 43 are C tables already. Of the rest, about 220 are
    written once or never after setup (the intrinsic types `any_t`..., options, switches): plain
    copies in each worker. The AST, `c.t` (7,878 reads), is written while checking: 86 `ast.intern`
    calls (58 with a constant string, which can be interned at setup), the JSX elements' object
    literal nodes (`chk.jsx_obj`, new nodes per element) and one node changed and restored
    (bind.vu, `c.t.nd[n].b = -1`). Binding's maps (`locals`, `ltypes`, `nsym`, `smore`, `merged_ns`,
    `parent`, `globals`, `gtypes`) are filled lazily. Both need to be finished before the workers
    start (VTSC_EAGER_BIND's pass, the constant names, the JSX nodes made in bind) and then shared
    read-only: a `Shared[...]` can't hold a handle, so the tree goes into it on its own, or into C
    columns as the types did. The interning maps that make types (`unions`, `strlits`, `numlits`,
    `biglits`, `nums`, `tmpls`/`tmpl_ids`, `mappers`/`mapper_ids`, `intern_tbl`/`intern_at`,
    `t_alias`/`t_alias_args`, `t_origin`, `tl_cache`, `alias_inst`, `inst_icache`/`inst_acache`,
    `enum_type`/`enum_union`, `tuple_labels`) must be one table for all workers, in C, with a
    find-or-add that two workers can't both win, or two equal types get two ids. The names table
    (`c.t.names`) too, since a string literal type is its name's id. Everything else (about 200:
    `ntype`, narrowing, contexts, the relation and inference caches, diagnostics) is per worker.
  - Determinism with several workers: ids then depend on which worker makes a type first. M2
    showed nothing printed depends on the file order, but not on interleaving inside one file's
    check; the gates (1, 2, 4, 8 workers, 20 runs each, byte-identical) are what decides it.
- Step 4.1, views and table groups (landed 2026-11-24): every table is made through one owner,
  `types.Store` (ctab.h `cs_new`; tsprog keeps it, `tabs`, beside the checker until the checker is
  done), and what `C` holds are views: `Tab`, `Lst`, `Ph` and `Grp` whose drop does nothing, each
  made again in another task from its address as an Int (`ct_addr`/`ct_view`, `cl_`, `ph_`,
  `cg_`). The columns come in groups that share one row counter (`c.gt`: `tk tf ta tb`; `c.go`: the
  object columns; `c.gs`: the signatures'; `c.gy`: the symbols'): a row is taken once with a
  fetch-add (`cg_row`), its entries written with `ct_put` / `cl_init` (each raises its column's
  length to cover the row, a compare-and-swap max, so bounds checks still hold), and only then is
  the index handed on. `tl` takes a union's or intersection's members as one run (`ct_run`: one
  fetch-add for the run). What isn't thread-safe yet: a list column's pool (`cl_add`/`cl_set`
  append without a reservation), `ph_put`/`ph_grow`, and the `ct_len(c.ffi, c.hs_node)` and
  `ct_len(c.ffi, c.htk)` watermarks in chk.vu and tyops.vu ("the signatures made since"), which
  another worker's rows would break. Probes 133/133, vtests the same 3 failures byte for byte, the
  CI job's 88 outputs byte-identical; 18.55 / 16.54 / 54.64 G instructions (+0.4, -1.4, -1.0% on
  the pre-M3 base).
- Step 4.2, binding finished and the tree frozen before checking (landed 2026-11-24):
  - VTSC_EAGER_BIND's pass is the path (`VTSC_EAGER_BIND=0` names scopes lazily, as before) and
    names every kind of scope `scope_names` knows (`bind.scope_kind`: blocks, case clauses,
    function-likes' parameters, for / for-in heads, catch bindings, class expressions), not just
    blocks and module bodies: over vtests, the lazy path had named 5,771 scopes after checking
    started (3,028 lib methods' parameter scopes, 1,482 functions', 707 arrows'...). With
    VTSC_SO_CHECK=1, naming a scope after checking starts panics, except one case left: the root of
    a file that isn't a module, named when something imports it (`root_exports`; job invocation 76
    met it once, @types/node's test.d.ts). Naming every script's root eagerly is wrong (its
    declarations get local symbols instead of the globals': tried, 86 vtests failed, Symbol.iterator
    lost), and so is computing every file's exports eagerly (the same). What it needs: the files an
    import resolves to, known before checking, and only those roots named.
  - Each JSX element's object literal (chk.jsx_obj) is made in that pass, so no node is added while
    checking (VTSC_SO_CHECK=1 panics if the tree grew, and if jsx_obj makes one late).
  - bind.vu's change-and-restore of a `typeof a.b<T>` node is gone (`bind.tquery_flow` reads the
    query without its type arguments).
  - The names the checker asks for by a constant text are interned when the checker is made
    (`c.kn[types.KN_...]`, 27 names, 46 sites); the rest (49 sites: "{i}", "arg{j}", numeric and
    `[Symbol.x]` keys, JSX attribute names) go through `types.name_id`, the one place left that
    adds to the names table while checking: step 3's concurrent names table goes there.
- Step 4.3 started, interned lists in C (landed with 4.2): `intern_find`/`intern_put` (unions,
  intersections, their origins, `union_plain`) and `bind.ref_of`'s references (tag 5, before a map
  of hashes) are one lock-free table, ctab.h `ik_*`: 2^18 bucket heads, each a chain of entries in
  an append-only pool, an entry linked by a compare-and-swap on its head; `ik_put` returns the value
  already there when another worker added the key first, and every caller now returns what
  `intern_put` returns (the side tables, `t_origin`, `t_ctv`, `t_iorigin`, written before it, so
  before the id is published). Chosen over lock-striped open addressing: no resize to coordinate.
  Not measured against it.
  Gates for 4.2 and 4.3 together: probes 133/133 and vtests' 3 failures byte for byte (both with
  VTSC_SO_CHECK=1 too), the CI job's 88 outputs byte-identical with VTSC_SO_CHECK=1 (no panic);
  18.43 / 16.46 / 54.15 G instructions (-0.3, -1.8, -1.9% on the pre-M3 base).
- Next (step 4.3, the rest): the other interning maps as `ik_*` keys (`strlits`, `numlits`,
  `biglits`, `unions` (Str keys), `tmpls`/`tmpl_ids`, `mappers`/`mapper_ids`, `inst_cache`,
  `t_alias`..., `tl_cache`, `alias_inst`, `inst_icache`/`inst_acache`, `enum_type`/`enum_union`,
  `tuple_labels`): a Str key becomes its Ints (name ids, type ids), a key's side attributes C
  columns written before `ik_put`. Then the names: `c.t.names` frozen when checking starts, and
  `types.name_id` finding a name in it read-only (an `ast` find without insert) or in a C string
  table (ids from the frozen length up, so single-threaded ids stay the same); the ~160 direct
  `c.t.names[x]` reads in the checker's files (bind 33, chk 56, rel 36, show 17, types 9, tyops
  4, trules 3+3) become `nm(c, x)`. Then a list column's pool reservation (`cl_add`/`cl_set`),
  `ph_put` without moving slots, and the `ct_len` watermarks (chk.vu `cur_id`/`nsg`, tyops'
  `tk0`).
- Step 4.3, names made while checking in C (landed 2026-11-24): `types.freeze_names` (when checking
  starts) fixes `c.names0`, the names table's length; from then on `types.name_id` finds a name in
  the frozen table read-only (`ast.find_name`) or finds or adds it in ctab.h's `ns_*` table (a
  lock-free chained table as `ik_*`, the ids an append-only column, taken by fetch-add), its id
  `names0 + k`, so single-threaded ids are the ones `ast.intern` gave before. A name's text is
  `types.name_text(c, id)` (or bind/chk's `nm`): the checker's files read a type's or symbol's name
  through it (130 sites); a node's own name (`c.t.names[c.t.nd[x].s]`, 31 sites) stays a direct
  read, since nodes are frozen with their names. First measured +4.4 / +5.4 / +1.7% instructions:
  `name_text` returns a copy where the list read had been a view, and cmp_types compares literal and
  alias names on every union sort; `types.name_cmp` / `name_js_cmp` compare two ids' texts without
  copying when both are frozen, and the `+ ""` after each call (a second copy) went. VTSC_SO_CHECK=1
  panics if the names table grew while checking. Probes 133/133, vtests' 3 failures byte for byte
  (both with VTSC_SO_CHECK=1), the CI job's 88 outputs byte-identical with VTSC_SO_CHECK=1; 18.43 /
  16.49 / 54.35 G instructions (-0.3, -1.7, -1.5% on the pre-M3 base).
- Step 4.2's open case closed (landed 2026-11-24): the late root wasn't an import's target but
  `bind.ns_import_file`, which for a name found in no scope (a global) looks for the file's own
  import of it at the file's root, and named the root to do so: in @types/node's test.d.ts, a script,
  `import TestFn = test.TestFn` inside its `declare module "node:test"`. A file that isn't a module
  has no imports at its root (any import makes it a module), so it now looks only in a module's
  root. With that, VTSC_SO_CHECK=1 panics on any scope named after checking starts, scripts' roots
  included. Probes 133/133, vtests' 3 failures byte for byte, the CI job's 88 outputs
  byte-identical, all with VTSC_SO_CHECK=1 and no panic; 18.60 / 16.55 / 54.45 G instructions.
- Step 4.4, the tables' appends safe for several tasks (landed 2026-11-24): a list column's pool
  is reserved by fetch-add (`cl_res`); `cl_add` grows a row in place only by a compare-and-swap of
  the pool's end from the row's end, else writes the row again in a new reservation (single-threaded,
  the same offsets as before). The property table (`ph_*`) is chained as `ik_*` (2^20 bucket heads,
  entries in an append-only pool, linked by compare-and-swap), so nothing moves under a reader:
  `ph_grow` is gone. A literal type and its fresh copy take two rows at once (`types.mk2`, ctab.h
  `cg_rows`), so the fresh one is always the next row (`fresh_of`, `regular_of`). `sig_push` returns
  the signature's id: the five chk.vu sites that took `ct_len(hs_node)` before pushing use it.
  tyops' `tk0` watermark is left: it only feeds the debug counts (`c.debug_counts`). Bounds checks
  read a column's length with a relaxed atomic load (`ct_len0`), which TSan wants. `ctab_stress.vu`:
  8 tasks find-or-add 4,000 keys 80,000 times each in `ik_*`, `ns_*`, `ph_*`, `ct_publish`, with
  `cg_rows` and `cl_add`/`cl_set` rows among them, then check every task got one id per key; under
  TSan (`CC=clang ../vu build --tsan`) 10 runs clean, exit 0 (the first runs found the length
  races above); a planted bug (ik_put/ns_put not walking the entries added after their first look)
  is caught every run. Archer isn't installed on this Mac (only needed for par loops). Probes
  133/133, vtests' 3 failures byte for byte, the CI job's 88 outputs byte-identical, each with and
  without VTSC_SO_CHECK=1 (no panic); 18.55 / 16.50 / 54.32 G instructions (+0.4, -1.6, -1.6% on
  the pre-M3 base).
- The payoff, estimated before more plumbing (2026-11-24, build at step 4.4; the session's scratch
  `m5/pay.sh`, `m5/ph.sh`, `m5/crit_cold.sh`, `m5/model.py`). A threaded prototype with one global
  lock around what isn't thread-safe can't be built in Vu as it stands: tasks share only frozen
  values (no task can reach another's `var c: C`), and nearly every checker function writes a Vu
  map in `C` (ntype, caches, diagnostics), so such a lock would cover the whole check. So this is a
  model from measurements instead. Serial type-aware runs (plain rules off, one worker): plan idx
  78 / 32 / 76 check 1.15 / 1.59 / 5.39 s of 1.85 / 2.11 / 6.24 s wall; the four largest
  type-aware invocations 14.8, 5.9, 5.4, 4.7 s of check in 16.5, 7.0, 6.5, 5.8 s. Today's forked
  shards (VTSC_JOBS 1/2/4/8, best of 2): idx 76 6.21 / 5.10 / 4.17 / 3.55 s wall, 6.6 / 9.1 / 12.0
  / 17.7 cpu-s; idx 78 is fastest on one (1.84 s). Modeling each invocation's type-aware part as
  (serial wall - check) + check / (1 + (N-1) * efficiency), never worse than today, its wall as the
  later of that and the plain lint's end (each invocation run alone, cold: `crit_cold.sh`), and the
  job as two at a time in plan order (that simulation gives 74.4 s for today's build, measured 78):
  N=4 56.5 s at perfect scaling, 59.5 at 75%, 64.1 at 50%; N=8 51.8-55.3; with the type-aware
  part free the job would still take 47.8 s, the plain lint's critical path. Against oxlint 1.79's
  74-79 s: threads alone are worth about 15-25%, not a dramatic lead; the plain lint (228 cpu-s
  against oxlint's 129, the largest package's plain lint 9.8 s alone) bounds the rest.
- Next (step 4.3's rest, in order): the other interning maps as `ik_*` keys (`strlits`,
  `numlits`/`nums`/`numtext`, `biglits`, `unions` (Str keys), `tmpls`/`tmpl_ids`,
  `mappers`/`mapper_ids` (and `c.mappers` itself: a list column of from and to), `inst_cache`,
  `ref_cache`, `t_alias`/`t_alias_args`, `t_origin`, `t_ctv`, `t_iorigin`, `tl_cache`, `alias_inst`,
  `inst_icache`/`inst_acache`, `enum_type`/`enum_union`, `tuple_labels`, `unres_names`): a Str key
  becomes its Ints, a type's side attributes C columns written before `ik_put` publishes it. Then
  a list column's pool reservation (`cl_add`/`cl_set` append without one), `ph_put` without moving
  slots (one region sized from the program, or a new table published by pointer), and the `ct_len`
  watermarks (chk.vu's `cur_id`/`nsg` over `hs_node`, tyops' `tk0` over `htk`), which another
  worker's rows would break. Then step 4's split of `C` and M4.
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
