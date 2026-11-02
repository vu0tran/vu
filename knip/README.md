# vknip

A rewrite in Vu of [knip](https://knip.dev) (npm `knip`, version **6.44.1**): it finds unused files,
unused dependencies and devDependencies, unlisted dependencies and binaries, unresolved imports,
unused exports and exported types, unused enum and namespace members, and duplicate exports in a
JavaScript or TypeScript project, and prints the report knip prints, byte for byte.

```
./vu build --release knip/vknip.vu -o vknip
cd my-project && /path/to/vknip                 # knip's default (symbols) report; exit 1 when it finds something
vknip --directory DIR --reporter json --include-entry-exports --jobs N
```

It follows knip's own code (graph/build.js, graph/analyze.js, the graph explorer, the import and
export visitors, DependencyDeputy, the script parser, the plugins below), reading files with vtsc's
parser (`ts/scan.vu`, `ts/parse.vu`, `ts/ast.vu`, linked into this folder unchanged; exact mode keeps
node ends). Files are parsed on all cores, wave by wave as the import graph reaches them.

## What it does

- **Entry files**: package.json `main`, `module`, `browser`, `bin`, `types`, `typings`, `exports`
  (wildcards expanded), `imports`; knip's default entries `{index,cli,main}.{ext}` and
  `src/{index,cli,main}.{ext}`; `.d.ts` files a tsconfig.json includes; files named in scripts
  (`node x.js`, `tsx x.ts`, `mocha test/`...), `require.resolve`, `import.meta.resolve`,
  `new URL('./x', import.meta.url)`, `child_process` commands; the plugins' entries. tsconfig
  `outDir`/`rootDir` map package.json entries in `dist` back to `src`.
- **Project files**: `**/*.{js,mjs,cjs,jsx,ts,tsx,mts,cts}` minus `node_modules` and what
  `.gitignore` files ignore (nested ones too, `!` re-includes, `.git/info/exclude`), with knip's
  quirks (a pattern `*` doesn't cover subfolders; `.gitignore` checks of unresolved imports don't
  match dot folders with `**`).
- **The graph**: static imports and re-exports (named, default, namespace, `export *`,
  `export * as ns`, type-only), dynamic `import()` (awaited bindings, destructuring, `.then`, loader
  arrows `() => import(x)`), `require` (bindings, destructuring), `module.exports`/`exports.x`, `import
  x = require()`, `export =`, `import('x')` types, `declare module` augmentations, `/// <reference>`,
  `@jsxImportSource`, JSDoc `import('x')` types, `@vitest-environment`.
- **Resolution** (oxc-resolver as knip configures it): relative paths, extension aliases (`.js` ->
  `.ts`, `.tsx`, `.d.ts`; `.mjs` -> `.mts`...), directory `index` files and `package.json` main, the
  nearest tsconfig.json's `paths` and `baseUrl` (with `extends`, including packages), the project's
  own `paths` as a fallback, package.json `imports` (`#x`), the package's own name through
  `exports`, packages in `node_modules` (and above), node builtins.
- **Exports**: what is referenced through re-export chains, aliases, namespaces (member access,
  destructuring, passing a namespace whole, `Object.keys`, spreads), the TypeScript types an exported
  value's signature uses (knip's `referencedIn`, including the return types of local functions it
  calls), exports of entry files skipped, JSDoc `@public`/`@beta`/`@alias` skipped, enum members (with
  `E.A`, `E['A']`, whole-enum reads), namespace members (and their references to each other), duplicate
  exports.
- **Dependencies**: imports, script binaries (through the `bin` of installed packages), `@types/x`
  for used or typed packages, peer dependencies of used packages (host dependencies), `engines`,
  `optionalDependencies` that aren't installed; knip and typescript never reported.
- **Scripts**: a small shell reader (operators, quotes, `$(...)`, redirections, `VAR=x` prefixes,
  `NODE_OPTIONS`) and knip's resolvers for npm (`run`, `exec`, `--` forwarding into the script),
  npx, pnpm (`run`, `exec`, `dlx`, `--filter`), pnpx, yarn, bun, cross-env, c8, node, tsx, ts-node,
  tsc (`-p` reads that tsconfig), mocha, vitest, eslint, prettier, oxlint, oxfmt, jest, playwright,
  typedoc, borp, and the fallback (positional files for esbuild, zx..., `concurrently` commands).
- **Report**: the symbols reporter as knip prints it when stdout isn't a terminal: sections in
  knip's order, rows sorted with ICU's collation order (punctuation, digits, letters, lowercase
  first), the table's column widths, and its truncation to 120 columns (paths from the start,
  names from the end, with `…`). `--reporter json` writes knip's JSON shape (issues are grouped by
  file in the order vknip found them, which can differ from knip's).

