# Releasing

Six things are released from this repository, each by pushing a tag:

| tag | workflow | what gets published |
|---|---|---|
| `vX.Y.Z` | `release.yml` | Vu itself: compiler + std + MCP servers (GitHub release, `install.sh`, `Formula/vu.rb`) |
| `vlint-vX.Y.Z` | `release-tools.yml` | vlint (oxlint drop-in): GitHub release `vlint-vX.Y.Z` with archives + npm `@vu0tran/vlint` |
| `vgolint-vX.Y.Z` | `release-tools.yml` | vgolint (golangci-lint drop-in): GitHub release `vgolint-vX.Y.Z` with archives, `install.sh`, a Homebrew formula file |
| `vsc-vX.Y.Z` | `release-tools.yml` | vsc (ShellCheck 0.11.0 drop-in): GitHub release `vsc-vX.Y.Z` with ShellCheck-named archives, `install.sh` + npm `@vu0tran/vsc` |
| `vjq-vX.Y.Z` | `release-tools.yml` | vjq (jq 1.7.1 drop-in): GitHub release `vjq-vX.Y.Z` with jq-named binaries, archives, `install.sh` + npm `@vu0tran/vjq` |
| `vknip-vX.Y.Z` | `release-tools.yml` | vknip (knip 6.44.1 drop-in): GitHub release `vknip-vX.Y.Z` with archives, `install.sh` + npm `@vu0tran/vknip` |

`release.yml` only reacts to `v[0-9]*` tags, so the tool tags don't start a Vu release. The tool
releases are created with `--latest=false`: `releases/latest` stays Vu's, which Vu's `install.sh`
depends on. A tool's version is its own (vsc 0.1.0 checks as ShellCheck 0.11.0 does); nothing in the
source needs bumping: the version is the tag's.

Each npm tool is five packages: one per platform (`@vu0tran/TOOL-linux-x64`, `-linux-arm64`,
`-darwin-x64`, `-darwin-arm64`, holding the binary) and the main one (`@vu0tran/TOOL`, a Node launcher
with the commands, naming the others as optionalDependencies). They are published in that order.

## Once: npm publishing rights (vlint, vsc, vjq, vknip)

