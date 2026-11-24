# vgolint: golangci-lint in Vu

`vgolint` is a drop-in replacement for `golangci-lint run` (v2.14.0): same command line, same
config files, same output in every format, same exit codes, **for the linters it implements**
(Coverage below). A config that enables a linter vgolint doesn't have, or a revive rule it doesn't
have, gets one warning on stderr naming it, and that linter reports nothing: check the warning
before treating vgolint's output as golangci-lint's, or set `VGOLINT_REQUIRE_ALL=1` to make it an
error.

```
vu build --release golint/main.vu -o vgolint
vgolint run                      # as golangci-lint run: finds .golangci.yml, lints ./...
vgolint run -E misspell --output.json.path report.json ./pkg/...
vgolint linters | help linters | version | config path | cache clean
```

Its own Go front end (scanner, parser, a type checker that loads dependencies from GOROOT and
the module cache lazily) feeds ports of the linters. Packages are found as `go list` finds them
for the go command's build context (its GOOS, GOARCH, cgo, tool and release tags; build tags from
`run.build-tags` included) and linted on all cores; results are
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
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.14.0
# vgolint:
curl -sSfL https://raw.githubusercontent.com/vu0tran/vu/main/golint/install.sh | sh -s -- -b $(go env GOPATH)/bin v0.1.0
```

It checks the archive against `SHA256SUMS` and installs `vgolint` and `golangci-lint`, a link to it,
so Makefiles and scripts that call `golangci-lint run` keep working. A `golangci-lint` that is
already in the folder and isn't vgolint's is left alone unless `-f` is given; `-n` installs
`vgolint` only. With no version it installs the newest vgolint release. The version is vgolint's own
(`v0.1.0`), not golangci-lint's: `golangci-lint version` says which golangci-lint it mirrors
(`golangci-lint has version 2.14.0 built with vgolint (Vu) ...`).

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

Platform notes: packages are matched for the build context `go list` reports (GOOS and GOARCH from
the environment, as for go), so a Mac lints `_darwin.go` files as golangci-lint there does. The result cache works on macOS too (it was off there until 2026-11-20: its key
read `/proc/self/exe`).

The cache and local replaces: a module replaced with a local folder (`replace example.com/x =>
./x`) is no longer a reason to turn the cache off; the files of its packages that a linted package
imports, and those they import, go into that package's key. On a 2,981-package monorepo with two
such modules (2,900 files in them) a run whose results all come from the cache takes 1.76 s against
13.8 to 15.0 s without (it was 12.7 s on every run before: the cache was off there for both reasons).
The files are read and hashed on all cores, each once (they were read one after another and each
hashed twice). Checked on a module with a local replace: a changed signature in the replaced
module, imported directly and through another of its packages, reaches the next cached run, as
without the cache.

**Patterns and the uncached run (2026-11-20).** A package path given without `/...` (`vgolint run
./a ./b`) is now that one package, as `go list` reads it; it used to take every package under it
too, so on that monorepo, named as 2,981 folders, many packages were linted several times and their
issues printed up to 3 times. A package named twice, or under two patterns, is linted once. The
same run (2,981 packages, the repo's own config, 10 cores, macOS) without the cache now takes 5.5 to
6.3 s (it was 13.8 to 15.0) and with it 0.75 s (1.76): besides the patterns, gocyclo looked for
`//gocyclo:ignore` above every function by scanning the file's comments from the end (now only over
the limit), SA1019 found each declaration's doc comment by a scan from the file's start and copied
the declaring file per object, the deprecation table and the misspell and exclusion patterns were
built for each package or worker (now on first use), misspell lowered every word of every line (a
filter of the typos' hashes skips files with none), the package order read every file again, and
the workers read the module's files again. Packages go to the workers in runs of neighbouring
folders (which import mostly the same packages: each worker loads its own copy of what they import),
the largest first. Output is byte for byte what it was, with the repeated issues gone (16 issues,
the same set). `VGOLINT_T=1` prints each phase's time and each package over 0.3 s on stderr. What's
left is mostly type-checking the imported packages, which each of the 10 workers does for itself
(11,274 loads of 3,734 packages there).

**Later the same day: 4.8 to 5.4 s uncached, 0.6 s cached.** Each worker allocated its rule patterns
and staticcheck's standard library tables again (now once per worker, on first use, and a rule's
patterns only when an issue of one of its linters meets it); the module's files are read on 4 threads
(macOS opens files more slowly from more at once: 0.45 s against 0.22 for these 16,445); most of
staticcheck's checks get only the nodes of the kind they look at, from one pass, instead of each
walking all of them; children are walked without building a list per node; unused's edges are keyed
by Int; a linted package's tables are dropped once it's done. Measured: user time 37.7 to 35.5 s,
system 6.5 to 4.6 s. What doesn't pay here: workers by region of the tree (each still loads 1,200 to
1,500 imported packages, most of them imported all over the repo), and parsing a big imported file a
declaration at a time (496 to 304 MB parsed, 6.5 to 5.5 GB of memory, the same time). What's left
is mostly the imported packages each worker loads, parses and type-checks for itself (about a
quarter of the time): sharing them would take one type-checked copy built before the workers start,
which this design can't build in parallel.

