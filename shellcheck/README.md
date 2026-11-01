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
`nvm/nvm.sh`; those two are left out of every comparison.

**Result** (`test/runall.sh`, `test/cmp.py`): on the 5353 files, for every code vsc implements,
vsc prints exactly the lines ShellCheck prints: same position, severity, code and message,
**zero missing and zero extra**. Codes vsc doesn't implement are not counted as matches. Of all
41,717 lines ShellCheck prints on the corpus, vsc prints XX (XX%); the rest belong to the
unimplemented codes listed at the end.

PARITY_TABLE

**Attack rounds** (`test/attack.py`): generated scripts compared with ShellCheck in the codes vsc
implements. Four generators: a grammar of shell features (expansions, tests, redirections,
bashisms, directives, under each shebang), byte-level mutations of corpus files (mostly broken
scripts, for the parse errors), splices of corpus fragments, and token insertions (keywords and
operators dropped into corpus files).

ATTACK_ROUNDS

## Speed

BENCH

## Not done

- Unimplemented codes (each found on the corpus, with its count): UNIMPL.
- Optional checks (`--enable`), `-x` (following sourced files), `.shellcheckrc`, formats other
  than gcc, fix suggestions.
- The data flow analysis has a step budget; past it a function's analysis is abandoned (the two
  big files above hit it). ShellCheck has no budget there and runs out of memory on the same
  files, so their output was never compared.