Plugins (knip has about 200; these are the ones the test corpus needed and a few common ones):
Node.js (`server.js`, `node --test` test files), TypeScript (each tsconfig: `extends`, `references`,
`types`, `plugins`, `importHelpers`, `jsxImportSource`), Vitest and Vite, Jest, Mocha (`.mocharc`
JSON, package.json, command-line specs), Ava (package.json config), xo, tsx (`--test`), ESLint (legacy
JSON configs and package.json `eslintConfig`: `extends`, `plugins`, `parser`; flat configs are entry
files), Prettier (JSON and package.json configs: `plugins`), Changelogen, Oxlint, Oxfmt, unbuild,
esbuild, TypeDoc, nyc, tsd, pnpm, GitHub Actions (`run:` steps with their `working-directory`),
husky, lint-staged (package.json), Playwright, MCP (`.mcp.json` servers), Borp (`.borp.yaml`). A
plugin's JavaScript or TypeScript config file is an entry file, as in knip, but vknip doesn't run it
(knip loads it with jiti and reads the settings it returns), so settings only a JS config gives
(custom test globs, setup files) aren't seen.

## Parity

Each project's whole output was compared with knip's (`test/parity.py`), then per issue type.

**Real projects** (21): small and medium libraries with `pnpm install --ignore-scripts`
dependencies, chosen because they have no JavaScript config files for knip to execute
(unjs/defu, scule, uncrypto; lukeed/dequal, kleur, klona, uvu; developit/mitt; flightcontrolhq/superjson;
sindresorhus/ky, execa, p-queue; chalk/chalk; isaacs/node-lru-cache, node-glob, node-tar;
expressjs/express; koajs/koa; sindresorhus/got; fastify/fastify), plus a large one: microsoft/vscode
(its JS, TS, JSON, YAML and shell files; no `node_modules`). knip ran without any configuration.

| issue type | knip found | vknip: same | missing | extra |
|---|---:|---:|---:|---:|
| Unused files | 841 | 841 | 0 | 0 |
| Unused dependencies | 2 | 2 | 0 | 0 |
| Unused devDependencies | 47 | 47 | 0 | 0 |
| Unlisted binaries | 3 | 3 | 0 | 0 |
| Unresolved imports | 3 | 3 | 0 | 0 |
| Unused exports | 47 | 47 | 0 | 0 |
| Unused exported types | 90 | 90 | 0 | 0 |
| Duplicate exports | 3 | 3 | 0 | 0 |

All 20 small and medium projects: **identical output** (20/20).

vscode (20,700 files, 15,000 TypeScript): 12,666 of 12,667 lines identical:

| issue type | knip found | vknip: same | missing | extra |
|---|---:|---:|---:|---:|
| Unused files | 2692 | 2692 | 0 | 0 |
| Unused dependencies | 10 | 10 | 0 | 0 |
| Unused devDependencies | 32 | 32 | 0 | 0 |
| Unlisted dependencies | 2007 | 2007 | 0 | 0 |
| Unlisted binaries | 21 | 21 | 0 | 0 |
| Unresolved imports | 10 | 10 | 0 | 0 |
| Unused exports | 3953 | 3953 | 0 | 0 |
| Unused exported types | 2581 | 2580 | 1 | 1 |
| Unused exported enum members | 1103 | 1103 | 0 | 0 |
| Unused exported namespace members | 244 | 244 | 0 | 0 |
| Duplicate exports | 3 | 3 | 0 | 0 |

The one different line names the namespace an unused type is reached through: two files import the
module under different names, and knip names the first importer it analyzed, which follows the order
the file system lists directories in (knip's glob doesn't sort); vknip lists them sorted.