**Imported packages once for all workers (Memo, 2026-11-20): about 4.1 s uncached.** With Vu's
`Memo` (SPEC.md), an imported package's files are read and indexed once for the run, by whichever
worker needs the package first (`tc.read_dep`, keyed by folder), and each of its files parsed once
(`tc.parse_dep`); a worker copies a parsed file into its own package (`ast.append`: nodes renumbered,
names appended, not interned again). The exclusion rules' patterns are compiled once for the run the
same way. On the 2,981 packages: 4.06 to 4.11 s (4.8 to 5.4 before), system time 4.6 to 2.8 s; byte
for byte the same output, cached and uncached. One worker takes 24.3 s of user time and ten 32.7 s:
what the ten still do each for themselves is mostly type-checking the imported declarations they use
(shared, it would need their objects and types numbered apart from each worker's, and types compared
by structure rather than by number), and copying the parsed files.

**3.4 s uncached (later on 2026-11-20).** Median 3.44 s, best 3.40, over 8 runs on the 2,981
packages (end to end, output checked each time; Spotlight and media analysis used about half a core
to a core meanwhile). Without the cache the workers start right after the folder walk (0.04 s, on 4
threads): each builds its folders' packages itself, reading their files through a Memo the imported
packages' loader shares, and the results go into go list's order afterwards, from the imports the
workers report (`stream_lint`; `VGOLINT_STREAM=0` reads everything first, as the cache does). The
scanner tells keywords apart in place and the parser interns names from the source bytes; vet and
gocyclo walk without a list per node, and the other linters reuse vet's walk; staticcheck compares
callee names in place and builds doc comments only when they hold a deprecation; printf keeps each
function's print kind. Nothing is freed before the run's exit (the Memos live in `run_lint`, and
workers park their state in a channel): freeing kept main, which shares a thread with a worker,
waiting up to half a second. Vu's runtime now finds its string pool with one thread-local lookup
instead of two (macOS makes each a call). User time 32.7 -> 28.0 s; exit, unmapping about 6 GB,
takes 0.10 to 0.14 s of the run.

