# Releasing

Three things are released from this repository, each by pushing a tag:

| tag | workflow | what gets published |
|---|---|---|
| `vX.Y.Z` | `release.yml` | Vu itself: compiler + std + MCP servers (GitHub release, `install.sh`, `Formula/vu.rb`) |
| `vlint-vX.Y.Z` | `release-tools.yml` | vlint (oxlint drop-in): GitHub release `vlint-vX.Y.Z` with archives + npm packages |
| `vgolint-vX.Y.Z` | `release-tools.yml` | vgolint (golangci-lint drop-in): GitHub release `vgolint-vX.Y.Z` with archives, `install.sh`, a Homebrew formula file |

`release.yml` only reacts to `v[0-9]*` tags, so the tool tags don't start a Vu release. The tool
releases are created with `--latest=false`: `releases/latest` stays Vu's, which Vu's `install.sh`
depends on.

## Once: the npm token (vlint only)

1. On npmjs.com, sign in as the account (or organization) that owns the scope in `NPM_SCOPE` at the
   top of `.github/workflows/release-tools.yml` (`@vu0tran` now). The scope must be yours: for the
   user `vu0tran` it is; otherwise create an organization of that name, or change `NPM_SCOPE` (and
   the scope in `packaging/npm/vlint/README.md` follows it when the packages are made).
2. Create an access token: Access Tokens, Generate New Token, **Granular Access Token**, permission
   **Read and write** for packages (for the first release, "All packages": the five packages don't
   exist yet; after it you can narrow it to `@vu0tran/vlint` and the four `@vu0tran/vlint-*`
   platform packages), and allow it to publish without 2FA (the "bypass two-factor
   authentication" option) since CI can't answer a 2FA prompt. npm limits how long write tokens
   live (90 days at most when this was written; not checked against your account): renew the secret
   before it expires.
3. In the GitHub repository: Settings, Secrets and variables, Actions, New repository secret,
   name **`NPM_TOKEN`**, the token as the value.

Later, npm's trusted publishing (OIDC, no token) can replace the secret: on each of the five
packages' settings on npmjs.com, add this repository and `release-tools.yml` as a trusted
publisher; the workflow already has `id-token: write`. Then delete the secret.

vgolint needs no secret (the GitHub release uses the workflow's own token).

## A dry run first

Actions, **release-tools**, Run workflow, leave **tag** empty, pick the tool (or both). It builds
every platform on its own runner, smoke-tests each binary against the original tool's saved output,
makes and installs the npm tarballs in a scratch project and runs `npx oxlint` / `npx vlint` there,
runs `npm publish --dry-run`, and uploads the archives and tarballs as the run's artifacts.
Nothing is published. The version is `0.0.0-dev.<run number>`.

## Releasing vlint

```sh
git tag vlint-v0.1.0 && git push origin vlint-v0.1.0
```

The version is the tag's (`0.1.0`); nothing in the source needs bumping. The workflow:

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

## Releasing again

A tag whose run failed part-way: Actions, release-tools, Run workflow, **tag** = `vlint-v0.1.0` (the
tag must exist). Archives are re-uploaded over the release's, and npm packages already published
are skipped (npm never accepts the same version twice: a broken npm release needs a new version).

## Locally

```sh
sh packaging/tools/build.sh vlint 0.1.0 linux-x64        # dist/vlint-0.1.0-linux-x64.tar.gz
sh packaging/tools/build.sh vgolint 0.1.0 linux-x64      # dist/vgolint-0.1.0-linux-amd64.tar.gz
CC=aarch64-linux-gnu-gcc STRIP=aarch64-linux-gnu-strip sh packaging/tools/build.sh vlint 0.1.0 linux-arm64
sh packaging/tools/smoke.sh vlint path/to/vlint
node packaging/npm/vlint/make.mjs --version 0.1.0 --dist dist --out npm --allow-missing
```
