# vknip

A rewrite in Vu of [knip](https://knip.dev) (npm `knip`, version **6.44.1**): it finds unused files,
unused dependencies and devDependencies, unlisted dependencies and binaries, unresolved imports,
unused exports and exported types, unused enum and namespace members, and duplicate exports in a
JavaScript or TypeScript project or monorepo, and prints the report knip prints, byte for byte. It is
meant as a drop-in replacement: the same command line, the same configuration files, the same
reporters, the same exit codes.

```
./vu build knip/vknip.vu -o vknip
cd my-project && /path/to/vknip                 # knip's default (symbols) report; exit 1 when it finds something
vknip --directory DIR --reporter json --workspace packages/x --production --strict
vknip --fix --allow-remove-files              # knip's --fix, file for file
```

It follows knip's own code (graph/build.js, graph/analyze.js, the graph explorer, the import and
export visitors, DependencyDeputy, the script parser, the plugins), reading files with vtsc's
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
  names from the end, with `…`). `--reporter json` writes knip's JSON,
  issues in knip's order (unused files as knip's crawler lists them: by workspace, by depth, folder
  by folder).

## Configuration

vknip reads the configuration knip reads, from the same places, in the same order: `knip.json`,
`knip.jsonc`, `.knip.json`, `.knip.jsonc`, `knip.ts`, `knip.js`, `knip.config.ts`, `knip.config.js`
(and the other extensions knip accepts), the `knip` field of package.json, or `--config FILE`. A
JavaScript or TypeScript configuration runs in node, as in knip: vknip starts one node process, which
imports the file with the project's jiti (or the one installed next to its knip, or any `jiti@2` in
`node_modules/.pnpm`; native `import()` without one) and writes the result back as JSON. A config that
exports a function is called (with knip's argument), and a promise is awaited. Load errors are
reported as knip reports them.

The schema: `entry`, `project`, `paths`, `ignore`, `ignoreFiles`, `ignoreDependencies`,
`ignoreBinaries`, `ignoreMembers`, `ignoreUnresolved`, `ignoreWorkspaces`, `ignoreIssues`,
`includeEntryExports`, `rules` (`error`/`warn`/`off`), `include`/`exclude`, `tags`, `workspaces` (with
globs: `packages/*` settings apply to each matching workspace), `treatConfigHintsAsErrors`, and each
plugin's settings: `false` (off), `true` (on), a config file
pattern or list (`"vitest": "config/vitest.ts"`), or an object with `config`, `entry` and `project`.
Strings or regular expressions where knip takes both. Not read: `ignoreExportsUsedInFile` (accepted,
no effect; see Gaps) and `compilers` (custom compiler functions).

## Workspaces

npm and yarn `workspaces` (array or `{packages}`, nested globs, `!` exclusions), pnpm's
`pnpm-workspace.yaml`, and the `workspaces` keys of the configuration; `ignoreWorkspaces`. Each
workspace gets its own manifest, dependencies, tsconfig `paths`, plugins, entry and project patterns
and `.gitignore` files; root files don't count for nested workspaces and the other way round, as knip
splits them. Imports between workspaces resolve to the other workspace's sources (through `exports`,
`main` and the tsconfig `outDir` mapping when it isn't built), and count as a dependency of the
importing workspace. Dependencies follow DependencyDeputy: a dependency listed at the root counts for
nested workspaces, `--strict` only counts the workspace's own `dependencies` and peers, binaries come
from each workspace's and its ancestors' `node_modules/.bin`. `--workspace` takes names, folders and
globs (`-W @scope/*`, `-W !legacy`) and runs the selected workspaces and the ones they depend on, with
knip's errors for a selector that matches nothing. pnpm and package.json `catalog:`/`catalogs:`
entries: unused catalog entries and references to missing ones.

## Command line

All of knip 6.44.1's options are parsed with node's `parseArgs` rules (short groups, `--x=v`, the same
error messages and the help text). What they do:

| option | status |
|---|---|
| `--config`, `--directory`, `--workspace`, `--tsConfig`, `--no-gitignore` | as knip |
| `--production`, `--strict` | as knip (production entries and dependencies only; strict ownership) |
| `--include`, `--exclude`, `--dependencies`, `--exports`, `--files` | as knip, with the rules from the configuration |
| `--include-entry-exports`, `--tags`, `--no-tag-hints`, `--treat-tag-hints-as-errors` | as knip (`@tag` and `-tag`, member tags) |
| `--no-exit-code`, `--max-issues`, `--max-show-issues` | as knip (exit code 1 when error-level issues exceed the maximum, 2 on errors) |
| `--no-config-hints`, `--treat-config-hints-as-errors` | as knip; hints are printed on stderr in knip's table |
| `--reporter` (repeatable), `--output-file` | `symbols` (default), `compact`, `json`, `markdown`, `codeowners`, `disclosure` |
| `--fix`, `--fix-type`, `--allow-remove-files`, `--format` | as knip for exports, types, default exports, dependencies (package.json rewritten in its own indentation) and files; `--format` accepted, no formatter run |
| `--no-progress`, `--debug`, `--performance`, `--memory`, `--trace*`, `--duration` | accepted, no output |
| `--cache`, `--cache-location`, `--watch`, `--use-tsconfig-files`, `--preprocessor`, `--cycles` | accepted, no effect |
| `--jobs N` | vknip only: parser threads |

knip 6 has no `--include-libs` (it was removed upstream), so there is nothing to port.

## Plugins

All 202 of knip's plugins are in a table generated from knip itself (`tools/dump_plugins.mjs` loads
each plugin and writes its enablers, config file patterns, entry, production and project patterns;
`tools/gen_plugins.py` turns that into `plugins.vu`). So every plugin is enabled when knip enables it
(dependencies, regular-expression enablers, root-only plugins, `isEnabled` checks that look at files)
and contributes its config files, entry, production and project patterns. What a plugin finds by
running its `resolveConfig` (reading the loaded config) is ported plugin by plugin:

