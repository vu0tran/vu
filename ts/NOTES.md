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

## Checks before committing

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
