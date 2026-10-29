# Contributing to Vu

Thank you for looking. Vu was written by an AI model under its author's direction (see README.md),
and it takes contributions from people the same way: a change comes with the tests that attack
it, and every claim in the docs is measured or checked.

## Getting set up

You need a C compiler (gcc or clang) and Python 3. Nothing else:

```
git clone https://github.com/vu0tran/vu && cd vu
./vu version          # builds the compiler from compiler/vuc_seed.c the first time
```

## The loop

1. Change the compiler's parts, `compiler/*.vu` (see the map in CLAUDE.md). Don't change
   `compiler/vuc.vu`: it's the parts joined together. The C runtime is in `compiler/rt/`.
2. `compiler/build.sh` rebuilds the compiler with itself until it reaches a fixed point (about
   40 s). Commit the refreshed `compiler/vuc_seed.c` with your change.
3. `tests/try.sh FILE.vu` checks a program, runs it, runs it again under AddressSanitizer and
   UBSan, compares the output, and audits the C for warnings.
4. Write targeted tests in `tests/targeted/N_name.vu` that attack your change. Each starts with
   two lines, `# attack: what it tries` and `# expect: output TEXT` (or `reject MSG` or
   `panic MSG`). `tests/run_quick.sh PATTERN` runs the ones whose names match.
5. Before a pull request, `tests/gate.sh` runs everything (about 40 minutes on 2 cores) and must
   print `GATE PASSED`.

## What to write where

- The language: SPEC.md, short, with examples first.
- What changed, with the numbers you measured and what your tests found: CHANGELOG.md.
- A number in any document comes with the script or command that produced it.

## Reporting bugs

Open an issue with the smallest program that shows it, what it printed, and what you expected.
Memory-safety and capability bugs are especially welcome: see BREAK_IT.md.
