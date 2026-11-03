# vsc

[ShellCheck](https://www.shellcheck.net) 0.11.0 rewritten in [Vu](https://github.com/vu0tran/vu):
the same checks (every SC1xxx, SC2xxx and SC3xxx code and the optional checks), the same command
line, the same `.shellcheckrc` lookup and directives, the same output in every format (byte for
byte, fixes included) and the same exit codes, with about 25 times less CPU time. Its output was
compared with ShellCheck 0.11.0's release binary on 7,601 real scripts, 385 command line cases and
17,700 generated scripts: nothing known differs on a file ShellCheck finishes.

## Install

```sh
npm install --save-dev @vu0tran/vsc
npx shellcheck scripts/*.sh        # or npx vsc
```

### In place of the `shellcheck` package

The package has two commands, `vsc` and `shellcheck`. To switch a project that runs `shellcheck`
from npm (the [`shellcheck`](https://www.npmjs.com/package/shellcheck) wrapper), change one line in
`package.json`:

```diff
   "devDependencies": {
-    "shellcheck": "^4.1.0"
+    "shellcheck": "npm:@vu0tran/vsc@^0.1.0"
   }
```

Scripts such as `"lint:sh": "shellcheck -x scripts/*.sh"` then run vsc. Don't install it next to
another package that has a `shellcheck` command (both would claim `node_modules/.bin/shellcheck`).

Outside npm: release archives with `vsc` and `shellcheck` for Linux and macOS, an install script, a
GitHub Action in place of ludeeus/action-shellcheck, and pre-commit hooks:
https://github.com/vu0tran/vu/tree/main/shellcheck#install

## What's the same, what isn't

- `shellcheck --version` prints ShellCheck 0.11.0's text: vsc reports the version it matches.
- `--jobs N` (vsc only) checks files on N threads with the same output.
- Where ShellCheck runs out of memory or hangs (huge configure scripts, a closed stdin or stdout),
  vsc finishes.
- Platforms: Linux x64 and ARM64 (static binaries: any glibc or musl), macOS 12 or later on Apple
  silicon and Intel. No Windows build. On macOS, vsc was built and smoke-tested but not compared
  as thoroughly as on Linux.

## How it's installed

Like esbuild and oxlint: this package holds a small Node launcher, and npm installs the one
platform package that fits the machine (`@vu0tran/vsc-linux-x64`, `-linux-arm64`, `-darwin-x64`,
`-darwin-arm64`, picked by their `os`/`cpu` fields) as an optional dependency. Installing with
`--omit=optional` leaves the binary out. `VSC_BINARY=/path/to/vsc` runs another binary.

Source, measurements and how parity is checked: https://github.com/vu0tran/vu/tree/main/shellcheck
