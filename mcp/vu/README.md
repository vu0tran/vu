# mcp-vu

Vu's checker as an MCP server, for a model (Claude Code, Cursor, any MCP client) writing Vu:

- `vu_check`: runs the type and ownership checker on a program, given as one `source` or as
  `files` (names to contents, for a program of several modules), and returns the first error with
  its file, line, message and source line (also as `structuredContent`), or says it checks. It
  builds nothing and runs no part of the program; it takes milliseconds.
- `vu_docs`: the language in brief (`llms.txt`), for a model that hasn't seen Vu.

```
./vu build mcp/vu/main.vu -o mcp-vu
./mcp-vu --vu /path/to/vu           # default: the vu on PATH (or $VU); llms.txt is read from beside it
```

In a client's configuration: `{"command": "/path/to/mcp-vu", "args": ["--vu", "/path/to/vu"]}`.

Each check writes the files into a new private temporary folder (`fs.temp_dir()`), runs
`vu check --json` on them and removes them. File names must be letters, digits and `_` ending in
`.vu`, so a request can't write anywhere else. `tests/run_mcp_vu.sh` checks the answers for a
clean program, an error, a multi-file program and bad requests.