**Generated projects** (141, `test/cases.py`, `test/cases2.py`, `test/random_cases.py`): 41 written to
exercise one feature each (re-export chains, namespaces, enums, type-only imports, CommonJS, dynamic
imports, unresolved and unlisted packages, scripts and binaries, tsconfig paths, index files and
extensions, defaults and duplicates, JSDoc tags, `export =`, destructuring, test runners,
`.gitignore`, package.json entries and `imports`, `outDir` mapping, self-references, `node --test`,
comment imports, shadowing, JSX member expressions, workers, augmentations, `@types` and peer
dependencies, query specifiers, loader imports) and 100 random ones (modules with random exports,
imported in random ways). **141/141 identical.** Three rounds: the first two (feature projects, then
40 random) found one difference (tsconfig files named by `tsc -p` are read even when the TypeScript
plugin isn't enabled), the third (16 harder feature projects and 60 more random ones) found nothing.

The real-project rounds found more: per-file nearest tsconfig `paths` (vscode's extensions), the
Playwright and MCP plugins, mocha's command-line specs, `child_process` commands in source files,
workflow `working-directory`, namespace members referring to each other, `export {}` not counting as
an export, arrow functions' expression bodies in exported signatures, the Borp plugin, `.gitignore`'s
`*` pattern, and exports of skipped files.

## Benchmark

CPU time (user + system, so both of vknip's threads count) and wall time, best of 5 runs (best of 2
for knip on vscode), on a 2-core machine shared with other jobs (load average around 8, so wall
times are noisy; CPU times are the fair comparison). knip runs on Node 22 and parses with oxc
(native code); its startup alone (`knip --version`) costs 0.72 s of CPU (`node -e 0`: 0.04 s), which is most of its time
on the small projects.

| project | files | knip CPU s | vknip CPU s | CPU ratio | knip wall s | vknip wall s |
|---|---:|---:|---:|---:|---:|---:|
| express | 142 | 1.44 | 0.030 | 48x | 3.86 | 0.076 |
| fastify | 304 | 3.08 | 0.107 | 29x | 7.71 | 0.275 |
| got | 98 | 2.40 | 0.102 | 24x | 6.29 | 0.255 |
| koa | 82 | 1.42 | 0.017 | 83x | 3.62 | 0.057 |
| node-glob | 59 | 1.10 | 0.009 | 128x | 3.53 | 0.024 |
| node-tar | 73 | 1.22 | 0.017 | 73x | 3.69 | 0.056 |
| chalk | 20 | 1.00 | 0.007 | 144x | 2.76 | 0.020 |
| defu | 9 | 1.01 | 0.005 | 196x | 3.13 | 0.005 |
| dequal | 9 | 0.97 | 0.003 | 351x | 2.86 | 0.003 |
| execa | 639 | 1.44 | 0.027 | 54x | 4.54 | 0.060 |
| kleur | 13 | 0.92 | 0.003 | 315x | 2.65 | 0.003 |
| klona | 37 | 0.91 | 0.003 | 276x | 2.73 | 0.008 |
| ky | 98 | 1.97 | 0.052 | 38x | 6.10 | 0.155 |
| mitt | 3 | 0.96 | 0.006 | 173x | 2.93 | 0.015 |
| node-lru-cache | 49 | 1.06 | 0.008 | 125x | 2.55 | 0.016 |
| p-queue | 17 | 1.26 | 0.016 | 78x | 3.30 | 0.049 |
| scule | 4 | 1.01 | 0.006 | 173x | 3.03 | 0.014 |
| superjson | 20 | 1.05 | 0.009 | 119x | 2.57 | 0.020 |
| uncrypto | 5 | 0.94 | 0.007 | 141x | 2.07 | 0.007 |
| uvu | 93 | 0.95 | 0.006 | 147x | 1.40 | 0.006 |
| vscode | 15571 | 46.27 | 10.31 | 4.5x | 160.79 | 25.15 |

On vscode vknip takes 10.3 s of CPU with one thread or two (`--jobs 1`: 10.36 s), so its wall time
halves on an idle 2-core machine; knip's work there is mostly on one thread. About half of vknip's
time is vtsc's parser; the rest is the walk over each tree, module resolution, and the file walk with
its `.gitignore` matching.

## Not done

- Workspaces (monorepos): only the root package is read.
- Running JavaScript/TypeScript config files (see Plugins), and the ~170 other plugins.
- knip's configuration (`knip.json`: `entry`, `project`, `ignore*`, plugin settings), `--production`,
  `--strict`, `--fix`, `--cache`, `--watch`, tags, catalogs, cycles, compilers (`.vue`, `.svelte`,
  `.mdx`, `.astro`), published type dependencies of non-private packages, JSDoc `@import` tags.
- Files this parser rejects are read as having no imports or exports (oxc recovers from more errors).
- Configuration hints (knip prints them to standard error).

## Tests

`test/` has the scripts: `run_cases.py` writes the generated projects and saves knip's output
(`KNIP=.../knip/bin/knip.js CASES=cases.py python3 run_cases.py OUT REF`), `cmp_cases.sh` compares
vknip with it, `parity.py` and `catdiff.py` compare real projects per issue type, `bench.py` times
both, and `globtest.vu` checks the glob matcher against picomatch (`globcases.js`: 1,440 cases, one
known difference: `!(x)` against a dot file).