- **Ported** (config read, as knip's resolveConfig/resolveFromAST does): Vitest and Vite (projects,
  workspaces, setup files, environments, coverage providers, `index.html` scripts, `resolve.alias`
  into paths), Jest (presets, transforms, setup files, reporters, projects), Mocha, Ava, ESLint (legacy
  configs, `extends`, plugins, parsers, settings), Prettier, Playwright, Storybook, Cypress, Changesets,
  commitlint, semantic-release, PostCSS, Babel, release-it, Stylelint, tsup, tsdown, Rollup, Rolldown,
  Rslib, esbuild, lint-staged, Nx (project.json targets, executors, commands), xo, nyc, Oxlint, remark,
  mdxlint, unbuild, Angular (angular.json builders, options, files), Astro and Starlight, Turbo, plus
  the hand-written ones: Node.js, TypeScript (each tsconfig: `extends`, `references`, `types`,
  `plugins`, `importHelpers`, `jsxImportSource`), tsx, husky, MCP, GitHub Actions, Borp, TypeDoc.
- **Patterns only** (97 plugins, among them Next.js, Nuxt, webpack, Svelte/SvelteKit, Docusaurus,
  Remix, Karma, Gatsby, Expo): resolveConfig isn't ported; when such a plugin has a config file vknip
  uses the plugin's default entry and production patterns instead (knip would use what the config
  says, which for most projects is the default).
- **Compilers**: `.vue` (scripts, `src` imports, scss `<style>` imports), `.svelte`, `.astro`
  (frontmatter, scripts, styles), `.mdx`, `.css` with Tailwind (`@import`, `@plugin`, `@config`,
  `@source`...) and `.scss`/`.sass` (`@use`, `@import`, `@forward`, `url()`), `.prisma`, each enabled
  as knip enables it.

The coverage table is at the end of this file.

## Parity

The whole output (stdout, stderr, exit code) of each run was compared with knip 6.44.1's
(`test/cmp_corpus.py` for real projects, `test/gen_cmp.py` and `test/cmp_cases.sh` for generated ones),
then the issues per type.

**Real projects** (23, listed with their commits in `test/corpus.txt`, dependencies installed with
`pnpm install --ignore-scripts`): 20 libraries (chalk, defu, dequal, execa, kleur, klona, ky, mitt,
node-lru-cache, p-queue, scule, superjson, uncrypto, uvu, express, fastify, got, koa, node-glob,
node-tar) and 3 pnpm monorepos with JavaScript and TypeScript configs loaded through node (webpro-nl/knip:
7 workspaces, its own `knip.json`; changesets/changesets: 24 workspaces, 24 JS/TS config files;
unjs/unhead: 28 workspaces, 57 config files, Vue, Svelte, React, Nuxt and Angular packages). knip ran with the project's own configuration.

