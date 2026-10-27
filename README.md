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

Vu is an experiment, and v0 runs on Linux only. The compiler is written in Vu.

## Getting started

You need gcc (or clang, with `CC=clang`) on Linux. Clone the repository and run `./vu`. The first
run builds the compiler from `compiler/vuc_seed.c`, the C the compiler produces from itself, so no
other tools are needed.

```
./vu run examples/binarytrees.vu 16      # build without optimization and run
./vu check examples/json.vu              # type and ownership errors only, in milliseconds
./vu build examples/nbody.vu -o nbody    # optimized binary (-O3 -march=native)
./vu build app.vu --san                  # with AddressSanitizer, UBSan and LeakSanitizer
./vu help                                # every command and flag
```

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
```

A call that can fail must be handled, or the program doesn't compile. `throws E` with an enum `E`
gives typed errors that callers can match on.

### Enums, generics and closures

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
scheduler and epoll loop. Network calls and channel operations suspend only the task that makes
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

## The standard library

Built in: strings, lists, maps, files (`Fs`), processes, environment and signals (`Os`), TCP, TLS
(OpenSSL) and DNS (`Net`), channels and timers, JSON, and formatting with Python's names
(`split`, `join`, `strip`, `"{x:.3f}"`). Written in Vu, in `std/`:

- `http`: an HTTP/1.1 server and client, over TCP or TLS;
- `time`: UTC dates, ISO 8601 and HTTP dates, RFC 3339 parsing;
- `log`: timestamped or JSON log lines.

## Performance

Measured with `bench/compare.sh` on a 2-vCPU Linux VM: median of 5, `-O3 -march=native`, each
program's output checked against Vu's before it's timed. Seconds, lower is better.

| | binary-trees 20 | n-body 50M | fannkuch-redux 11 | nsieve 13 | mandelbrot 8000 (2 threads) | spectral-norm 8000 (2 threads) |
|---|---|---|---|---|---|---|
| C | 11.24 s, 130 MB | 3.08 s | **2.71 s** | 4.53 s | **2.82 s** | 2.13 s |
| C++ | 11.67 s, 132 MB | 4.47 s | 3.35 s | **1.58 s** | 2.91 s | **1.79 s** |
| Rust | 13.13 s, 130 MB | **2.59 s** | 3.09 s | 4.37 s | 2.95 s | 1.89 s |
| Go | 23.51 s, 191 MB | 4.82 s | 3.23 s | 4.28 s | 2.97 s | 2.69 s |
| **Vu** | **3.63 s, 66 MB** | 5.33 s | 3.66 s | 4.17 s | 2.93 s | 3.77 s |

- **binary-trees:** Vu is about 3x faster than C in half the memory. The compiler knows when each
  node dies, so freed nodes go onto a per-type free list and are reused with no runtime checks.
- **Behind on n-body, fannkuch-redux and spectral-norm.** Earlier builds matched C on all three
  (CHANGELOG.md), so this is a slowdown that crept in, not a limit of the design. It's being fixed;
  these numbers will change.
- nsieve's C++ version is fast because `vector<bool>` packs the sieve into bits; the others use a
  byte per number.
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
  runs only the front end, so a mistake is reported in milliseconds (0.14 s for the 6,500-line
  compiler).
- **Checks in one command.** `tests/try.sh file.vu` checks a program, runs it, runs it again under
  the sanitizers and compares the output, and audits the generated C.

## How it's tested

`tests/gate.sh` runs every suite: about 500 targeted programs that each try to break one rule,
21 programs the compiler must refuse, every program built five ways (gcc and clang, optimized or
not, two allocators) that must print the same, JSON tests, memory tests, and network, TLS and HTTP
tests against Python and curl. Each runs under
AddressSanitizer, UBSan and LeakSanitizer, and the threaded programs also run under
ThreadSanitizer. The compiler compiles itself, and every rebuild must reach a fixed point (stages
2 and 3 produce identical C) before it's installed. Each new feature went through rounds of
attacks until a whole round found nothing; CHANGELOG.md lists what each round found.

## Limits

- Linux only (epoll; the task switch is hand-written for x86-64, with `ucontext` elsewhere).
- Strings are byte strings, with no Unicode handling beyond UTF-8 checks in JSON.
- No methods, traits or interfaces. Generics are constrained only by how they're used.
- Tasks don't move between threads, so an idle thread doesn't take work from a busy one, and a
  task that never waits keeps the other tasks on its thread from running.
- No package manager. Modules are files, found next to the importing file or in `std/`.
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
