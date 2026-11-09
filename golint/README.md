# vgolint: golangci-lint in Vu

`vgolint` is a drop-in replacement for `golangci-lint run` (v2.5.0): same command line, same
config files, same output in every format, same exit codes, for the linters it implements.

```
vu build --release golint/main.vu -o vgolint
vgolint run                      # as golangci-lint run: finds .golangci.yml, lints ./...
vgolint run -E misspell --output.json.path report.json ./pkg/...
vgolint linters | help linters | version | config path | cache clean
```

Its own Go front end (scanner, parser, a type checker that loads dependencies from GOROOT and
the module cache lazily) feeds ports of the linters. Packages are found as `go list` finds them
for linux/amd64 (build tags from `run.build-tags` included) and linted on all cores; results are
cached per run, keyed by every linted file, go.mod/go.sum, the Go version, the effective config
and the binary (`--no-cache` turns that off).

## Install

Releases are tagged `vgolint-vX.Y.Z` and have archives named as golangci-lint's
(`vgolint-0.1.0-linux-amd64.tar.gz`, `-linux-arm64`, `-darwin-amd64`, `-darwin-arm64`) with
`SHA256SUMS`. Each archive holds one binary, `vgolint`. Linux binaries are static (any glibc or
musl); macOS binaries need macOS 12 or later. There is no Windows build (Vu doesn't target Windows).

**The installer** has golangci-lint's interface, so switching is one line:

```sh
# golangci-lint:
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.5.0
# vgolint:
curl -sSfL https://raw.githubusercontent.com/vu0tran/vu/main/golint/install.sh | sh -s -- -b $(go env GOPATH)/bin v0.1.0
```

It checks the archive against `SHA256SUMS` and installs `vgolint` and `golangci-lint`, a link to it,
so Makefiles and scripts that call `golangci-lint run` keep working. A `golangci-lint` that is
already in the folder and isn't vgolint's is left alone unless `-f` is given; `-n` installs
`vgolint` only. With no version it installs the newest vgolint release. The version is vgolint's own
(`v0.1.0`), not golangci-lint's: `golangci-lint version` says which golangci-lint it mirrors
(`golangci-lint has version 2.5.0 built with vgolint (Vu) ...`).

**What it needs where it runs** (as golangci-lint does): the Go toolchain's standard library
source and the module cache, because it type-checks against them. It reads source files and never
runs the Go compiler (the only `go` command it runs is `go env`). It finds them as golangci-lint does: `GOROOT` and
`GOMODCACHE` if set, else from `go env GOROOT GOMODCACHE` (the `go` on `PATH`), else
`/usr/local/go` and `$GOPATH/pkg/mod` (`~/go/pkg/mod`). Unlike golangci-lint, it never downloads
modules: run `go mod download` first where the cache may be empty (a fresh CI runner without a
module cache). A dependency missing from the cache isn't reported: vgolint lints without its types
(checked: an import of an absent module gave the other findings and no error, where golangci-lint
reports a typecheck error), so findings that need them can be missed. It also uses `git` for `--new`, `--new-from-rev` and the other diff modes.

**GitHub Actions**: golangci-lint-action downloads golangci-lint's own releases, so use the
composite action in this repository instead, with the same common inputs (`version`, `args`,
`working-directory`, `only-new-issues`, `install-only`, `problem-matchers`, `github-token`):

```diff
   - uses: actions/setup-go@v6
     with:
       go-version: stable
-  - uses: golangci/golangci-lint-action@v8
+  - uses: vu0tran/vu/golint/action@vgolint-v0.1.0
     with:
-      version: v2.5
+      version: v0.1.0
       args: --timeout=5m
```

It installs the release on `PATH` (`vgolint` and `golangci-lint`), runs `go mod download`
(`go-mod-download: false` skips it), and runs `vgolint run ARGS`. `only-new-issues` takes the pull
request's diff (or a push's) from the GitHub API and passes it as `--new-from-patch`, as
golangci-lint-action does. Not supported: golangci-lint-action's caching inputs (`skip-cache`,
`skip-save-cache`, `cache-invalidation-interval`), `install-mode`, `verify` (vgolint doesn't check
configs against golangci-lint's JSON schema) and Windows runners.

**Homebrew**: each release carries `vgolint.rb`, a formula for it (`packaging/homebrew/vgolint_formula.sh`
writes it); it isn't published. It installs `vgolint` only, since a `golangci-lint` command would
clash with Homebrew's golangci-lint.

Releasing: `RELEASING.md`.

Platform notes: packages are matched for linux/amd64 on every platform (as above), so on macOS
files with `_darwin.go` suffixes or `//go:build darwin` lines are skipped where golangci-lint on a
Mac would lint them. On macOS the result cache is off (it is keyed by `/proc/self/exe`).

## Drop-in status

### Commands

| command | status |
|---|---|
| `run` | supported (see flags) |
| `linters` | supported (same listing; vgolint warns on stderr about enabled linters it skips) |
| `help`, `help linters`, `help formatters` | supported (golangci-lint's own text) |
| `version`, `--version` | prints `golangci-lint has version 2.5.0 built with vgolint (Vu) ...` |
| `config path`, `config verify` | path: supported; verify: loads and validates the config (no JSON-schema check) |
| `cache clean`, `cache status` | vgolint's own cache |
| `fmt`, `migrate`, `custom`, `formatters` | not yet |

### `run` flags

| flag | status |
|---|---|
| `-c/--config`, `--no-config` | supported (`~/` expanded; both together give golangci-lint's error) |
| `--default`, `-E/--enable`, `-D/--disable`, `--enable-only`, `--fast-only` | supported (unknown names, formatters and `typecheck` give golangci-lint's errors) |
| `-j/--concurrency` | supported |
| `--issues-exit-code` | supported |
| `--build-tags` | supported |
| `--tests` | supported |
| `--timeout` | parsed and validated; not enforced |
| `--modules-download-mode` | validated; vgolint never downloads |
| `--allow-parallel-runners`, `--allow-serial-runners` | accepted (vgolint takes no lock) |
| `--path-prefix`, `--path-mode` | supported |
| `--show-stats` | supported |
| `--output.{text,json,tab,html,checkstyle,code-climate,junit-xml,teamcity,sarif}.path` | supported (stdout, stderr or a file relative to the base path) |
| `--output.text.{print-linter-name,print-issued-lines,colors}`, `--output.tab.{print-linter-name,colors}`, `--output.junit-xml.extended` | supported |
| `--max-issues-per-linter`, `--max-same-issues`, `--uniq-by-line` | supported, in golangci-lint's warm-cache order (below) |
| `-n/--new`, `--new-from-rev`, `--new-from-merge-base`, `--new-from-patch`, `--whole-files` | supported (git diff, untracked files count as new) |
| `--fix` | accepted; no fixes are applied yet |
| `--cpu-profile-path`, `--mem-profile-path`, `--trace-path` | accepted, ignored |
| `--color`, `-v`, `-h` | `--color` supported (colors as fatih/color decides: a terminal, `TERM` not `dumb`, no `NO_COLOR`); `-v` accepted |

Bad usage gives golangci-lint's messages and exit code 3 (`unknown flag`, `invalid argument ... for
"--max-same-issues" flag`, `unknown command`).

### Config

- Discovery as viper does it for golangci-lint: `.golangci.json`, `.toml`, `.yaml`, `.yml` (that
  order) in the working directory, then from the first argument's folder up to `/`, then `$HOME`.
- YAML (block and flow collections, quoting, block scalars, anchors and merge keys), TOML and JSON,
  read into one tree with viper's case-insensitive keys and mapstructure's weak typing (a scalar
  where a list is expected is split at commas). The YAML reader gives the same tree as PyYAML on
  256 real configs (the 248 below plus the corpus').
- The v2 schema: `version` (anything but "2" is golangci-lint's migration error), `run.*`,
  `output.formats.*`, `output.sort-order|show-stats|path-prefix|path-mode`, `linters.default|enable|
  disable|settings|exclusions` (`generated: strict|lax|disable`, `presets`, `rules` with
  `path/path-except/text/source/linters`, `paths`, `paths-except`, `warn-unused`),
  `issues.max-*|uniq-by-line|new*|whole-files|fix`, `severity.default|rules`, `formatters.enable|
  settings|exclusions.paths`. Flags override the file; `-E/-D/--build-tags` append, as in golangci-lint.
- Validation with golangci-lint's messages: exclusion rules (two conditions, path vs path-except,
  regexps), presets, sort-order, path-mode, relative-path-mode, modules-download-mode, durations,
  severity rules, unknown linters and groups.
- `run.relative-path-mode` (cfg, the default; wd; gomod; gitroot) decides what printed paths and
  `path` rules are relative to, as in golangci-lint.
- Regexps are Go's syntax rewritten for std's `re` (`(?i)` and the other flags, `(?P<n>...)`, `\z`,
  `\Q..\E`, `[[:class:]]`).
- `//nolint` as golangci-lint 2.5.0 reads it: v2 names only (`//nolint:gosimple` no longer covers
  staticcheck), ranges widened to the next declaration or statement, unknown names reported as a
  warning, and nolintlint's unused-directive findings.

### Output

Each format byte-identical to golangci-lint's on the same issues: text (colors, source lines and
carets, the summary), tab (tabwriter alignment), json (report with the linters list and warnings),
html, checkstyle, code-climate (MD5 fingerprints), junit-xml (plain and extended), teamcity and
sarif. Checked on uuid with all nine at once (`--output.*.path`): eight identical, json identical
except `SuggestedFixes` (vgolint has no fixes yet). Warnings go to stderr as
`level=warning msg="[runner/...] ..."`.

The per-linter and same-text limits keep the first issues in golangci-lint's processing order,
which vgolint reproduces as golangci-lint has it with a warm cache: packages in `go list -deps
-test` order (untested packages by dependencies, then each tested package's test variant and
external test package), then linter by linter (those with their own reporters first), each in its
report order (errcheck's sorted by file name). golangci-lint itself isn't deterministic here:
a cold run orders packages by which finishes first, a warm one by iterating a Go map of packages
(`loadIssuesFromCache`), and some analyzers (staticcheck's ST1006, unconvert) report in map order,
so where the limits cut across packages its own output changes from run to run. Without limits
(or where they don't cut) the output is the same.

## Coverage

What golangci-lint enables by default (`linters.default: standard`), and the optional linters by
how often the 248 configs of the 500 most-starred Go repositories on GitHub (stars > 1500, fetched
2026-11-01) enable them:

| linter | configs enabling it | vgolint |
|---|---:|---|
| govet | 216 | 22 of the 33 default analyzers; `enable/disable/enable-all/disable-all` |
| ineffassign | 210 | yes |
| staticcheck | 206 | 68 checks, the IR-based SA4006/SA4009/SA4017/SA5011 among them; `checks` (globs, `-X`, golangci-lint's defaults) |
| unused | 196 | yes |
| errcheck | 168 | yes; `exclude-functions`, `disable-default-exclusions` |
| misspell | 145 | yes (locale US/UK, ignore-rules, extra-words, mode) |
| goimports | 132 | not yet |
| unconvert | 132 | yes (fast-math) |
| revive | 115 | not yet |
| gofmt | 114 | not yet |
| bodyclose | 94 | not yet |
| gocritic | 90 | not yet |
| gosec | 86 | not yet |
| whitespace | 81 | yes (multi-if, multi-func) |
| nolintlint | 80 | yes (allow-unused, require-explanation, require-specific, allow-no-explanation) |
| unparam | 77 | not yet |
| gofumpt | 74 | not yet |
| copyloopvar | 68 | yes (check-alias; off below Go 1.22) |
| nakedret | 66 | yes (max-func-lines) |
| asciicheck | 57 | yes |
| dogsled | 42 | yes (max-blank-identifiers) |
| predeclared | 35 | yes (ignore, qualified-name) |
| gocyclo | 31 | yes (min-complexity, `//gocyclo:ignore`) |

Enabled linters that vgolint doesn't implement are skipped with one stderr warning
(`VGOLINT_QUIET=1` silences it); nolintlint then doesn't judge directives naming them.

## Parity

- Default linters (`default: standard`), no limits, against golangci-lint 2.5.0 (2026-11-09):
  - golang.org/x/{tools (go, internal, refactor), net, text, crypto, mod, sync}: 3151 of the 3151
    findings of the implemented checks, none extra. The one finding of an unported check is
    SA4020's. These six modules ranked which staticcheck checks to port next: the 21-module corpus
    below never triggered 17 of them.
  - the 21-module corpus (blackfriday ... zap, plus `synth`): 1793 of 1796, none extra. The three
    misses are synthetic cases of aliasing the IR resolves: `p := &x; *p`, `ok := p != nil; if ok`,
    `q := p`.
- staticcheck's IR checks (SA4006, SA4009, SA4017, SA5011) run on a model of its IR rather than
  the IR (`ssa.vu`): which locals it lifts to registers (partly, before their address is taken),
  liveness, the exit block reading named results, NoReturn and purity facts (the standard
  library's dumped from staticcheck itself: `tools/dumpfacts`, `tools/gen_ssadata.py`), and for
  SA5011 and `x = y` the IR's values: phis, sigmas at the post-dominance frontier, renaming.
- The optional linters above, same 21 modules, all enabled with gocyclo at 10: 900 of 900
  findings, none extra (gocyclo 563, whitespace 204, nakedret 79, predeclared 41, misspell 9,
  dogsled 4; `tools/opt_a.yml`). A second config with every setting changed (`tools/opt_b.yml`:
  gocyclo 20, dogsled 1, nakedret 5, predeclared qualified, whitespace multi-if/multi-func,
  misspell US, copyloopvar check-alias): 936 of 936, none extra. unconvert and nolintlint
  (`tools/opt_c.yml`): 24 of 25, none extra (the miss: a conversion of an index into a generic
  `~[]byte | ~string` value, whose element type vgolint's checker doesn't derive). asciicheck,
  copyloopvar, unconvert and nolintlint, which the corpus barely exercises, also on a synthetic
  module: 26 of 26.
- Each corpus repo with its own config and golangci-lint's default flags (limits on), comparing
  the printed blocks of implemented linters (`tools/own_cmp.py`): identical on 12 of 21 repos
  (279 of 732 blocks are in those repos); the three v1 configs (gin, goleveldb, otto) give the same
  error on stderr and exit code 3; bolt, gopher-lua and synth differ by SA4006/SA4009/SA5011/SA4017,
  testify and websocket by which errcheck issues the 50-per-linter limit keeps; the rest differ only by the unimplemented SSA checks,
  by which issues the limits keep where golangci-lint's own order isn't stable (above), and on
  cobra by a `//nolint:gosec` that golangci-lint reports as unused and vgolint, which doesn't run
  gosec, leaves alone.
- 16 command-line scenarios (subfolders, path prefix/abs, stats, json/checkstyle/sarif with
  severities, exit code, enable-only, groups, limits, `linters`, tests off, tab) and the diff modes
  (`--new`, `--new-from-rev`, `--whole-files`) against golangci-lint: identical but json's
  `SuggestedFixes`.

## Speed

Wall clock, ms, default linters, no limits, 2-core VM, 2026-11-09 (`tools/bench2.sh`,
`tools/bench_edit.sh`; best of 3, cold runs once). Over the 21 corpus modules and x/net, text,
crypto and mod:

| | vgolint | golangci-lint | vgolint faster by |
|---|---:|---:|---:|
| both caches warm (nothing changed) | 9-99 | 292-1261 | 13x-43x (median 35x) |
| cold (golangci-lint after `cache clean`; vgolint `--no-cache`) | 60-1259 | 2373-26762 | 18x-88x (median 39x) |
| vgolint `--no-cache` against golangci-lint warm | 60-1259 | 292-1261 | 1.0x-5.7x (median 2.7x) |

The edit loop: one file changed, then the module linted again, both caches otherwise warm
(vgolint's cache is per package since 2026-11-09: the edited package and those that import it
are linted again, the rest read):

| module | file | vgolint | golangci-lint |
|---|---|---:|---:|
| dns | msg.go | 313 | 6871 |
| gin | context.go | 194 | 3313 |
| x/text | language/language.go | 786 | 12615 |
| x/text | unicode/norm/normalize.go | 776 | 11679 |
| x/net | http2/frame.go | 295 | 4480 |
| x/net | html/parse.go | 100 | 1544 |

dns and gin are one package each, so an edit there lints it all again. With the whole-run cache
before, x/text took 1261 and 1224 ms and x/net 639 and 652; reading a cache entry per package
costs the no-change run of x/text 99 ms where one entry took 54. Cached and uncached output are
the same byte for byte (stdout, stderr, exit code) on the 21 corpus modules under the four
configs, cold and warm (168 runs), and on x/text, net and dns.

## Tools

`tools/gd.py` (default linters vs saved golangci-lint findings), `tools/cmp_cfg.py` (any config),
`tools/own_cmp.py` (each repo's own config, default flags, printed blocks), `tools/scen.sh` (one
command line, both tools, stdout/stderr/exit code), `tools/freq_fetch.sh` + `tools/freq_count.py`
(the GitHub config survey), `tools/doccmp.py` (the YAML/TOML/JSON reader against Python's),
`tools/gen_lintersdb.py` and `tools/gen_misspell.py` (generated tables).

## Not done

- Formatters (gofmt, goimports, gofumpt, gci, golines): need a go/printer port.
- revive, gocritic, gosec, bodyclose, unparam and the rest of the long tail.
- staticcheck: 92 of its checks (most never fire on the modules measured; SA4020 does once),
  and the IR's alias resolution in SA4006/SA5011 above. govet's lostcancel, ifaceassert, loopclosure (pre-1.22), directive, slog, unsafeptr, stdversion,
  buildtag, cgocall, asmdecl, framepointer.
- Suggested fixes (`--fix`, json's `SuggestedFixes`).
- errcheck's `check-type-assertions` and `check-blank`; unused's settings; staticcheck's
  `initialisms`/`dot-import-whitelist`/`http-status-code-whitelist`.
- Parse errors are printed as vgolint's own `typechecking error` lines, not as golangci-lint's
  `typecheck` issues.
