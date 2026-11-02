# vsc: a drop-in replacement for ShellCheck, in Vu

`vsc` is ShellCheck 0.11.0 rewritten in Vu: the same command line, the same output in every
format (byte for byte, fixes included), the same `.shellcheckrc` lookup and directives, the same
exit codes, and all of ShellCheck's checks: the 511 codes in its source (SC1000-SC1146 parse
messages, SC2000-SC2335, SC3001-SC3067 bashisms) and its 11 optional checks. It uses 30 times less
CPU (below). It is a port of ShellCheck's own design, about 17,000 lines of Vu in this directory:

| file | what | ShellCheck source |
|---|---|---|
| `parse.vu` | the parser, with every SC1xxx parse warning and error, `.shellcheckrc` parsing, following sourced files | `Parser.hs` |
| `ast.vu`, `astlib.vu` | the syntax tree (flat arrays) and its helpers | `AST.hs`, `ASTLib.hs` |
| `check.vu` | variable flow, every check, fixes, `# shellcheck disable=` filtering, post-dominators | `AnalyzerLib.hs`, `Analytics.hs`, `Checks/*.hs` |
| `cfg.vu`, `dfa.vu` | control flow graph and the data flow analysis over it | `CFG.hs`, `CFGAnalysis.hs` |
| `data.vu` | variable lists | `Data.hs` |
| `fmt.vu` | the output formats, applying fixes, the diff | `Formatter/*.hs`, `Fixer.hs`, the Diff package |
| `vsc.vu` | command line (GetOpt), rc file lookup, reading files, `--jobs N` workers | `shellcheck.hs` |
| `sys_glue.c` | isatty, getcwd, realpath (for `--color=auto`, rc lookup, `-x`) | |
| `test/` | corpus collection, reference runs, comparisons, attack generator, command line cases, benchmark | |

```
./vu build --release shellcheck/vsc.vu -o vsc
./vsc [OPTIONS...] FILES...       # exactly shellcheck's options; see ./vsc --help
```

## Drop-in status

**Command line.** Every option of `shellcheck --help`, parsed as GHC's GetOpt parses them
(bundled short options, `-fgcc`, `--format=gcc`, unique prefixes of long options, `--`, the same
messages for unknown, ambiguous and missing arguments, exit 3), and `SHELLCHECK_OPTS`:

