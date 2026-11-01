# vsc: a ShellCheck-compatible shell linter in Vu

`vsc` lints shell scripts and prints what ShellCheck 0.11.0 prints with `-f gcc`
(`file:line:col: severity: message [SCxxxx]`), for the checks it implements. It is a port of
ShellCheck's own design, about 11,000 lines of Vu in this directory:

| file | what | ShellCheck source |
|---|---|---|
| `parse.vu` | the parser, with every SC1xxx parse warning and error | `Parser.hs` |
| `ast.vu`, `astlib.vu` | the syntax tree (flat arrays) and its helpers | `AST.hs`, `ASTLib.hs` |
| `check.vu` | variable flow, the checks, `# shellcheck disable=` filtering | `AnalyzerLib.hs`, `Analytics.hs`, `Checks/*.hs` |
| `cfg.vu`, `dfa.vu` | control flow graph and the data flow analysis over it | `CFG.hs`, `CFGAnalysis.hs` |
| `data.vu` | variable lists | `Data.hs` |
| `vsc.vu` | command line, output, `--jobs N` workers | `Formatter/GCC.hs` |
| `test/` | corpus collection, reference runs, comparison, attack generator, benchmark | |

```
./vu build --release shellcheck/vsc.vu -o vsc
./vsc [--jobs N] FILE...        # -f gcc is accepted and ignored: it's the only format
```

Default options only: no `-x` (sourced files are reported as SC1091 like ShellCheck does), no
optional checks, no `.shellcheckrc`. Shebangs, `# shellcheck shell=`, file extensions and
`disable=`/`enable=`/`source=` directives are read as ShellCheck reads them.

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

**Result** (`test/runall.sh`, `test/cmp.py`): on the 5353 files, for every code vsc implements,
vsc prints exactly the lines ShellCheck prints: same position, severity, code and message,
**zero missing and zero extra**. Codes vsc doesn't implement are not counted as matches. Of all
41,717 lines ShellCheck prints on the corpus, vsc prints 41,608 (99.74%); the other 109 belong
to 39 codes vsc doesn't implement (listed at the end). vsc implements 315 codes; 140 of them
occur on the corpus, with these counts (ShellCheck = vsc, every line identical):

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
| SC2199 | 9 | SC1001 | 8 | SC2013 | 8 | SC2296 | 8 |
| SC1009 | 7 | SC1054 | 7 | SC2044 | 7 | SC2098 | 7 |
| SC2125 | 7 | SC2269 | 7 | SC3044 | 7 | SC2010 | 6 |
| SC2043 | 6 | SC2061 | 6 | SC2091 | 6 | SC2240 | 6 |
| SC2327 | 6 | SC2328 | 6 | SC2009 | 5 | SC2097 | 5 |
| SC3037 | 5 | SC1050 | 4 | SC1071 | 4 | SC1078 | 4 |
| SC1079 | 4 | SC3054 | 4 | SC1089 | 3 | SC2041 | 3 |
| SC2179 | 3 | SC3045 | 3 | SC1010 | 2 | SC1036 | 2 |
| SC1049 | 2 | SC1088 | 2 | SC2011 | 2 | SC3030 | 2 |
| SC3057 | 2 | SC3061 | 2 | SC1008 | 1 | SC1011 | 1 |
| SC1019 | 1 | SC1020 | 1 | SC1035 | 1 | SC1055 | 1 |
| SC1058 | 1 | SC1064 | 1 | SC1065 | 1 | SC1102 | 1 |
| SC2045 | 1 | SC2082 | 1 | SC2144 | 1 | SC2198 | 1 |
| SC3006 | 1 | SC3009 | 1 | SC3014 | 1 | SC3020 | 1 |
| SC3026 | 1 | SC3060 | 1 | SC3066 | 1 | SC3067 | 1 |

The other implemented codes (most of the SC1xxx parse errors and the bashism codes) don't occur
on the corpus; they're covered by the attack rounds below.

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

## Not done

- Unimplemented codes (each found on the corpus, with its count): SC2003 (8), SC2115 (6), SC2194 (6), SC2218 (6), SC2219 (5), SC2221 (5), SC2222 (5), SC2294 (5), SC2309 (5), SC2121 (4), SC2320 (4), SC2070 (3), SC2103 (3), SC2157 (3), SC2184 (3), SC2185 (3), SC2210 (3), SC2215 (3), SC2319 (3), SC2000 (2), SC2017 (2), SC2062 (2), SC2142 (2), SC2163 (2), SC2321 (2), SC2077 (1), SC2093 (1), SC2100 (1), SC2152 (1), SC2156 (1), SC2190 (1), SC2213 (1), SC2220 (1), SC2253 (1), SC2305 (1), SC2316 (1), SC2318 (1), SC2324 (1), SC2333 (1).
- Optional checks (`--enable`), `-x` (following sourced files), `.shellcheckrc`, formats other
  than gcc, fix suggestions.
- The data flow analysis has a step budget; past it a function's analysis is abandoned (the two
  big files above hit it). ShellCheck has no budget there and runs out of memory on the same
  files, so their output was never compared.
