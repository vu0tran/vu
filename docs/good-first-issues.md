# Good first issues (drafts)

Twenty issues, each small enough for someone new to the compiler. They're drafts for the owner to
review and open, not issues yet. Each one names where to start.

1. **`\x` and `\u` escapes in strings.** Models write `"\x00"` and `"é"`, and today they need
   `chr(n)`. Lexer: `c1_front.vu`. Tests: `tests/selfhost/`.
2. **A clearer error for `else` inside an expression.** `for x in f() else []:` reports "expected
   ':', found 'else'". It should say that `else` works at statement level and suggest
   `let xs = f() else []`. Parser: `c1_front.vu`.
3. **`xs.copy()` for lists.** The error lists the methods there are; a copy is the one people try
   first. `c3b_calls.vu`.
4. **`s.bytes()` as well as `bytes(s)`.** The same reasoning: models write the method. `str_method`
   in `c3b_calls.vu`.
5. **`vu check --caps --json`.** For tools that show a program's capabilities. `caps_text` in
   `c5_build.vu`.
6. **A `vu_caps` tool in the MCP server `mcp/vu`.** It returns what `vu check --caps` prints.
7. **`vu build --lib --prefix NAME`.** It would export `NAME_f` for `export fn f`, so names like
   `puts` don't collide with the C library. `export_code` in `c5_build.vu`.
8. **`var` list parameters for exported functions.** Copy the list in, then copy it back if its
   length didn't change. `check_export` in `c2_types.vu`, `export_code` in `c5_build.vu`.
9. **Typed errors (`throws E`) from exported functions.** Hand C the message the variant prints
   (`vu_etext_E`).
10. **A precompiled header for split builds.** Every part parses the same header. Use clang's
    `-include-pch` and gcc's `.gch`, and measure with `bench/rebuild/run.sh`.
11. **Split builds for programs with extern C files.** Today they're built as one file, because
    the glue's own state would be copied into every part. Compile the glue once, in part 0.
12. **Try clang for optimized builds.** On `bench/rebuild`'s C, clang -O3 takes 2.1 s and gcc
    9.3 s. Measure the benchmarks' run times with both before changing anything.
13. **Tasks in libraries.** `vu build --lib` refuses tasks, because the scheduler starts itself on
    the first thread that uses it. `vu_tasks_init` in `compiler/rt/tasks.c`.
14. **macOS: `install_name` for `.dylib` libraries,** so they can be loaded from anywhere.
15. **Python wheels in CI.** Build `packaging/python` for Linux and macOS (cibuildwheel) and run
    its test.
16. **`vu fmt` for long `export fn` lines.** Check what it does with a signature over 100
    characters.
17. **`tests/run_split.sh`: also compare programs with `# args:` lines and stdin.**
18. **The time server's AddressSanitizer crash on CI.** It has happened twice on Linux x86-64
    runners, never locally. The next one will print AddressSanitizer's own report.
19. **The Homebrew formula.** Once there's a release, test `brew install` on a Mac
    (`packaging/homebrew`).
20. **`install.sh` on macOS and Linux ARM.** Once there's a release, run the installer on each
    and fix what breaks.
