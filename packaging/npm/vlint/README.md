# vlint

An oxlint-compatible linter written in [Vu](https://github.com/vu0tran/vu), meant as a drop-in
replacement for oxlint 1.90.0: the same command line, configuration files, output and exit codes.
It runs oxlint's default rules and about 215 of the rules projects most often turn on, reads
`.oxlintrc.json`, and checks `.js .mjs .cjs .jsx .ts .mts .cts .tsx` plus the scripts in `.vue`,
`.astro` and `.svelte` files.

## Install

```sh
npm install --save-dev @vu0tran/vlint
npx vlint src/
```

### In place of oxlint

The package has two commands, `vlint` and `oxlint`. To switch a project that runs `oxlint` in its
scripts, change one line in `package.json`:

```diff
   "devDependencies": {
-    "oxlint": "^1.90.0"
+    "oxlint": "npm:@vu0tran/vlint@^0.4.0"
   }
```

`npm run lint` (`"lint": "oxlint src"`) then runs vlint. To go back, restore the line.

The `oxlint` command is there so scripts don't change. The trade-off: it takes oxlint's name.
Don't install `@vu0tran/vlint` next to the real `oxlint` in one project (both would claim
`node_modules/.bin/oxlint`, and which one wins depends on the order npm links them), or globally
next to a global oxlint. With the alias above, `require("oxlint")` gets this package, which has
no JavaScript API (oxlint's `defineConfig` isn't there; JS plugins in the configuration work, see below).

## What's the same

- **Configuration**: `.oxlintrc.json`/`.jsonc` (found as oxlint finds it, or `-c`), nested
  configs, `extends`, `overrides`, `rules` with severities and options, `categories`, `plugins`,
  `env`/`globals`, `ignorePatterns`, `options` (`typeAware`, `denyWarnings`, `maxWarnings`,
  `reportUnusedDisableDirectives`, ...), with oxlint's error messages for bad configs.
- **Ignore files**: `.gitignore`, `.eslintignore`, `--ignore-path`, `--ignore-pattern`,
  `--no-ignore`.
- **Options**: `-A/-W/-D`, the plugin flags, `--deny-warnings`, `--max-warnings`, `--quiet`,
  `--silent`, `-f` with every format (`default`, `agent`, `json`, `unix`, `github`, `gitlab`,
  `junit`, `checkstyle`, `stylish`, `sarif`), `--fix`, `--fix-suggestions` and
  `--fix-dangerously` (for the fixes vlint has), `--threads`, `--rules`, `--init`,
  `--print-config`, `--report-unused-disable-directives`, `--no-error-on-unmatched-pattern`,
  `--debug files`, exit codes and messages for bad usage.
- **Bulk suppressions**: `oxlint-suppressions.json`, `--suppress-all`, `--prune-suppressions`
  (and pruning on `--fix`), as oxlint does them.
- **Type-aware linting**: `--type-aware` / `--type-check` run `oxlint-tsgolint` (install it as you
  would for oxlint), with all 61 type-aware rules.
- **Output**: oxlint's report for terminals, its one-line agent format and every `-f` format,
  byte for byte in the cases compared, including "Found N warnings and M errors."
- **Diagnostics**: identical (position, rule, message, help, labels, order) on date-fns, zod,
  remeda, immer, jotai, ky, mitt, p-queue, redux, reselect, preact, excalidraw and vscode, and on
  real projects with their own configs, for every rule vlint has.
- `eslint-disable` / `oxlint-disable` comments, as oxc reads them.
- **JS plugins** (`jsPlugins`, in the config and in overrides): run in Node (which must be on
  `PATH`) with oxlint's own plugin runtime, on an ESTree view of vlint's tree that matches oxc's
  (same nodes, spans, tokens and comments); same context, `sourceCode`, scope manager, selectors,
  fixes and suggestions, and oxlint's errors for missing or misnamed plugins. 21 real plugins
  (eslint-plugin-react, react-hooks, sonarjs, perfectionist, @stylistic, playwright, storybook,
  testing-library, ...) with every rule on gave identical output on excalidraw.
- **Import plugin**: the module graph oxlint builds (oxc_resolver's resolution as oxlint sets it
  up, tsconfig `paths`/`baseUrl`/`extends`/`references`), for `import/namespace`, `default`,
  `named`, `no-cycle`, `no-duplicates`, `extensions`, `no-self-import`, `no-named-as-default`,
  `no-named-as-default-member`.
- Speed: less CPU time than oxlint on a single thread with the default rules (0.99 s against
  3.83 s on a 3,445-file corpus of TypeScript and bundled JavaScript, best of 5, measured on a
  2-core VM); with a large configuration that turns on the import graph and the vitest rules
  (kimi-code), more (2.9 s against 2.2 s).

## What's not there yet

Check that your project doesn't depend on these before switching:

- **Rules**: vlint has all of oxlint's defaults plus about 215 more (`prefer-const`, `no-shadow`,
  `no-restricted-imports`, `react-hooks/rules-of-hooks`, `react-hooks/exhaustive-deps`,
  `react/only-export-components`, `no-console`, `eqeqeq`, `curly`, `no-redeclare`,
  `import/first`, the import graph rules, `typescript/no-explicit-any`,
  `typescript/ban-ts-comment`, 34 jsx-a11y rules, the jest and vitest rules that run on test calls
  (`expect-expect`, `valid-expect`, `valid-title`, ...), ...; the list is in the source's README).
  A rule it doesn't have is accepted in the configuration and reports nothing. Missing, notably:
  the React Compiler rules oxlint turns on with the react plugin (`react/refs`, `react/purity`,
  `react/set-state-in-effect`, ...); vue, nextjs; `no-regex-spaces`, `oxc/no-map-spread`,
  `react/no-unstable-nested-components`; many pedantic and style rules. Counted on 1,830 real
  `.oxlintrc.json` files, vlint has 74% of the rules they turn on by name and 85% counting what
  their categories turn on.
- **JavaScript config files** (`oxlint.config.ts`, a `vite.config.ts` `lint` field): refused. With
  several `jsPlugins` entries, `--print-config` can list them in another order than oxlint.
- **Options**: `--lsp` isn't supported. `--fix-suggestions`/`--fix-dangerously` don't apply the
  suggestions of `no-unused-vars`, `no-new-array` and `no-extra-boolean-cast` yet.
- Parse errors: some files that oxc rejects are accepted by vlint (several of oxc's early
  errors aren't made), vlint reports only the first syntax error, and its messages don't always
  use oxc's wording (89 of oxc's 369 parser fixtures give identical output).
- Platforms: Linux x64 and ARM64 (static binaries: any glibc or musl), macOS 12 or later on Apple
  silicon and Intel. No Windows build (Vu doesn't target Windows yet). On macOS, `--cache` caches
  nothing (it keys the cache by `/proc/self/exe`, which macOS doesn't have).

## How it's installed

Like oxlint: this package holds a small Node launcher, and npm installs the one platform package
that fits the machine (`@vu0tran/vlint-linux-x64`, `-linux-arm64`, `-darwin-x64`, `-darwin-arm64`,
picked by their `os`/`cpu` fields) as an optional dependency. Installing with
`--omit=optional` leaves the binary out. `VLINT_BINARY=/path/to/vlint` runs another binary.

Source, measurements and how parity is checked: https://github.com/vu0tran/vu/tree/main/ts
