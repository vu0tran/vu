# Vu

Vu is a small, compiled systems language with Python-style syntax. It's designed to be cheap for
an LLM to read and write, quick to compile, free of memory bugs without a garbage collector, and
about as fast as C. The compiler checks types and ownership, translates the program to C, and
builds a native binary with the system C compiler.

```
type Tree:
  left, right: Tree?

fn make(d: Int) -> Tree:
  if d == 0: return Tree(nil, nil)
  return Tree(make(d - 1), make(d - 1))

fn check(t: Tree) -> Int:
  var n = 1
  if l = t.left: n += check(l)
  if r = t.right: n += check(r)
  return n

fn main():
  print("nodes: {check(make(arg(1, 10)))}")
```

Vu is an experiment. v0 runs on Linux (x86-64 and ARM64); macOS builds but hasn't been run on a
Mac yet. The compiler is written in Vu.

## Getting started

You need gcc (or clang, with `CC=clang`) on Linux, and git for packages. Clone the repository and run `./vu`. The first
run builds the compiler from `compiler/vuc_seed.c`, the C the compiler produces from itself, so no
other tools are needed.

```
./vu run examples/binarytrees.vu 16      # build without optimization and run
./vu check examples/json.vu              # type and ownership errors only, in milliseconds
./vu build examples/nbody.vu -o nbody    # optimized binary (-O3 -march=native)
./vu build app.vu --san                  # with AddressSanitizer, UBSan and LeakSanitizer
./vu fmt app.vu                          # format in place
./vu test app_test.vu                    # run each fn test_... in its own process
./vu run --profile app.vu                # optimized, then where the CPU time went
./vu build --wasm app.vu                 # a WebAssembly (WASI) module, with zig
./vu help                                # every command and flag
```

`vu lsp` gives editors the compiler's errors as you type, formatting, hover, go to definition and
completion.

The language is described in [SPEC.md](SPEC.md), which is short and starts with examples. How the
language was built, and every measurement along the way, is in [CHANGELOG.md](CHANGELOG.md).

## What it looks like

### Ownership without annotations

Every value has one owner and is freed when its owner goes out of scope. Parameters are read-only
borrows by default. A function that changes an argument declares it `var`, and the caller marks
it with `&`, so every mutation is visible where it happens. A function that keeps its argument
declares it `own`, and the argument is moved.

```
fn advance(var bodies: [Body], dt: Float): ...
advance(&bodies, 0.01)

fn add(var lexer: Lexer, own tok: Token):
  lexer.toks.push(tok)          # stored, not copied
add(&lx, t)                     # t is moved; using it again is a compile error
```

There are no lifetime annotations, no reference types and no `unsafe`. The rules are stricter than
Rust's in places: for example, a `var` argument blocks every other use of the same variable in that
call. In return, they fit in a few pages of SPEC.md. Use after move, iterator invalidation,
aliased mutation, dangling borrows and data races in parallel loops are all compile errors.
Indexing is bounds-checked, and integer overflow stops the program.

### Errors are values you must handle

```
fn parse_digit(b: Byte) -> Int throws:
  if b < '0' or b > '9': fail "not a digit: {b}"
  return int(b) - 48

let d = parse_digit(b)?              # pass it on
let d = parse_digit(b) else 0        # or use a fallback
match parse_digit(b):                # or inspect it
  ok(d): print("{d}")
  err(msg): print(msg)

let name = user.nickname else "anon" # an optional (Str?) works the same way
```

A call that can fail must be handled, or the program doesn't compile. `throws E` with an enum `E`
gives typed errors that callers can match on.

### Enums, generics, interfaces and closures

```
type Shape:
  Circle(r: Float)
  Rect(w, h: Float)

fn area(s: Shape) -> Float:
  match s:
    Circle(r): return 3.14159 * r * r
    Rect(w, h): return w * h

fn largest[T](xs: [T], better: fn(T, T) -> Bool) -> T?: ...

let k = 3
let scaled = map_all(xs, fn(x) => x * k)    # borrows k; can't outlive it
let add_n = own fn(x) => x + n              # owns a copy of n, an ordinary value
```

```
interface Shape:
  fn area(s: Self) -> Float

impl Shape for Rect:
  fn area(r: Rect) -> Float:
    return r.w * r.h

fn total[T: Shape](xs: [T]) -> Float: ...      # statically dispatched, like a direct call
let shapes: [Shape] = [Circle(1), Rect(2, 3)]  # interface values: dispatched through a table
```