**Imported packages cached on disk (2026-11-22): 3.9 to 3.2 s uncached on the corpus.** A folder of
the standard library or the module cache doesn't change between runs, so what a run reads and parses
there (the files that build, what each declares, each file's tree with function bodies skipped) is
kept in `~/.cache/vgolint/deps` (`$XDG_CACHE_HOME`), keyed by the folder, the Go installation and
the build tags, and used with `--no-cache` too, which is about the linted packages' results
(`VGOLINT_DEP_CACHE=0` turns it off; `cache clean` empties it). A folder's entry holds its files'
indexes; each file has its own entry, read only when a declaration in it is needed (gin's run reads
138 files from the 59 folders it takes a declaration from, which hold 1,465 non-test Go files). A cached tree goes straight into the worker's package, renumbered
as it's read. Literals are no longer looked up in the parser's name table (most are different):
x/text's CPU time 1.62 to 1.36 s. On the 21 corpus modules and x/text, net, crypto and mod
(`--no-cache`, best of 3, 2 cores, both binaries measured in the same session): 3,895 to 3,222 ms
wall, 6,144 to 5,012 ms CPU, byte for byte the same output under the default config and the three
`tools/opt_*.yml` (66 runs), cold or warm, and with entries truncated, deleted or overwritten with
noise, or two runs filling an empty cache at once. The cache takes about 31 MB for x/text's
imports, and the run that fills it costs about 0.1 s more (x/text: 0.89 s against 0.69 to 0.85).
What's left is flat: type-checking the linted packages and the imported declarations they use (each
worker for itself) about a third, staticcheck a quarter (its IR 9%), parsing the linted files 14%,
vet 9%, ineffassign 7%, unused 6%.

## goimports, ST1000 and ST1003, a whole monorepo (2026-11-24)

goimports (`goimports.vu`), on the printer: x/tools' own import sorting (not go/ast's: grouping by
`local-prefixes`, comments attached to the spec before them, merged lines, Go's pdqsort so that ties
land where sort.Sort puts them), the blank lines between groups, and on code that compiles the one
change goimports makes there, naming an import whose package name isn't the one its path suggests.
Files that import "C" are skipped by both formatters, as in golangci-lint. Identical text and JSON
(SuggestedFixes included) on 33 hand-made cases, a 884-file library scrambled seven ways with seven
`local-prefixes` settings (478 to 589 issues each), and scrambled copies of x/tools v0.50.0 (709
issues) and x/net v0.59.0 (354).

staticcheck's ST1000 and ST1003 (`sc_g7.vu`: lintName, `initialisms` or v0.8.1's default list, its
exceptions), so all 161 of v0.8.1's checks are in: 162 of the 173 testdata suites now identical.

The whole 105-pattern monorepo, golangci-lint 2.14.0 (empty cache, 4 cores) against vgolint:

| config | issues | |
|---|---:|---|
| its own (gofmt and goimports on) | 5 | byte-identical |
| strict: staticcheck `all` but ST1000/ST1003, govet, lll, revive, depguard, misspell, gocyclo, no limits | 187,963 | all the same; only the order of issues at one position differs, which golangci-lint's unstable sort doesn't fix |
| ST1000 and ST1003 with initialisms | 8,687 | byte-identical (golangci-lint 98 s, vgolint 17 s) |

