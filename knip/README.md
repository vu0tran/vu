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

## Install

Releases are tagged `vknip-vX.Y.Z` (vknip's own versions; every one behaves as knip 6.44.1). knip is
an npm package, and so is vknip: `@vu0tran/vknip` has the commands `vknip` and `knip`, so switching
a project is one line in package.json:

```diff
   "devDependencies": {
-    "knip": "^6.44.1"
+    "knip": "npm:@vu0tran/vknip@^0.1.0"
   }
```

(or `npm install --save-dev @vu0tran/vknip`). The package also has the types of `import type {
KnipConfig } from "knip"`, `defineConfig` from `knip/config` and knip's `schema.json`, written for
vknip (the types by hand, looser than knip's), and depends on jiti, which vknip's node processes use
for JavaScript and TypeScript configs when the project has none. Linux x86-64 and ARM64 (static
binaries), macOS 12 or later; Node.js where it runs, as for knip. For machines without npm, the
release archives (`vknip-0.1.0-linux-x64.tar.gz`, ...: `vknip` and `knip`) install with
`curl -fsSL https://raw.githubusercontent.com/vu0tran/vu/main/packaging/tools/install.sh | sh -s -- vknip`;
TypeScript configs then load with the project's jiti, or Node's own type stripping (which rejects
enums and namespaces).

It follows knip's own code (graph/build.js, graph/analyze.js, the graph explorer, the import and
export visitors, DependencyDeputy, the script parser, the plugins), reading files with vtsc's
parser (`ts/scan.vu`, `ts/parse.vu`, `ts/ast.vu`, linked into this folder unchanged; exact mode keeps
node ends). Files are parsed on all cores, wave by wave as the import graph reaches them, and linked
in order as they come in; in a large project the workspaces' files are parsed ahead, while node loads
the configs (see n8n under Benchmark).

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
- **Report**: the symbols reporter as knip prints it (colors and widths of a terminal too): sections in
  knip's order, rows sorted with ICU's collation order (punctuation, digits, letters, lowercase
  first), the table's column widths, and its truncation to 120 columns (paths from the start,
  names from the end, with `…`). `--reporter json` writes knip's JSON,
  issues in knip's order (unused files as knip's crawler lists them: by workspace, by depth, folder
  by folder).

## Configuration

