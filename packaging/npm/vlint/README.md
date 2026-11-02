# vlint

An oxlint-compatible linter written in [Vu](https://github.com/vu0tran/vu): oxlint 1.90.0's 96
default rules (the `correctness` rules that need no type information, from `eslint`, `typescript`,
`unicorn` and `oxc`), with the same diagnostics at the same positions and the same messages, and
`--fix` with oxlint's safe fixes. It checks `.js .mjs .cjs .jsx .ts .mts .cts .tsx`.

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
+    "oxlint": "npm:@vu0tran/vlint@^0.1.0"
   }
```

`npm run lint` (`"lint": "oxlint src"`) then runs vlint. To go back, restore the line.

The `oxlint` command is there so scripts don't change. The trade-off: it takes oxlint's name.
Don't install `@vu0tran/vlint` next to the real `oxlint` in one project (both would claim
`node_modules/.bin/oxlint`, and which one wins depends on the order npm links them), or globally
next to a global oxlint. With the alias above, `require("oxlint")` gets this package, which has
no JavaScript API (oxlint's `defineConfig` and JS plugins aren't there).

## What's the same

- The diagnostics: every warning matched oxlint 1.90.0's (position, rule, message, help) on
  date-fns, zod, remeda, immer, jotai, ky, mitt, p-queue, redux, reselect (3,445 files),
  JavaScript from `node_modules`, preact, excalidraw and vscode (11,000 diagnostics).
- `--fix`: the files are rewritten as `oxlint --fix` rewrites them (compared file by file on the
  same corpora: identical except for files oxc can't parse and ties between fixes with the same
  span).
- `eslint-disable` / `oxlint-disable` comments.
- With no paths it lints the current folder. The exit code is 1 when there are errors (parse
  errors; the default rules warn) or no files to lint, and 0 otherwise. Paths are printed as
  oxlint prints them.
- The CPU time: about the same as oxlint's on those corpora (measured on a loaded 2-core VM).

## What's not there yet

Be sure your project doesn't depend on these before switching:

- **No configuration.** `.oxlintrc.json`, `-c/--config`, nested configs, `rules`, `categories`,
  `plugins`, `overrides`, `env`/`globals` and `settings` are not read: vlint always runs the 96
  default rules with their default options. A project whose config turns rules off or on will
  see different results.
- **No ignore files.** `.gitignore`, `.eslintignore`, `ignorePatterns` and `--ignore-path` are not
  read. With no paths, vlint skips `node_modules` folders (which oxlint skips through
  `.gitignore`); with paths, it lints every matching file under them.
- **One output format**: one line per diagnostic, `file:line:col: warning plugin(rule): message
  help: ...`, which is what oxlint prints when it runs under an AI agent. Not oxlint's graphical
  report for terminals, its summary line, or `-f/--format`.
- **Options**: only `--fix`, paths, and vlint's own `--jobs N`, `--cache` and `--cache-location
  PATH` (an ESLint-style result cache). Other oxlint options (`-A/-W/-D`, `--deny-warnings`,
  `--max-warnings`, `--quiet`, `--type-aware`, `--fix-suggestions`, `--fix-dangerously`, ...) are
  refused with exit code 2 rather than ignored.
- Parse errors: a few files that oxc rejects are accepted by vlint, and the parse error messages
  don't always use oxc's wording.
- Platforms: Linux x64 and ARM64 (static binaries: any glibc or musl), macOS 12 or later on Apple
  silicon and Intel. No Windows build (Vu doesn't target Windows yet). On macOS, `--cache` caches
  nothing (it keys the cache by `/proc/self/exe`, which macOS doesn't have).

## How it's installed

Like oxlint: this package holds a small Node launcher, and npm installs the one platform package
that fits the machine (`@vu0tran/vlint-linux-x64`, `-linux-arm64`, `-darwin-x64`, `-darwin-arm64`,
picked by their `os`/`cpu` fields) as an optional dependency. Installing with
`--omit=optional` leaves the binary out. `VLINT_BINARY=/path/to/vlint` runs another binary.

Source, measurements and how parity is checked: https://github.com/vu0tran/vu/tree/main/ts
