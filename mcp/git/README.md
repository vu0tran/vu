# mcp-git

The MCP git server in Vu: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`,
`git_commit`, `git_add`, `git_reset`, `git_log`, `git_create_branch`, `git_checkout`, `git_show`
and `git_branch`, answering as the reference server (`mcp-server-git` 2026.10.28, Python, through
GitPython) does: the same tools, schemas, argument checks (pydantic's lax rules and messages),
results and errors (GitPython's `GitCommandError` text included). The parts of GitPython the
reference leans on are ported: its revision parser (`HEAD~2`, `v1a^{commit}`, `HEAD:d/c.txt`,
`:a.txt`, `@{1}`, short shas, its order of looking names up and its error messages), its commit
writer (it writes the commit object itself, so no hooks run and the dates come from
`GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` as GitPython reads them), its reading of `git diff-tree`
patches for `git_show`, its ref-name rules for new branches, and its confinement checks.

```
./vu build mcp/git/main.vu -o mcp-git
./mcp-git [--repository /path/to/repo]      # with it, every repo_path must be inside that repository
```

It needs the `git` program, as GitPython does.

## Measured

2-vCPU Linux VM, Python 3.13 (`mcp/bench_start.py`: median of 15 starts, then 1,000 calls), on
this repository:

| | Vu | Python reference |
|---|---|---|
| install | one 402 KB binary (and git) | a virtualenv with GitPython (and git) |
| start to the `initialize` answer | 2.7–3.4 ms | 649–702 ms |
| memory (RSS) | 2.2 MB | 73 MB |
| `git_status` calls per second | 157 | 123 |
| `git_log` (10 commits) calls per second | 115 | 78 |

The calls are mostly git's own work: both servers run the `git` program for them.

## Checked

`tests/run_mcp_git.sh` gives both servers their own copy of the same repository and runs random
sessions: file edits (text, Latin-1, emoji, binary), renames, mode changes and deletions made the same
in both copies, then status, the diffs, `git_add` with good and bad paths (outside the repository,
absolute, starting with `-`), commits (the dates fixed, so both write the same hashes), logs with
counts and dates, branches made from names, tags, annotated tags and shas (and names git or GitPython
refuse), checkouts, `git_show` of commits, trees, blobs and about forty revision expressions, resets,
branch lists, arguments of the wrong type or missing, repository paths that aren't repositories, and
a run confined with `--repository`. Every answer is compared as JSON: about 3,300 answers on twelve
seeds and two confined runs, the same, plain and with AddressSanitizer.

## Where it differs

- `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` are read in git's own form (`1705321825 +0200`) and as
  ISO 8601 (`2024-01-15 14:30:25 +0200`); GitPython also reads RFC 2822 and `YYYY.MM.DD`-style dates.
  Without them, the zone of a new commit is UTC here and the local zone in GitPython.
- `git_commit` doesn't run the repository's hooks (GitPython runs `pre-commit`, `commit-msg` and
  `post-commit` from `.git/hooks`).
- Revision expressions GitPython reads that need a date (`main@{yesterday}`) or another checkout
  (`@{-1}`), or name an upstream (`@{u}`), fail here.
- A repository that git can't read (a broken `.git`, a missing object) fails with git's message,
  where GitPython's own readers may fail differently.
