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
./vu help                                # every command and flag
```

`vu lsp` gives editors the compiler's errors as you type, and formatting.

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
(calling C).

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

## The standard library

Built in: strings (with Unicode case, characters and search), lists, maps, files (`Fs`), processes,
environment and signals (`Os`), TCP, TLS (OpenSSL) and DNS (`Net`), channels and timers, JSON,
hashing (SHA-256, HMAC, PBKDF2) and base64, and formatting with Python's names (`split`, `join`,
`strip`, `"{x:.3f}"`). Written in Vu, in `std/`:

- `http`: an HTTP/1.1 and HTTP/2 server (HTTP/2 by prior knowledge or ALPN over TLS) and an HTTP/1.1
  client;
- `ws`: WebSockets, server and client;
- `pg`: a PostgreSQL client (SCRAM-SHA-256, parameters only);
- `re`: regular expressions with Python's syntax, in time linear in the text, and as fast as
  Python's on most patterns (faster on many: CHANGELOG.md, round 10);
- `zlib`: zlib, gzip and raw DEFLATE decompression, the same results as Python's `zlib` (and zlib's
  error messages), 1.2–1.3x C zlib's time on compressible data (as fast as Python's, which is C zlib,
  and twice as fast as Go's), with no capability at all and a size limit for zip bombs
  (CHANGELOG.md, rounds 12 and 13);
- `path` and `cli`: file paths as Python's `os.path` gives them, and command-line arguments;
- `time`: UTC dates, ISO 8601 and HTTP dates, RFC 3339 parsing;
- `log`: timestamped or JSON log lines.

## Performance

Measured with `bench/compare.sh` on a 2-vCPU Linux VM: median of 5, `-O3 -march=native`, each
program's output checked against Vu's before it's timed. Seconds, lower is better.

| | binary-trees 20 | n-body 50M | fannkuch-redux 11 | nsieve 13 | mandelbrot 8000 (2 threads) | spectral-norm 8000 (2 threads) |
|---|---|---|---|---|---|---|
| C | 11.31 s, 130 MB | 3.16 s | **2.85 s** | 5.10 s | **2.84 s** | 2.45 s |
| C++ | 11.61 s, 132 MB | 4.62 s | 3.53 s | **2.55 s** | **2.84 s** | **1.82 s** |
| Rust | 13.11 s, 130 MB | **2.81 s** | 3.26 s | 4.84 s | 2.93 s | 2.00 s |
| Go | 25.10 s, 191 MB | 5.19 s | 3.21 s | 4.73 s | 2.93 s | 3.06 s |
| **Vu** | **4.39 s, 66 MB** | 3.56 s | 3.14 s | 4.70 s | 3.00 s | 2.55 s |

- **binary-trees:** Vu is about 2.6x faster than C in half the memory. The compiler knows when each
  node dies, so freed nodes go onto a per-type free list and are reused with no runtime checks.
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

Most of Vu's design follows from being written by an LLM:

- **Few tokens.** On the benchmark programs, Vu needs 21–42% fewer tokens than C, C++, Rust or Go
  (counted with the GPT-4o tokenizer, comments stripped, each formatted with its standard tool).
- **One way to write things.** The syntax is indentation-based, names are ASCII only, there are no
  methods or inheritance, and there is no global mutable state.
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
qemu, and macOS builds (12 minutes on a 2-core machine when little has changed, 26 when everything
is rebuilt; CHANGELOG.md, round 14). Each runs under
AddressSanitizer, UBSan and LeakSanitizer, and the threaded programs also run under
ThreadSanitizer. The compiler compiles itself, and every rebuild must reach a fixed point (stages
2 and 3 produce identical C) before it's installed. Each new feature went through rounds of
attacks until a whole round found nothing; CHANGELOG.md lists what each round found.

## Limits

- Linux on x86-64 and ARM64. macOS (kqueue) builds for ARM64 and x86-64 but hasn't been run on a
  Mac.
- Strings are bytes. Text functions (`chars()`, `upper()`, `ord`...) read them as UTF-8; there is
  no Unicode normalization and no character classes (`isalpha`).
- No methods: functions take the value they work on as their first argument (`area(c)`).
- Only new tasks move between threads: two tasks that have started on the same thread and never
  wait take turns only when one of them waits.
- No package registry: packages are git repositories, named by URL.
- The safety rules are conservative, and some correct programs need rewriting to pass.
- Not yet tested: whether an LLM given only SPEC.md writes correct Vu more often than Rust.

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
| `tests/` | the test suites; `tests/gate.sh` runs them all |
| `bench/` | benchmark programs in C, C++, Rust and Go, and the scripts that time them |
| `SPEC.md` | the language |
| `CHANGELOG.md` | how it was built, round by round, with measurements |
| `attic/` | the retired Python compiler |