| reporter | identical runs |
|---|---:|
| default (symbols), stdout + stderr + exit code | 21/23 |
| `--reporter json`, byte for byte | 21/23 |

| issue type | knip found | vknip: same | missing | extra |
|---|---:|---:|---:|---:|
| Unused files | 948 | 948 | 0 | 7 |
| Unused dependencies | 19 | 19 | 0 | 7 |
| Unused devDependencies | 75 | 75 | 0 | 3 |
| Referenced optional peerDependencies | 3 | 3 | 0 | 0 |
| Unlisted dependencies | 58 | 58 | 0 | 0 |
| Unlisted binaries | 7 | 6 | 1 | 0 |
| Unresolved imports | 6 | 6 | 0 | 0 |
| Unused exports | 262 | 182 | 80 | 5 |
| Unused exported types | 170 | 163 | 7 | 2 |
| Duplicate exports | 11 | 11 | 0 | 0 |

The two different projects:

- **changesets**: every difference comes from files that use `await using` declarations, which the
  shared TypeScript parser (`ts/parse.vu`) rejects; vknip then reads those files as having no
  imports, so what they import looks unused (3 files, 8 dependencies, the `taskkill.exe` binary, a few
  exports). It's a parser gap; the parser is shared with vtsc and vlint and was left alone here.
- **unhead**: Nuxt's auto-imports (knip's Nuxt plugin registers a compiler that adds the imports Nuxt
  generates) and Nuxt's config, which knip loads and vknip doesn't (79 of the 80 missing exports are
  in Nuxt-facing packages), and the error knip prints when a Nuxt config fails to load.

The previous single-package corpus (the 20 libraries above plus microsoft/vscode, see git history of
this file) is unchanged: vscode was 12,666 of 12,667 lines identical before this work; it wasn't re-run
(its checkout was removed for disk space).

**Generated projects**, each written to exercise one feature (`test/cases*.py`):

| set | what | identical |
|---|---|---:|
| `cases.py`, `cases2.py`, `random_cases.py` | the graph, exports, dependencies, scripts (first rewrite) | 82/82 |
| `cases3.py` | configuration files (JSON, JSONC, package.json, TS and JS configs, functions), the schema, workspaces (npm, yarn, pnpm, nested, ignored), `--workspace` selectors and their errors, the flags, every reporter, rules, hints, exit codes | 84/84 runs |
| `cases4.py` | plugins: Vitest projects and workspaces, Jest, ESLint, Playwright, Storybook, Cypress, Nx, commitlint, lint-staged, Babel, PostCSS, Next.js (fallback), config load errors | 25/25 runs |
| `cases5.py` | `--fix` and `--fix-type` on fresh copies, the files compared byte for byte after the fix | 21/21 runs |
| `cases6.py` | catalogs, compilers (Vue, Svelte, MDX, CSS/Tailwind, SCSS), yarn nested globs, `ignoreWorkspaces`, tags | 15/15 runs |

Attack rounds (each a new set of cases or a new real project, then fixes until it passed):

1. Configuration and workspaces (cases3): selectors, `ignoreWorkspaces`, `packages/*` keys, rules,
   `--max-issues` and exit codes, the reporters' details (markdown escaping, codeowners, disclosure).
2. Plugins (cases4): config files named by other configs (vitest projects, eslint `extends`, nx
   targets) read in a second pass as knip's configFilesMap does; `config_seen` was shared between
   plugins (lint-staged skipped package.json).
3. `--fix` (cases5): `export` keyword removal, specifier lists, default exports, package.json rewritten
   in its indentation, files removed only with `--allow-remove-files`.
4. Monorepos (knip, changesets, unhead): workspace-package imports as dependencies, root plugins
   seeing other workspaces' binaries (dependency metadata is now loaded for every workspace before
   any plugin runs), the order of unused files in JSON, the GitHub Actions `working-directory`.
5. Catalogs, compilers, tags (cases6): catalog issues have no position in JSON, scss `<style>` imports
   in `.vue` files, `@lintignore` on enum members.
6. Unported resolvers (cases4 additions): a plugin with a config file but no ported resolveConfig
   added no entries at all; it now uses its default entries; Storybook and Cypress ported. This
   round found nothing else.

