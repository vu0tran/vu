# vjq

[jq](https://jqlang.org) 1.7.1 rewritten in [Vu](https://github.com/vu0tran/vu): the same filter
language and built-ins, command line, output bytes, error messages and exit codes, with 2.7 to 4.2
times less CPU time than jq on a 100 MB document (ten filters). jq 1.7.1's own test suites pass, and its output was
compared byte for byte with jq 1.7.1's release binary on generated programs and documents.

## Install

```sh
npm install --save-dev @vu0tran/vjq
echo '{"a": [1, 2]}' | npx jq -c '.a | map(. * 10)'      # or npx vjq
```

### In place of jq

The package has two commands, `vjq` and `jq`. In a project's `package.json` scripts (`"x": "jq ..."`)
`jq` then runs vjq. With a global install (`npm install -g @vu0tran/vjq`) the `jq` command can
shadow a system jq, depending on the order of your `PATH`: install it globally only if that is
what you want, or call `vjq`.

Outside npm: release binaries named as jq's (`jq-linux-amd64`, `jq-macos-arm64`, ...), archives with
`vjq` and `jq`, and an install script: https://github.com/vu0tran/vu/tree/main/jq#install

## What's the same, what isn't

- `jq --version` prints `jq-1.7.1`: vjq reports the version it matches.
- Regular expressions: vjq has its own engine, written to behave as the Oniguruma jq 1.7.1
  bundles. A few constructs (absent groups `(?~...)`, callouts, subexpression calls `\g<name>`,
  `\X`, `\y`, variable-length look-behind, raw `\xHH` bytes above 0x7F, some nested classes) are
  left to Oniguruma, which the Linux binaries never load (they are static; the macOS ones look
  for it only in dyld's default paths): such a pattern is then an error (`not supported by vjq's
  regex engine`). Everything else matched jq's Oniguruma on 250,000 fuzzed patterns.
- `--debug-dump-disasm` and `--debug-trace` are accepted but print nothing.
- Platforms: Linux x64 and ARM64 (static binaries: any glibc or musl), macOS 12 or later on Apple
  silicon and Intel. No Windows build.

## How it's installed

Like esbuild and oxlint: this package holds a small Node launcher, and npm installs the one
platform package that fits the machine (`@vu0tran/vjq-linux-x64`, `-linux-arm64`, `-darwin-x64`,
`-darwin-arm64`, picked by their `os`/`cpu` fields) as an optional dependency. Installing with
`--omit=optional` leaves the binary out. `VJQ_BINARY=/path/to/vjq` runs another binary.

Source, measurements and how parity is checked: https://github.com/vu0tran/vu/tree/main/jq
