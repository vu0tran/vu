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
- **Plugin visitors** (knip's `registerVisitors`, for the plugins enabled in any workspace):
  `jest.mock()` and the other module methods of Jest (virtual mocks skipped), `vi.mock(import())` /
  `rs.mock(import())` with a factory, scripts run by execa, zx and nano-spawn, `import.meta.glob`
  (Vite; `?raw` globs as program files), `require.context` (webpack, Rspack), `fs/promises` `glob`
  (Node.js), pino transports, knex clients.
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
Strings or regular expressions where knip takes both. `ignoreExportsUsedInFile` (`true` or per symbol
type) counts an export referenced in its own file as used, from the same reference positions knip's
localRefs visitor reads. Not read: `compilers` (custom compiler functions), `cycles` (see Gaps).
Absolute paths in a loaded JavaScript config (`path.resolve(__dirname, ...)`) come back
project-relative, so aliases and entries built from them work. TOML configs (`wrangler.toml`,
`netlify.toml`, `Tauri.toml`) are read by a small TOML reader (`toml.vu`).

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
| `--reporter` (repeatable), `--output-file` | `symbols` (default), `compact`, `json`, `markdown`, `codeowners`, `disclosure`, `github-actions`, `codeclimate`, `sarif`; not `cycles`, nor a path to a custom reporter module |
| `--fix`, `--fix-type`, `--allow-remove-files`, `--format` | as knip for exports, types, default exports, dependencies (package.json rewritten in its own indentation) and files; `--format` accepted, no formatter run |
| `--no-progress`, `--debug`, `--performance`, `--memory`, `--trace*`, `--duration` | accepted, no output |
| `--cache`, `--cache-location` | accepted; vknip has no cache (its full run is faster than knip's cached one) |
| `--watch`, `--use-tsconfig-files`, `--preprocessor`, `--cycles` | accepted, no effect (see Gaps) |
| `--jobs N` | vknip only: parser threads |

knip 6 has no `--include-libs` (it was removed upstream), so there is nothing to port.

## Plugins

All 202 of knip's plugins are in a table generated from knip itself (`tools/dump_plugins.mjs` loads
each plugin and writes its enablers, config file patterns, entry, production and project patterns;
`tools/gen_plugins.py` turns that into `plugins.vu`). So every plugin is enabled when knip enables it
(dependencies, regular-expression enablers, root-only plugins, `isEnabled` checks that look at files)
and contributes its config files, entry, production and project patterns. What a plugin finds by
running its `resolveConfig` (reading the loaded config) is ported plugin by plugin:

- **Ported**: what 160 of the 202 plugins do (resolveConfig, resolveFromAST, resolve and visitors,
  as far as each has them), among them Vite/Vitest, Next.js (config functions called with the build
  phase; read from the AST when the config doesn't load), Nuxt (srcDir/app entries, modules, layers,
  aliases, `.nuxt` types and paths), webpack and Rspack and Rsbuild (config, rule and entry functions
  called by the node process, loaders, ProvidePlugin, aliases), Docusaurus, SvelteKit, React Router
  (routes.ts loaded), Expo and Expo Router, Storybook, Jest, ESLint (legacy and flat configs), Karma,
  Electron Forge, Serverless, GraphQL Codegen, Prisma, Metro, Tauri, Netlify, Wrangler, Drizzle and
  the small ones; `filterTransitiveDependencies` (Prettier, Oxlint, Metro,
  webpack); configs that only re-export a package aren't loaded (`isExternalReExportsOnly`).
- **Partly ported** (42): some part isn't, listed in the coverage table at the end: the custom
  element and `styleUrls` visitors (Angular, Lit, Stencil, FAST, Catalyst, which need decorators the
  parser keeps only in the linter's mode), and the resolveConfig of Lefthook, tsdown, Bun, Eleventy,
  Gatsby, textlint, Relay, rstest, Storybook's AST part, xo's AST part, Quasar, Qwik, Marko, mise,
  moonrepo, Taskfile, Nx's executors, and a dozen rarely used ones. Where resolveConfig isn't ported
  and the plugin has a config file, its default entry patterns are used.
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

After this round (knip3; baseline in parentheses: the corpus fetched again with
`test/fetch_corpus.sh`, knip 6.44.1 run again, its default output the same as the cached one):

| reporter | identical runs |
|---|---:|
| default (symbols), stdout + stderr + exit code | 23/23 (21) |
| `--reporter json` | 23/23 (21) |
| `--reporter compact` | 23/23 (21) |
| `--reporter markdown` | 23/23 (21) |
| `--reporter disclosure` | 23/23 (20) |
| `--reporter github-actions` | 23/23 (not implemented) |
| `--reporter sarif` | 23/23 (not implemented) |
| `--reporter codeclimate` | 23/23 (not implemented) |
| `--reporter codeowners` | 1/23 (stderr is knip's crash; stdout and exit code 22/23, see below) |

| issue type | knip found | vknip: same | missing | extra |
|---|---:|---:|---:|---:|
| Unused files | 948 | 948 | 0 (0) | 0 (4) |
| Unused dependencies | 19 | 19 | 0 | 0 |
| Unused devDependencies | 75 | 75 | 0 | 0 (3) |
| Referenced optional peerDependencies | 3 | 3 | 0 | 0 |
| Unlisted dependencies | 58 | 58 | 0 | 0 |
| Unlisted binaries | 7 | 7 | 0 | 0 |
| Unresolved imports | 6 | 6 | 0 | 0 |
| Unused exports | 262 | 262 | 0 (79) | 0 (1) |
| Unused exported types | 170 | 170 | 0 (5) | 0 (1) |
| Duplicate exports | 11 | 11 | 0 | 0 |

What the baseline differences were:

- **unhead** (79 exports, 5 types, 4 files, 2 devDependencies): a Vitest project config
  (`bench/vitest.config.ts`) aliased `@unhead/schema-org` to `path.resolve(__dirname, ...)`; the
  absolute path was joined as if it were relative, so the alias never matched, the schema-org and vue
  sources it reached looked unused, and their exports weren't reported. Absolute paths in loaded
  configs are now made project-relative by the loader. The rest was Nuxt: its resolveConfig (ported:
  `app/app.vue` of a fixture was an entry) and the load error knip prints for a Nuxt config whose
  tsconfig extends a `.nuxt` file that doesn't exist.
- **changesets** (1 devDependency): unplugin-icons' `resolve()` ignores `@iconify-json/*`; the
  `await using` declarations that caused the rest before were already parsed by `ts/parse.vu`.

Orders knip doesn't keep: its JSON, markdown and codeclimate reports list unused files in the order
its asynchronous directory crawler meets them, which changes from run to run (three runs on uvu gave
three different orders); its default report sorts them. Runs whose issues are the same but in another
order count as identical (`cmp_corpus.py` labels them). The compact and codeowners reporters sort with
comparators that aren't consistent for equal paths (`a > b ? 1 : -1`), so the order they print depends
on V8's TimSort steps: `jssort.vu` reproduces V8's algorithm (checked against node on 300 arrays of up
to 3,000 items). codeowners: knip crashes with a stack trace when `.github/CODEOWNERS` is missing (21
projects) and with a TypeError on changesets (an empty issue group); vknip prints the same
`Error: ENOENT ...` line and exit code for the first, and the report for the second.

The previous single-package corpus (the 20 libraries above plus microsoft/vscode, see git history of
this file) is unchanged: vscode was 12,666 of 12,667 lines identical before this work; it wasn't re-run
(its checkout was removed for disk space).

**Generated projects**, each written to exercise one feature (`test/cases*.py`):

| set | what | identical |
|---|---|---:|
| `cases.py`, `cases2.py`, `random_cases.py` | the graph, exports, dependencies, scripts (first rewrite) | 82/82 |
| `cases3.py` | configuration files, the schema, workspaces, `--workspace`, the flags, every reporter, rules, hints, exit codes | 84/84 runs |
| `cases4.py` | plugins (first ports), config load errors | 25/25 runs |
| `cases5.py` | `--fix` and `--fix-type`, files compared after the fix | 21/21 runs |
| `cases6.py` | catalogs, compilers, yarn globs, `ignoreWorkspaces`, tags, `ignoreExportsUsedInFile` | 18/18 runs |
| `cases7.py` | the plugins ported in this round (Next.js, webpack, Nuxt, flat ESLint, Expo, Docusaurus, SvelteKit, React Router, Rsbuild, Karma, Serverless, 40 more), with `--production` | 46/46 runs |
| `cases8.py` | the visitors: mocks, execa/zx/nano-spawn, `import.meta.glob`, `require.context`, fs glob, pino, knex | 9/9 runs |

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

7. Corpus again (knip3 baseline): absolute paths from loaded configs (79 missing exports in unhead);
   Nuxt's resolveConfig; plugin `resolve()` ignores; a plugin's own ignores gave "Remove from
   ignoreUnresolved" hints.
8. Reporters on the corpus: compact and codeowners orders (V8 TimSort), duplicates joined with ", " in
   disclosure, codeowners with no CODEOWNERS file; then github-actions (the unconfigured hints are the
   symbols reporter's own), codeclimate (exports analyzed in the graph's order), sarif.
9. Plugins (cases7, written per plugin from knip's sources, 46 runs): a workspace's own package name
   in a plugin input resolved through vknip's workspace map where node's resolver (knip's) doesn't;
   Nuxt `alias` folders are checked from the working folder; an Astro frontmatter of two `---` lines
   crashed vknip (slice out of bounds); a YAML config knip can't parse loads in vknip (see Gaps).
10. Visitors (cases8): `?raw` `import.meta.glob` files are program files (used, exports analyzed).
11. `ignoreExportsUsedInFile` (3 cases with every reference position): found nothing.
12. Speed: the new code showed in callgrind (see Benchmark); fixed, then the corpus, reporters and
    all generated sets again: nothing.

## Benchmark

CPU time (user + system of the process and everything it waited for, so vknip's node process that
loads JavaScript configs counts, and both of its threads), best of 3 runs for knip 6.44.1 (Node 22),
best of 5 for vknip (release build), measured in this round on the 2-core machine shared with other
jobs (load average 1.1 to 1.5 during the runs). "before" is vknip at the start of the round (e9b2fe3),
run interleaved with the current one.

| project | files | knip CPU s | vknip CPU s | CPU ratio | vknip before CPU s |
|---|---:|---:|---:|---:|---:|
| chalk | 20 | 1.00 | 0.011 | 91x | 0.010 |
| defu | 9 | 1.02 | 0.010 | 102x | 0.010 |
| dequal | 9 | 0.89 | 0.007 | 127x | 0.007 |
| execa | 639 | 1.34 | 0.036 | 37x | 0.035 |
| kleur | 13 | 0.93 | 0.009 | 103x | 0.009 |
| klona | 37 | 0.97 | 0.008 | 121x | 0.008 |
| ky | 98 | 1.71 | 0.053 | 32x | 0.056 |
| mitt | 3 | 0.96 | 0.010 | 96x | 0.010 |
| node-lru-cache | 49 | 1.01 | 0.013 | 78x | 0.013 |
| p-queue | 17 | 1.29 | 0.021 | 61x | 0.020 |
| scule | 4 | 0.95 | 0.011 | 86x | 0.012 |
| superjson | 20 | 1.10 | 0.014 | 79x | 0.015 |
| uncrypto | 5 | 0.96 | 0.010 | 96x | 0.010 |
| uvu | 93 | 0.98 | 0.012 | 82x | 0.012 |
| express | 142 | 1.57 | 0.035 | 45x | 0.036 |
| fastify | 304 | 3.00 | 0.114 | 26x | 0.118 |
| got | 98 | 2.40 | 0.096 | 25x | 0.101 |
| koa | 82 | 1.34 | 0.022 | 61x | 0.023 |
| node-glob | 59 | 1.14 | 0.013 | 88x | 0.013 |
| node-tar | 73 | 1.21 | 0.023 | 53x | 0.023 |
| changesets | 164 | 2.96 | 0.521 | 6x | 0.508 |
| knip | 4678 | 4.24 | 0.590 | 7x | 0.565 |
| unhead | 860 | 9.26 | 5.165 | 2x | 5.039 |

Against the start of the round the CPU time is the same within noise (total 6.65 s before, 6.80 s
after; unhead, which now loads its Nuxt configs through node as knip does, 5.04 to 5.17 s). Instructions
(callgrind, builds with `VU_MARCH=x86-64-v2`, one run each): node-glob 55.70 M before, 55.88 M after
(+0.3%), fastify 548.4 M to 550.1 M (+0.3%), changesets 1,048.6 M to 1,057.6 M (+0.9%), knip
2,259.5 M to 2,265.3 M (+0.3%); what was added is the visitors and the config reading this round
ported. Two regressions the first measurement showed were fixed: the visitors searched each file's
source with memmem for a dozen names (now they look the names up in the parser's interned names), and
filterTransitiveDependencies read the JSON schema an `.oxlintrc.json` names on every run (now only
when a dependency could become optional), which had made node-glob 2.5 times slower.

## Gaps

- **Plugins**: 42 of 202 have a part not ported (the coverage table lists which): the custom element
  and `styleUrls` visitors (Angular, Lit, Stencil, FAST, Catalyst: the parser keeps decorators only in
  vlint's mode), and the resolveConfig or resolveFromAST of Lefthook, tsdown, Bun, Eleventy, Gatsby,
  textlint, Relay, rstest, Storybook (AST part), xo (AST part), Quasar, Qwik, Marko, mise, moonrepo,
  Taskfile, Nx executors, Astro Markdoc, Capacitor, filesystem-routing, Flue, Ladle, LintHTML,
  Lunaria, Nest, npm-package-json-lint, OpenClaw, osls, Playwright CT, Railway, Raycast, React Cosmos,
  @solidjs/vite-plugin, TypeScript Content Mapper, Varlock, vite-plugin-pages and
  vite-plugin-vue-layouts-next. Their default entry patterns are used.
- **Nuxt and Vue auto-imports**: knip's compilers that add the imports Nuxt (`.nuxt/imports.d.ts`,
  `components.d.ts`) and unplugin-auto-import / unplugin-vue-components generate, including template
  tags and identifiers read with `vue/compiler-sfc`. Without `.nuxt` (as in the corpus, installed
  with `--ignore-scripts`) knip's compilers add nothing, so the corpus doesn't show it.
- `--cycles` and the `cycles` reporter and config; custom `compilers`; less and stylus compilers;
  custom reporter and preprocessor modules; `--watch`; `--trace*` and `--performance` output;
  fixes of enum and namespace members and of catalog entries; published type dependencies of
  non-private packages.
- A YAML config knip's parser rejects (say an implicit map key) loads in vknip instead of giving
  knip's "Error loading ..." message.
- The JSON, markdown and codeclimate reporters list unused files in vknip's crawl order (by depth,
  folder by folder, names sorted), knip in its asynchronous crawler's order, which varies.
- vscode wasn't re-measured: with the 23-project corpus installed the disk had about 1.4 GB free, and
  its checkout with dependencies wasn't fetched (how much it needs wasn't measured).

## Tests

`test/` has the scripts: `cmp_corpus.py` compares real projects with knip (`WORK=dir`, knip's output
cached in `dir/ref`), `gen_cmp.py CASES OUT` writes the generated projects of a cases file, runs knip
once (cached) and vknip on each command line, and compares stdout, stderr, exit code and, for `--fix`
cases, the files left behind; `run_cases.py` and `cmp_cases.sh` do the same for the first sets;
`bench.py` times both; `globtest.vu` checks the glob matcher against picomatch, `yamltest.vu` the
YAML reader against the `yaml` package (102 files of the corpus, identical).

## Plugin coverage

Generated from knip's plugin list and vknip's code (`tools/plugtab.py`): what each
plugin has (resolveConfig, resolveFromAST, resolve, visitors) and whether vknip ports it. "tested on"
names the generated cases and the corpus projects whose dependencies enable the plugin. 160 plugins
are complete, 42 have a part not ported.

| plugin | status | tested on |
|---|---|---|
| Angular (`angular`) | resolveConfig ported; visitors NOT ported | unhead |
| Astro (`astro`) | resolveFromAST ported; resolve ported | generated; knip |
| Astro DB (`astro-db`) | complete (static plugin) |  |
| Astro Markdoc (`astro-markdoc`) | resolveConfig NOT ported |  |
| astro-og-canvas (`astro-og-canvas`) | resolve ported |  |
| Ava (`ava`) | resolveConfig ported | ky, uvu |
| Babel (`babel`) | resolveConfig ported | generated; uvu |
| Biome (`biome`) | resolveConfig ported |  |
| Borp (`borp`) | ported (hand-written) | fastify |
| Buf (`buf`) | resolveConfig ported |  |
| bumpp (`bumpp`) | complete (static plugin) | unhead |
| Bun (`bun`) | resolveConfig NOT ported; resolve NOT ported |  |
| c8 (`c8`) | complete (static plugin) | generated |
| Capacitor (`capacitor`) | resolveConfig NOT ported |  |
| Catalyst (`catalyst`) | visitors NOT ported |  |
| Changelogen (`changelogen`) | complete (static plugin) | defu, scule, uncrypto |
| Changelogithub (`changelogithub`) | complete (static plugin) |  |
| Changesets (`changesets`) | resolveConfig ported | generated; changesets |
| Commitizen (`commitizen`) | resolveConfig ported | generated |
| commitlint (`commitlint`) | resolveConfig ported | generated |
| Convex (`convex`) | resolveConfig ported | generated |
| create-typescript-app (`create-typescript-app`) | complete (static plugin) |  |
| CSpell (`cspell`) | resolveConfig ported | generated |
| Cucumber (`cucumber`) | resolveConfig ported |  |
| Cypress (`cypress`) | resolveConfig ported | generated |
| Danger (`danger`) | complete (static plugin) |  |
| dependency-cruiser (`dependency-cruiser`) | complete (static plugin) |  |
| Docusaurus (`docusaurus`) | resolveConfig ported; resolve ported | generated |
| dotenv (`dotenv`) | complete (static plugin) | generated |
| Drizzle (`drizzle`) | resolveConfig ported |  |
| Electron Forge (`electron-forge`) | resolveConfig ported |  |
| electron-vite (`electron-vite`) | resolveConfig ported | generated |
| Eleventy (`eleventy`) | resolveConfig NOT ported |  |
| esbuild (`esbuild`) | resolveFromAST ported | generated; node-glob, node-lru-cache, node-tar, unhead +1 |
| ESLint (`eslint`) | resolveConfig ported; resolveFromAST ported | generated; changesets, express, fastify, mitt +3 |
| eve (`eve`) | complete (static plugin) |  |
| execa (`execa`) | visitors ported | generated; chalk |
| Expo (`expo`) | resolveConfig ported; resolve ported | generated |
| Expo Router (`expo-router`) | resolveConfig ported | generated |
| Expressive Code (`expressive-code`) | complete (static plugin) | knip |
| FAST (`fast`) | visitors NOT ported |  |
| filesystem-routing (`filesystem-routing`) | resolveFromAST NOT ported |  |
| Flue (`flue`) | resolveFromAST NOT ported |  |
| Fumadocs (`fumadocs`) | complete (static plugin) |  |
| Gatsby (`gatsby`) | resolveConfig NOT ported |  |
| GitHub Action (`github-action`) | resolveConfig ported | generated |
| GitHub Actions (`github-actions`) | ported (hand-written) |  |
| glob (`glob`) | complete (static plugin) |  |
| GraphQL Codegen (`graphql-codegen`) | resolveConfig ported |  |
| Hardhat (`hardhat`) | resolve ported |  |
| husky (`husky`) | ported (hand-written) | generated |
| i18next Parser (`i18next-parser`) | complete (static plugin) |  |
| Jasmine (`jasmine`) | resolveConfig ported | generated |
| Jest (`jest`) | resolveConfig ported; visitors ported | generated; uvu |
| Karma (`karma`) | resolveConfig ported | generated |
| Knex (`knex`) | resolveConfig ported; visitors ported | generated |
| kysely-codegen (`kysely-codegen`) | complete (static plugin) |  |
| Ladle (`ladle`) | resolveConfig NOT ported |  |
| laravel-vite-plugin (`laravel-vite-plugin`) | resolveFromAST ported | generated |
| Lefthook (`lefthook`) | resolveConfig NOT ported |  |
| Lingui (`lingui`) | complete (static plugin) |  |
| lint-staged (`lint-staged`) | resolveConfig ported | generated; changesets |
| LintHTML (`linthtml`) | resolveConfig NOT ported |  |
| Lit (`lit`) | visitors NOT ported |  |
| lockfile-lint (`lockfile-lint`) | complete (static plugin) |  |
| Lost Pixel (`lost-pixel`) | complete (static plugin) |  |
| Lunaria (`lunaria`) | resolveConfig NOT ported |  |
| markdownlint (`markdownlint`) | resolveConfig ported | generated; fastify |
| Marko (`marko`) | resolveConfig NOT ported |  |
| Mastra (`mastra`) | complete (static plugin) |  |
| MCP (`mcp`) | ported (hand-written) |  |
| MDX (`mdx`) | resolveConfig ported | generated; knip |
| mdxlint (`mdxlint`) | resolveConfig ported | knip |
| Metro (`metro`) | resolveConfig ported | generated |
| mise (`mise`) | resolveConfig NOT ported |  |
| Mocha (`mocha`) | resolveConfig ported | generated; express, mitt, uvu |
| moonrepo (`moonrepo`) | resolveConfig NOT ported |  |
| Mock Service Worker (`msw`) | resolveConfig ported | generated |
| nano-spawn (`nano-spawn`) | visitors ported | generated |
| Nano Staged (`nano-staged`) | resolveConfig ported | generated |
| Nest (`nest`) | resolveConfig NOT ported |  |
| Netlify (`netlify`) | resolveConfig ported |  |
| Next.js (`next`) | resolveConfig ported; resolveFromAST ported | generated |
| next-intl (`next-intl`) | complete (static plugin) |  |
| Next.js MDX (`next-mdx`) | resolveFromAST ported |  |
| Nitro (`nitro`) | resolveConfig ported; resolve ported |  |
| Node.js (`node`) | ported (hand-written); visitors ported |  |
| node-modules-inspector (`node-modules-inspector`) | complete (static plugin) |  |
| nodemon (`nodemon`) | complete (static plugin) |  |
| npm-package-json-lint (`npm-package-json-lint`) | resolveConfig NOT ported |  |
| Nuxt (`nuxt`) | resolveConfig ported; resolve ported | generated; unhead |
| @nuxtjs/i18n (`nuxtjs-i18n`) | complete (static plugin) |  |
| Nx (`nx`) | resolveConfig ported; resolve NOT ported | generated |
| nyc (`nyc`) | resolveConfig ported | express |
| oclif (`oclif`) | resolveConfig ported | generated |
| openapi-ts (`openapi-ts`) | complete (static plugin) |  |
| OpenClaw (`openclaw`) | resolveConfig NOT ported; resolveFromAST NOT ported |  |
| orval (`orval`) | resolveFromAST ported | generated |
| osls (`osls`) | resolveConfig NOT ported |  |
| Oxfmt (`oxfmt`) | complete (static plugin) | changesets, defu, knip |
| Oxlint (`oxlint`) | resolveConfig ported | defu, knip, node-glob, node-lru-cache +1 |
| Panda CSS (`panda-css`) | resolveConfig ported |  |
| Parcel (`parcel`) | resolveConfig ported | generated |
| Payload CMS (`payload`) | resolveConfig ported | generated |
| pino (`pino`) | visitors ported | generated; fastify |
| Playwright (`playwright`) | resolveConfig ported | generated; unhead |
| Playwright for components (`playwright-ct`) | resolveConfig NOT ported |  |
| playwright-test (`playwright-test`) | complete (static plugin) |  |
| Plop (`plop`) | complete (static plugin) |  |
| pm2 (`pm2`) | resolveConfig ported | generated |
| pnpm (`pnpm`) | resolveConfig ported | generated |
| PostCSS (`postcss`) | resolveConfig ported | generated |
| pre-commit (`pre-commit`) | resolve ported | generated |
| Preconstruct (`preconstruct`) | resolveConfig ported | generated |
| Prettier (`prettier`) | resolveConfig ported | generated; knip, mitt, node-glob, node-lru-cache +3 |
| Prisma (`prisma`) | resolveConfig ported | generated |
| PurgeCSS (`purgecss`) | complete (static plugin) |  |
| Quasar (`quasar`) | resolveFromAST NOT ported |  |
| Qwik (`qwik`) | resolveFromAST NOT ported |  |
| Railway (`railway`) | resolveFromAST NOT ported |  |
| Raycast (`raycast`) | resolveConfig NOT ported |  |
| React Cosmos (`react-cosmos`) | resolveConfig NOT ported |  |
| React Email (`react-email`) | complete (static plugin) |  |
| React Native (`react-native`) | resolveConfig ported; resolve ported | generated |
| React Router (`react-router`) | resolveConfig ported | generated |
| Relay (`relay`) | resolveConfig NOT ported |  |
| Release It! (`release-it`) | resolveConfig ported | generated; knip |
| Remark (`remark`) | resolveConfig ported | knip |
| Remix (`remix`) | complete (static plugin) |  |
| Rolldown (`rolldown`) | resolveFromAST ported | knip, unhead |
| Rollup (`rollup`) | resolveFromAST ported | unhead |
| Rsbuild (`rsbuild`) | resolveConfig ported |  |
| Rslib (`rslib`) | resolveFromAST ported |  |
| Rspack (`rspack`) | resolveConfig ported; visitors ported | generated |
| Rstest (`rstest`) | resolveConfig NOT ported; visitors ported |  |
| Sanity (`sanity`) | complete (static plugin) |  |
| Semantic Release (`semantic-release`) | resolveConfig ported | generated |
| Sentry (`sentry`) | complete (static plugin) |  |
| Serverless Framework (`serverless-framework`) | resolveConfig ported |  |
| simple-git-hooks (`simple-git-hooks`) | resolveConfig ported | generated |
| size-limit (`size-limit`) | resolve ported |  |
| @solidjs/vite-plugin (`solidjs-vite-plugin`) | resolveFromAST NOT ported |  |
| SST (`sst`) | resolveFromAST ported | generated |
| Starlight (`starlight`) | resolveFromAST ported | knip |
| Stencil (`stencil`) | resolveFromAST ported; visitors NOT ported |  |
| Storybook (`storybook`) | resolveConfig ported; resolveFromAST NOT ported | generated |
| Stryker (`stryker`) | resolveConfig ported |  |
| Stylelint (`stylelint`) | resolveConfig ported | generated |
| Svelte (`svelte`) | complete (static plugin) | generated; unhead, uvu |
| @sveltejs/package (`sveltejs-package`) | complete (static plugin) |  |
| SvelteKit (`sveltekit`) | resolveFromAST ported | generated |
| SVGO (`svgo`) | complete (static plugin) |  |
| SVGR (`svgr`) | resolveConfig ported |  |
| SWC (`swc`) | resolveConfig ported |  |
| Syncpack (`syncpack`) | complete (static plugin) |  |
| Tailwind (`tailwind`) | complete (static plugin) | unhead |
| TanStack Router (`tanstack-router`) | resolveConfig ported |  |
| Taskfile (`taskfile`) | resolveConfig NOT ported |  |
| Tauri (`tauri`) | resolveConfig ported |  |
| Temporal.io (`temporal`) | complete (static plugin) |  |
| textlint (`textlint`) | resolveConfig NOT ported |  |
| Travis CI (`travis`) | resolveConfig ported |  |
| ts-node (`ts-node`) | complete (static plugin) | generated |
| tsd (`tsd`) | resolveConfig ported | generated |
| tsdown (`tsdown`) | resolveConfig NOT ported; resolveFromAST ported | changesets |
| tsrs (`tsrs`) | ported (hand-written) |  |
| tsup (`tsup`) | resolveConfig ported; resolveFromAST ported | generated |
| tsx (`tsx`) | ported (hand-written) | generated |
| Turborepo (`turbo`) | resolve ported |  |
| TypeDoc (`typedoc`) | ported (hand-written) | node-glob, node-lru-cache, node-tar |
| TypeScript (`typescript`) | ported (hand-written) | generated; chalk, changesets, defu, execa +10 |
| TypeScript Content Mapper (`typescript-content-mapper`) | resolveConfig NOT ported |  |
| unbuild (`unbuild`) | resolveConfig ported | defu, scule, uncrypto, unhead |
| UnoCSS (`unocss`) | complete (static plugin) |  |
| unplugin-auto-import (`unplugin-auto-import`) | complete (static plugin) | unhead |
| unplugin-icons (`unplugin-icons`) | resolve ported | generated; changesets |
| unplugin-vue-components (`unplugin-vue-components`) | complete (static plugin) | unhead |
| @intlify/unplugin-vue-i18n (`unplugin-vue-i18n`) | complete (static plugin) |  |
| unplugin-vue-markdown (`unplugin-vue-markdown`) | complete (static plugin) |  |
| unplugin-vue-router (`unplugin-vue-router`) | complete (static plugin) | unhead |
| Varlock (`varlock`) | resolve NOT ported |  |
| Vercel (`vercel`) | complete (static plugin) |  |
| Vercel OG (`vercel-og`) | complete (static plugin) |  |
| Vike (`vike`) | complete (static plugin) |  |
| Vite (`vite`) | resolveConfig ported; resolveFromAST ported; resolve ported; visitors ported | generated; changesets, defu, scule, superjson +2 |
| vite-plugin-pages (`vite-plugin-pages`) | resolveFromAST NOT ported; resolve ported |  |
| vite-plugin-pwa (`vite-plugin-pwa`) | resolveFromAST ported | generated |
| vite-plugin-vue-layouts-next (`vite-plugin-vue-layouts-next`) | resolveFromAST NOT ported |  |
| vite-plus (`vite-plus`) | resolveFromAST ported | generated |
| @vite-pwa/assets-generator (`vite-pwa-assets-generator`) | complete (static plugin) |  |
| VitePress (`vitepress`) | complete (static plugin) | changesets |
| Vitest (`vitest`) | resolveConfig ported; visitors ported | generated; changesets, defu, scule, superjson +2 |
| Vue (`vue`) | resolveConfig ported | generated; changesets, unhead |
| WebdriverIO (`webdriver-io`) | resolveConfig ported |  |
| webpack (`webpack`) | resolveConfig ported; visitors ported | generated; knip, unhead |
| Wireit (`wireit`) | resolveConfig ported | generated |
| Wrangler (`wrangler`) | resolveConfig ported | generated |
| WXT (`wxt`) | resolveConfig ported | generated |
| xo (`xo`) | resolveConfig ported; resolveFromAST NOT ported | chalk, execa, got, ky +1 |
| Yarn (`yarn`) | resolveConfig ported |  |
| yorkie (`yorkie`) | resolveConfig ported | generated |
| zx (`zx`) | visitors ported | generated |