`match` must cover every variant. Generic functions and types are specialized for each use and
checked separately. A borrowing closure is free to create and can't escape, and an `own` closure
can be stored, sent over a channel or run in a task.

### JSON without a tree

```
type Item:
  sku: Str
  qty: Int
  gift: Bool?

let order = from_json(body, Order)?     # checked against the type
print(to_json(order.items[0]))          # {"sku":"A-1","qty":2,"gift":null}
```

The parser and printer for each type are generated at compile time. Errors say where they occur:
`items[0].qty: expected a number at byte 49`.

### Capabilities

A program can touch files, processes, the network or C code only if `main` asks for that
capability and passes it to the code that needs it:

```
fn main(fs: Fs, net: Net) throws:
  let conf = fs.read("app.json")?
  ...
```

A function that isn't handed `Fs` can't read a file, and its signature shows it. The other
capabilities are `Os` (processes, environment, time, signals), `Net` (TCP, TLS, DNS) and `Ffi`
(calling C). A capability can also be narrowed: `dir.open(fs, path)` gives a `Dir` that reaches only
what's inside one folder, enforced by the kernel, so code handed a `Dir` can't touch any other file.

### An MCP server in Vu

`mcp/filesystem` is the Model Context Protocol filesystem server as one Vu program: the same 14 tools,
arguments, results and messages as the reference server (`@modelcontextprotocol/server-filesystem`
2.0.1, in Node), for clients of the 2026-07-28 protocol and the earlier ones.

It starts in 1.7 ms instead of 203, uses 2 MB instead of 72, and searches 2,000 files in 2.6 ms
instead of 149. And `main` opens each allowed folder as a `Dir` and passes on nothing else, so the
compiler guarantees the tools can't open a socket, start a program or read a file outside those
folders, and the kernel enforces the folder boundary. Measured on a 2-vCPU Linux VM against the
reference server on Node 22 (`mcp/filesystem/README.md` has the details):

| | Vu | Node reference |
|---|---|---|
| install | one 352 KB binary (libc only) | Node (125 MB) + 25 MB of node_modules |
| start to the `initialize` answer | 1.7 ms | 203 ms |
| memory (RSS), idle / after the runs below | 2.1 / 4.5 MB | 72 / 113 MB |
| `read_text_file`, calls per second | 15,740 | 1,811 |
| `search_files` over 2,000 files | 2.6 ms | 149 ms |
| `directory_tree` of 2,000 files | 4.2 ms | 16.2 ms |

`tests/run_mcp.sh` sends both servers the same requests (every tool, errors, bad arguments, both
protocol eras, random edits, names and glob patterns) and checks every answer is the same JSON:
12,600 answers on nine seeds, plain and under AddressSanitizer.

Two more of the reference servers are rewritten the same way, each checked against its Python
original (`mcp-server-time` and `mcp-server-fetch` 2026.10.28) and measured the same way:

| | Vu | Python reference |
|---|---|---|
| `mcp/time`: start / memory / `convert_time` calls per second | 1.8 ms / 1.9 MB / 12,212 | 683 ms / 69 MB / 773 |
| `mcp/fetch`: start / memory | 3.6 ms / 5.0 MB | 730 ms / 83 MB |
| `mcp/fetch`: an HTML page, local server | 107 calls/s | 8 calls/s (pure Python), 881 ms a call (Readability.js) |

The fetch server answers as the reference does down to its argument errors (pydantic's messages),
its URL rewriting, its robots.txt reading (Protego), its refusal of private addresses, its
redirects and its text decoding; each of those parts is compared with the library the reference
uses on thousands of generated inputs. The Markdown of an HTML page is its own: on the 130 pages of
Readability's test suite its words agree with the reference's at a median F1 of 0.98. Its `main`
takes only `Net`, so it can't touch a file, and it connects to the addresses it checked (the
reference looks names up twice). `mcp/fetch/README.md` lists every difference.

### Tasks on every core

```
fn worker(own jobs: Chan[Int], own results: Chan[Int]):
  while true:
    let n = jobs.recv() else return
    results.send(n * n)

fn main() throws:
  let jobs: Chan[Int] = chan(16)
  let results: Chan[Int] = chan(16)
  for i in 0..4:
    spawn worker(jobs, results)
  ...
```

