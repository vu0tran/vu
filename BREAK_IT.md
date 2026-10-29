# Break it

Vu makes two promises. Code that doesn't call C can't corrupt memory. And code can't reach files,
programs, the network or C unless it was handed the capability to. If you find a program that
breaks either one, report it, and you'll be listed below.

## What counts

- **Memory safety.** A Vu program without `extern` blocks that, built with `vu build` or
  `vu run`, crashes with a segmentation fault, reads or writes memory it shouldn't (an
  AddressSanitizer report with `vu build --san`), or behaves differently from what the
  language says because of undefined behavior in the C it was compiled to.
- **Capabilities.** A function that reads or writes a file, runs a program, opens a connection or
  calls C without being given `Fs`, `Os`, `Net` or `Ffi` (or a `Dir`, a closure or a struct that
  carries one). Also: code given a `Dir` reaching outside its folder, a package doing something
  its `vu.pkg` line didn't grant, or an exported library function (`vu build --lib`) reaching
  any of these.
- **The checker.** A program `vu check` accepts that uses a value after moving it, changes a
  list while a view of it lives, or otherwise gets past the ownership rules.
- **The MCP servers** (`mcp/`). One of them reaching something outside what it was started with:
  the fetch server connecting to a private address it refused, or the filesystem server outside
  its folders.

Bugs in C code reached through `extern` blocks don't count: Vu doesn't check C.

## How to report

Open an issue with the program and the command that shows the problem. For an MCP server problem
that could hurt people already running it, use GitHub's private vulnerability report instead
(the repository's Security tab).

## Hall of fame

No one yet.