On the way: the build context now comes from `go list` rather than being linux/amd64 (the standard
library lints as the `std` and `cmd` modules: 20,463 of golangci-lint's 20,514 issues on darwin, the
rest vendored packages and checks that skip their own package); govet's buildtag and directive read
the files build constraints leave out; patterns load as go list loads them (no package at all, a
named folder with no Go file or whose files are all left out: golangci-lint's errors and exit codes);
cached issues keep their extra source lines; and the type checker types imported generic fields and
methods in time, scopes local aliases, and keys parsed dependency files by path (a panic before).

`VGOLINT_REQUIRE_ALL=1` turns the "not implemented, skipped" warning into an error (exit 3), so a CI
job can't pass on a linter, govet analyzer or revive rule that never ran. `tools/shadow.sh` runs
vgolint beside golangci-lint in CI: golangci-lint's exit code is the job's, and the two tools' issues
(limits off) are compared and reported without failing it unless `SHADOW_STRICT=1`.

## gofmt (2026-11-24)

The gofmt formatter, as golangci-lint 2.14.0 runs it (github.com/golangci/gofmt, which is Go
1.27.3's cmd/gofmt): each file is parsed (`fparse.vu`, go/parser with every position go/ast keeps
and its comment groups), the rewrite rules applied (with go/ast's comment map, so comments attached
to a replaced node go, as in gofmt), its imports sorted (ast.SortImports), simplified (`-s`, the
default), and printed by a port of go/printer (`printer.vu`: printer.go and nodes.go function for
function, nodeSize's second printer, the //go:build fixing, text/tabwriter and the trimmer; doc
comments reformatted by go/doc/comment's parser and printer, `doccmt.vu`). A file that comes out
different gives golangci-lint's "File is not properly formatted" issues: the unified diff of
rogpeppe/go-internal, its hunks read as sourcegraph/go-diff reads them and turned into changes as
golangci-lint does, one issue per change (golangci-lint keeps a file's first), with its
`SuggestedFixes` in JSON. `vgolint fmt-debug [-s] [-r RULE] [-d] FILE` prints a file as it formats it.

Checked against Go 1.27.3's gofmt byte for byte, every file the same:

| corpus | files | `gofmt` | `gofmt -s` | `gofmt -r 'interface{} -> any'` |
|---|---:|---:|---:|---:|
| Go 1.27.3's src (testdata left out) | 6,827 | 6,827 | 6,827 | |
| the monorepo | 20,362 | 20,362 | 20,362 (`-s -r`, its settings) | |
| the module cache: every .go file but the toolchains' (13 GB) that gofmt accepts | 137,304 | 137,304 | 29,978 of a 30,000-file sample | the same 29,978 |
| Go's src, mangled | 6,827 | 6,827 | 6,827 | |
| the monorepo, mangled | 20,362 | 20,362 | 20,362 (`-s -r`) | |
| the module-cache sample, mangled | 29,978 | 29,978 | 29,978 | |
| Go's src, mangled with comments | 6,827 | 6,827 | 6,827 | |
| the monorepo, mangled with comments | 20,362 | | 20,362 (`-s -r`) | |
| 20,454 files of the module-cache sample, mangled with comments | 20,454 | 20,454 | | |

The mangled copies change what gofmt fixes: spacing between tokens, line breaks after `( [ { ,` and
operators (added and removed), indentation, blank lines, the space before trailing comments, a
missing final newline; the second set also puts `/* */` comments between tokens, `//` comments at
line ends, multi-line comments on their own lines and generated doc comments (paragraphs, lists,
code, headings, link definitions, `` and '') above declarations. Also identical: gofmt's own
testdata (cmd/gofmt's 24 cases with their flags, go/printer's 39 inputs and goldens, each also with
`-s` and two rewrite rules), go/doc/comment's 53 test inputs as `//` and `/* */` doc comments, the
1,215 files under Go's testdata folders that gofmt accepts, and about 23,000 generated files (random
programs, with and without `-s`) that aim at one part each (doc comments, import blocks with
duplicates and comments, `interface{}` in every position with comments around it, struct and const
alignment, line breaks in expressions, calls and signatures, statements with comments, block
comments, build lines, simplify's cases, number literals, CRLF and BOM, one-line function bodies
near the 100-column limit, key-value columns, selector chains, type parameters, statement sequences
with empty statements and labels, expressions of every kind, declarations, closures; 1,499 of them
module-cache files mangled with comments). Those found two differences, both fixed: a label last in
a block after an empty statement, and `2.5.F` (a selector on a float literal), which the scanner
read as one number.

The issues, golangci-lint 2.14.0 against vgolint, text and JSON (SuggestedFixes included)
identical:

- the monorepo with its own gofmt settings (rewrite `interface{}` -> `any`): 55 issues (all in
  folders its own config excludes, so with the whole config: none, as golangci-lint).
- A copy of the monorepo with 568 files mangled (spacing, or spacing and comments), its own
  config, twelve folders holding most of them: 252 gofmt issues (and every other linter's issues as
  before).
- 40 hand-made files of what the diff-to-issue path has to handle (`tools/fmtcases`: a deletion
  first, additions only, no final newline, CRLF, a BOM, build lines, generated files,
  `//nolint:gofmt`, duplicate and unsorted imports, doc comments).
- Standard-library packages copied into modules (18, and 37 others that build outside std), as
  they are and each set mangled with three seeds, under four configs (defaults, `simplify: false`, two rewrite
  rules with exclusion paths, generated files linted): 28 to 93 issues each.

With nothing unformatted, `0 issues.` as before; the other linters' output on the monorepo with
its own config is the same as before, byte for byte.

The cost, the monorepo with its own config (gofmt on), `--no-cache`, three
runs each on a loaded 10-core Mac: 43.4 s of CPU before, 49.2 s with gofmt (+13%); wall 6.1 s and
6.7 s. Formatting all 20,362 files on their own (`fmttest bench`, `-s` and the rewrite rule, one
thread) takes 10.8 s; vgolint formats only the files whose issues it can report (generated files
are skipped under `generated: lax`). The printer stops a nodeSize print once it can't fit, looks
lines up in a table, and the tabwriter keeps cells as stretches of its input.

## The rest of staticcheck and govet, as golangci-lint 2.14.0 (2026-11-24)

The 87 staticcheck checks vgolint didn't have are ported from v0.8.1 (`sc_g1.vu` to `sc_g5.vu`),
and the 25 it had that differed from v0.8.1 (they came from v0.6.1, golangci-lint 2.5.0's) are
updated; govet gains asmdecl, buildtag, cgocall, directive, framepointer, hostport, ifaceassert,
lostcancel, slog, stdversion, unsafeptr and waitgroup (`vet_g6.vu`). Several are modelled on
staticcheck's IR: block graphs with dominators and reaching definitions, lifting, nilness. Also: a
type declaration `type S[P *C, Q any]` parses as a type parameter list; related-information issues
follow their check's setting; SA1019's deprecation data is v0.8.1's; SA9007 reads the environment.

Each check's own testdata (staticcheck v0.8.1's, x/tools v0.50.0's for govet), each package a
module linted with only that check by golangci-lint 2.14.0 and by vgolint, text compared exactly:
158 of 173 identical. The 15 others: six whose testdata imports other testdata packages or
missing modules (identical once made loadable), two where golangci-lint's unstable sort orders
issues at one position differently, one that differs because golangci-lint loads darwin files on
a Mac, one `//line` case, ST1000 and ST1003 (not ported), and buildtag/directive's excluded files.
On the 2,981-package monorepo: its own config identical on three folders (`0 issues.`), the strict
config and revive's defaults identical but for which of two revive rules on one line golangci-lint
keeps (it changes between its runs).

golangci-lint isn't deterministic where limits cut: with the default max-same-issues 3 and
max-issues-per-linter 50, which of several identical messages it shows changes from run to run
(three runs, two different selections). vgolint finds the same issues and always shows the same ones.

## lll, depguard, revive and four staticcheck checks (2026-11-23)

Ported from the versions golangci-lint 2.14.0 pins (lll from golangci-lint itself, depguard v2.2.1,
revive v1.17.0, staticcheck v0.8.1); the rest of vgolint followed 2.5.0 until 0.6.0, which is
compared against 2.14.0 throughout.

- **lll**: line-length, tab-width; //go: lines and import blocks skipped.
- **depguard**: rule lists, files globs (gobwas/glob), allow/deny with `$gostd`, the three list
  modes, descriptions as suggestions; with no rules, list Main (the standard library only).
- **revive**: the 23 default rules and their arguments, golangci-lint's way of choosing rules (no
  settings: the defaults; settings: the listed rules, plus enable-default-rules or enable-all-rules),
  the confidence cutoff, `//revive:disable` directives, issues with a line range (all their source
  lines printed, `LineRange` in JSON).
- **staticcheck**: SA1000 (invalid regular expressions: `resyntax.vu`, Go 1.27.3's regexp/syntax
  parse checks with its messages, the same answer as regexp.Compile on 23,105 patterns), ST1020,
  ST1021, ST1022, and `dot-import-whitelist` for ST1001.
- Folders whose files are all `package x_test` were never linted; they are now.

Checked against golangci-lint 2.14.0 on the 2,981-package monorepo above:

- its lib/ folder with its own config: `0 issues.`, as golangci-lint (gofmt and goimports, which
  that config enables, are named on stderr as skipped).
- lib/ with a strict variant (lll at 100, no exclusion presets, depguard denying fmt, testify and
  uuid, revive's defaults, staticcheck all): byte-identical output, 5,445 issues (revive 2,224, lll
  2,680, depguard 337, errcheck 199, staticcheck 5).
- revive's defaults on lib/ and two large services: byte-identical, 6,886 issues
  over 14 rules; the rules that don't fire there (and arguments) on hand-written cases, 11 configs,
  1,284 issues, identical in text and JSON. vgolint takes 0.15 to 0.42 s on each folder, golangci-lint
  2.76 s on the larger service with its cache empty.
- SA1000 on staticcheck's own testdata and 16 more cases; depguard on three configs over its modes
  and globs: identical.

Where golangci-lint itself isn't deterministic, vgolint can't match it run for run: revive runs its
rules in Go map order, so when two rules report on one line, which one uniq-by-line keeps (and the
order of issues at one position) changes between runs; vgolint keeps the one listed first. And
golangci-lint 2.14.0's cache doesn't notice a change of revive's settings: after editing them, clear
it (`golangci-lint cache clean`) before comparing.

## Drop-in status

### Commands

| command | status |
|---|---|
| `run` | supported (see flags) |
| `linters` | supported (same listing; vgolint warns on stderr about enabled linters it skips) |
| `help`, `help linters`, `help formatters` | supported (golangci-lint's own text) |
| `version`, `--version` | prints `golangci-lint has version 2.14.0 built with vgolint (Vu) ...` |
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
  settings|exclusions.paths` (gofmt's `simplify` and `rewrite-rules`). Flags override the file; `-E/-D/--build-tags` append, as in golangci-lint.
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
| govet | 216 | golangci-lint 2.14.0's default analyzers (`loopclosure` fires only before Go 1.22); not the non-default atomicalign, deepequalerrors, fieldalignment, findcall, httpmux, inline, nilness, reflectvaluecompare, shadow, sortslice, unusedwrite; `enable/disable/enable-all/disable-all` |
| ineffassign | 210 | yes |
| staticcheck | 206 | all 161 of v0.8.1's checks, as staticcheck v0.8.1 has them; `checks` (globs, `-X`, golangci-lint's defaults), `dot-import-whitelist`, `initialisms` |
| unused | 196 | yes |
| errcheck | 168 | yes; `exclude-functions`, `disable-default-exclusions` |
| misspell | 145 | yes (locale US/UK, ignore-rules, extra-words, mode) |
| goimports | 132 | yes (`local-prefixes`), as x/tools v0.50.0 on code that compiles |
| unconvert | 132 | yes (fast-math) |
| revive | 115 | its 23 default rules with their arguments (golangci-lint 2.14.0's revive v1.17.0); not the other 82 |
| gofmt | 114 | yes (simplify, rewrite-rules), byte for byte as Go 1.27.3's gofmt |
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

Also: lll and depguard (as golangci-lint 2.14.0 runs them).

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

- Formatters gofumpt, gci, golines (the printer, `printer.vu`, is the base for them).
- revive's 82 non-default rules; gocritic, gosec, bodyclose, unparam and the rest of the long tail.
- govet's non-default analyzers listed under Coverage, and `loopclosure` before Go 1.22.
- Facts from other packages' function bodies (imported packages are type-checked without them):
  SA4018's purity, SA4023's nilness, SA5012's even-length arguments and lostcancel's no-return
  functions are known for the standard library (generated tables) but not for the module's own
  packages.
- `//line` directives aren't followed (one S1006 case).
- Suggested fixes (`--fix`; json's `SuggestedFixes` only for the formatters).
- errcheck's `check-type-assertions` and `check-blank`; unused's settings; staticcheck's
  `http-status-code-whitelist`.
- Parse errors are printed as vgolint's own `typechecking error` lines, not as golangci-lint's
  `typecheck` issues.