`spawn` starts a lightweight task. Tasks run on one thread per core, and each thread has its own
scheduler and epoll loop; a thread with nothing to do takes new tasks from a busy one. Network calls and channel operations suspend only the task that makes
them. Tasks share nothing but channels and `Shared[T]` values. A `Shared[T]` is read-only, so any
number of threads can read it without locks. If every task is waiting and nothing can wake them,
the program reports a deadlock instead of hanging. For data parallelism, `par for` splits a loop
across cores, and the compiler refuses loops whose iterations would race.

### A web server

```
import http

fn main(net: Net, os: Os) throws:
  let greeting = "hello"
  own fn route(req: http.Request) -> http.Response:
    if req.path == "/": return http.text(200, greeting)
    return http.text(404, "not found")
  http.serve(net, os, 8080, route, 5.0)?      # stops gracefully on SIGTERM or SIGINT
```

`http.serve` runs one task per connection on every core. On SIGTERM or SIGINT it stops accepting,
lets requests already in progress finish (giving up after the 5-second grace period), closes idle
connections and returns.

For an app, the `web` module adds routes with parameters, middleware, forms, cookies (signed ones
too), static files and HTML templates that escape whatever they insert:

```
import http
import web

fn user(req: http.Request, c: web.Ctx) -> http.Response:
  return web.html(200, web.render("<h1>{{name}}</h1>", [web.v("name", web.param(c, "name"))]))

fn main(net: Net, os: Os, fs: Fs) throws:
  var app = web.app()
  web.use(&app, web.logger(os))
  web.use(&app, web.same_origin)                          # refuses cross-site form posts
  web.get(&app, "/users/:name", user)
  web.get(&app, "/static/*file", web.files(fs, "public"))
  web.serve(net, os, app, 8080)?
```

A template is a `const` parameter, like SQL for `pg`: text from a request can be a value, never
markup. `vu new web NAME` writes a starter app with a Dockerfile, a `fly.toml` and a README that
says how to deploy it; `vu build --static` makes a binary that needs no shared libraries.

### Calling C

```
extern "sqlite_glue.c":
  link "sqlite3"
  type Db drop db_close
  fn db_open(ffi: Ffi, path: Str) -> Db throws
  fn db_exec(ffi: Ffi, db: Db, sql: Str) throws
```

C handles are owned like any other value and freed exactly once, by their drop function.

### SQL that can't be injected

```
import pg
var db = pg.connect(net, pg.config("localhost", 5432, "app", password, "appdb"))?
let rows = pg.query(net, &db, "select name from users where id = $1", [id])?
pg.query(net, &db, "select name from users where id = " + id, [])?   # compile error
```

The SQL parameter is `const`: its argument must be text written in the program, so values can
only travel as parameters.

### Packages that can't do more than you allow

```
# vu.pkg
need github.com/someone/pg-pool v1.2.0 net
need github.com/someone/slugify v0.3.1
```

`vu get` fetches packages with git and records each one's commit and a hash of its files in
`vu.lock`, which every build checks. A package gets only the capabilities its line grants: if a
new version of `slugify` starts reading files or calling C, the build stops until you allow it.
Packages in the registry go by name (`vu add clock` writes `need clock v1.2.0 os`), and `vu get`
refuses one whose commit or files aren't what was published.

## The standard library

Built in: strings (with Unicode case, characters and search), lists, maps, files (`Fs`), processes,
environment and signals (`Os`), TCP, TLS (OpenSSL) and DNS (`Net`), channels and timers, JSON,
hashing (SHA-256, HMAC, PBKDF2) and base64, and formatting with Python's names (`split`, `join`,
`strip`, `"{x:.3f}"`). Written in Vu, in `std/`:

- `http`: an HTTP/1.1 and HTTP/2 server (HTTP/2 by prior knowledge or ALPN over TLS) and a client that
  keeps connections open and speaks HTTP/2 to servers that offer it;
- `web`: routes, middleware, forms, file uploads, cookies, static files and escaping HTML templates, on `http`;
- `ws`: WebSockets, server and client (and WebSocket routes in `web`);
- `pg`: a PostgreSQL client (SCRAM-SHA-256, TLS, parameters only), and `sqlite` (through libsqlite3);
- `re`: regular expressions with Python's syntax, in time linear in the text, and as fast as
  Python's on most patterns (faster on many: CHANGELOG.md, round 10);