The workflow **stages** each npm version (`npm stage publish`, [staged
publishing](https://docs.npmjs.com/staged-publishing), npm 11.15 or later, installed in the npm
job): staging needs no 2FA, and nothing goes live until you approve it with 2FA. So the token
needs no 2FA bypass.

1. **The token, once:** npmjs.com (signed in as `vu0tran`, the owner of the `@vu0tran` scope in
   `NPM_SCOPE` at the top of `.github/workflows/release-tools.yml`), Access Tokens, Generate New
   Token, Granular Access Token: **Read and write** on **All packages** (a token limited to selected
   packages can't create new ones). In the GitHub repository: Settings, Secrets and variables,
   Actions, secret **`NPM_TOKEN`**. npm limits how long write tokens live: renew it before it expires.
2. **Each release:** push the tag; the run builds, tests, creates the GitHub release and stages the
   five npm packages (its log ends with a notice saying so). Then approve them, with your 2FA code:
   npmjs.com, your account, **Staged Packages**, Approve on each (platform packages first, the main
   one last); or from a terminal: `npm stage list`, then `npm stage approve ID` for each.
3. **Then check:** Actions, release-tools, Run workflow with the tag (e.g. `vsc-v0.1.0`): it skips
   what is published and installs each tool from npm on the four platforms. Until the approval, the
   run's check job tests the GitHub release only and says the npm check is waiting.

**Trusted publishing** (OIDC, no token: [docs](https://docs.npmjs.com/trusted-publishers)) can
replace the token for packages that exist: on each package's settings on npmjs.com, Trusted
Publisher, GitHub Actions, user `vu0tran`, repository `vu`, workflow `release-tools.yml`. The npm
job has `id-token: write` and npm 11.15 or later, so the workflow uses it when it's set up, and the
token otherwise. Staging still waits for your approval.

**What happened with vlint 0.1.0** (before staging): the account requires 2FA for publishing and the
token had no 2FA bypass, so publishing from CI failed; the run's tarballs were published by hand
from a Mac with an OTP ("By hand", below). That path still works.

vgolint needs no secret, nor do the GitHub releases of the others (the workflow's own token).

## By hand: publishing a run's npm tarballs

Every run of `release-tools.yml` (dry runs included) uploads the npm packages it made, packed and
already installed and smoke-tested, as the artifact **`npm-tarballs-TOOL`** (`npm-tarballs-vsc`,
...; vlint 0.1.0's run called it `npm-tarballs`). To publish them yourself:

1. Download the artifact from the tag's run (Actions, release-tools, the run, Artifacts), or
   `gh run download RUN_ID -R vu0tran/vu -n npm-tarballs-vsc`, and unzip it. It holds five files:
   `vu0tran-vsc-linux-x64-0.1.0.tgz`, `-linux-arm64-`, `-darwin-x64-`, `-darwin-arm64-` and
   `vu0tran-vsc-0.1.0.tgz`. (Use the tag's run: a dry run's packages have the version
   `0.0.0-dev.N`.)
2. `npm login` once, then in that folder publish the four platform packages first and the main
   one last (it names the others; installing it before they exist would leave the binary out):

   ```sh
   npm publish ./vu0tran-vsc-linux-x64-0.1.0.tgz --access public --otp CODE
   npm publish ./vu0tran-vsc-linux-arm64-0.1.0.tgz --access public --otp CODE
   npm publish ./vu0tran-vsc-darwin-x64-0.1.0.tgz --access public --otp CODE
   npm publish ./vu0tran-vsc-darwin-arm64-0.1.0.tgz --access public --otp CODE
   npm publish ./vu0tran-vsc-0.1.0.tgz --access public --otp CODE
   ```

   (CODE: a fresh code from the authenticator for each command; without `--otp` npm asks for it,
   or opens the browser). Keep the `./`:
   `npm publish dir/file.tgz` without it can be taken for a GitHub repository `dir/file.tgz`.
   A prerelease version (`0.2.0-rc.1`) needs `--tag next`, or it becomes `latest`.
3. Re-run the workflow for the tag (Run workflow, **tag** = `vsc-v0.1.0`): the npm job finds every
   package published and skips it, and the check job installs from the registry on the four
   platforms. Packages published by hand have no provenance statement (only CI publishes add one).

## A dry run first

Actions, **release-tools**, Run workflow, leave **tag** empty, pick the tool (or all). It builds
every platform on its own runner, smoke-tests each binary against the original tool's saved output
(and the Linux ones again in Alpine), makes and installs the npm tarballs in a scratch project and
runs the commands there (`npx oxlint`, `shellcheck`, `jq`, `knip` from `node_modules/.bin`), runs
`npm publish --dry-run`, and uploads the archives and tarballs as the run's artifacts. Nothing is
published. The version is `0.0.0-dev.<run number>`.

## Releasing vlint

```sh
git tag vlint-v0.1.0 && git push origin vlint-v0.1.0
```

The workflow:

1. builds `vlint` for linux-x64, linux-arm64 (static, `-march=x86-64-v2` / `armv8-a`), darwin-arm64
   and darwin-x64 (macOS 12+), smoke-tests each (and the Linux ones again in Alpine);
2. creates the GitHub release `vlint-v0.1.0` with `vlint-0.1.0-<platform>.tar.gz` and `SHA256SUMS`;
3. publishes to npm, with provenance: `@vu0tran/vlint-linux-x64`, `-linux-arm64`, `-darwin-x64`,
   `-darwin-arm64`, then `@vu0tran/vlint` (a version with a `-`, like `0.2.0-rc.1`, goes under the
   dist-tag `next`); packages already at that version are skipped, so a failed run can be re-run;
4. installs `oxlint@npm:@vu0tran/vlint@0.1.0` from the registry on all four platforms and runs it on
   the fixture.

Users then install it with `npm i -D @vu0tran/vlint`, or switch from oxlint by changing one line:
`"oxlint": "npm:@vu0tran/vlint@^0.1.0"` (see `packaging/npm/vlint/README.md`).

## Releasing vgolint

```sh
git tag vgolint-v0.1.0 && git push origin vgolint-v0.1.0
```

The workflow builds the same four platforms, smoke-tests them (with Go installed, as vgolint reads
the standard library), and creates the GitHub release `vgolint-v0.1.0` with
`vgolint-0.1.0-{linux,darwin}-{amd64,arm64}.tar.gz` (golangci-lint's naming), `SHA256SUMS`,
`install.sh` and `vgolint.rb` (a Homebrew formula for that release; not published anywhere), then
installs it with `golint/install.sh` on all four platforms and runs it on the fixture.

Users then install it with:

```sh
curl -sSfL https://raw.githubusercontent.com/vu0tran/vu/main/golint/install.sh | sh -s -- -b $(go env GOPATH)/bin v0.1.0
```

or in GitHub Actions with `uses: vu0tran/vu/golint/action@vgolint-v0.1.0` (see `golint/README.md`).
To offer it through Homebrew, copy `vgolint.rb` from the release to `Formula/vgolint.rb` on main
(this repository is already a tap: `brew install vu0tran/vu/vgolint`).

## Releasing vsc

```sh
git tag vsc-v0.1.0 && git push origin vsc-v0.1.0
```

The workflow builds `vsc` for the four platforms (as vlint), smoke-tests each against ShellCheck
0.11.0's saved output (`packaging/tools/fixtures/vsc.expected`: ten invocations, every format), and
publishes:

- the GitHub release `vsc-v0.1.0`: `vsc-v0.1.0.linux.x86_64.tar.xz`, `.linux.aarch64`,
  `.darwin.x86_64`, `.darwin.aarch64` (ShellCheck's names, `shellcheck-v0.11.0.linux.x86_64.tar.xz`,
  with `vsc` for `shellcheck`), each holding `vsc-v0.1.0/vsc`, `vsc-v0.1.0/shellcheck` (a link to
  it), LICENSE, NOTICE and README.md; `SHA256SUMS`; `install.sh` (`packaging/tools/install.sh`);
- npm: `@vu0tran/vsc-<platform>` then `@vu0tran/vsc`, with the commands `vsc` and `shellcheck`;
- then the check job installs it with `install.sh` and from npm (`shellcheck@npm:@vu0tran/vsc@0.1.0`)
  on all four platforms, runs the fixture through both, and runs `shellcheck/action` on it.

Users switch with one line: `"shellcheck": "npm:@vu0tran/vsc@^0.1.0"` in package.json, or
`uses: vu0tran/vu/shellcheck/action@vsc-v0.1.0` in place of `ludeeus/action-shellcheck` (same
inputs), or `repo: https://github.com/vu0tran/vu` / `rev: vsc-v0.1.0` / `id: shellcheck` in a
pre-commit config (`.pre-commit-hooks.yaml`; it runs the installed vsc). See `shellcheck/README.md`, Install.

## Releasing vjq

```sh
git tag vjq-v0.1.0 && git push origin vjq-v0.1.0
```

The Linux binaries are static and never load Oniguruma (`jq/glue.c` skips `dlopen` in a static
program), so the few regex constructs vjq leaves to Oniguruma are an error in them; the macOS ones
link only libSystem and try `dlopen("libonig.5.dylib")` at the first such construct, which finds a
libonig only in dyld's default paths (Intel Homebrew's `/usr/local/lib`; not tested). The constructs:
`jq/README.md`, Regular expressions. jq's five test suites pass with the static binary. The workflow publishes:

- the GitHub release `vjq-v0.1.0`: the bare binaries `jq-linux-amd64`, `jq-linux-arm64`,
  `jq-macos-amd64`, `jq-macos-arm64` (jq's release asset names, so a `curl -o /usr/local/bin/jq
  .../releases/download/jq-1.7.1/jq-linux-amd64` line changes only its URL), the archives
  `vjq-0.1.0-{linux,macos}-{amd64,arm64}.tar.gz` (`vjq` and `jq`, a link to it), `SHA256SUMS` and
  `install.sh`;
- npm: `@vu0tran/vjq-<platform>` then `@vu0tran/vjq`, with the commands `vjq` and `jq`;
- then the check job installs it with `install.sh`, the bare binary and npm on all four platforms,
  and runs `jq/action`.

## Releasing vknip

```sh
git tag vknip-v0.1.0 && git push origin vknip-v0.1.0
```

npm is vknip's main channel, as it is knip's: `@vu0tran/vknip-<platform>` then `@vu0tran/vknip`,
with the commands `vknip` and `knip`, so `"knip": "npm:@vu0tran/vknip@^0.1.0"` switches a project.
The main package depends on `jiti` (`^2.7.0`, knip 6.44.1's range), which vknip's node process uses
to load JavaScript and TypeScript configs when the project has no jiti of its own (the launcher puts
it on `NODE_PATH`), and holds `types.d.ts`, `knip/config` (`defineConfig`) and knip's `schema.json`,
so `import type { KnipConfig } from "knip"` keeps type-checking. The GitHub release
`vknip-v0.1.0` has `vknip-0.1.0-<platform>.tar.gz` (`vknip` and `knip`), `SHA256SUMS` and
`install.sh`, for machines without npm (their node then needs the project's jiti, or Node's own
type stripping, for TypeScript configs). The check job installs it with `install.sh` and
`knip@npm:@vu0tran/vknip@0.1.0` on all four platforms and runs the fixture (whose `knip.config.ts`
loads through node).

## Releasing again

A tag whose run failed part-way: Actions, release-tools, Run workflow, **tag** = `vsc-v0.1.0` (the
tag must exist). Archives are re-uploaded over the release's, and npm packages already published
are skipped (npm never accepts the same version twice: a broken npm release needs a new version).

## Locally

```sh
sh packaging/tools/build.sh vlint 0.1.0 linux-x64        # dist/vlint-0.1.0-linux-x64.tar.gz
sh packaging/tools/build.sh vgolint 0.1.0 linux-x64      # dist/vgolint-0.1.0-linux-amd64.tar.gz
sh packaging/tools/build.sh vsc 0.1.0 linux-x64          # dist/vsc-v0.1.0.linux.x86_64.tar.xz
sh packaging/tools/build.sh vjq 0.1.0 linux-x64          # dist/vjq-0.1.0-linux-amd64.tar.gz, dist/jq-linux-amd64
sh packaging/tools/build.sh vknip 0.1.0 linux-x64        # dist/vknip-0.1.0-linux-x64.tar.gz
CC=aarch64-linux-gnu-gcc STRIP=aarch64-linux-gnu-strip sh packaging/tools/build.sh vlint 0.1.0 linux-arm64
sh packaging/tools/smoke.sh vsc path/to/vsc              # against ShellCheck 0.11.0's saved output
SMOKE_SAVE=1 sh packaging/tools/smoke.sh vsc path/to/shellcheck-0.11.0   # saves the original's output
node packaging/npm/make.mjs --tool vsc --version 0.1.0 --dist dist --out npm --allow-missing
```

`make.mjs` has one table of the tools (archive names, commands, extra files); the launcher is
`packaging/npm/launcher.js` (vlint keeps its own, `packaging/npm/vlint/bin/vlint.js`, whose
`--version` and `--help` are vlint's).
