# Working on Vu

Vu is a language that compiles to C. There is one compiler, `compiler/vuc`, written in Vu
(`compiler/*.vu`). It's bootstrapped from `compiler/vuc_seed.c`, its own C output, so building it
needs only a C compiler. `./vu` runs it (and builds it from the seed the first time). The language
is in `SPEC.md`; results and history are in `README.md`. The retired Python compiler is in
`attic/vu.py`, for reference only: don't change it or test against it.

## The loop

1. Change `compiler/*.vu` (map below) and rebuild: `compiler/build.sh` (about 40 s). It builds
   the compiler with itself until it reaches a fixed point, then installs it as `compiler/vuc`
   and refreshes `vuc_seed.c`; on any failure the old compiler stays. Commit the new seed with
   the change.
2. A feature the compiler's own source wants to use: add it first, rebuild, then use it in
   `compiler/*.vu` and rebuild again (the installed compiler must understand the source).
3. Try a program: `tests/try.sh FILE.vu [ARGS]` (check, quick run, ASan/UBSan/LSan run with the
   same output, and the C audited with the gate's warning flags).
4. `tests/run_quick.sh PATTERN...` rebuilds the compiler and runs the targeted tests whose names
   match.
5. Attack the feature: write targeted tests (see "Writing tests"), and keep doing rounds until
   one finds nothing. Report every round's findings honestly, and don't count your own test
   mistakes as findings. Audit new C in each round (`try.sh` does): the gate fails on any warning,
   and newer gcc turns some (incompatible pointer types) into errors.
6. Run the **full gate** (about 30 minutes, in the background) once per batch of features, before
   syncing or packaging, not after each one: `tests/gate.sh`. It must print GATE PASSED. Nothing
   CPU-heavy runs while it does: several checks measure time and fail on a starved machine.

## Speed rules

- Check, don't build: `./vu check FILE` (milliseconds; every compile error comes from the
  front end). For the compiler's own source: `compiler/vuc check compiler/vuc.vu` (0.15 s).
- **Never edit the repo while a gate runs.** The suites read `compiler/vuc` and the test files
  mid-run; edits make the results meaningless. Work in a copy (`cp -r` into the scratchpad) or a
  worktree, and copy back after.
- Don't re-run the full gate to check one fix: use `run_quick.sh` with a pattern.
- Long suites go in the background; wait with a `run_in_background` `until grep ...; do sleep 10; done`.

## The compiler's source

- `compiler/build.sh` joins the parts into `compiler/vuc.vu` (Vu has no modules for the
  compiler's own source yet): edit the parts, never `vuc.vu`.
- The C runtime and the code templates (lists, maps, boxes) are plain C in `compiler/rt/`.
  `tools/gen_runtime.vu` turns them into `runtime_gen.vu` (build.sh runs it); holes in templates
  are written `@@NAME@@`.
- vuc caches types by `node.id`; nodes it creates itself get negative ids (`synth_node`), and each
  module's parser starts at `index << 32`.
- Types are strings: `Int`, `[T]`, `{K: V}`, `T?`, `Chan[T]`, struct and enum names, `!T` for a
  result (`!T#E` for throws E), `~void`, `~nil`.

| file | what |
|---|---|
| `c1_front.vu` | lexer, parser, string helpers, `report` |
| `c2_types.vu` | checker state, `collect`, `tn`, `ct`, `resolve`, generics, scopes, `declare`, `read_check`, `write_check`, `move_place` |
| `c3_expr.vu` | `place`, `gen`, `value`, `coerce`, `bw_begin`/`bw_end` (borrowing), `effects`, `g_*`, `g_call` |
| `c3b_calls.vu` | `call_user`, `fs_call`, `os_call`, built-ins, `str_method`, JSON |
| `c4_stmt.vu` | `stmts`, `hoist_tries`, `s_*`, `if_chain`, `last_use`, `stmt_value` |
| `c5_build.vu` | `gen_fn`, `gen_consts`, `build`, `load_program`, module resolution (`res_*`), `main` |
| `rt/*.c`, `rt/help.txt` | the C runtime, templates, and the help text |

## Writing Vu (including the compiler's own source)

- Every string interpolates: literal braces are doubled, even inside nested strings
  (`"{id("}}")}"`). Strings may appear inside `{...}`.
- `else` (a fallback for a call that can fail) is statement-level only: `let x = f() else 0`,
  never inside an argument, an interpolation or a condition.
- `match` works on enums (and calls that can fail), not on Int or Str.
- Moving: `let y = x` moves lists, structs and enums. `let y = s.field` of a non-Str value is
  a read-only view that freezes `s` until the block ends (so `s.push`/`s = ...` fail). Copy
  the fields you need (`let n = s.name + ""` for a Str, an index loop for lists) when you'll
  change `s` in the same block.
- Passing a variable to an `own` parameter moves it; a Str used again is copied.
- `var` parameters need `&` at the call, and a `&` argument can't appear twice in one call
  (use a separate statement).
- Locals may shadow functions and built-ins, but then those functions can't be called in that
  scope.

## Writing tests

- Targeted tests (`tests/targeted/N_name.vu`) start with two header lines:
  `# attack: ...` and `# expect: output TEXT` / `reject MSG` / `panic MSG` (a kind and a
  message: `# expect: reject` alone is read as an output test). The header shifts every
  reported line by **2**: write expected line numbers after counting it.
- `output` compares stdout exactly, as one string: print one line, mind trailing spaces.
- Compute expected values by running a Python equivalent, never by hand.
- Multi-file programs go in `tests/modules/NAME/` (`main.vu` has the header).
- Debugging and command-line behavior: `tests/run_debug.py`, `tests/run_cli.sh`.
- Memory that must stay bounded (resident memory read from /proc): `tests/memory/*.vu`, run by
  `tests/run_memory.sh` (plain release builds only: sanitizers keep freed memory in quarantine).
- Network servers: `tests/net/*.vu`, driven by Python clients in `tests/run_net.py`. A server's
  stdout reaches a pipe only at exit, so wait for the listening socket, not a "ready" line.
- Lexer and parser edge cases go in `tests/selfhost/`, with their expected result in
  `tests/selfhost/expected.tsv` (`tests/run_selfhost.sh` explains the columns).
- Calling C: `tests/ffi/NN_name/main.vu` with glue in `tests/ffi/glue/`, checked by `tests/run_ffi.py`.
- JSON: `tests/run_json.sh` runs the json example on generated documents, and `from_json`/`to_json`
  (`tests/json/typed.vu`) against a Python model of the same types (`typed_model.py`). Run fuzz
  builds with the suites' options (`LSAN_OPTIONS=use_poisoned=1` for pool builds; TSan with
  `CC=clang` and Archer, as `run_targeted.sh` does), or they report false leaks and races.

- Tasks run on several threads: `tests/run_mt.sh` repeats every task program under
  ThreadSanitizer (`CC=clang ./vu build --tsan`). A sanitizer run that can't start (a wrong
  suppressions path makes TSan exit with 66 before running anything) must count as a failure,
  never as "no reports": check the exit code and the output, not just the absence of warnings.

## Docs

After a feature: `SPEC.md` (the language, short, examples first) and `README.md` (what
changed, measured numbers, the attack rounds with what each found). Claims must be measured
or checked. Say so when something wasn't.
