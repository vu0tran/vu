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
