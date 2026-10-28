# mcp-filesystem

The [Model Context Protocol](https://modelcontextprotocol.io) filesystem server, written in Vu. It
stands in for the reference server, `@modelcontextprotocol/server-filesystem` 2.0.1 (Node): the
same 14 tools (`read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`,
`create_directory`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `move_file`,
`search_files`, `get_file_info`, `list_allowed_directories` and the deprecated `read_file`), with the
same arguments, results, error messages and tool descriptions, over stdio, for clients of the
2026-07-28 protocol and of the earlier revisions that start with `initialize`.

```
./vu build mcp/filesystem/main.vu -o mcp-filesystem
./mcp-filesystem ~/projects/site ~/notes
```

In a client's configuration, the command is the binary and the arguments are the folders:

```json
{ "mcpServers": { "filesystem": { "command": "/usr/local/bin/mcp-filesystem", "args": ["/Users/me/projects/site"] } } }
```

## What it can reach

`main` is the only function that receives `Fs`, and it uses it once: to open each folder given on
the command line as a `dir.Dir`. From then on the server holds only those Dirs. Every path in a
request is checked as the reference checks it, and then resolved by the kernel inside one of the
folders (`openat2` with `RESOLVE_BENEATH` on Linux), so a symlink that leads out, a `..`, or a folder
renamed while a request runs can't take it anywhere else. The program has no `Net` and no `Os`, so
it can't open a connection, start a program or read the environment: code that tried wouldn't
compile (`unknown name 'net'`).

## Measured


Linux VM, 2 vCPUs, Node 22, `mcp/filesystem/bench.py` (median of 15 starts; then 2,000 reads of a
600-byte file, and 20 runs each of `search_files` and `directory_tree` over 40 folders of 50 files):

| | Vu | Node reference |
|---|---|---|
| install | one 352 KB binary (needs only libc) | Node (125 MB) + 25 MB of node_modules (12 packages) |
| start to the `initialize` answer | 1.7 ms | 203 ms |
| memory (RSS), idle / after the runs | 2.1 / 4.5 MB | 72 / 113 MB |
| `read_text_file`, calls per second | 15,740 | 1,811 |
| `search_files` (`**/f1*.txt`) over 2,000 files | 2.6 ms | 149 ms |
| `directory_tree` of 2,000 files | 4.2 ms | 16.2 ms |

## Checked

`tests/run_mcp.sh` builds the server (plain and with AddressSanitizer/UBSan) and sends it and the
reference server the same requests, each on its own copy of a fixture tree, comparing every answer
as JSON: every tool on files with CRLF lines, no final newline, Unicode and space in names, symlinks
inside the folder, missing paths, folders where files are expected; `head` and `tail` with 0,
negative and fractional counts; argument errors (the same messages as the reference's schemas);
the protocol in both eras; then random `edit_file` edits (the diff text must be the same: the diff
is a port of jsdiff's), random file names in `list_directory_with_sizes` (ICU's order) and random
glob patterns in `search_files` and `directory_tree`. Nine seeds: about 12,600 answers, all the
same. The glob matcher alone agrees with minimatch on 40,000 random patterns.

## Where it differs from the reference

- **Symlinks between allowed folders.** A symlink inside one allowed folder that points into
  another is refused (the kernel resolves each path inside one folder); the reference follows it.
  On systems without `openat2` (and with `VU_DIR_WALK=1`), any symlink on a path is refused.
- **No MCP roots.** The folders come from the command line only; with none, the server exits with
  a usage message. (Roots are deprecated in the 2026-07-28 protocol.)
- **`~` isn't expanded.** The server can't read `HOME` (it has no `Os`), so a path starting with `~`
  is refused with a message asking for the full path.
- **Protocol eras per request.** A request with the 2026-07-28 `_meta` is answered as that revision,
  one without it as the earlier ones, on the same connection; the reference picks one era per
  connection from its first message. A request for a 2026-era version the server doesn't speak gets
  `-32022 Unsupported protocol version`, as the specification says; the reference serves it.
- **Unicode respelling.** The reference retries a missing path with NFC/NFD and Unicode-space
  variants of its names (for macOS); this server doesn't.
- **Times** in `get_file_info` are in UTC (the reference uses the local zone; run it with `TZ=UTC`
  and they match).
- **Some error texts**, where the reference's come from its workaround for Node's lack of `openat`:
  writing into a folder that doesn't exist says `ENOENT: no such file or directory, open '...'`.
- **Globs**: minimatch's extglobs (`+(a|b)`, `@(...)`, `!(...)`) aren't supported; their characters
  match themselves. **Names beyond ASCII** in `list_directory_with_sizes` sort by code point after
  the ASCII ones (ICU's full order isn't here).
- **`head` and `tail`** read the whole file (the reference reads from the end for `tail`); the
  results are the same.