| option | status |
|---|---|
| `-a`, `--check-sourced` | supported |
| `-C[WHEN]`, `--color[=WHEN]` | supported (auto: stdout is a terminal and `TERM` isn't empty or `dumb`) |
| `-i`, `--include` / `-e`, `--exclude` | supported (`SC` prefixes, repeated options, `Invalid number`) |
| `--extended-analysis=bool` | supported |
| `-f`, `--format` | supported: `tty` (default), `gcc`, `checkstyle`, `diff`, `json`, `json1`, `quiet` |
| `--list-optional` | supported (same text) |
| `--norc`, `--rcfile=RCFILE` | supported |
| `-o`, `--enable` | supported (`all` or names) |
| `-P`, `--source-path` | supported (`SCRIPTDIR`, `:`-separated) |
| `-s`, `--shell` | supported |
| `-S`, `--severity` | supported |
| `-V`, `--version` | supported (prints 0.11.0's text) |
| `-W`, `--wiki-link-count` | supported |
| `-x`, `--external-sources` | supported |
| `--help` | supported |
| `-` (stdin) | supported |
| `--jobs N` | vsc only: check files on N threads (0: one per CPU); same output |

Exit codes as ShellCheck: 0 no comments, 1 comments (and `-f quiet` stops at the first file with
any), 2 a file couldn't be read (`file: openBinaryFile: does not exist (No such file or
directory)` and the like, in each format's way: stderr, or a checkstyle error element), 3 bad
usage, 4 bad option values.

**Output.** All seven formats, including their quirks: tty and json print columns with tabs counted
to the next multiple of 8 while gcc, checkstyle and json1 count characters; json and json1 list
newer files first and repeat a file's comments once per file they mention; the tty format's code
excerpts, `^--` markers, "Did you mean:" with the fixes applied, the "For more information"
footer (`-W`) and colors; the `diff` format's unified diffs of all fixes, with three lines of
context, `\ No newline at end of file` and "none were auto-fixable".

**Fixes.** Every fix ShellCheck suggests (SC2006, SC2086, SC2164, SC2268, SC2295, SC2250,
SC2292, ... 26 codes), with the same replacements, precedences and insertion points, applied the
same way (Fixer.hs: overlapping fixes dropped, multi-line replacements, precedence order).

**Configuration.** `.shellcheckrc` (or `shellcheckrc`) in the file's directory and every parent,
then `~/.shellcheckrc` and `$XDG_CONFIG_HOME/shellcheckrc` (`~/.config/shellcheckrc`); `--rcfile`
replaces the search, `--norc` turns it off; an rc file that doesn't parse gives SC1134 as
ShellCheck does. Its keys and the `# shellcheck` directives: `disable` (codes, ranges, `all`),
`enable`, `source`, `source-path` (with `SCRIPTDIR`), `shell`, `external-sources` (rc file only,
SC1144 in scripts), `extended-analysis`, and the messages for unknown keys and values (SC1107,
SC1103, SC1145, SC1146, SC1125).

**Sourced files.** `source`/`.` are followed as ShellCheck follows them: when the file was also
given as input, with `-x`, or with `external-sources=true`, looked up relative to the current
directory, then `-P` paths, then `source-path` directives; their variables and functions count,
their own comments are dropped unless `-a`, and SC1090/SC1091/SC1093/SC1094 come out the same.

## How it's tested: parity with ShellCheck

The parser is a faithful emulation of ShellCheck's Parsec parser, including how Parsec picks the
error message when several alternatives fail (the message and position of SC1072, and the
SC1073/SC1009 context lines, depend on it), so a broken script gets the same parse errors.

**Corpus.** Every shell script (by extension or shebang, zsh excluded) from 19 repositories:
nvm, ohmyzsh, docker-install, kubernetes, shellcheck, pure-bash-bible, rbenv, pyenv, asdf,
acme.sh, n, bats-core, docker official-images (corpus 1: 1710 files, 6.5 MB) and git,
termux-packages (a third of its build scripts), oh-my-bash, LinuxGSM, bash-it, Bash-Snippets
(corpus 2: 3645 files, 14.9 MB). The reference is ShellCheck 0.11.0 (the static release binary)
run once per file. It runs out of memory (over 5 GB) on two files, `acme.sh/acme.sh` and
`nvm/nvm.sh`; those two are left out of every comparison. Revisions: acme.sh 37d064f, asdf
ae14f6e, bats-core 5b61d8f, docker-install ada7a56, kubernetes b818dfa3, n f2fa928, nvm 5e38bc0,
official-images ed47b18, ohmyzsh 17a2b4c, pure-bash-bible 8c19d0b, pyenv e6669f0, rbenv 07e9b1e,
shellcheck 919d37c, Bash-Snippets 581a6b4, LinuxGSM 6c2e06a, bash-it 72ea9e2, git 50fe5cc,
oh-my-bash 94c2977, termux-packages 8d09238. `test/collect.py` picks the files, `test/runref.sh`
runs the reference (one file at a time, 120 s and 3 GB limits).

**Result on the corpus** (`test/cmpj.py`, reference `shellcheck -f json1` per file, vsc on all
files at once): all 5353 files identical, every field of every comment (position, end position,
severity, code, message, and the fix with its replacements, precedences and insertion points):
**41,717 of 41,717 comments, 4,432 of them with fixes**. 179 codes occur on the corpus:

| code | lines | code | lines | code | lines | code | lines |
|---|--:|---|--:|---|--:|---|--:|
| SC2034 | 15771 | SC2016 | 10071 | SC2086 | 3903 | SC1091 | 2624 |
| SC2154 | 2342 | SC2148 | 1478 | SC2155 | 609 | SC2164 | 365 |
| SC2207 | 327 | SC2004 | 301 | SC2046 | 265 | SC2329 | 250 |
| SC2239 | 229 | SC1083 | 199 | SC3043 | 177 | SC2181 | 175 |
| SC2162 | 164 | SC2031 | 156 | SC2128 | 141 | SC1007 | 133 |
| SC2064 | 99 | SC2030 | 93 | SC2059 | 79 | SC2206 | 77 |
| SC2006 | 67 | SC2139 | 61 | SC2295 | 61 | SC1090 | 56 |
| SC2015 | 51 | SC2035 | 48 | SC2188 | 48 | SC2119 | 41 |
| SC2145 | 40 | SC2094 | 34 | SC2268 | 34 | SC2068 | 31 |
| SC2223 | 29 | SC2001 | 28 | SC2005 | 28 | SC2048 | 28 |
| SC2283 | 28 | SC2153 | 27 | SC2124 | 26 | SC2018 | 25 |
| SC2028 | 25 | SC2102 | 25 | SC2231 | 25 | SC2019 | 24 |
| SC2116 | 24 | SC2166 | 24 | SC1003 | 23 | SC2027 | 22 |
| SC2129 | 21 | SC2238 | 20 | SC2317 | 20 | SC1087 | 19 |
| SC2053 | 19 | SC2126 | 19 | SC2178 | 19 | SC2143 | 18 |
| SC2076 | 17 | SC2026 | 14 | SC2090 | 13 | SC2140 | 13 |
| SC1112 | 12 | SC2038 | 12 | SC2069 | 12 | SC2088 | 12 |
| SC2120 | 12 | SC2209 | 12 | SC3003 | 12 | SC1072 | 11 |
| SC1073 | 11 | SC2235 | 11 | SC2254 | 11 | SC2089 | 10 |
| SC3010 | 10 | SC3062 | 10 | SC2012 | 9 | SC2021 | 9 |
| SC2199 | 9 | SC1001 | 8 | SC2003 | 8 | SC2013 | 8 |
| SC2296 | 8 | SC1009 | 7 | SC1054 | 7 | SC2044 | 7 |
| SC2098 | 7 | SC2125 | 7 | SC2269 | 7 | SC3044 | 7 |
| SC2010 | 6 | SC2043 | 6 | SC2061 | 6 | SC2091 | 6 |
| SC2115 | 6 | SC2194 | 6 | SC2218 | 6 | SC2240 | 6 |
| SC2327 | 6 | SC2328 | 6 | SC2009 | 5 | SC2097 | 5 |
| SC2219 | 5 | SC2221 | 5 | SC2222 | 5 | SC2294 | 5 |
| SC2309 | 5 | SC3037 | 5 | SC1050 | 4 | SC1071 | 4 |
| SC1078 | 4 | SC1079 | 4 | SC2121 | 4 | SC2320 | 4 |
| SC3054 | 4 | SC1089 | 3 | SC2041 | 3 | SC2070 | 3 |
| SC2103 | 3 | SC2157 | 3 | SC2179 | 3 | SC2184 | 3 |
| SC2185 | 3 | SC2210 | 3 | SC2215 | 3 | SC2319 | 3 |
| SC3045 | 3 | SC1010 | 2 | SC1036 | 2 | SC1049 | 2 |
| SC1088 | 2 | SC2000 | 2 | SC2011 | 2 | SC2017 | 2 |
| SC2062 | 2 | SC2142 | 2 | SC2163 | 2 | SC2321 | 2 |
| SC3030 | 2 | SC3057 | 2 | SC3061 | 2 | SC1008 | 1 |
| SC1011 | 1 | SC1019 | 1 | SC1020 | 1 | SC1035 | 1 |
| SC1055 | 1 | SC1058 | 1 | SC1064 | 1 | SC1065 | 1 |
| SC1102 | 1 | SC2045 | 1 | SC2077 | 1 | SC2082 | 1 |
| SC2093 | 1 | SC2100 | 1 | SC2144 | 1 | SC2152 | 1 |
| SC2156 | 1 | SC2190 | 1 | SC2198 | 1 | SC2213 | 1 |
| SC2220 | 1 | SC2253 | 1 | SC2305 | 1 | SC2316 | 1 |
| SC2318 | 1 | SC2324 | 1 | SC2333 | 1 | SC3006 | 1 |
| SC3009 | 1 | SC3014 | 1 | SC3020 | 1 | SC3026 | 1 |
| SC3060 | 1 | SC3066 | 1 | SC3067 | 1 |  |  |

**Formats** (`test/cmpfmt.sh`): on a random sample of 400 corpus files (150 + 250), each run alone
in `tty`, `diff`, `checkstyle` and `json`: stdout, stderr and exit status identical for all 400 in
each format. One invocation over 40 files in each of the seven formats and with `-W 10`:
identical (this checks the json file order, the checkstyle wrapper and the tty footer across files).

**Optional checks** (`-o all -f json1`, a separate random sample of 700 corpus files): 17,711 of
17,711 comments identical, among them SC2250 8,519, SC2312 1,493, SC2292 1,300, SC2154 (uppercase)
1,033, SC2248 408, SC2244 108, SC2249 66, SC2243 32, SC2310 16, SC2002 11, SC2230 9, SC2335 2,
SC2236 2.

**Command line, configuration and sourcing** (`test/cases.py`): 79 small cases, each a directory
of files and an argument list (rc files in the directory, a parent, home and XDG; `--norc`,
`--rcfile` (also missing), parse errors in rc files, every key; `-x`, `-a`, `-P`, `SCRIPTDIR`,
source directives, missing, recursive and broken sourced files in every format; directives in
scripts; `-s`, `-S`, `-i`, `-e`, `-o`, `-W`, `--color`, `SHELLCHECK_OPTS`, stdin, missing files,
directories, `--`, BOM, CRLF, Latin-1 and UTF-8 text, tabs, a file without a final newline, a
multi-line fix): stdout, stderr and exit status identical in all 79 (one, Latin-1 bytes in a tty
excerpt, differed at first and was fixed: ShellCheck reads bytes that aren't UTF-8 as Latin-1
characters and prints them in UTF-8).

**Attack rounds** (`test/attack.py`): generated scripts compared with ShellCheck in the codes vsc
implements. Four generators: a grammar of shell features (expansions, tests, redirections,
bashisms, directives, under each shebang), byte-level mutations of corpus files (mostly broken
scripts, for the parse errors), splices of corpus fragments, and token insertions (keywords and
operators dropped into corpus files).

| round | inputs | found |
|---|---|---|
| 1 | 1900 generated, 600 mutated | 3 bugs: the error position when `<`/`>` isn't followed by `(` (SC1072 one column off); Parsec's `many` drops the error left by an iteration that consumed input (SC1072 message and position after an `elif` body); the `${var:-..}` guard pattern of SC2154 is matched at every line start, as regex-tdfa does |
| 2 | 2000 generated, 1500 mutated, 800 spliced, 800 token-inserted | nothing |
| 3 (after 47 more codes) | 2500 generated (with the new checks' constructs), 1000 each of mutated, spliced, token-inserted | nothing |
| 4 | 2500 generated, 1500 mutated | nothing |

Adding checks also found one bug on the corpus itself, not by an attack round: SC2043 was given
for `for x in 'single'`, where ShellCheck's earlier clause gives SC2041 instead (fixed by
implementing SC2041 and SC2066 in the same order). vsc gives 180 distinct codes on round 3's generated files.

Round 5 (after the command line, fixes and the remaining codes; `test/attack.py` now compares
`-f json1`, so fixes and end positions too, and its grammar has the new checks' constructs):
1500 generated, 1500 generated with `-o all`, 1000 mutated, 600 spliced with `-o all`, 600
token-inserted: nothing. The generated files give 333 distinct codes.

## Speed

The whole corpus (5353 files, 21 MB; the two files ShellCheck can't finish are left out), one
invocation per corpus, output to /dev/null (`test/bench.py`). The machine is a 2-core VM that was
heavily loaded by other jobs during the runs (load average 7 to 10), so wall-clock numbers are
inflated for both tools and CPU time is the steadier measure. ShellCheck 0.11.0 was run once
(20 minutes); vsc three times, best run shown. Measured 2026-11-01.

| | wall s | CPU (user) s | max RSS |
|---|--:|--:|--:|
| shellcheck 0.11.0 (single-threaded) | 1239.5 | 463.2 | 459 MB |
| vsc, 1 thread | 33.4 | 14.8 | 42 MB |
| vsc, `--jobs 2` | 34.4 | 16.2 | 66 MB |

Instruction counts, which the load doesn't affect (callgrind, vsc built with
`VU_MARCH=x86-64-v2`, a random sample of 100 corpus 2 files, 585 KB): shellcheck 21.85 billion,
vsc 1.26 billion, 17.3 times fewer. On CPU time over the whole corpus vsc is 31 times faster.
Two workers didn't help here: with the machine's two cores already busy, there was no idle
core to use, so this measurement says nothing about multi-core scaling.

On the two files ShellCheck runs out of memory on, vsc takes 1.45 s CPU and 433 MB
(`acme.sh/acme.sh`, 9931 lines) and 2.15 s and 148 MB (`nvm/nvm.sh`, 6742 lines); both hit the data
flow step budget.

## Known differences and limits

- **The data flow step budget.** vsc stops a data flow analysis after 4,000,000 steps in one file
  (or 1,000,000 iterations of one loop, where ShellCheck itself stops with "DFA did not reach fix
  point"); ShellCheck has no total budget. Measured on the whole corpus with the budget lifted:
  the most any file needs is 163,296 steps (`acme.sh/acme.sh`) and 7,257 iterations of one loop
  (`nvm/nvm.sh`), so the budget is 24 times what the largest file needs and no corpus file
  reaches it. Those two files are the ones ShellCheck runs out of memory on (over 5 GB); no
  file ShellCheck can finish comes near the budget. Like ShellCheck, vsc turns off the analysis
  cache when 10,000 iterations of a loop are left (it used to do it after 10,000 iterations;
  no corpus file comes near either point).
- **Paths.** `canonicalizePath` (deciding whether a sourced file was given as input, and where
  to start looking for `.shellcheckrc`) is realpath for paths that exist and the existing prefix
  plus the rest otherwise, as the directory package does; not tested on case-insensitive or
  unusual file systems.
- **Locale.** vsc always writes UTF-8. ShellCheck writes in the locale's encoding, so under a
  non-UTF-8 locale it may print non-ASCII text differently (or fail to); compared under UTF-8.
- **Read errors** other than "does not exist", "is a directory" and "permission denied" are
  mapped to GHC's wording by errno and weren't all compared (the tests run as root, so
  "permission denied" wasn't either).
- **Not compared:** parse problems inside a `.shellcheckrc` other than its SC1134 (e.g. a
  carriage return in the rc file, reported by ShellCheck at a position in the rc file and dropped
  by vsc).
- `--jobs N` is an addition; ShellCheck rejects it.