- `zlib`: zlib, gzip and raw DEFLATE decompression, the same results as Python's `zlib` (and zlib's
  error messages), 1.2–1.3x C zlib's time on compressible data (as fast as Python's, which is C zlib,
  and twice as fast as Go's), with no capability at all and a size limit for zip bombs
  (CHANGELOG.md, rounds 12 and 13); and compression to the same formats, within 1% of C zlib's
  size at levels 6 and 9 in 1.6x its time (round 19);
- `path` and `cli`: file paths as Python's `os.path` gives them, and command-line arguments;
- `time`: UTC dates, ISO 8601 and HTTP dates, RFC 3339 parsing, and time zones from the system's tz
  database (the same answers as Python's zoneinfo for all 498 zones, 1800 to 2200);
- `log`: timestamped or JSON log lines;
- `heap`: a priority queue in a list, ordered by any comparison;
- `dir`: a folder as a capability (paths resolved inside it by the kernel); `stdio`: standard input
  by lines; `json`: JSON of any shape as a tree of values, written as JavaScript writes it; `mcp`: a
  Model Context Protocol server over stdio.

## Performance

Measured with `bench/compare.sh` on a 2-vCPU Linux VM: median of 5, `-O3 -march=native`, each
program's output checked against Vu's before it's timed. Seconds, lower is better.

| | binary-trees 20 | n-body 50M | fannkuch-redux 11 | nsieve 13 | mandelbrot 8000 (2 threads) | spectral-norm 8000 (2 threads) |
|---|---|---|---|---|---|---|
| C | 6.89 s, 130 MB | 3.16 s | **2.85 s** | 5.10 s | **2.84 s** | 2.45 s |
| C, Vu's allocator | 2.73 s, 66 MB | | | | | |
| C++ | 8.66 s, 132 MB | 4.62 s | 3.53 s | **2.55 s** | **2.84 s** | **1.82 s** |
| Rust | 8.60 s, 130 MB | **2.81 s** | 3.26 s | 4.84 s | 2.93 s | 2.00 s |
| Go | 18.97 s, 240 MB | 5.19 s | 3.21 s | 4.73 s | 2.93 s | 3.06 s |
| **Vu** | **2.62 s, 66 MB** | 3.56 s | 3.14 s | 4.70 s | 3.00 s | 2.55 s |

- **binary-trees is an allocator result.** Vu is 2.6x faster than C that calls `malloc` and `free`
  per node, in half the memory, because the compiler knows when each node dies: freed nodes go on a
  free list for their type and new ones are carved from big chunks, with no runtime checks. C written
  with that same allocator (`bench/bt_pool.c`) ties it: 2.73 s against 2.62 s. So the win is that Vu
  does it for you, safely; it isn't faster code than C can be. (This column is from one run on
  2026-10-28, with the pooled C added; the others are from round 11.)
- **Every check stays on, and the rest are within 1.04–1.13x of C** (fannkuch-redux ahead of Rust
  and Go). Vu checks every index and every Int operation, and in hot loops it makes those checks
  cheap instead of dropping them: a loop's indexes that the loop bounds (`xs[i]`, `xs[i + 1]`,
  `xs[0]`) are checked once before it starts, and a loop that only computes numbers runs first with
  its checks recorded instead of stopping it, which lets the C compiler vectorize it, and again
  checked only if one failed (details in CHANGELOG.md, round 11). That took spectral-norm from
  3.3 s to 2.4–2.5 s, and fannkuch-redux from 3.4 s to 3.1–3.2 s. n-body asks for fused
  multiply-add, as C's compiler does by itself: `fma(a, b, c)` gives the same result on every
  machine, which leaving the choice to the C compiler doesn't (4.5 s to 3.6 s).
- What's left: fannkuch-redux's flips index the list by values read from it, which no check before
  the loop can cover (Rust pays the same). The rest of n-body's gap to C hasn't been investigated.
- nsieve's C++ version is fast because `vector<bool>` packs the sieve into bits; the others use a
  byte per number.
- Against Python 3.13 and JavaScript on Node 22 (`bench/dyn/compare.sh`: every language pinned to one
  core, the same size for all, median of 3, outputs checked): Vu is 4.3–140x faster than Python
  (binary-trees 15x, n-body 81x, spectral-norm 140x, nsieve 4.3x, fannkuch-redux 31x, mandelbrot 32x)
  and 1.1–5.2x faster than Node (binary-trees 5.2x, the rest 1.1–1.9x). Sizes are smaller than the
  table above's for n-body (5M steps), spectral-norm (2000) and mandelbrot (4000), where Python would
  take minutes per run.
