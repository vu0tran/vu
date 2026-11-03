# vknip

[knip](https://knip.dev) 6.44.1 rewritten in [Vu](https://github.com/vu0tran/vu): it finds unused
files, dependencies, exports, types and members and unlisted dependencies in JavaScript and
TypeScript projects and monorepos, with knip's command line, configuration files, plugins,
reporters and exit codes, and prints knip's report byte for byte. It took 2 to 127 times less CPU
time than knip on the 23 projects it was measured on (`knip --version` prints 6.44.1, the version
it matches).

## Install

```sh
npm install --save-dev @vu0tran/vknip
npx knip                 # or npx vknip
```

### In place of knip

The package has two commands, `vknip` and `knip`. To switch a project that runs knip, change one
line in `package.json`:

```diff
   "devDependencies": {
-    "knip": "^6.44.1"
+    "knip": "npm:@vu0tran/vknip@^0.1.0"
   }
```

`npm run knip` (`"knip": "knip"`) then runs vknip, with the same `knip.json` / `knip.ts` /
`knip.config.ts` / `package.json#knip` configuration. With this alias, `import type { KnipConfig }
from "knip"` and `import { defineConfig } from "knip/config"` in a config keep working (the package
has their types, written by hand from knip's schema and looser than knip's), and so does
`node_modules/knip/schema.json`. To go back, restore the line.

## Node.js

vknip itself is a native binary, but JavaScript and TypeScript configurations (`knip.ts`,
`vite.config.ts`, `next.config.js`, ...) run in Node.js, as in knip: vknip starts one `node` process
(the one running this package's launcher) that imports them with [jiti](https://github.com/unjs/jiti):
the project's own when it has one, else the one this package depends on (the version range knip
6.44.1 uses). The launcher asks for Node 18 or later (checked with Node 22 only); knip itself wants
20.19 or later.

## What's not there

Be sure your project doesn't depend on these before switching:

- knip's JavaScript API (`main()` from `knip`), custom reporters and preprocessors, `knip-bun`.
- `--cycles` and the `cycles` configuration, custom `compilers`, the less and stylus compilers,
  `--watch`, `--trace*` and `--performance`.
- 42 of knip's 202 plugins have a part not ported (their default entry patterns are used); Nuxt and
  Vue auto-imports. The list: https://github.com/vu0tran/vu/tree/main/knip#gaps
- Platforms: Linux x64 and ARM64 (static binaries: any glibc or musl), macOS 12 or later on Apple
  silicon and Intel. No Windows build.

## How it's installed

Like esbuild and oxlint: this package holds a small Node launcher, and npm installs the one
platform package that fits the machine (`@vu0tran/vknip-linux-x64`, `-linux-arm64`, `-darwin-x64`,
`-darwin-arm64`, picked by their `os`/`cpu` fields) as an optional dependency. Installing with
`--omit=optional` leaves the binary out. `VKNIP_BINARY=/path/to/vknip` runs another binary.

Source, measurements and how parity is checked: https://github.com/vu0tran/vu/tree/main/knip