vknip reads the configuration knip reads, from the same places, in the same order: `knip.json`,
`knip.jsonc`, `.knip.json`, `.knip.jsonc`, `knip.ts`, `knip.js`, `knip.config.ts`, `knip.config.js`
(and the other extensions knip accepts), the `knip` field of package.json, or `--config FILE`. A
JavaScript or TypeScript configuration runs in node, as in knip: vknip keeps node processes for the
whole run, which import each file with the project's jiti (or the one installed next to its knip, or
any `jiti@2` in `node_modules/.pnpm`, looked for from the project's folder, then the working one;
native `import()` without one) and send the result back as JSON. A config that exports a function is
called (with knip's argument), and a promise is awaited. Load errors are reported as knip reports
them, and what a config prints is printed where knip would load it. The configs found up front are
loaded by up to 4 processes at once (`--jobs`, else the cores), started while vknip reads the project
when its workspaces have JavaScript configs; the ones found later go to the first process, whose
module cache already holds what earlier configs imported. A TypeScript config whose leading imports
take only a define helper from its package (`defineConfig` from `vite` and `vitest/config`,
`defineProject`, `defineWorkspace`, `defineBuildConfig` from `unbuild`, `defineConfig` from `tsdown`,
`astro/config`, `vitepress` and `@playwright/test`) gets the helper without the package being loaded,
when the import resolves to that package (its package.json names the package's repository, at a
version that has the helper, and its entry file names it): loading vite or unbuild for an identity
function took half a second each. Any other import, or a helper called in a way it doesn't cover
(`defineConfig(a, b)`), loads the file as it is.

The schema: `entry`, `project`, `paths`, `ignore`, `ignoreFiles`, `ignoreDependencies`,
`ignoreBinaries`, `ignoreMembers`, `ignoreUnresolved`, `ignoreWorkspaces`, `ignoreIssues`,
`includeEntryExports`, `rules` (`error`/`warn`/`off`), `include`/`exclude`, `tags`, `workspaces` (with
globs: `packages/*` settings apply to each matching workspace), `treatConfigHintsAsErrors`, and each
plugin's settings: `false` (off), `true` (on), a config file
pattern or list (`"vitest": "config/vitest.ts"`), or an object with `config`, `entry` and `project`.
Strings or regular expressions where knip takes both. `ignoreExportsUsedInFile` (`true` or per symbol
type) counts an export referenced in its own file as used, from the same reference positions knip's
localRefs visitor reads. `compilers` (functions run in node) and `cycles` are read too.
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
| `--config`, `--directory`, `--workspace`, `--tsConfig`, `--no-gitignore`, `--use-tsconfig-files` | as knip |
| `--production`, `--strict` | as knip (production entries and dependencies only; strict ownership, type-only imports skipped, caught optional peers) |
| `--include`, `--exclude`, `--dependencies`, `--exports`, `--files`, `--cycles` | as knip, with the rules from the configuration; `--cycles` is knip's findAllCycles (graph order, `cycles.allow`, `cycles.dynamicImports`) |
| `--include-entry-exports`, `--tags`, `--no-tag-hints`, `--treat-tag-hints-as-errors` | as knip (`@tag` and `-tag`, member tags) |
| `--no-exit-code`, `--max-issues`, `--max-show-issues` | as knip (exit code 1 when error-level issues exceed the maximum, 2 on errors) |
| `--no-config-hints`, `--treat-config-hints-as-errors` | as knip; hints are printed on stderr in knip's table |
| `--reporter` (repeatable), `--reporter-options`, `--output-file` | `symbols` (default), `compact`, `json`, `markdown`, `codeowners`, `cycles`, `disclosure`, `github-actions`, `codeclimate`, `sarif`, and a path to a custom reporter module (run in node with knip's ReporterOptions) |
| `--preprocessor`, `--preprocessor-options` | as knip (modules run in node, their output passed on) |
| `--fix`, `--fix-type`, `--allow-remove-files`, `--format` | as knip for exports, types, default exports, enum and namespace members, dependencies (package.json rewritten in its own indentation), catalog entries and files; `--format` runs the formatter knip's formatly would pick |
| `--watch` | as knip: inotify on the project's folders, each change reanalyzed, the watch reporter's screen redrawn (see Gaps for how it differs inside) |
| `--cache`, `--cache-location` | as knip's FileEntryCache (a file's analysis reused while its size and mtime stay the same); vknip also keeps the JavaScript configs' values (below) |
| `--trace`, `--trace-export`, `--trace-file`, `--trace-dependency` | knip's trees (buildExportsTree, formatTrace), and for a name a file has only through `export *` its origins as knip's resolveExportOrigins finds them (`[ambiguous]` when several, the origin's tree when one) |
| `--performance`, `--performance-fn`, `--memory`, `--memory-realtime`, `--duration` | knip's tables and formats, vknip's work timed under knip's function names |
| `--no-progress` | as knip (it, `--debug` and CI turn off the terminal's progress and redraws) |
| `--debug` | accepted; knip's debug output isn't printed (see Gaps) |
| `--jobs N`, `--debug-inputs` | vknip only: parser threads (all the cores by default) and node processes for configs (at most 4); the inputs each plugin and compiler gave |

Colors follow knip's: `FORCE_COLOR`, `NO_COLOR`, a terminal (node's styleText codes in titles, tables,
hints, compact and codeowners lines), tables as wide as the terminal. knip 6 has no `--include-libs`
(it was removed upstream), so there is nothing to port.

## Plugins

All 202 of knip's plugins are in a table generated from knip itself (`tools/dump_plugins.mjs` loads
each plugin and writes its enablers, config file patterns, entry, production and project patterns;
`tools/gen_plugins.py` turns that into `plugins.vu`). So every plugin is enabled when knip enables it
(dependencies, regular-expression enablers, root-only plugins, `isEnabled` checks that look at files)
and contributes its config files, entry, production and project patterns. What a plugin finds by
running its `resolveConfig`, `resolveFromAST`, `resolve` and visitors is ported plugin by plugin, and
all 202 are complete: the coverage table at the end (generated by `tools/plugtab.py` from knip's
plugin list and vknip's code) lists what each has and which tests reach it. Among them Vite/Vitest,
Next.js (config functions called with the build phase; read from the AST when the config doesn't
load), Nuxt (srcDir/app entries, modules, layers, aliases, `.nuxt` types and paths), webpack, Rspack
and Rsbuild (config, rule and entry functions called by the node process, loaders, ProvidePlugin,
aliases), Docusaurus, SvelteKit, React Router (routes.ts loaded), Expo and Expo Router, Storybook,
Jest, ESLint (legacy and flat configs), Angular, Lit, Stencil, FAST and Catalyst (custom element and
`styleUrls` visitors, from the parser's decorator list), Lefthook, Bun, Eleventy, Gatsby, Nx, mise,
Taskfile and the small ones; `filterTransitiveDependencies` (Prettier, Oxlint, Metro, webpack);
configs that only re-export a package aren't loaded (`isExternalReExportsOnly`).

**Compilers**: `.vue` (scripts through `vue/compiler-sfc` in node, `src` imports, scss `<style>`
imports), `.svelte`, `.astro` (frontmatter, scripts, styles), `.mdx`, `.css` with Tailwind (`@import`,
`@plugin`, `@config`, `@source`...), `.scss`/`.sass` (`@use`, `@import`, `@forward`, `url()`), less,
stylus, `.prisma`, Marko, tsrx, and the configuration's own `compilers` functions (run in node), each
enabled per workspace as knip enables it. **Auto-imports**: the imports Nuxt (`.nuxt/imports.d.ts`,
`components.d.ts`) and unplugin-auto-import / unplugin-vue-components generate, template tags and
identifiers included, as knip's compilers add them. They need the generated files: after
`nuxt prepare` (see the framework apps below).

**YAML configs** (GitHub workflows, Lefthook, mocharc, pnpm-workspace, borp...) are read by vknip's own
reader (`yaml.vu`). A file that reader could read differently from the `yaml` package knip uses, or
that `yaml` rejects (`yaml.irregular`: indentation that matches no open block, tabs, duplicate keys,
nested compact mappings, block scalar headers, anchors and aliases, tags, directives, several
documents, flow collections and quotes over several lines), is parsed by the `yaml` package in node
instead (the project's, the one next to its knip, or the npm package's own dependency), with knip's
`Error loading FILE (message)` when it rejects it.

## Parity

The whole output (stdout, stderr, exit code) of each run was compared with knip 6.44.1's
(`test/cmp_corpus.py` for real projects, `test/gen_cmp.py` and `test/cmp_cases.sh` for generated ones,
`test/cmp_fixtures.py` for knip's own test fixtures), then the issues per type.

**knip's own tests**: every fixture knip's tests use (packages/knip/test/**/*.test.ts of the knip repo,
with the options each test passes mapped to flags): **957/957** identical (688 at 98acf53, 904 at
the start of this round). The `exec('knip ...')` command lines of knip's tests (`test/cmp_cli.py`,
commands that write files skipped): 118/118 (95 at the start of this round: the other 23 were
`--trace-export` of names re-exported with `export *`).

**Real projects** (23, listed with their commits in `test/corpus.txt`, dependencies installed with
`pnpm install --ignore-scripts`): 20 libraries (chalk, defu, dequal, execa, kleur, klona, ky, mitt,
node-lru-cache, p-queue, scule, superjson, uncrypto, uvu, express, fastify, got, koa, node-glob,
node-tar) and 3 pnpm monorepos with JavaScript and TypeScript configs loaded through node (webpro-nl/knip:
7 workspaces, its own `knip.json`; changesets/changesets: 24 workspaces, 24 JS/TS config files;
unjs/unhead: 28 workspaces, 57 config files, Vue, Svelte, React, Nuxt and Angular packages). knip ran
with the project's own configuration.

| run | identical |
|---|---:|
| default (symbols), stdout + stderr + exit code | 23/23 |
| `--production` | 23/23 |
| `--strict` | 23/23 |
| `--reporter json`, `compact`, `markdown`, `disclosure`, `github-actions`, `sarif`, `codeclimate` | 23/23 each |
| `--reporter codeowners` | 1/23 (stderr is knip's crash; stdout and exit code 22/23, see below) |
| `FORCE_COLOR=1` (symbols, compact, disclosure, github-actions; `test/cmp_env.py`) | 23/23 each |
| `--cache`, 36 edit steps on fastify (`test/cmp_cache.py`: knip, vknip `--cache`, vknip) | 36/36 |

| issue type | knip found | vknip: same | missing | extra |
|---|---:|---:|---:|---:|
| Unused files | 948 | 948 | 0 | 0 |
| Unused dependencies | 19 | 19 | 0 | 0 |
| Unused devDependencies | 75 | 75 | 0 | 0 |
| Referenced optional peerDependencies | 3 | 3 | 0 | 0 |
| Unlisted dependencies | 58 | 58 | 0 | 0 |
| Unlisted binaries | 7 | 7 | 0 | 0 |
| Unresolved imports | 6 | 6 | 0 | 0 |
| Unused exports | 262 | 262 | 0 | 0 |
| Unused exported types | 170 | 170 | 0 | 0 |
| Duplicate exports | 11 | 11 | 0 | 0 |

**Framework apps** (14, also in `test/corpus.txt` with pinned commits, the folder knip runs in, the
generator run after the install, and `test/fetch_corpus.sh` fetches them), each compared in 8 runs: no
flags, `--production`, `--strict`, `--reporter json`, `--reporter compact`, `--include-entry-exports`,
`--dependencies`, `--reporter markdown`. All 112 runs identical.

| app | repository @ commit | setup |
|---|---|---|
| Nuxt | nuxt-ui-templates/starter @ 9deb447 | `nuxt prepare` |
| Nuxt | nuxt-ui-templates/dashboard @ 82afa8d | `nuxt prepare` (auto-imported components and composables: without `.nuxt`, 16 files are reported unused) |
| Next.js | nextjs/saas-starter @ 6e33e58 | |
| SvelteKit | sveltejs/realworld @ df79670 | `svelte-kit sync` (its lockfile is broken upstream: installed without it) |
| React Router | remix-run/react-router-templates @ 067adb3: default, node-custom-server, unstable_rsc-framework-mode, unstable_rsc-data-mode-vite | `react-router typegen` (not in the last) |
| Astro | satnaing/astro-paper @ befb05d | `astro sync` |
| Angular | gothinkster/angular-realworld-example-app @ d426ec8 | |
| Expo | obytes/react-native-template-obytes @ fd9b358 | |
| Storybook | storybookjs/design-system @ 0c4c043 | |
| Docusaurus | facebook/docusaurus @ 2a89055, examples/classic | installed in that folder alone |
| webpack | wbkd/webpack-starter @ 493d511 | |

Orders knip doesn't keep: its JSON, markdown and codeclimate reports list unused files in the order
its asynchronous directory crawler meets them, which changes from run to run (three runs on uvu gave
three different orders); its default report sorts them. Runs whose issues are the same but in another
order count as identical (`cmp_corpus.py` labels them). The compact and codeowners reporters sort with
comparators that aren't consistent for equal paths (`a > b ? 1 : -1`), so the order they print depends
on V8's TimSort steps: `jssort.vu` reproduces V8's algorithm (checked against node on 300 arrays of up
to 3,000 items). codeowners: knip crashes with a stack trace when `.github/CODEOWNERS` is missing (21
projects) and with a TypeError on changesets (an empty issue group); vknip prints the same
`Error: ENOENT ...` line and exit code for the first, and the report for the second.

**--watch** (`test/cmp_watch.py`): knip `--watch` and vknip `--watch` run in a terminal (a pty) on a
generated project through 12 edits (exports, new, imported and deleted files, the same contents written
again, a README, package.json, knip.json, a new folder with a file); the screen after each step and
whether it was redrawn: 13/13 identical (the time and memory of the summary line left out).

**YAML**: `test/yamlirr.vu` on 4,260 mutants of the corpus' 206 YAML files: none that the `yaml`
package rejects is read by vknip's reader (6 of the 206 originals are handed to `yaml`).

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
| `cases7.py` | plugins (Next.js, webpack, Nuxt, flat ESLint, Expo, Docusaurus, SvelteKit, React Router, Rsbuild, Karma, Serverless, 40 more), with `--production` | 46/46 runs |
| `cases8.py` | the visitors: mocks, execa/zx/nano-spawn, `import.meta.glob`, `require.context`, fs glob, pino, knex | 9/9 runs |
| `cases9.py` | tsconfig `references` (paths, baseUrl and rootDirs of the referenced config that includes the file), with `--strict` and `--production` | 11/11 runs |
| `cases10.py` | YAML configs knip's parser rejects or vknip's reader isn't sure about | 8/8 runs |
| `cases11.py` | what the framework apps showed: config files under folders named like a dependency (`webpack --config webpack/x.js`) | 5/5 runs |

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
   disclosure, codeowners with no CODEOWNERS file; then github-actions, codeclimate, sarif.
9. Plugins (cases7, 46 runs): a workspace's own package name in a plugin input resolved through
   vknip's workspace map where node's resolver (knip's) doesn't; Nuxt `alias` folders; an Astro
   frontmatter of two `---` lines crashed vknip (slice out of bounds).
10. Visitors (cases8): `?raw` `import.meta.glob` files are program files (used, exports analyzed).
11. `ignoreExportsUsedInFile` (3 cases with every reference position): found nothing.
12. Speed: the new code showed in callgrind; fixed, then everything again: nothing.

This round (from 0bae240):

13. knip's own fixtures, 904/957 to 957/957, each difference fixed in knip's way: glob results in
    knip's crawl order (a folder's files before its subfolders'); Vite inline module scripts read after
    comments are removed; `vi.mock` in a scope that shadows `vi`; webpack rules that are functions;
    expanded scripts run in their workspace's folder; JSDoc `@import` tags; `node:module` `register`
    and `findPackageJSON`; `new Worker(path.join(__dirname, ...))`; symbolic links neither listed nor
    followed (imports through them resolve to the real path); function bodies as scopes; knip's
    localToExports; negated-only ignore patterns; enum string members by their raw text; subpath
    imports and workspace exports as knip's findWorkspacePackageTarget; tsconfig types, plugins and
    jsxImportSource resolved from the workspace reading the config; tsconfig `extends` of workspace
    packages; built files a relative import reaches mapped to their source; the root workspace always
    has the top-level ignores; workspaces in knip's order; invalid manifests reported with V8's
    JSON.parse message; the `.gitignore` files above the project up to the git root; entry
    re-exports tagged `@public`; config files other workspaces' scripts name are development entries
    in production.
14. `--production` and `--strict` on the corpus (now 23/23 each): optional peers imported in a
    `try` block (IMPORT_FLAGS.CAUGHT) count in `--strict`; package entries without the development
    entry files in production; config inputs aren't production entries.
15. Framework apps (the 14 above): a Nuxt tsconfig's gitignored `.nuxt` references are skipped (knip's
    input handler); `--strict` drops type-only imports of packages (skipTypeOnly); tsconfig
    `references` as oxc-resolver's `references: 'auto'` applies them, with rootDirs (React Router's
    `+types`); `webpack --config webpack/x.js` read `webpack/x.js` as a package path. Then cases9 and
    cases11, written from these: found nothing.
16. YAML: the first mutant runs found files the `yaml` package rejects that `yaml.irregular` let
    through to vknip's reader; fixed until none passed. cases10 found only a mistake in my own test
    (a `run:` list that knip itself crashes on).
17. `--watch`: a folder created after the start wasn't watched (a file in it gave no redraw); fixed.
18. `--trace-export` through `export *` (knip's CLI tests, 95/118): knip's resolveExportOrigins
    ported (the origins of a name through star re-exports, pass-through and aliased re-exports,
    namespace re-exports and re-exports of packages and builtins as terminals, explicit exports
    first, cycles); extract records each export's binding and isBindingReExport. 118/118.
19. Speed: the first measurement of this round's code showed +0.7% to +2.6% instructions (prefilters
    over the source for `@` tags, the resolver's tsconfig selection, the link checks, the crawl order's
    path keys); fixed (one pass over the `@` characters, a cache fast path when no tsconfig has
    references, a cached set of link folders, a cheaper sort key). After the `--trace` work,
    +0.17% on node-glob, from bigger structures copied by value (see Benchmark); fixed. Then
    everything again: nothing.

## Benchmark

CPU time (user + system of the process and everything it waited for, so vknip's node process that
loads JavaScript configs counts, and both of its threads), best of 3 runs each, knip 6.44.1 (Node 22)
and vknip (release build), measured in this round on the 2-core machine shared with other jobs.

| project | files | knip CPU s | vknip CPU s | CPU ratio | knip wall s | vknip wall s |
|---|---:|---:|---:|---:|---:|---:|
| chalk | 20 | 0.80 | 0.010 | 81x | 0.62 | 0.010 |
| defu | 9 | 0.84 | 0.009 | 96x | 0.66 | 0.009 |
| dequal | 9 | 0.75 | 0.007 | 105x | 0.61 | 0.007 |
| execa | 639 | 1.10 | 0.046 | 24x | 0.85 | 0.039 |
| kleur | 13 | 0.67 | 0.007 | 102x | 0.55 | 0.007 |
| klona | 37 | 0.68 | 0.006 | 107x | 0.55 | 0.007 |
| ky | 98 | 1.40 | 0.058 | 24x | 0.96 | 0.040 |
| mitt | 3 | 0.69 | 0.008 | 86x | 0.56 | 0.008 |
| node-lru-cache | 49 | 0.76 | 0.011 | 68x | 0.60 | 0.011 |
| p-queue | 17 | 0.91 | 0.016 | 58x | 0.68 | 0.012 |
| scule | 4 | 0.70 | 0.008 | 88x | 0.55 | 0.008 |
| superjson | 20 | 0.72 | 0.012 | 61x | 0.57 | 0.011 |
| uncrypto | 5 | 0.69 | 0.007 | 96x | 0.54 | 0.007 |
| uvu | 93 | 0.73 | 0.010 | 74x | 0.59 | 0.010 |
| express | 142 | 1.23 | 0.029 | 42x | 0.89 | 0.023 |
| fastify | 304 | 2.19 | 0.089 | 25x | 1.44 | 0.062 |
| got | 98 | 1.68 | 0.081 | 21x | 1.13 | 0.051 |
| koa | 82 | 1.08 | 0.017 | 62x | 0.81 | 0.014 |
| node-glob | 59 | 0.80 | 0.011 | 75x | 0.65 | 0.011 |
| node-tar | 73 | 0.88 | 0.019 | 45x | 0.68 | 0.017 |
| changesets | 164 | 2.25 | 0.474 | 5x | 1.57 | 0.458 |
| knip | 4678 | 3.12 | 0.478 | 7x | 2.07 | 0.402 |
| unhead | 860 | 6.60 | 3.670 | 2x | 4.68 | 3.047 |

Against the start of the round (0bae240, built from `git archive` and run on the same machine): CPU
5.32 s in total before, 5.17 s after. Instructions (callgrind, `--jobs 1`, builds with
`VU_MARCH=x86-64-v2`, both binaries measured one after the other; the baseline's own runs differed by
up to 18,000 instructions on node-glob and 350,000 on knip):

| project | 0bae240 | now | change |
|---|---:|---:|---:|
| node-glob | 56,346,670 | 56,371,669 | +0.04% |
| fastify | 563,353,451 | 548,291,002 | -2.7% |
| changesets | 1,053,080,934 | 1,049,131,502 | -0.4% |
| knip | 2,002,175,639 | 2,002,327,543 | +0.01% |

node-glob and knip are slightly above the baseline: 9,000 and 78,000 instructions above its highest
run, about half and a quarter of the spread between its own runs. The export bindings that
`--trace` needs first cost +0.17% on node-glob: their maps and a field made each file's parse state
and result bigger, and those are copied by value. They are now recorded only under `--trace`, in
lists the parse state already has.

### Monorepos and workspaces

Issue #2 measured vknip 0.1.0 slower than knip on a monorepo with one workspace selected
(`-D <root> -W <workspace> --reporter compact`). On the corpus monorepo with JavaScript configs
(unhead) it was too: `-W packages/vue` took 2.95 s against knip's 2.75 s. Without node that run takes
0.12 s; the rest was node. vknip started a node process per config mode, and then one per
config found later (the projects a root `vitest.config.ts` lists): 9 processes for `-W packages/vue`,
each importing vite, unbuild and the rest again. Now (counted with strace) 2 processes serve the run:
they stay up, the configs found up front are spread over them, and the ones found later go to the
first, whose module cache already holds what earlier configs imported. TypeScript configs that
import only a define helper don't load its package (see Configuration): unbuild's
`defineBuildConfig` had cost 0.8 s, `@playwright/test`'s `defineConfig` 0.3 s, `vitest/config`'s
`defineConfig` about 0.15 s.

Running from another folder with `--directory` also failed before: jiti and the `yaml` package were
looked for from the working folder only, so every TypeScript config of a project whose jiti is in
its own `node_modules` failed to load (`__dirname is not defined in ES module scope`, extra errors in
the report). On the 100 `-W`/`-D` command lines of the parity check below, 0.1.0 matched knip on 80;
now on 97 (the other 3: knip's uncaught-error stack trace for a missing CODEOWNERS file, which vknip
prints as its first line). `test/cases12.py` (31 command lines, identical) attacks the loading:
define helpers with real vite, vitest, unbuild and @playwright/test (two arguments, aliases, type
imports, `.mts`/`.cts`/`.js`, a missing package, a fake `vite` that isn't vite, a helper the version
lacks), a config imported by another, large answers, a config that prints (knip prints that output;
vknip discarded it, now it prints it where knip loads the file), and a monorepo of 6 workspaces with
`-W`, `-D` and `--production`.

Wall and CPU seconds (CPU includes the node processes), best of 5 after a warm-up run, each tool's
runs together (taking turns, one tool's writes to the shared jiti cache slowed the other's next
run), knip 6.44.1 and vknip on Node 22, Linux, the shared 2-core machine (load average 2 to 4 during
these runs, so differences under about 0.05 s are noise). "vknip 0.1.0" is the released npm binary;
"before" is 1af38b4 (0.1.0 and the issue #1 fix); "now, npm launcher" runs this build through the npm
package's `bin/vknip.js` as `node bin/vknip.js`, as the issue did. mono1 is a generated pnpm monorepo
(150 workspaces of 20 files, no configs: `test/genmono.py mono1 150 20`); "subdir" runs in a
workspace's folder without `-W`.

| case | knip wall | knip CPU | vknip 0.1.0 | before (1af38b4) | now wall | now CPU | now, npm launcher | knip / now |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| changesets | 1.891 | 1.650 | 0.368 | 0.315 | 0.317 | 0.350 | 0.316 | 6.0x |
| changesets -W cli | 1.129 | 1.557 | 0.266 | 0.265 | 0.322 | 0.318 | 0.477 | 3.5x |
| changesets -W types | 1.120 | 1.560 | 0.265 | 0.315 | 0.319 | 0.274 | 0.318 | 3.5x |
| changesets -D -W cli compact | 1.626 | 1.575 | 0.265 | 0.318 | 0.324 | 0.290 | 0.319 | 5.0x |
| changesets --production | 1.330 | 1.263 | 0.377 | 0.370 | 0.324 | 0.298 | 0.367 | 4.1x |
| changesets subdir packages/cli | 0.631 | 0.595 | 0.016 | 0.016 | 0.016 | 0.017 | 0.064 | 39.4x |
| knip | 1.740 | 2.583 | 0.317 | 0.375 | 0.319 | 0.305 | 0.321 | 5.5x |
| knip -W knip | 1.742 | 2.567 | 0.373 | 0.315 | 0.318 | 0.364 | 0.316 | 5.5x |
| knip -W docs | 0.618 | 0.788 | 0.215 | 0.215 | 0.165 | 0.212 | 0.165 | 3.7x |
| knip -W vscode-knip | 1.575 | 2.425 | 0.315 | 0.316 | 0.265 | 0.321 | 0.268 | 5.9x |
| knip -D -W docs compact | 0.576 | 0.784 | 0.265 | 0.265 | 0.165 | 0.203 | 0.215 | 3.5x |
| knip --production | 1.386 | 2.030 | 0.321 | 0.315 | 0.266 | 0.319 | 0.268 | 5.2x |
| knip subdir packages/docs | 0.575 | 0.596 | 0.016 | 0.016 | 0.037 | 0.029 | 0.115 | 15.5x |
| mono1 (synthetic, 150 ws) | 2.689 | 2.651 | 0.670 | 0.669 | 0.720 | 0.710 | 0.818 | 3.7x |
| mono1 -W p140 | 1.488 | 1.397 | 0.216 | 0.216 | 0.167 | 0.140 | 0.272 | 8.9x |
| unhead | 3.401 | 4.753 | 2.328 | 2.290 | 1.177 | 1.984 | 1.176 | 2.9x |
| unhead -W unhead | 3.218 | 4.585 | 2.081 | 2.141 | 0.973 | 1.357 | 0.974 | 3.3x |
| unhead -W vue | 2.750 | 3.783 | 2.833 | 2.950 | 0.875 | 1.260 | 0.972 | 3.1x |
| unhead -W schema-org | 2.758 | 3.882 | 2.082 | 2.295 | 1.026 | 1.627 | 1.124 | 2.7x |
| unhead -W examples/vite-ssr-vue | 2.446 | 3.545 | 1.829 | 1.897 | 0.622 | 0.916 | 0.671 | 3.9x |
| unhead -D -W vue compact | 2.710 | 3.796 | 2.855 | 2.745 | 0.971 | 1.365 | 1.028 | 2.8x |
| unhead --production | 3.256 | 4.416 | 2.541 | 2.482 | 1.236 | 2.201 | 1.275 | 2.6x |
| unhead subdir packages/vue | 1.036 | 0.732 | 0.050 | 0.044 | 0.027 | 0.023 | 0.064 | 38.4x |

Every case is now at least 2.6 times faster than knip in wall time; the unhead cases went from about
knip's time to a third of it. Where vknip needs no node (changesets, knip, mono1) nothing changed
beyond noise; mono1's 0.72 s against 0.67 s before is within the spread of its runs. The launcher adds
about 0.03 to 0.05 s (node's start). Not measured: macOS (the issue's machine), and the private
monorepo of the report.

### n8n: a large monorepo

n8n is the largest public repository that uses knip: 109 workspaces, 33,236 files in the project
after `.gitignore`, 26,206 of them analyzed. It was cloned with its dependencies installed (pnpm;
one change: `packages/frontend/editor-ui/package.json` points `wa-sqlite` to a local copy, as the
machine's proxy blocks codeload.github.com; n8n's packages weren't built, so knip and vknip both fail
to load about 150 vitest and oxlint configs and print the same 318 lines of errors). Run in the
repository's folder with no arguments (and the arguments shown), wall and CPU seconds (user + system
of vknip, its threads and its node processes) and the largest resident set, best of 3 runs for
vknip, one run for knip 6.44.1 (Node 22), on the shared 2-core machine (load average about 1 to 2).
"before" is 6d92970.

| case | knip wall | knip CPU | knip MB | before wall | before CPU | now wall | now CPU | now MB | knip / now |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| (whole repo) | 114.2 | 123.5 | 1656 | 34.63 | 38.27 | 7.14 | 11.58 | 463 | 16.0x |
| -W packages/cli | 107.1 | 116.6 | 1620 | 31.13 | 34.11 | 6.80 | 10.99 | 453 | 15.7x |
| -W packages/nodes-base | 91.2 | 98.3 | 1050 | 15.60 | 17.26 | 4.03 | 6.20 | 310 | 22.6x |
| -W packages/frontend/editor-ui | 91.3 | 98.2 | 1271 | 19.49 | 21.68 | 4.75 | 7.60 | 264 | 19.2x |
| --production | 84.6 | 89.5 | 978 | 12.64 | 14.98 | 4.78 | 7.05 | 246 | 17.7x |

Output is identical in every case: stdout byte for byte (empty: no issues), stderr the same lines
(sorted; knip prints the config errors in another order).

Where the time went (vknip's sampling profiler, `vu build --profile`, and timestamps at each phase:
`VKNIP_PHASES=1` prints them on stderr), and what changed, in order of size:

1. **Glob matching: 72% of the CPU.** Every `glob_files` call tested every project file against
   every pattern (68 million path-pattern tests on n8n, the path split into parts for each), and
   every `.gitignore` pattern of every workspace was tried on every folder of each path checked
   (each import of a workspace package, each unresolved import). Now the project files are sorted
   once after the walk; a pattern is tried only on the range of files below its literal folders,
   a pattern without glob characters is looked up, one with a single segment sees only the root's
   files; `.gitignore` and negated patterns are kept by their literal prefix, and a path looks up
   its own prefixes; and a pattern alternative first checks that its literal segments are among the
   path's parts and that its last segment matches the last part. 32.9 s -> 10.9 s wall.
2. **Repeated directory listings and stats.** 122,331 directory opens for 19,787 folders (strace):
   the walk listed each folder twice (names, then its symbolic links), every `glob_fs` pattern
   (tsconfig `include`, the configuration's entries, each plugin's config files) walked the folders
   again, and `**` listed each folder twice. The listings and stats now come from a cache for the
   run (`term_glue.c`: each folder read once, each path stat-ed once; the resolver uses it too), and
   segment patterns are compiled once per glob. With a cache of package resolutions (each package
   folder and specifier once, and each folder's package lookup and source mapping once), and an
   `entry_hints` that looked through all entries for each workspace: 10.9 s -> 8.5 s.
3. **One core idle.** `strace -f` counted 13 to 17 s of futex: that is node's idle helper threads
   and vknip's first thread waiting for its main one, not contention. The real gap was that files
   were read only after all workspaces' entries were known, and linked only after all were read. Now
   the included workspaces' JavaScript and TypeScript files are read on the other cores while node
   loads the configs and the entries are found (a wave takes a file's result when it was read with
   the same tags and no compiler), and each file is linked as soon as its result arrives. Not in
   `--production` (the graph reaches far fewer files) or projects under 1,000 such files (the
   threads and unreached files cost more than the overlap gives). 8.5 s -> 7.1 s.

The corpus didn't get slower: best of 5 against 6d92970, the 23 projects' CPU 3.70 s -> 3.39 s and wall 2.44 s -> 2.07 s in total (knip 0.317 -> 0.199 s wall, changesets 0.329 -> 0.256, unhead 1.466 -> 1.292; the small ones within 1 ms either way, the machine's noise). Instructions
(callgrind, `--jobs 1`, `VU_MARCH=x86-64-v2` builds): node-glob 56.4 M -> 55.4 M, fastify 548 M ->
527 M, changesets 1,049 M -> 380 M, knip 2,003 M -> 979 M.

What's left on n8n (7.1 s): node loading the configs (2.5 s of wall, shared with the reading
threads), the workspaces' entries and plugins on one core (1.8 s), and linking (resolution, 2 s),
which stays on one core because the resolver's caches and tsconfig state are one value.

**A private monorepo on macOS** (`js/` of a company repository: 73 workspaces, about 30,000 files
analyzed, no dependencies installed, so both tools print the same config-loading errors; Apple
silicon, 10 cores, Node 25, jiti from NODE_PATH as the npm launcher sets it). Median of 9 alternating
runs (knip: 3), wall and CPU seconds; stdout identical between the vknip builds in every run. The
machine wasn't idle (a `git status` of the desktop app and macOS's media analysis took one to two
cores throughout), so the numbers are a little worse than a quiet machine's:

| | knip 6.44.1 | vknip before | vknip now |
|---|---:|---:|---:|
| wall | 21.15 | 5.41 | 1.98 |
| CPU | 29.52 | 14.24 | 10.96 |

Found with `sample` (macOS) and `VKNIP_PHASES=1`, in order of size:

1. **Issue locations rescanned their file from the start.** `extract.loc` counted the UTF-16 offset
   from byte 0 for every issue in a file with non-ASCII text: in generated GraphQL files of 1 to 4 MB
   with hundreds of ignored exports, 1.7 s on the main thread. Each line start's UTF-16 offset is now
   kept with the file (`lines16`), so a location scans only its line. 5.4 s -> 3.6 s.
2. **Linking on one core.** Each wave's imports are resolved on resolver threads as files come in
   (this was `VKNIP_PRERESOLVE=1`, off because each thread's fresh copy of the resolver loaded every
   tsconfig again). The threads now hand their resolvers, caches and all, to the next wave's threads
   while the configuration (`resolve.cfg_key`) is the same, and it is on for waves of 256 files or
   more; while the main thread waits for a file's resolution it passes the files read meanwhile to
   the resolver threads (a `select` on both channels). The main thread's linking 0.8 s -> 0.25 s.
3. **The main thread kept off its own thread.** New tasks go to the threads in turn, the main
   thread's too, and a task runs until it waits: a parse worker on the main thread's thread, whose
   queue was never empty, ran whenever the main thread waited and kept it waiting until the parse was
   done (0.9 s once node's answers came early). Workers now give the thread's other tasks a turn
   after each file when one is ready (`term.yield_if_ready`, a look at the thread's ready queues;
   `os.sleep(0)` after each file instead went through the timers and slowed the parse by half).
4. **Node off the critical path.** The project's `knip.config.ts` is plain data (an object literal
   with a type annotation): such a config (type-only imports, types, `const`s of literals and
   `export default` of an object; strings without escapes, integers, booleans, null, arrays and
   objects with plain keys; anything else goes to node as before, and not with `--cache`) is read
   from its AST (`asth.static_config`; on this one byte for byte jiti's JSON, and on 23 tricky
   configs either jiti's value or node). And the plugins' configs, which depend only on the
   workspaces' dependencies and configuration, are loaded by node on a thread of its own while the
   project is walked, rather than after. 0.17 s + about 0.3 s of waiting.
5. **Reading the files.** macOS serializes `open` in the kernel: 38,000 of the files took 0.35 s on
   4 threads and 0.85 s (8 s of system time) on 10. Three threads read the speculative parse's files
   ahead of the workers (`term.readahead`/`take`: a worker that gets ahead reads its file itself), and
   the parse takes its files from a queue in C (`term.job_next`) that puts the first wave's files
   first once the wave is known: the first wave's wait for the parse 0.3 to 0.5 s -> 0.03 s. A cap on
   concurrent reads (4) saved CPU but no wall time, and was left out.
6. **Ignore patterns tried on every issue.** `ignored_issue_file` matched every `ignore` pattern (and
   `should_ignore_issue` every `ignoreIssues` pattern) for each issue: now remembered per file (and
   per type), and a pattern whose literal folders the path isn't in is skipped. About 0.25 s.
7. **The walk listed one folder at a time.** Three threads list the project's folders breadth first
   into the listing cache from the start of the run (not node_modules or .git), outside the cache's
   lock; the kinds a listing tells (folder, plain file) answer later stats, and a name a listed
   folder doesn't have (ASCII, no symbolic links there, none the same but for case) isn't stat-ed.
   Gitignore patterns `**/name` are looked up by name instead of tried on each path. The walk
   0.44 s -> 0.17 s.
8. **Smaller ones.** `glob_files` looks up patterns that name files or one folder's files (brace
   lists like `dangerfile.{js,cjs,mjs,ts}`, `dir/*.ts`) instead of trying them on every file below
   their folders, and matches `dir/**/*.ext` by prefix and suffix (238 ms -> about 100). Values of the
   configuration are read in place (`pkg.get` copies: `early_cfg_off` copied the whole top level per
   workspace and compiler). `local_refs` (ignoreExportsUsedInFile) records only the file's export
   names, sorted, for a lookup by bisection. Whole-file `find`s of multi-byte needles look for their
   rarest byte with a one-byte find (`extract.ffind`: macOS's `memmem` is 0.9 GB/s, its `memchr`
   20). Gitignore checks of resolved files remember each folder's answer.

The `--cache` format is now `vknip-cache-2` (files' entries carry `lines16` and sorted
`local_refs`): a cache written by an earlier version is read as empty and rebuilt once.

Checked: stdout byte for byte and stderr between the builds on this repository for the default
run, `--production`, `--strict`, the json and compact reporters, `-W` (two workspaces), `--include`,
`--cache` (cold and warm), `--no-gitignore`, `--jobs 1`, and with each new path turned off
(`VKNIP_NO_STATIC_CFG`, `VKNIP_NO_EARLY_PF`, `VKNIP_NO_READAHEAD`, `VKNIP_NO_PRELIST`,
`VKNIP_PRERESOLVE=0`); `test/cases.py` to `cases11.py` against knip give what they gave before
(268 of 269 identical; the one difference, cli_basic with two reporters, was there before). Not measured or checked: Linux, the corpus, knip's fixtures (`cmp_fixtures.py`).

What's left (about 1.9 s): the speculative parse and node's configs sharing the cores (node takes
0.1 to 0.4 s of waiting depending on how starved it is), the workspaces' entries and plugins on one
core (0.4 to 0.55 s), the later waves (about 0.4 s), and the walk (0.17 s).

**Configs with `--cache`** (issue #4: on a large private workspace, loading configs and finishing
the graph were most of a 7 s run). vknip `--cache` also keeps the values of the JavaScript configs
it loaded with Node.js, and uses them while nothing they depended on changed: the loader records
every module and file a config loaded or read, each path it looked for and didn't find (a module
not built yet, an optional dependency), each folder it listed and each environment variable it
read (kept as a hash), and the lockfiles are always included. On n8n (2 cores, the issue's command
line: `--include dependencies,unlisted,binaries,unresolved`), with Node.js not started at all when
nothing changed:

| run | wall |
|---|---|
| no `--cache` | 7.37-7.88 s (3 runs) |
| `--cache`, before this | 7.26-7.90 s (2 runs after the one that filled it: only the files' analyses were kept, and parsing wasn't the slow part) |
| `--cache`, now | 5.17-5.26 s (3 runs; the run that fills it: 9.65 s) |

stdout and stderr are byte for byte those of a run without `--cache`. `test/cmp_cfg_cache.sh`
changes a project step by step (a file a config imports, the config, an environment variable it
reads and one it doesn't, a module it looked for appearing and going, a lockfile, a copy of the
project with a file changed but not its size or time, sharing the cache) and checks that the output
is always that of a run without the cache and that the configs are loaded again exactly when they
should be: 15/15 (the copy fails without the cache's record of the folder it was made in). Tried on n8n too: editing a vite plugin file, `NODE_ENV`, the
lockfile, building a missing `dist` file and adding a config each reloaded and matched an uncached
run; `OLDPWD` and new variables didn't. Two things the first version got wrong and that n8n showed:
`stat` on a folder (path resolution does it to every parent) was taken as listing it, so any file
created in `/tmp` reloaded the configs; and `Object.keys(process.env)` (the `debug` package, in vite
and playwright) and playwright's `{ ...process.env }` counted every variable's value, so `cd`
(`OLDPWD`) reloaded them; a list of the variables now counts only their names, and a copy of them
all, read in the order they were listed, the same. Not noticed: a different Node.js, a variable that's
new and that a config only finds by listing them all.

Also: the resolver kept each package's whole `package.json` and copied it for every lookup; it keeps
only `"exports"` now (n8n, cached: 5.15-5.22 s -> 4.91-5.09 s in one set of runs, close to the
machine's noise). What's left on n8n with `--cache`
(5.0 s): the main thread is the whole run, linking (resolution, about 1.8 s) and the workspaces'
globs and plugins (1.5 s). The first run after the files left the page cache took 119 s, all of it
reading them (setup and plugin detection, which don't start Node.js, took 50-200 times as long):
that's the disk, not vknip.

## Gaps

- **`--debug`**: knip's debug output (the options, workspaces, plugins, inputs and files it found) isn't
  printed; `--debug-inputs` prints vknip's own list.
- **`--watch`** gives knip's screens, but works differently inside: each change reruns the whole
  analysis in a child process (knip updates its graph for the changed files), an added file counts
  by its extension alone, and an added file that is gitignored still redraws the screen.
- **YAML**: when no `yaml` package can be found (neither the project's, knip's nor the npm package's),
  the files `yaml.irregular` flags are read by vknip's own reader, which accepts some that knip's
  parser rejects.
- The JSON, markdown and codeclimate reporters list unused files in knip's crawl order as it comes out
  when the crawler's reads finish in order; knip's own order varies from run to run.
- vscode wasn't re-measured: its checkout with dependencies wasn't fetched (how much disk it needs
  wasn't measured; the machine had about 2 GB free).

## Tests

`test/` has the scripts: `cmp_corpus.py` compares real projects with knip (`WORK=dir`, knip's output
cached in `dir/ref`), `fetch_corpus.sh` clones `corpus.txt` (and installs and sets up the framework
apps), `gen_cmp.py CASES OUT` writes the generated projects of a cases file, runs knip once (cached)
and vknip on each command line, and compares stdout, stderr, exit code and, for `--fix` cases, the
files left behind; `run_cases.py` and `cmp_cases.sh` do the same for the first sets;
`cmp_fixtures.py` runs knip's own test fixtures, `cmp_cli.py` the command lines of knip's tests,
`cmp_env.py` runs with environment variables (`FORCE_COLOR=1`), `cmp_cache.py` edits a project step
by step under `--cache`, `cmp_watch.py` drives `--watch` in a pty; `bench.py` times both;
`globtest.vu` checks the glob matcher against picomatch, `yamltest.vu` the YAML reader against the
`yaml` package (102 files of the corpus, identical), `yamlirr.vu` which YAML files go to the `yaml`
package.

## Plugin coverage

Generated from knip's plugin list and vknip's code (`tools/plugtab.py`): what each
plugin has (resolveConfig, resolveFromAST, resolve, visitors) and whether vknip ports it. "tested on"
names the generated cases and the corpus projects whose dependencies enable the plugin. All 202
plugins are complete.

| plugin | status | tested on |
|---|---|---|
| Angular (`angular`) | resolveConfig ported; visitors ported | unhead |
| Astro (`astro`) | resolveFromAST ported; resolve ported | generated; knip |
| Astro DB (`astro-db`) | complete (static plugin) |  |
| Astro Markdoc (`astro-markdoc`) | resolveConfig ported |  |
| astro-og-canvas (`astro-og-canvas`) | resolve ported |  |
| Ava (`ava`) | resolveConfig ported | ky, uvu |
| Babel (`babel`) | resolveConfig ported | generated; uvu |
| Biome (`biome`) | resolveConfig ported |  |
| Borp (`borp`) | ported (hand-written) | fastify |
| Buf (`buf`) | resolveConfig ported |  |
| bumpp (`bumpp`) | complete (static plugin) | unhead |
| Bun (`bun`) | resolveConfig ported; resolve ported |  |
| c8 (`c8`) | complete (static plugin) | generated |
| Capacitor (`capacitor`) | resolveConfig ported |  |
| Catalyst (`catalyst`) | visitors ported |  |
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
| Eleventy (`eleventy`) | resolveConfig ported |  |
| esbuild (`esbuild`) | resolveFromAST ported | generated; node-glob, node-lru-cache, node-tar, unhead +1 |
| ESLint (`eslint`) | resolveConfig ported; resolveFromAST ported | generated; changesets, express, fastify, mitt +3 |
| eve (`eve`) | complete (static plugin) |  |
| execa (`execa`) | visitors ported | generated; chalk |
| Expo (`expo`) | resolveConfig ported; resolve ported | generated |
| Expo Router (`expo-router`) | resolveConfig ported | generated |
| Expressive Code (`expressive-code`) | complete (static plugin) | knip |
| FAST (`fast`) | visitors ported |  |
| filesystem-routing (`filesystem-routing`) | resolveFromAST ported |  |
| Flue (`flue`) | resolveFromAST ported |  |
| Fumadocs (`fumadocs`) | complete (static plugin) |  |
| Gatsby (`gatsby`) | resolveConfig ported |  |
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
| Ladle (`ladle`) | resolveConfig ported |  |
| laravel-vite-plugin (`laravel-vite-plugin`) | resolveFromAST ported | generated |
| Lefthook (`lefthook`) | ported (hand-written) | generated |
| Lingui (`lingui`) | complete (static plugin) |  |
| lint-staged (`lint-staged`) | resolveConfig ported | generated; changesets |
| LintHTML (`linthtml`) | resolveConfig ported |  |
| Lit (`lit`) | visitors ported |  |
| lockfile-lint (`lockfile-lint`) | complete (static plugin) |  |
| Lost Pixel (`lost-pixel`) | complete (static plugin) |  |
| Lunaria (`lunaria`) | resolveConfig ported |  |
| markdownlint (`markdownlint`) | resolveConfig ported | generated; fastify |
| Marko (`marko`) | resolveConfig ported |  |
| Mastra (`mastra`) | complete (static plugin) |  |
| MCP (`mcp`) | ported (hand-written) |  |
| MDX (`mdx`) | resolveConfig ported | generated; knip |
| mdxlint (`mdxlint`) | resolveConfig ported | knip |
| Metro (`metro`) | resolveConfig ported | generated |
| mise (`mise`) | resolveConfig ported |  |
| Mocha (`mocha`) | resolveConfig ported | generated; express, mitt, uvu |
| moonrepo (`moonrepo`) | resolveConfig ported |  |
| Mock Service Worker (`msw`) | resolveConfig ported | generated |
| nano-spawn (`nano-spawn`) | visitors ported | generated |
| Nano Staged (`nano-staged`) | resolveConfig ported | generated |
| Nest (`nest`) | resolveConfig ported |  |
| Netlify (`netlify`) | resolveConfig ported |  |
| Next.js (`next`) | resolveConfig ported; resolveFromAST ported | generated |
| next-intl (`next-intl`) | complete (static plugin) |  |
| Next.js MDX (`next-mdx`) | resolveFromAST ported |  |
| Nitro (`nitro`) | resolveConfig ported; resolve ported |  |
| Node.js (`node`) | ported (hand-written); visitors ported |  |
| node-modules-inspector (`node-modules-inspector`) | complete (static plugin) |  |
| nodemon (`nodemon`) | complete (static plugin) |  |
| npm-package-json-lint (`npm-package-json-lint`) | resolveConfig ported |  |
| Nuxt (`nuxt`) | resolveConfig ported; resolve ported | generated; unhead |
| @nuxtjs/i18n (`nuxtjs-i18n`) | complete (static plugin) |  |
| Nx (`nx`) | resolveConfig ported; resolve ported | generated |
| nyc (`nyc`) | resolveConfig ported | express |
| oclif (`oclif`) | resolveConfig ported | generated |
| openapi-ts (`openapi-ts`) | complete (static plugin) |  |
| OpenClaw (`openclaw`) | resolveConfig ported; resolveFromAST ported |  |
| orval (`orval`) | resolveFromAST ported | generated |
| osls (`osls`) | resolveConfig ported |  |
| Oxfmt (`oxfmt`) | complete (static plugin) | changesets, defu, knip |
| Oxlint (`oxlint`) | resolveConfig ported | defu, knip, node-glob, node-lru-cache +1 |
| Panda CSS (`panda-css`) | resolveConfig ported |  |
| Parcel (`parcel`) | resolveConfig ported | generated |
| Payload CMS (`payload`) | resolveConfig ported | generated |
| pino (`pino`) | visitors ported | generated; fastify |
| Playwright (`playwright`) | resolveConfig ported | generated; unhead |
| Playwright for components (`playwright-ct`) | resolveConfig ported |  |
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
| Quasar (`quasar`) | resolveFromAST ported |  |
| Qwik (`qwik`) | resolveFromAST ported |  |
| Railway (`railway`) | resolveFromAST ported |  |
| Raycast (`raycast`) | resolveConfig ported |  |
| React Cosmos (`react-cosmos`) | resolveConfig ported |  |
| React Email (`react-email`) | complete (static plugin) |  |
| React Native (`react-native`) | resolveConfig ported; resolve ported | generated |
| React Router (`react-router`) | resolveConfig ported | generated |
| Relay (`relay`) | resolveConfig ported |  |
| Release It! (`release-it`) | resolveConfig ported | generated; knip |
| Remark (`remark`) | resolveConfig ported | knip |
| Remix (`remix`) | complete (static plugin) |  |
| Rolldown (`rolldown`) | resolveFromAST ported | knip, unhead |
| Rollup (`rollup`) | resolveFromAST ported | unhead |
| Rsbuild (`rsbuild`) | resolveConfig ported |  |
| Rslib (`rslib`) | resolveFromAST ported |  |
| Rspack (`rspack`) | resolveConfig ported; visitors ported | generated |
| Rstest (`rstest`) | resolveConfig ported; visitors ported |  |
| Sanity (`sanity`) | complete (static plugin) |  |
| Semantic Release (`semantic-release`) | resolveConfig ported | generated |
| Sentry (`sentry`) | complete (static plugin) |  |
| Serverless Framework (`serverless-framework`) | resolveConfig ported |  |
| simple-git-hooks (`simple-git-hooks`) | resolveConfig ported | generated |
| size-limit (`size-limit`) | resolve ported |  |
| @solidjs/vite-plugin (`solidjs-vite-plugin`) | resolveFromAST ported |  |
| SST (`sst`) | resolveFromAST ported | generated |
| Starlight (`starlight`) | resolveFromAST ported | knip |
| Stencil (`stencil`) | resolveFromAST ported; visitors ported |  |
| Storybook (`storybook`) | resolveConfig ported; resolveFromAST ported | generated |
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
| Taskfile (`taskfile`) | resolveConfig ported |  |
| Tauri (`tauri`) | resolveConfig ported |  |
| Temporal.io (`temporal`) | complete (static plugin) |  |
| textlint (`textlint`) | resolveConfig ported |  |
| Travis CI (`travis`) | resolveConfig ported |  |
| ts-node (`ts-node`) | complete (static plugin) | generated |
| tsd (`tsd`) | resolveConfig ported | generated |
| tsdown (`tsdown`) | resolveConfig ported; resolveFromAST ported | changesets |
| tsrs (`tsrs`) | ported (hand-written) |  |
| tsup (`tsup`) | resolveConfig ported; resolveFromAST ported | generated |
| tsx (`tsx`) | ported (hand-written) | generated |
| Turborepo (`turbo`) | resolve ported |  |
| TypeDoc (`typedoc`) | ported (hand-written) | node-glob, node-lru-cache, node-tar |
| TypeScript (`typescript`) | ported (hand-written) | generated; chalk, changesets, defu, execa +10 |
| TypeScript Content Mapper (`typescript-content-mapper`) | resolveConfig ported |  |
| unbuild (`unbuild`) | resolveConfig ported | defu, scule, uncrypto, unhead |
| UnoCSS (`unocss`) | complete (static plugin) |  |
| unplugin-auto-import (`unplugin-auto-import`) | complete (static plugin) | unhead |
| unplugin-icons (`unplugin-icons`) | resolve ported | generated; changesets |
| unplugin-vue-components (`unplugin-vue-components`) | complete (static plugin) | unhead |
| @intlify/unplugin-vue-i18n (`unplugin-vue-i18n`) | complete (static plugin) |  |
| unplugin-vue-markdown (`unplugin-vue-markdown`) | complete (static plugin) |  |
| unplugin-vue-router (`unplugin-vue-router`) | complete (static plugin) | unhead |
| Varlock (`varlock`) | resolve ported |  |
| Vercel (`vercel`) | complete (static plugin) |  |
| Vercel OG (`vercel-og`) | complete (static plugin) |  |
| Vike (`vike`) | complete (static plugin) |  |
| Vite (`vite`) | resolveConfig ported; resolveFromAST ported; resolve ported; visitors ported | generated; changesets, defu, scule, superjson +2 |
| vite-plugin-pages (`vite-plugin-pages`) | resolveFromAST ported; resolve ported |  |
| vite-plugin-pwa (`vite-plugin-pwa`) | resolveFromAST ported | generated |
| vite-plugin-vue-layouts-next (`vite-plugin-vue-layouts-next`) | resolveFromAST ported |  |
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
| xo (`xo`) | resolveConfig ported; resolveFromAST ported | chalk, execa, got, ky +1 |
| Yarn (`yarn`) | resolveConfig ported |  |
| yorkie (`yorkie`) | resolveConfig ported | generated |
| zx (`zx`) | visitors ported | generated |