- On HTTP, a Vu server on one core handled 121k requests/s for a minimal reply and 25.5k for a
  5.8 KB JSON order parsed and answered, against 112k and 9.5k for a raw-TCP Go server (details and
  memory in CHANGELOG.md, round 7).

## Built for the model that writes it

Vu's compiler, runtime, standard library, tests and these documents were written by an AI model
(Anthropic's Claude), working in rounds that its author directed and reviewed; the changelog
records each round. Most of Vu's design follows from that:

- **Few tokens.** On the benchmark programs, Vu needs 21–42% fewer tokens than C, C++, Rust or Go
  (counted with the GPT-4o tokenizer, comments stripped, each formatted with its standard tool).
- **One way to write things.** The syntax is indentation-based, names are ASCII only, there is no
  inheritance (`x.f(y)` is just `f(x, y)`), and there is no global mutable state.
- **Errors a model can act on.** Compile errors name the variable and both places involved, and
  say what to write instead. A panic prints a backtrace with Vu file and line numbers. `vu check`
  runs only the front end, so a mistake is reported in milliseconds (0.4 s for the compiler itself,
  14,700 lines).
- **Checks in one command.** `tests/try.sh file.vu` checks a program, runs it, runs it again under
  the sanitizers and compares the output, and audits the generated C.

## How it's tested

`tests/gate.sh` runs every suite: about 600 targeted programs that each try to break one rule,
21 programs the compiler must refuse, every program built five ways (gcc and clang, optimized or
not, two allocators) that must print the same, JSON tests, memory tests, and network, TLS, HTTP,
HTTP/2 and WebSocket tests against Python's libraries and hand-made hostile input (including the
known HTTP/2 attacks), a real PostgreSQL server and a fake hostile one, text, regular expressions,
paths and hashing compared with Python on random input, the targeted programs again on ARM64 under
qemu, macOS builds, and the compiler built to WebAssembly checked against the native one on all
1,288 checks and formats of the targeted programs (12 minutes on a 2-core machine when little has changed, 26 when everything
is rebuilt; CHANGELOG.md, round 14). Each runs under
AddressSanitizer, UBSan and LeakSanitizer, and the threaded programs also run under
ThreadSanitizer. The compiler compiles itself, and every rebuild must reach a fixed point (stages
2 and 3 produce identical C) before it's installed. Each new feature went through rounds of
attacks until a whole round found nothing; CHANGELOG.md lists what each round found.

## Limits

- Linux on x86-64 and ARM64. The compiler also builds to WebAssembly (`tools/wasm.sh`), where it
  checks and formats but can't build programs: that's the playground on vulang.org. Programs build
  to WebAssembly (WASI) with `vu build --wasm` if they use no tasks, sockets, processes or C.
- macOS (kqueue) builds for ARM64 and x86-64 but hasn't been run on a
  Mac.
- Strings are bytes. Text functions (`chars()`, `upper()`, `normalize()`, `is_alpha()`...) read them
  as UTF-8, with Python's Unicode tables (15.1); `\w` in `re` is ASCII.
- Only new tasks move between threads: two tasks that have started on the same thread and never
  wait take turns only when one of them waits.
- The safety rules are conservative, and some correct programs need rewriting to pass.
- Tested on 10 small tasks only (CHANGELOG.md, round 20): three models wrote Vu from SPEC.md alone that
  passed every test as often as their Rust (30 of 30 each, after two compiler fixes the test found).

## Repository

| Path | What's there |
|---|---|
| `vu` | the command: builds the compiler on first use, then runs it |
| `compiler/*.vu` | the compiler, in Vu (front end, checker, C code generator, build driver) |
| `compiler/rt/` | the C runtime: memory, strings, tasks and the scheduler, JSON, TLS |
| `compiler/vuc_seed.c` | the compiler compiled to C, to bootstrap from |
| `compiler/build.sh` | rebuilds the compiler and checks the fixed point |
| `std/` | the standard library modules written in Vu |
| `examples/` | the benchmark programs and a JSON parser |
| `mcp/filesystem/`, `mcp/time/`, `mcp/fetch/` | MCP servers: filesystem, time, fetch |
| `tests/` | the test suites; `tests/gate.sh` runs them all |
| `bench/` | benchmark programs in C, C++, Rust and Go, and the scripts that time them |
| `SPEC.md` | the language |
| `CHANGELOG.md` | how it was built, round by round, with measurements |
| `attic/` | the retired Python compiler |
