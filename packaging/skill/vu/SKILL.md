---
name: vu
description: Write small tools, scripts and MCP servers in Vu (a compiled, memory-safe language with Python-like syntax) instead of shell or Python, when the result should start fast, use little memory, or touch only what it says it touches. Covers checking, showing the person what the program can reach, and running it.
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
- There are no `\x` or `\u` escapes: use `chr(n)` for a character by number.

## When not to use Vu

For a one-off command or a pipeline of existing programs, use the shell. Vu pays off for a tool
that runs often, handles data in loops, or should be limited to what it needs.