## Benchmark

CPU time (user + system of the process and everything it waited for, so vknip's node process that
loads JavaScript configs counts, and so do both of its threads) and wall time, best of 3 runs each,
release build (`./vu build`, -O3), knip 6.44.1 on Node 22. The machine has 2 cores shared with other
jobs and its load average was 24 to 27 during the run, so **wall times are inflated about tenfold and
noisy**; CPU times are the fair comparison. knip's startup alone costs about 0.7 s of CPU.

| project | files | knip CPU s | vknip CPU s | CPU ratio | knip wall s | vknip wall s |
|---|---:|---:|---:|---:|---:|---:|
| chalk | 20 | 1.09 | 0.011 | 98x | 8.60 | 0.098 |
| defu | 9 | 1.14 | 0.011 | 108x | 10.85 | 0.108 |
| dequal | 9 | 1.04 | 0.008 | 130x | 9.98 | 0.082 |
| execa | 639 | 1.62 | 0.035 | 46x | 17.50 | 0.364 |
| express | 142 | 1.80 | 0.042 | 43x | 18.65 | 0.380 |
| fastify | 304 | 3.75 | 0.116 | 32x | 37.35 | 1.340 |
| got | 98 | 2.73 | 0.126 | 22x | 28.86 | 1.248 |
| kleur | 13 | 1.17 | 0.009 | 134x | 12.46 | 0.077 |
| klona | 37 | 1.15 | 0.008 | 139x | 11.40 | 0.081 |
| koa | 82 | 1.80 | 0.024 | 76x | 19.32 | 0.200 |
| ky | 98 | 2.17 | 0.058 | 38x | 16.83 | 0.541 |
| mitt | 3 | 1.06 | 0.011 | 100x | 7.32 | 0.100 |
| node-glob | 59 | 1.25 | 0.015 | 84x | 9.69 | 0.143 |
| node-lru-cache | 49 | 1.20 | 0.013 | 89x | 10.14 | 0.086 |
| node-tar | 73 | 1.53 | 0.025 | 61x | 14.79 | 0.248 |
| p-queue | 17 | 1.51 | 0.021 | 71x | 14.68 | 0.217 |
| scule | 4 | 1.11 | 0.012 | 94x | 9.38 | 0.078 |
| superjson | 20 | 1.24 | 0.015 | 83x | 9.82 | 0.136 |
| uncrypto | 5 | 1.03 | 0.009 | 110x | 7.25 | 0.079 |
| uvu | 93 | 1.17 | 0.012 | 94x | 9.38 | 0.124 |
| knip | 4678 | 6.02 | 0.633 | 10x | 50.99 | 5.264 |
| changesets | 164 | 3.35 | 0.570 | 6x | 24.68 | 4.594 |
| unhead | 860 | 12.59 | 6.397 | 2x | 103.23 | 56.700 |

On the monorepos much of vknip's time is node, which loads the JavaScript and TypeScript configs
(measured in one separate run with a wrapper around `node`): on unhead its node processes (57 config
files imported through jiti, with vite, nuxt and vitest behind them) took 5.9 of vknip's 6.7 CPU
seconds, on changesets 0.42 of 0.79, on knip 0.21 of 1.23. The single-package projects load none.

## Gaps

- **Parser**: `await using` declarations (and whatever else `ts/parse.vu` rejects) make a file read as
  having no imports or exports; oxc, knip's parser, accepts them.
- **resolveConfig** of 97 plugins (Next.js, Nuxt, webpack, SvelteKit, Docusaurus, Remix, Karma, ...):
  default entries are used instead of the config's; Nuxt's auto-import compiler.
- `ignoreExportsUsedInFile`, fixes of enum and namespace members and of catalog entries, published type
  dependencies of non-private packages, less and stylus compilers, custom `compilers` in the
  configuration, cycles (`--cycles`).
- `--cache`, `--watch`, `--trace*`, `--performance`, the `github-actions`, `sarif` and `codeclimate`
  reporters, custom reporter and preprocessor modules.
- vscode wasn't re-measured after the workspace rewrite.

## Tests

