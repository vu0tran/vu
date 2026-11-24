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
| `tsconf.vu` | vtsc: tsconfig.json (`read`: options through extends, root files, `unmodeled`; `path_targets`) |
| `tsres.vu` | vtsc: where a package's types are (`resolve_types`, `auto_types`, `triple_slash`); `vtsc.run` loads them as package files (`c.pkg_files`: declared, never checked) |
| `vlint.vu` | vlint's driver: CLI, file walk, workers, tsgolint, output |
| `rules.vu` | the `L` state, the walk, oxlint's default rules, semantic errors (below) |
| `rmore.vu` … `rmore8.vu` | non-default rules ported in batches (each file's header lists its rules); `rmore.vu` has the `newr` scheme: setup says which node kinds a rule needs, `node()` runs them |
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
