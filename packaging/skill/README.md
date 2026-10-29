# An agent skill for Vu

`vu/SKILL.md` teaches an agent (Claude Code, or any that reads skills) to write small tools in Vu,
check them with `vu check`, show the person what a program can reach with `vu check --caps` before
running it, and run it with `vu run`. To use it with Claude Code, copy the `vu` folder into
`~/.claude/skills/` (for every project) or a project's `.claude/skills/`.

Not tested yet: an agent session using the skill. The commands it names are tested in
`tests/run_cli.sh` (`--caps`, the run cache) and `tests/run_mcp_vu.sh` (the MCP tool).
