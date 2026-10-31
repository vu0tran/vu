---
name: vu
description: Write small tools, scripts, MCP servers and web backends in Vu (a compiled, memory-safe language with Python-like syntax) instead of shell, Python or Node, when the result should start fast, use little memory, touch only what it says it touches, or be a backend with accounts that's secure without extra work. Covers checking, showing the person what the program can reach, running it, and starting a backend.
---

# Writing tools in Vu

Vu compiles to C and runs at about C speed. Its programs can reach files, programs, the network
or C code only through capabilities that `main` asks for, so what a program can touch is decided
by one line, and `vu check --caps` shows it.

Read `llms.txt` (next to the `vu` binary in a release, or https://vulang.org/llms.txt) once
before writing Vu: it is the language in brief.

## The loop

1. Write the program to a `.vu` file. Ask `main` only for what it needs:
   `fn main():` (nothing), `fn main(fs: Fs)` (files), `fn main(os: Os)` (programs, environment,
   stdin), `fn main(net: Net)` (network), `fn main(ffi: Ffi)` (C code). Add `throws` to `main`
   to use `?` on failing calls.
2. Run `vu check FILE.vu`. It takes milliseconds and builds nothing. Each error names the line and
   says what to write instead; fix them and check again until it prints nothing.
3. Run `vu check --caps FILE.vu` and tell the person what it prints before the first run. It
   lists exactly what the program can reach, for example `fs files and folders` and nothing
   else. If the person approves, later runs of the same file need no new approval unless the
   capabilities change.
4. Run it with `vu run FILE.vu ARGS...`. The first run compiles (a fraction of a second for a
   small program). Later runs of the unchanged file start the kept binary in about 10 ms. A file
   whose first line is `#!/usr/bin/env -S vu run` can be made executable and run directly.

## Backends

Start from a template rather than an empty file: `vu new app NAME` (pages rendered on the server,
with accounts), `vu new api NAME` (a JSON API with accounts), or `vu new web NAME` (pages, no
database). Each has a Dockerfile and a `railway.json` and runs with `DATABASE_URL` set. Build on
the standard library instead of writing these yourself; each is tested against a reference:

- `auth`: password hashes, sessions, CSRF tokens. Never hash passwords or make tokens by hand.
- `pg`: SQL is a string literal in the program and values go as `$1` parameters (building SQL from
  values doesn't compile). `pg.from_url(os.env("DATABASE_URL"))`, `pg.pool`, `pg.give_back`.
- `migrate`: tables live in `migrations/NNN_name.sql`; add a file to change them, never edit one
  that has run.
- `web`: routes, middleware (`web.same_origin`, `web.limit`), forms, cookies, templates that escape
  every value (`web.render` with `web.v`).
- `jobs` (background work that must survive restarts), `mail` (SMTP, Resend), `stripe` (Checkout,
  verified webhooks), `s3` (objects, presigned URLs).

A handler that needs a database connection takes `var db: pg.Db` and is routed with a small
wrapper that takes one from the pool (see `route` in the templates).

## Mistakes models make in Vu

- Every string interpolates: write literal braces doubled (`"{{"`), even inside nested strings.
- `else` (a fallback for a failing call) works only at statement level:
  `let x = f() else 0`, never inside an argument, an interpolation or a condition.
- `match` works on enums and on failing calls, not on `Int` or `Str`: use `if`/`elif`.
- `let y = x` moves a list, struct or enum: `x` can't be used after. For a `Str`, `let n = s.name + ""`
  copies.
- `var` parameters need `&` at the call (`grow(&xs)`), and the same variable can't be passed with
  `&` twice in one call.
- An optional is read with `if v = opt:` or `opt else default`, not by comparing with `nil`.
- There are no `\x` or `\u` escapes: use `chr(n)` for a character by number (`str([byte(0)])`
  for a zero byte).
- A `?` can't follow a call to its left in the same statement (`log(x) + f()?`): put the `?` call
  in its own `let` first.
- Maps: `k in m`, `m.get(k, default)`, `m.remove(k)`; there's no `.has`. Structs are built with
  every field (`User(id, name)`), and there are no type aliases.
- A closure with a `var` parameter must be `own fn(var x: T) => ...`.

## When not to use Vu

For a one-off command or a pipeline of existing programs, use the shell. Vu pays off for a tool
that runs often, handles data in loops, or should be limited to what it needs.
