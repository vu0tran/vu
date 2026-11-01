# Break it

Vu makes a few promises. Code that doesn't call C can't corrupt memory. Code can't reach files,
programs, the network or C unless it was handed the capability to, and a package gets only what its
`vu.pkg` line grants. And the standard library's web promises hold: SQL injection, unescaped HTML, a
route without a Who, and an HTTP client request to a cloud metadata address don't get past it. If you
find a program that breaks one, report it, and you'll be listed below.

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
- **The web promises.** SQL text built at run time reaching `pg.query` (or `exec`, `query_as`...);
  text reaching a page as HTML without `web.trust`; a route added without a Who, or a request getting
  past `web.SignedIn` or `web.Only` without middleware setting `"user"` or the check saying yes; the
  HTTP client connecting to a link-local address, or `get_public`, `send_public` or a `public_only`
  client connecting to a private one (by any spelling, redirect or DNS answer).
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
