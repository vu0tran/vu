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
report order (errcheck's sorted by file name). Cold golangci-lint runs order issues by which
package finishes first, so their limited output differs from run to run; and some analyzers
(staticcheck's ST1006) report in map order.

## Coverage

What golangci-lint enables by default (`linters.default: standard`), and the optional linters by
how often the 248 configs of the 500 most-starred Go repositories on GitHub (stars > 1500, fetched
2026-11-01) enable them:

| linter | configs enabling it | vgolint |
|---|---:|---|
| govet | 216 | 22 of the 33 default analyzers; `enable/disable/enable-all/disable-all` |
| ineffassign | 210 | yes |
| staticcheck | 206 | 43 checks; `checks` (globs, `-X`, golangci-lint's defaults) |
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

- Default linters, 21 modules (blackfriday ... zap), `default: standard`, no limits: 1744 of
  golangci-lint's 1754 findings, no extra findings except one ST1005 that golangci-lint hides
  behind an SA4006 on the same line. The 10 missing are the SSA checks SA4006, SA4009, SA5011 and
  SA4017.
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
  the printed blocks of implemented linters: identical on 13 repos; config errors (three v1
  configs) identical on stderr and exit code; the rest differ only by the unimplemented SSA checks
  and by which same-text issues the limits keep where golangci-lint's own order isn't stable.
- 16 command-line scenarios (subfolders, path prefix/abs, stats, json/checkstyle/sarif with
  severities, exit code, enable-only, groups, limits, `linters`, tests off, tab) and the diff modes
  (`--new`, `--new-from-rev`, `--whole-files`) against golangci-lint: identical but json's
  `SuggestedFixes`.

## Speed

CPU seconds (user+sys, best of 3), default linters, no limits, on a loaded 2-core VM: vgolint
without its cache vs golangci-lint with a warm cache.

| repo | vgolint | golangci-lint warm |
|---|---:|---:|
| dns | 0.58 | 1.05 |
| otto | 0.66 | 1.13 |
| zap | 0.43 | 1.10 |
| testify | 0.48 | 1.05 |
| gin | 0.56 | 1.19 |

The drop-in front end (config, processing, printing) didn't change vgolint's CPU time against the
previous version (0.58/0.70/0.45/0.46/0.51 s on the same repos, within noise;
`tools/bench_oldnew.sh`). Earlier full-corpus numbers: `tools/bench_cpu.txt`.

## Tools

`tools/gd.py` (default linters vs saved golangci-lint findings), `tools/cmp_cfg.py` (any config),
`tools/own_cmp.py` (each repo's own config, default flags, printed blocks), `tools/scen.sh` (one
command line, both tools, stdout/stderr/exit code), `tools/freq_fetch.sh` + `tools/freq_count.py`
(the GitHub config survey), `tools/doccmp.py` (the YAML/TOML/JSON reader against Python's),
`tools/gen_lintersdb.py` and `tools/gen_misspell.py` (generated tables).

## Not done

- Formatters (gofmt, goimports, gofumpt, gci, golines): need a go/printer port.
- revive, gocritic, gosec, bodyclose, unparam and the rest of the long tail.
- staticcheck's SSA checks (SA4006, SA4009, SA5011, SA4017 among the defaults) and govet's
  lostcancel, ifaceassert, loopclosure (pre-1.22), directive, slog, unsafeptr, stdversion,
  buildtag, cgocall, asmdecl, framepointer.
- Suggested fixes (`--fix`, json's `SuggestedFixes`).
- errcheck's `check-type-assertions` and `check-blank`; unused's settings; staticcheck's
  `initialisms`/`dot-import-whitelist`/`http-status-code-whitelist`.
- Parse errors are printed as vgolint's own `typechecking error` lines, not as golangci-lint's
  `typecheck` issues.