`test/` has the scripts: `cmp_corpus.py` compares real projects with knip (`WORK=dir`, knip's output
cached in `dir/ref`), `gen_cmp.py CASES OUT` writes the generated projects of a cases file, runs knip
once (cached) and vknip on each command line, and compares stdout, stderr, exit code and, for `--fix`
cases, the files left behind; `run_cases.py` and `cmp_cases.sh` do the same for the first sets;
`bench.py` times both; `globtest.vu` checks the glob matcher against picomatch, `yamltest.vu` the
YAML reader against the `yaml` package (102 files of the corpus, identical).

## Plugin coverage

"tested on" names the generated cases and the corpus projects whose dependencies enable the plugin
(plugins enabled by files aren't detected this way: GitHub Actions ran on all 23 projects, which all have
workflows).

| plugin | status | tested on |
|---|---|---|
| Angular (`angular`) | ported | unhead |
| Astro (`astro`) | ported | knip |
| Astro DB (`astro-db`) | complete (static plugin) |  |
| Astro Markdoc (`astro-markdoc`) | patterns; resolveConfig not ported (default entries used) |  |
| astro-og-canvas (`astro-og-canvas`) | patterns; resolve() not ported |  |
| Ava (`ava`) | ported | ky, uvu |
| Babel (`babel`) | ported | generated; uvu |
| Biome (`biome`) | patterns; resolveConfig not ported (default entries used) |  |
| Borp (`borp`) | ported (hand-written) | fastify |
| Buf (`buf`) | patterns; resolveConfig not ported (default entries used) |  |
| bumpp (`bumpp`) | complete (static plugin) | unhead |
| Bun (`bun`) | patterns; resolveConfig not ported (default entries used) |  |
| c8 (`c8`) | complete (static plugin) |  |
| Capacitor (`capacitor`) | patterns; resolveConfig not ported (default entries used) |  |
| Catalyst (`catalyst`) | complete (static plugin) |  |
| Changelogen (`changelogen`) | complete (static plugin) | defu, scule, uncrypto |
| Changelogithub (`changelogithub`) | complete (static plugin) |  |
| Changesets (`changesets`) | ported | generated; changesets |
| Commitizen (`commitizen`) | patterns; resolveConfig not ported (default entries used) |  |
| commitlint (`commitlint`) | ported | generated |
| Convex (`convex`) | patterns; resolveConfig not ported (default entries used) |  |
| create-typescript-app (`create-typescript-app`) | complete (static plugin) |  |
| CSpell (`cspell`) | patterns; resolveConfig not ported (default entries used) |  |
| Cucumber (`cucumber`) | patterns; resolveConfig not ported (default entries used) |  |
| Cypress (`cypress`) | ported | generated |
| Danger (`danger`) | complete (static plugin) |  |
| dependency-cruiser (`dependency-cruiser`) | complete (static plugin) |  |
| Docusaurus (`docusaurus`) | patterns; resolveConfig not ported (default entries used) |  |
| dotenv (`dotenv`) | complete (static plugin) |  |
| Drizzle (`drizzle`) | patterns; resolveConfig not ported (default entries used) |  |
| Electron Forge (`electron-forge`) | patterns; resolveConfig not ported (default entries used) |  |
| electron-vite (`electron-vite`) | patterns; resolveConfig not ported (default entries used) |  |
| Eleventy (`eleventy`) | patterns; resolveConfig not ported (default entries used) |  |
| esbuild (`esbuild`) | ported | node-glob, node-lru-cache, node-tar, unhead +1 |
| ESLint (`eslint`) | ported | generated; changesets, express, fastify, mitt +3 |
| eve (`eve`) | complete (static plugin) |  |
| execa (`execa`) | complete (static plugin) | chalk |
| Expo (`expo`) | patterns; resolveConfig not ported (default entries used) |  |
| Expo Router (`expo-router`) | patterns; resolveConfig not ported (default entries used) |  |
| Expressive Code (`expressive-code`) | complete (static plugin) | knip |
| FAST (`fast`) | complete (static plugin) |  |
| filesystem-routing (`filesystem-routing`) | patterns; resolveConfig not ported (default entries used) |  |
| Flue (`flue`) | patterns; resolveConfig not ported (default entries used) |  |
| Fumadocs (`fumadocs`) | complete (static plugin) |  |
| Gatsby (`gatsby`) | patterns; resolveConfig not ported (default entries used) |  |
| GitHub Action (`github-action`) | patterns; resolveConfig not ported (default entries used) |  |
| GitHub Actions (`github-actions`) | ported (hand-written) | all 23 corpus projects |
| glob (`glob`) | complete (static plugin) |  |
| GraphQL Codegen (`graphql-codegen`) | patterns; resolveConfig not ported (default entries used) |  |
| Hardhat (`hardhat`) | patterns; resolve() not ported |  |
| husky (`husky`) | ported (hand-written) |  |
| i18next Parser (`i18next-parser`) | complete (static plugin) |  |
| Jasmine (`jasmine`) | patterns; resolveConfig not ported (default entries used) |  |
| Jest (`jest`) | ported | generated; uvu |
| Karma (`karma`) | patterns; resolveConfig not ported (default entries used) |  |
| Knex (`knex`) | patterns; resolveConfig not ported (default entries used) |  |
| kysely-codegen (`kysely-codegen`) | complete (static plugin) |  |
| Ladle (`ladle`) | patterns; resolveConfig not ported (default entries used) |  |
| laravel-vite-plugin (`laravel-vite-plugin`) | patterns; resolveConfig not ported (default entries used) |  |
| Lefthook (`lefthook`) | patterns; resolveConfig not ported (default entries used) |  |
| Lingui (`lingui`) | complete (static plugin) |  |
| lint-staged (`lint-staged`) | ported | generated; changesets |
| LintHTML (`linthtml`) | patterns; resolveConfig not ported (default entries used) |  |
| Lit (`lit`) | complete (static plugin) |  |
| lockfile-lint (`lockfile-lint`) | complete (static plugin) |  |
| Lost Pixel (`lost-pixel`) | complete (static plugin) |  |
| Lunaria (`lunaria`) | patterns; resolveConfig not ported (default entries used) |  |
| markdownlint (`markdownlint`) | patterns; resolveConfig not ported (default entries used) | generated; fastify |
| Marko (`marko`) | patterns; resolveConfig not ported (default entries used) |  |
| Mastra (`mastra`) | complete (static plugin) |  |
| MCP (`mcp`) | ported (hand-written) |  |
| MDX (`mdx`) | patterns; resolveConfig not ported (default entries used) | knip |
| mdxlint (`mdxlint`) | ported | knip |
| Metro (`metro`) | patterns; resolveConfig not ported (default entries used) |  |
| mise (`mise`) | patterns; resolveConfig not ported (default entries used) |  |
| Mocha (`mocha`) | ported | generated; express, mitt, uvu |
| moonrepo (`moonrepo`) | patterns; resolveConfig not ported (default entries used) |  |
| Mock Service Worker (`msw`) | patterns; resolveConfig not ported (default entries used) |  |
| nano-spawn (`nano-spawn`) | complete (static plugin) |  |
| Nano Staged (`nano-staged`) | patterns; resolveConfig not ported (default entries used) |  |
| Nest (`nest`) | patterns; resolveConfig not ported (default entries used) |  |
| Netlify (`netlify`) | patterns; resolveConfig not ported (default entries used) |  |
| Next.js (`next`) | patterns; resolveConfig not ported (default entries used) | generated |
| next-intl (`next-intl`) | complete (static plugin) |  |
| Next.js MDX (`next-mdx`) | patterns; resolveConfig not ported (default entries used) |  |
| Nitro (`nitro`) | patterns; resolveConfig not ported (default entries used) |  |
| Node.js (`node`) | ported |  |
| node-modules-inspector (`node-modules-inspector`) | complete (static plugin) |  |
| nodemon (`nodemon`) | complete (static plugin) |  |
| npm-package-json-lint (`npm-package-json-lint`) | patterns; resolveConfig not ported (default entries used) |  |
| Nuxt (`nuxt`) | patterns; resolveConfig not ported (default entries used) | unhead |
| @nuxtjs/i18n (`nuxtjs-i18n`) | complete (static plugin) |  |
| Nx (`nx`) | ported | generated |
| nyc (`nyc`) | ported | express |
| oclif (`oclif`) | patterns; resolveConfig not ported (default entries used) |  |
| openapi-ts (`openapi-ts`) | complete (static plugin) |  |
| OpenClaw (`openclaw`) | patterns; resolveConfig not ported (default entries used) |  |
| orval (`orval`) | patterns; resolveConfig not ported (default entries used) |  |
| osls (`osls`) | patterns; resolveConfig not ported (default entries used) |  |
| Oxfmt (`oxfmt`) | complete (static plugin) | changesets, defu, knip |
| Oxlint (`oxlint`) | ported | defu, knip, node-glob, node-lru-cache +1 |
| Panda CSS (`panda-css`) | patterns; resolveConfig not ported (default entries used) |  |
| Parcel (`parcel`) | patterns; resolveConfig not ported (default entries used) |  |
| Payload CMS (`payload`) | patterns; resolveConfig not ported (default entries used) |  |
| pino (`pino`) | complete (static plugin) | fastify |
| Playwright (`playwright`) | ported | generated; unhead |
| Playwright for components (`playwright-ct`) | patterns; resolveConfig not ported (default entries used) |  |
| playwright-test (`playwright-test`) | complete (static plugin) |  |
| Plop (`plop`) | complete (static plugin) |  |
| pm2 (`pm2`) | patterns; resolveConfig not ported (default entries used) |  |
| pnpm (`pnpm`) | patterns; resolveConfig not ported (default entries used) | generated |
| PostCSS (`postcss`) | ported | generated |
| pre-commit (`pre-commit`) | patterns; resolve() not ported |  |
| Preconstruct (`preconstruct`) | patterns; resolveConfig not ported (default entries used) |  |
| Prettier (`prettier`) | ported | generated; knip, mitt, node-glob, node-lru-cache +3 |
| Prisma (`prisma`) | patterns; resolveConfig not ported (default entries used) |  |
| PurgeCSS (`purgecss`) | complete (static plugin) |  |
| Quasar (`quasar`) | patterns; resolveConfig not ported (default entries used) |  |
| Qwik (`qwik`) | patterns; resolveConfig not ported (default entries used) |  |
| Railway (`railway`) | patterns; resolveConfig not ported (default entries used) |  |
| Raycast (`raycast`) | patterns; resolveConfig not ported (default entries used) |  |
| React Cosmos (`react-cosmos`) | patterns; resolveConfig not ported (default entries used) |  |
| React Email (`react-email`) | complete (static plugin) |  |
| React Native (`react-native`) | patterns; resolveConfig not ported (default entries used) |  |
| React Router (`react-router`) | patterns; resolveConfig not ported (default entries used) |  |
| Relay (`relay`) | patterns; resolveConfig not ported (default entries used) |  |
| Release It! (`release-it`) | ported | generated; knip |
| Remark (`remark`) | ported | knip |
| Remix (`remix`) | complete (static plugin) |  |
| Rolldown (`rolldown`) | ported | knip, unhead |
| Rollup (`rollup`) | ported | unhead |
| Rsbuild (`rsbuild`) | patterns; resolveConfig not ported (default entries used) |  |
| Rslib (`rslib`) | ported |  |
| Rspack (`rspack`) | patterns; resolveConfig not ported (default entries used) |  |
| Rstest (`rstest`) | patterns; resolveConfig not ported (default entries used) |  |
| Sanity (`sanity`) | complete (static plugin) |  |
| Semantic Release (`semantic-release`) | ported | generated |
| Sentry (`sentry`) | complete (static plugin) |  |
| Serverless Framework (`serverless-framework`) | patterns; resolveConfig not ported (default entries used) |  |
| simple-git-hooks (`simple-git-hooks`) | patterns; resolveConfig not ported (default entries used) |  |
| size-limit (`size-limit`) | patterns; resolve() not ported |  |
| @solidjs/vite-plugin (`solidjs-vite-plugin`) | patterns; resolveConfig not ported (default entries used) |  |
| SST (`sst`) | patterns; resolveConfig not ported (default entries used) |  |
| Starlight (`starlight`) | ported | knip |
| Stencil (`stencil`) | patterns; resolveConfig not ported (default entries used) |  |
| Storybook (`storybook`) | ported | generated |
| Stryker (`stryker`) | patterns; resolveConfig not ported (default entries used) |  |
| Stylelint (`stylelint`) | ported | generated |
| Svelte (`svelte`) | complete (static plugin) | generated; unhead, uvu |
| @sveltejs/package (`sveltejs-package`) | complete (static plugin) |  |
| SvelteKit (`sveltekit`) | patterns; resolveConfig not ported (default entries used) |  |
| SVGO (`svgo`) | complete (static plugin) |  |
| SVGR (`svgr`) | patterns; resolveConfig not ported (default entries used) |  |
| SWC (`swc`) | patterns; resolveConfig not ported (default entries used) |  |
| Syncpack (`syncpack`) | complete (static plugin) |  |
| Tailwind (`tailwind`) | complete (static plugin) | unhead |
| TanStack Router (`tanstack-router`) | patterns; resolveConfig not ported (default entries used) |  |
| Taskfile (`taskfile`) | patterns; resolveConfig not ported (default entries used) |  |
| Tauri (`tauri`) | patterns; resolveConfig not ported (default entries used) |  |
| Temporal.io (`temporal`) | complete (static plugin) |  |
| textlint (`textlint`) | patterns; resolveConfig not ported (default entries used) |  |
| Travis CI (`travis`) | patterns; resolveConfig not ported (default entries used) |  |
| ts-node (`ts-node`) | complete (static plugin) |  |
| tsd (`tsd`) | patterns; resolveConfig not ported (default entries used) |  |
| tsdown (`tsdown`) | patterns; resolveConfig not ported (default entries used) | changesets |
| tsrs (`tsrs`) | patterns; resolveConfig not ported (default entries used) |  |
| tsup (`tsup`) | ported | generated |
| tsx (`tsx`) | ported (hand-written) |  |
| Turborepo (`turbo`) | ported |  |
| TypeDoc (`typedoc`) | ported (hand-written) | node-glob, node-lru-cache, node-tar |
| TypeScript (`typescript`) | ported (hand-written) | generated; chalk, changesets, defu, execa +10 |
| TypeScript Content Mapper (`typescript-content-mapper`) | patterns; resolveConfig not ported (default entries used) |  |
| unbuild (`unbuild`) | ported | defu, scule, uncrypto, unhead |
| UnoCSS (`unocss`) | complete (static plugin) |  |
| unplugin-auto-import (`unplugin-auto-import`) | complete (static plugin) | unhead |
| unplugin-icons (`unplugin-icons`) | patterns; resolve() not ported | changesets |
| unplugin-vue-components (`unplugin-vue-components`) | complete (static plugin) | unhead |
| @intlify/unplugin-vue-i18n (`unplugin-vue-i18n`) | complete (static plugin) |  |
| unplugin-vue-markdown (`unplugin-vue-markdown`) | complete (static plugin) |  |
| unplugin-vue-router (`unplugin-vue-router`) | complete (static plugin) | unhead |
| Varlock (`varlock`) | patterns; resolve() not ported |  |
| Vercel (`vercel`) | complete (static plugin) |  |
| Vercel OG (`vercel-og`) | complete (static plugin) |  |
| Vike (`vike`) | complete (static plugin) |  |
| Vite (`vite`) | ported | generated; changesets, defu, scule, superjson +2 |
| vite-plugin-pages (`vite-plugin-pages`) | patterns; resolveConfig not ported (default entries used) |  |
| vite-plugin-pwa (`vite-plugin-pwa`) | patterns; resolveConfig not ported (default entries used) |  |
| vite-plugin-vue-layouts-next (`vite-plugin-vue-layouts-next`) | patterns; resolveConfig not ported (default entries used) |  |
| vite-plus (`vite-plus`) | patterns; resolveConfig not ported (default entries used) |  |
| @vite-pwa/assets-generator (`vite-pwa-assets-generator`) | complete (static plugin) |  |
| VitePress (`vitepress`) | complete (static plugin) | changesets |
| Vitest (`vitest`) | ported | generated; changesets, defu, scule, superjson +2 |
| Vue (`vue`) | patterns; resolveConfig not ported (default entries used) | generated; changesets, unhead |
| WebdriverIO (`webdriver-io`) | patterns; resolveConfig not ported (default entries used) |  |
| webpack (`webpack`) | patterns; resolveConfig not ported (default entries used) | knip, unhead |
| Wireit (`wireit`) | patterns; resolveConfig not ported (default entries used) |  |
| Wrangler (`wrangler`) | patterns; resolveConfig not ported (default entries used) |  |
| WXT (`wxt`) | patterns; resolveConfig not ported (default entries used) |  |
| xo (`xo`) | ported | chalk, execa, got, ky +1 |
| Yarn (`yarn`) | patterns; resolveConfig not ported (default entries used) |  |
| yorkie (`yorkie`) | patterns; resolveConfig not ported (default entries used) |  |
| zx (`zx`) | complete (static plugin) |  |
