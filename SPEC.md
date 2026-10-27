# Vu v0

A small systems language aiming at four things at once: few tokens for an LLM to read and
write, fast compiles, no memory bugs, and C/Rust-level speed. The compiler translates Vu
to C and lets the system C compiler do the optimizing.

## A complete program

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

## Syntax

- Python-style: blocks open with `:` and are indented with spaces. A block can also be a
  single statement on the same line (`if x: return y`).
- Comments start with `#`. Names use ASCII letters, digits and `_` only, so two different
  names can never look identical.
- Source code is ASCII outside string literals and comments. Only space, tab, newline,
  carriage return, vertical tab and form feed count as whitespace, so a non-breaking space
  pasted from a web page is reported (`unexpected character U+00A0`) rather than silently
  accepted. Blocks and expressions can nest at most 4000 levels deep.
- Top level holds only `fn`, `type`, `const`, `interface` and `impl`. There is no global mutable state.

## Types

| Type | Meaning |
|---|---|
| `Int` | 64-bit signed integer. Overflow stops the program. |
| `Float` | 64-bit IEEE float |
| `Bool` | `true` / `false` |
| `Byte` | 0..255, one byte in memory. Literals: `65`, `0x41` or `'A'`. Overflow stops the program. |
| `Str` | an owned string of bytes: `s.len`, `s[i]` (a Byte), `s[a..b]` (a new Str), `+`, `+=`, `== <`, `s.reserve(n)` |
| `[T]` | growable list: `xs.len`, `xs.push(v)`, `xs.pop()` (removes and returns the last element; stops the program if empty), `xs[i]` (bounds-checked), `xs.reserve(n)` |
| `T?` | optional: either a `T` or `nil` (`Int?`, `Str?`, `[T]?`, a struct or enum...; not a capability or another optional). Recursive types must use it (or a list or map). |
| `{K: V}` | map from Int, Byte, Bool or Str keys to any value (see Maps) |
| `type Name:` | a struct, fields listed below it (`x, y: Float` declares two fields) |
| `type Name:` with variants | an enum (see Enums) |
| `Fs` | the capability to read and write files (see Capabilities) |

Structs are built with positional or named arguments: `Body(1, 2)` or `Body(x: 1, y: 2)`.
`s.reserve(n)` and `xs.reserve(n)` make room for `n` more bytes or elements up front, so a
string or list built in a loop of known length grows without reallocating (a negative `n`
stops the program).
Integer literals become a Float or Byte where one is expected. Other conversions are explicit:
`float(i)`, `int(f)`, `int(b)`, `byte(i)` (stops the program if i isn't 0..255).

String literals are `Str` values and can interpolate: `let msg = "{n} items"`. Escapes are
`\n \t \r \0 \\ \"`, and Byte literals take the same ones (`'\r'`). An interpolation can hold
any expression, including other strings, as in Python 3.12: `"{m["k"]} {", ".join(xs)}"`. Every
Vu string interpolates, so a literal brace is always doubled, inside nested strings too (`{{`).
Strings are
immutable byte strings (no Unicode handling in v0). `bytes(s)` copies one into a `[Byte]` list,
and `str(bs)` copies back.

## Variables and functions

- `let` is immutable, `var` is mutable. Every variable is initialized when declared. Types
  are inferred inside functions and written out in signatures.
- Parameters are **read-only by default**. A parameter declared `var` can be modified, and
  the caller marks the argument with `&`, so every mutation is visible at the call site:

  ```
  fn advance(var bodies: [Body], dt: Float): ...
  advance(&bodies, 0.01)
  ```

- **Owned parameters.** A parameter declared `own` takes ownership of its argument: inside
  the function it's a local the function may change, move, store or return, and it's freed
  at the end if it wasn't. At the call the argument is moved, exactly as by `let`, so using
  the variable afterwards is an error, and a field or a borrowed value can't be passed:

  ```
  fn add(var lexer: Lexer, own tok: Token):
    lexer.toks.push(tok)          # stored, not copied
  add(&lx, t)                     # t is moved; using it again is an error
  ```

  A `Str` variable that is used again (later, or elsewhere in the same statement) is copied
  instead of moved. The move happens after the other arguments are evaluated, so
  `consume(items, items.len)` works; borrowing the same variable in another argument is an
  error. `own` is only special before a parameter name. `swap(&a, &b)` exchanges two owned
  values of the same type without copying either.
- **Locals may shadow** a function, a constant or a built-in: `let text = ...` and
  `let max = 10` are fine. Calling the shadowed function in that scope is an error that says
  so. Type and variant names stay reserved.
- **Strings that can't be moved are copied.** Taking a `Str` from a field, a list element, a
  parameter, a loop binding, or a frozen variable copies it (`let name = p.name`). Other
  owned values (lists, structs, enums) are never copied implicitly.
- **`let` of a part is a view.** `let items = bag.items`, where the value is a list, struct
  or enum that can't be moved (it's a field or element, or something borrowed), gives a
  read-only view instead of a move. Until the view's block ends, the variable it comes from
  is frozen: it can be read but not changed or moved, so the view can never dangle.
  `var items = bag.items` still means a move and is rejected for a field.
## Enums and match

An enum lists its variants; each variant holds zero or more named values:

```
type Token:
  Num(value: Int)
  Word(text: Str)
  End

fn show(t: Token) -> Str:
  match t:
    Num(v): return "number {v}"
    Word(w): return "word " + w
    End: return "end"
```

- Variants are created like functions (`Num(1)`, `Word(text: "hi")`) or by name (`End`).
  Variant names are top-level names, so they must be unique in their module.
- `match` must handle every variant or end with a `_:` arm, and a `_` arm when every variant
  is already handled is an error (it would never run). `_` also skips a value: `Num(_):`.
- Bindings follow the same rules as `if v = opt`: they borrow from the matched value, which
  can't be changed or moved inside the arm. `match var x:` gives write access through the
  bindings (`Num(v): v += 1`).
- Enums whose variants hold no values can be compared with `==` and `!=`; others are
  inspected with `match`.
- An enum with only plain-data values is copied; otherwise it moves, like a struct. In an
  enum that moves, a variant holding more than 24 bytes is stored behind a pointer when
  another variant is smaller, so one big variant doesn't make every value big.

## Generics

Functions and types can take type parameters, in brackets after the name:

```
type Pair[A, B]:
  first: A
  second: B

type Opt[T]:
  Some(value: T)
  None

fn largest[T](xs: [T], better: fn(T, T) -> Bool) -> T?:
  if xs.len == 0: return nil
  var best = xs[0]
  for x in xs:
    if better(x, best): best = x
  return best

let p = Pair(1, "one")                       # Pair[Int, Str]
let o: Opt[Str] = None
let m = largest([3, 9, 4], fn(a, b) => a > b)  # T is Int: m is 9
let xs: [Int] = empty()                         # fn empty[T]() -> [T]: T from the expected type
```

- Type arguments are inferred, never written at a call: from the arguments, then from the type
  the result is expected to have (`let xs: [Int] = empty()`, `return`, a field, `?`, `else`).
  A closure argument's parameter types come from what's known by then, and its result tells the
  rest. When nothing says what a type parameter is, the error asks for a type.
- A generic type is written with its arguments (`Pair[Int, Str]`, `[Opt[Int]]`), except where it's
  created: `Pair(1, "one")`.
- Each use with new type arguments makes a separate copy of the function or type (as C++
  templates and Rust do), so generic code runs as fast as hand-written code. Each copy is
  checked on its own, and an error inside one says which: `(in largest[Str], used on line 12)`.
- Type arguments can be any type except capabilities, nothing, and borrowing closures. Type
  arguments nest at most 32 deep, and a program has at most 2,000 copies, so a function that
  calls itself with ever bigger types (`f[[T]]` from `f[T]`) is an error, not a hang.

## Interfaces

An interface names functions that several types provide. Each type gives its own in an `impl` block:

```
interface Shape:
  fn area(s: Self) -> Float
  fn grow(var s: Self, amount: Float)

impl Shape for Circle:
  fn area(c: Circle) -> Float:
    return 3.14159 * c.r * c.r
  fn grow(var c: Circle, amount: Float):
    c.r += amount

area(c)                                   # Circle's area: chosen by the type, at compile time
fn total[T: Shape](xs: [T]) -> Float: ... # a bound: T must implement Shape
let shapes: [Shape] = [Circle(1), Rect(2, 3)]   # values of any type that implements Shape
for s in shapes: print("{area(s)}")      # each calls its own type's area
```

- An interface function's first parameter is the value it works on, of type `Self` (borrowed, or `var`
  to change it). `Self` appears nowhere else: not in other parameters, not in the result.
- An `impl` gives every function of the interface, each with exactly the interface's signature
  (with the type in place of `Self`). Interfaces can be implemented for structs, enums (including
  generic instances like `Pair[Int, Str]`), `Int`, `Float`, `Bool`, `Byte` and `Str`, once per type.
- A call `area(x)` goes to the function for `x`'s type. In generic code, that's the type argument's
  function, so it costs what a direct call does. A bound (`[T: Shape]`) makes a type argument that
  doesn't implement the interface an error at the call, naming both.
- The interface's name is also a type: a `Shape` value holds a value of any type that implements it
  (on the heap) and calls that type's functions through a table, as Go's interface values and Rust's
  `Box<dyn Shape>` do. A value becomes one where a `Shape` is expected (`let`, a list, a field, an
  `own` parameter, `return`) and is moved in. Passed to a borrowed `Shape` parameter, it's lent:
  nothing is moved, copied or allocated.
- Interface functions can fail (`throws`, `throws E`) and take `var` and `own` parameters. An interface
  function isn't a value (wrap it: `fn(c: Circle) => area(c)`). Interface values can't be compared
  with `==`, matched, written as JSON, used as map keys, or put in a `Shared` value (the type behind
  one could hold a connection); they can go through channels.

## Closures and function values

```
fn apply(f: fn(Int) -> Int, x: Int) -> Int:
  return f(x)

fn adder(n: Int) -> fn(Int) -> Int:
  return own fn(x) => x + n         # owns a copy of n: can be returned and stored

fn main():
  let k = 10
  print("{apply(fn(x) => x * k, 4)}")  # 40: borrows k for the call
  let add5 = adder(5)
  print("{add5(1)}")                   # 6
  fn shout(s: Str) -> Str:             # a nested function with a block body
    return s + "!{k}"
  var handlers: [fn(Str) -> Str] = []
  handlers.push(on_get)                # a named function (fn on_get(path: Str) -> Str) is a value too
  print(shout(handlers[0]("/")))
```

- **Function types** are `fn(A, B) -> R`, `fn(Str) -> Int throws` (it fails with a message), and
  `fn(T)` for one that returns nothing. `(fn(Int) -> Int)?` is an optional one.
- **Closures**: `fn(x: Int) -> Int => x * k` is an expression. Parameter and return types can be
  left out when the context gives them (an argument, a typed `let`, a field). `fn name(...): ...`
  inside a function is a nested function with a block body, bound to `name`; it can't call
  itself (make it top-level to recurse). Closure parameters are read-only (no `var` or `own`).
- **What a closure can see.** It reads the variables it names from where it's written, and
  can't change them. A plain closure **borrows** them: it can be called, bound with `let`, or
  passed to a function, but not stored, returned, sent or put in a `var`, so it can never
  outlive what it points at. While a `let`-bound one exists, the variables it borrows are
  frozen (readable, not changeable or movable).
- **`own fn`** copies what it captures into the closure (Str and plain values are copied,
  lists, structs and enums are moved, so using them afterwards is an error). Such a closure is
  an ordinary owned value: it moves like a list, can be returned, stored in fields, lists and
  maps, sent on channels and given to `spawn`, and it's freed with its owner. A closure that
  captures nothing is a plain function value either way.
- **Calling**: `f(x)`, `h.handler(req)`, `routes[path](req)`, `make()(x)`. A function value that
  throws is handled like any call that can fail: `f(x)?`, `f(x) else d`, `match f(x):`.
- **Named functions as values**: `let f = double`, `apply(double, 3)`, `util.parse`. A function
  with `var` or `own` parameters, or one that fails with typed errors (`throws E`), can't be a
  value; wrap it in a closure. A generic function becomes a value given a type:
  `let f: fn(Int) -> Int = identity`.
- A closure that captures a capability (`os`, `net`) carries it: whoever holds the closure can
  use that capability through it.
- Function values can't be compared, printed or converted to JSON. A call through one is an
  indirect C call; a closure's captured variables live in an env (on the stack for a borrowing
  closure, on the heap for an own one).

## Errors

A function marked `throws` can stop with an error message instead of returning:

```
fn parse_digit(b: Byte) -> Int throws:
  if b < '0' or b > '9': fail "not a digit: {b}"
  return int(b) - 48
```

Every call to such a function must handle the error, or the program doesn't compile:

```
let d = parse_digit(b)?              # pass it on: only inside a function marked throws
let d = parse_digit(b) else 0        # replace it with a fallback value
let d = parse_digit(b) else continue # or leave: else return [value], else break, else continue,
                                     # or else fail value (in a function marked throws)
parse_digit(b) else panic("bad")     # or stop the program
match parse_digit(b):                # inspect it
  ok(d): print("{d}")
  err(msg): print(msg)
```

- `?` can go anywhere in an expression: `items.push(parse(&p)?)`, `add(num(a)?, num(b)?)`,
  `if parse(s)? > 3:`. Each one runs before the rest of its statement, in the order written,
  so it is an error where that would change what runs: after a call to its left in the same
  statement, on the right of `and`/`or`, in an `else` fallback, or in a `while` condition
  (which runs again on every pass). In an `elif` condition it runs only when the conditions
  before it were false.
- When an error passes up with `?` or `fail`, every value the function owns is freed first.
- `?` and `fail` aren't allowed inside `par` loops, since every iteration must run; use
  `else` or `match` there.
- If `main` is marked `throws` and an error reaches it, the program prints `error: <message>`
  to standard error and exits with code 1. (`panic` exits with 101.)
- File operations and reading numbers from text can fail the same way (see Built-ins).

### Typed errors

`throws E`, with `E` an enum, makes a function fail with values of `E` instead of messages, so
a caller can tell the errors apart:

```
type ConfigError:
  Missing(key: Str)
  Bad(key: Str, why: Str)

fn port(m: {Str: Str}) -> Int throws ConfigError:
  if not ("port" in m): fail Missing("port")
  let n = int(m["port"]) else -1
  if n < 0: fail Bad("port", "not a number")
  return n

match port(conf):
  ok(p): print("{p}")
  err(e):                      # e is a ConfigError
    match e:
      Missing(k): print("set {k}")
      Bad(k, why): print("{k}: {why}")
```

- `?` passes an `E` on from a function that `throws E` too, and also into a plain `throws`
  function, where it becomes the message (`Bad(port, not a number)`: the variant and its plain
  fields). A plain `throws` call can't be passed on with `?` inside `throws E` (handle it with
  `else` or `match`, and `fail` an `E`), and neither can a different enum's errors.
- A `main` marked `throws E` prints `error: <message>` and exits 1, as for messages.

## JSON

`to_json(x)` writes a value as JSON, and `from_json(text, Type)` reads one, checking it against
the type. The code for each type is generated at compile time, so no tree of JSON values is built:

```
type Item:
  sku: Str
  qty: Int
  gift: Bool?

type Order:
  id: Str
  items: [Item]

let o = from_json(body, Order)?             # it can fail, so ?, else or match
print(to_json(o.items[0]))                  # {"sku":"A-1","qty":2,"gift":null}
let counts = from_json(text, {Str: [Int]}) else {}
```

- Types: `Int`, `Float`, `Byte`, `Bool`, `Str`, lists, maps with `Str` keys, structs, enums and
  optionals of those. Anything else (a capability, a channel, a connection, a map with other
  keys) is a compile error that names the field.
- A struct is an object with its fields in order. A field that is missing is an error unless
  it's optional (then `nil`); fields the type doesn't have are skipped; a field that appears
  twice must be valid both times, and the last one is kept.
- An enum variant without fields is a string (`"Dot"`); one with fields is an object with one
  key: `{"Rect": {"w": 2, "h": 3}}`. Variants are named without their module.
- `nil` is `null`. A Float that is infinite or NaN is written as `null`; reading a number too
  large for a Float is an error. An `Int` must be written without a fraction or exponent and
  fit in 64 bits, and a `Byte` must be 0 to 255.
- Strings are checked to be UTF-8 and `\u` escapes (including surrogate pairs) are decoded;
  writing replaces invalid UTF-8 with U+FFFD. Nesting deeper than 1000 levels is an error.
- An error says where: `items[0].qty: expected a number at byte 49`.

## Maps

```
var counts: {Str: Int} = {}
counts["the"] = 1                    # insert or replace
counts[w] = counts.get(w, 0) + 1     # .get(key, default) for plain-data values
if "the" in counts: ...
let n = counts["the"]                # a missing key stops the program; check with 'in' first
counts.remove("the")                 # returns true if the key was there
for k in counts: print(k + " {counts[k]}")
for k, n in counts: print(k + " {n}")        # keys and values together, no second lookup
for k, var n in counts: n += 1               # change values in place
let squares = {1: 1, 2: 4, 3: 9}
```

- Keys are Int, Byte, Bool or Str. The map keeps its own copy of each key; a key variable
  that isn't used again in its block is moved into the map instead of copied.
- Iteration follows insertion order, like Python, so output is deterministic.
- Hashing uses SipHash with a random key per run, so input that an attacker controls can't
  be chosen to collide (hash flooding).
- While a loop or binding borrows a map, the map can't be changed. In `for k, var v in m`
  the loop has exclusive access: values change only through `v`, and keys never change.
- A key built by an expression (`m["k{i}"] = v`, `m[s[0..2]]`) works for inserting and for
  reading plain-data values. To read or change an owned value (a list, string, enum...)
  through a computed key, put the key in a variable first: `let k = s[0..2]`, then `m[k]`.
- In a `par` loop a map from outside is read-only; a list of maps can be split between
  iterations like any list (`rows[i][k] = v`).

## Memory model (why there are no memory bugs)

Every value has exactly one owner and is freed automatically when its owner goes out of
scope. There are no pointers or references in the type system, so there are no lifetimes
to annotate. The compiler enforces five rules:

1. **Moves.** Assigning a list, an optional, or a struct containing them moves it. Using a
   variable after it was moved is a compile error, including on only some paths and inside
   loops. Plain-data structs (only Int/Float/Bool fields) are copied instead.
2. **Borrows can't escape.** A function can read or modify what it's given but can't keep
   it, return it, or move out of it. References can't be stored, so they can't dangle.
3. **Exclusive mutation.** A value passed as `&x` can't also be passed in another argument
   of the same call. This rules out aliasing bugs like appending a list to itself.
4. **No mutation while borrowed.** Inside `for x in xs` or `if v = opt`, the borrowed value
   can't be modified, pushed to, or moved. This rules out iterator invalidation. With
   `for var x in xs` the loop gets exclusive access and the list can't be touched at all
   except through `x`.
5. **Nil is checked.** An optional must be unwrapped with `if x = opt:` before use.
6. **No data races.** In `par for i in a..b:` the iterations run on different threads.
   Inside the loop, everything from outside is read-only, except list elements indexed by
   exactly the loop counter: iteration `i` owns `xs[i]` and may read, write, or push to it.
   Any other access to `xs` in the loop is rejected, and so are `break` and `return`.

At runtime, indexing and slicing are bounds-checked, and integer arithmetic checks for
overflow and division by zero. A failed check stops the program with a message and exit
code 101. It never reads or writes memory it shouldn't. Recursion too deep for the stack
(on the main thread or a `par` worker) also stops with `panic: stack overflow` and exit
code 101, as in Rust, instead of crashing with a signal.

`main` runs on a thread with a 256 MB stack, so deep recursion (a recursive-descent parser,
a compiler walking a deep tree) has room before it reaches that limit.

Freed tree nodes go to a per-thread, per-type free list and are reused by later
allocations; at the start of each `par` loop the threads pool their free lists, so nodes freed
on one thread are reused by others. Short strings (up to 256 bytes) are reused the same way.
Building with `--malloc` uses plain `malloc`/`free` instead.

## Capabilities

A program can only touch files if `main` asks for the file-system capability and passes it
to the code that needs it:

```
fn save(fs: Fs, path: Str, text: Str) throws:
  fs.write(path, text)?         # writes a Str or [Byte]

fn main(fs: Fs) throws:
  save(fs, "out.txt", "hello")?
  let back = fs.read("out.txt") else ""
```

`fs.read` and `fs.write` can fail (missing file, no permission, a zero byte in the path), so
they are handled like calls to a `throws` function: with `?`, `else` or `match`.

An `Fs` can't be created anywhere else, so a function that isn't handed one has no way to
read or write files, and its signature shows that. `main` may only take capabilities as
parameters (`Fs`, `Os`, `Net` and `Ffi`, see Calling C). Printing to standard
output needs no capability. `fs.temp_dir()` creates a new private directory under `$TMPDIR`
(or `/tmp`) and returns its path; it can fail.

The operating-system capability `Os` (`fn main(os: Os)`, alone or next to `fs: Fs`)
covers the rest of the outside world:

- `os.run(["gcc", "-O2", "x.c"])` runs a program (found on `PATH`) with those arguments,
  waits, and returns its exit code (128 + the signal number if a signal killed it). Output
  goes to the program's own standard output and error. It fails if the list is empty, an
  argument contains a zero byte, or the program can't be started.
- `os.env("CC")` returns an environment variable, or `""` when it isn't set.
- `os.clock()` returns seconds from a monotonic clock, as a Float, for timing.
- `os.time()` returns the wall-clock time: seconds since 1970-01-01 00:00 UTC, as a Float (see
  the `time` module for dates).
- `os.sleep(seconds)` waits; other tasks run meanwhile.

The network capability `Net` (`fn main(net: Net)`) makes TCP servers and clients. It's built on
tasks (see Tasks and channels below), so each connection usually gets its own task, and code waits
for the network as if nothing else were running:

```
fn handle(net: Net, own c: Conn):
  while true:
    let data = net.recv(c, timeout: 30.0) else return   # "" once the other side has closed
    if data.len == 0: return
    net.send(c, data) else return                       # sends all of a Str or [Byte]

fn main(net: Net) throws:
  let l = net.listen(8080)?          # 0 picks a free port; net.port(l) says which
  while true:
    let c = net.accept(l) else continue
    spawn handle(net, c)
```

- `net.listen(port) -> Listener`, `net.accept(l) -> Conn`, `net.connect(host, port) -> Conn`,
  `net.recv(c) -> Str` and `net.send(c, data)` can each fail, so they're handled with `?`,
  `else` or `match`. `accept`, `connect`, `recv` and `send` take `timeout: seconds`; when it
  passes, the call fails with "timed out".
- A `Listener` or `Conn` is owned like a struct: moved (into a task, for example), borrowed,
  and closed when its owner goes out of scope. It can't be made any other way, copied, or
  compared.
- `recv` returns at least one byte unless the connection is closed (at most about 1 MB per
  call). TCP is a byte stream, so a request can arrive in pieces or several at once.
- `send` returns once the operating system has taken every byte; while the connection is full,
  other tasks run. It never kills the program when the other side has gone away.
- `connect` looks names up on a helper thread (other tasks keep running) and tries each
  address the name has.
- When the process runs out of file descriptors, `accept` waits and tries again until a
  connection is closed.

TLS uses the same `Conn` and `Listener`, so `recv`, `send` and `accept` work unchanged:

```
let c = net.tls_connect("example.com", 443)?               # checks the certificate and the name
let c = net.tls_connect("localhost", port, ca: ca_pem)?    # trust these certificates instead
let l = net.tls_listen(8443, cert: cert_pem, key: key_pem)?
```

- Certificates and keys are PEM text (read them with `fs.read`), so a program that has no `Fs`
  can't read key files from disk. `cert` may hold intermediate certificates after the server's.
- `tls_connect` checks the server's certificate against the system's certificates (or only
  those in `ca`) and that it is for the host name or IP address given. There is no option to
  turn the check off. `timeout:` covers connecting and the handshake.
- A server's handshake happens on its first `recv` or `send`, in the connection's own task, so
  a slow client can't hold up `accept`. A handshake that fails is that call's error.
- TLS 1.2 and 1.3 (OpenSSL), linked only into programs that use it. Keys protected by a
  password aren't supported.

## Tasks and channels

`spawn f(args)` runs `f` as a new task: a lightweight thread. Tasks run on every core: there is
one task thread per core the program may use (`VU_THREADS=n` sets the number), new tasks go to
the threads in turn, and each task stays on its thread. A task runs until it waits for the network,
a channel or a timer; then another task that's ready on that thread runs. Tasks share nothing but
channels: the arguments move into the new task, so every
parameter of `f` that isn't plain data or a capability must be `own`. `f` returns nothing and
can't fail (no caller would receive the result or the error). When `main` returns, the program
ends, whatever its tasks are doing.

Tasks talk through channels. `Chan[T]` is a queue of up to n values of type T:

```
fn worker(own jobs: Chan[Int], own results: Chan[Int]):
  while true:
    let n = jobs.recv() else return      # fails once the channel is closed and empty
    results.send(n * n)                  # moves the value in; waits while the channel is full

fn main() throws:
  let jobs: Chan[Int] = chan(16)         # chan(n) takes its type from where it goes
  let results: Chan[Int] = chan(16)
  for i in 0..4:
    spawn worker(jobs, results)          # passing a channel to an own parameter shares it
  for n in 0..100:
    jobs.send(n)
  jobs.close()
  var total = 0
  for k in 0..100:
    total += results.recv()?
```

- `ch.recv()` fails when the channel is closed and empty, or when its `timeout: seconds` passes.
  `ch.send(v)` on a closed channel stops the program. `ch.close()` wakes every task waiting on it.
- Passing a channel to an `own` parameter shares it (both sides keep using it); `ch.share()`
  makes another handle to store in a struct or list. The channel is freed, with any values still
  in it, when its last handle goes.
- `os.sleep(seconds)` waits without blocking other tasks.
- `ch.closed()` says whether the channel was closed: closing one channel is how one task tells
  many to stop (each checks `closed()` between the things it waits for).
- If every task is waiting on a channel and nothing (a connection, a timer) can wake any of
  them, the program stops with "deadlock".
- Each task has its own stack (8 MB of address space, used as it grows), so a stack overflow in a
  task is reported like one in `main`. A task that never waits keeps the other tasks on its thread
  from running (tasks on other threads carry on).
- Lines printed by tasks on different threads never mix: each `print` and `eprint` writes its line
  in one piece. The order of lines from different tasks is whatever order they ran in.
- A connection or listener can move to a task on another thread (through a channel or `spawn`);
  it's watched by the thread of the task using it.
- A closure that captures values can be moved into a task, but not shared by several directly:
  share it (below), or use a named function, which makes a new value each time it's named
  (`spawn serve(c, handle)`).

### Shared values

```
type Config:
  name: Str
  limits: {Str: Int}

fn handle(own c: Conn, own cfg: Shared[Config]): ...   # cfg.value.limits["max"]

let cfg = share(Config("prod", {"max": 100}))   # Shared[Config]: moved in, read-only from now on
spawn handle(c1, cfg)                            # an own parameter gets another handle to it
spawn handle(c2, cfg)
let h = share(own fn(req: Request) => answer(req, base))   # closures too: h.value(req)
```

- `share(v)` moves `v` into a `Shared[T]`, which any number of tasks, on any thread, can read at
  the same time. `s.value` is the value; nothing can change it (assignments, `push`, `&`, `var`
  bindings and moves out of it are compile errors), so readers never see it change and need no
  locks. It's freed when its last handle goes.
- Passing a `Shared` value to an `own` parameter (or `spawn`) gives the callee another handle, as
  for channels; `s.share()` makes one to store. `let t = s` moves the handle.
- A `Shared` value can't hold a connection, a listener or a C handle (using one from several tasks
  at once isn't safe), nor a closure that borrows local variables. Channels inside are fine.
- `.value` is read through a variable or field holding the handle, so the value stays alive while
  it's read: `make().value` is refused; write `let s = make()` first.

### Signals and stopping

`os.signals()` returns a `Chan[Str]` on which SIGTERM, SIGINT and SIGHUP arrive (as `"TERM"`,
`"INT"`, `"HUP"`) instead of ending the program. Every call gives a handle to the same channel. A
task waiting on it isn't part of a deadlock: a signal can always come.

```
let stop = os.signals()
spawn run_server(net, l, stopping)    # checks stopping.closed() between requests
let sig = stop.recv()?
stopping.close()                      # tell every task, then wait for them (or not) and return
```

`http.serve` (the standard library) does all of this for HTTP servers.
- Task operations (spawn, channels, the network, `os.sleep`) can't be used inside a `par` loop.

## Calling C

An `extern` block names a C file that is compiled into the program, the libraries it links,
and the handle types and functions it provides. Calling C needs the `Ffi` capability, so a
function that isn't handed one can't run C code:

```
extern "sqlite_glue.c":             # next to this .vu file
  link "sqlite3"                    # -lsqlite3
  type Db drop db_close             # an opaque C pointer; db_close(p) frees it
  fn db_open(ffi: Ffi, path: Str) -> Db throws
  fn db_exec(ffi: Ffi, db: Db, sql: Str) throws
  fn db_count(ffi: Ffi, db: Db, table: Str) -> Int

fn main(ffi: Ffi) throws:
  let db = db_open(ffi, "app.db")?
  db_exec(ffi, db, "create table if not exists t(x)")?
  print("{db_count(ffi, db, "t")}")
                                    # db is closed here, when it goes out of scope
```

- An extern function's first parameter is `ffi: Ffi` (it isn't passed to C). The others can be
  `Int`, `Float`, `Bool`, `Byte`, `Str` or an extern type; it returns one of those or nothing.
- A handle (`type Db drop db_close`) is owned like a struct: moved, borrowed, stored in lists,
  maps and fields, and freed exactly once, by calling its drop function, when its owner goes.
  Vu code can't make one (only extern functions return them), copy one, or compare two. An
  `own` parameter gives the handle to C, which must free it.
- An extern function can't be called inside a `par` loop (the program stops): C libraries
  aren't known to be thread-safe.
- `vu check` checks the Vu side; the C file is compiled by `vu build` and `vu run`.

The C side. The glue file is included after Vu's runtime, so it can use these:

| Vu | C parameter | C result |
|---|---|---|
| `Int` / `Float` / `Bool` / `Byte` | `int64_t` / `double` / `bool` / `uint8_t` | the same |
| `Str` | `const vu_str *s` (`s->data`, `s->len`; borrowed for the call) | `vu_str`, made with `vu_str_from(p, n)` |
| an extern type | `void *` | `void *` (never NULL) |
| `throws` | after the others: `T *out` (if it returns a value), then `vu_str *err` | `bool`: true on success; on failure set `*err = vu_errf("fmt", ...)` |

`vu_cstr(s)` makes a NUL-terminated copy (free it with `free`), or returns NULL when the string
contains a zero byte. The compiler declares each function's expected C signature before
including the file, so a definition that doesn't match is a compile error. C names can't be C
keywords or start with `vu_`, `fn_` or `drop_`.

C code is outside Vu's checks: the glue must not keep a borrowed `vu_str` pointer after the call,
free a borrowed handle, or return a handle that is still owned elsewhere.

## Control flow

```
if cond: ...
elif cond: ...
else: ...
if v = opt: ...          # unwrap an optional (read-only binding)
if var v = opt: ...      # unwrap with write access
while cond: ...
for i in 0..n: ...       # 0 to n-1
for i in 1..=n by 2: ... # inclusive, step 2
for x in xs: ...         # read each element
for var x in xs: ...     # modify each element
par for i in 0..n: ...   # iterations run in parallel on all cores (see rule 6)
break / continue / return
```

Operators: `+ - * / %` (Int `/` truncates), `<< >> & | ^` (Int and Byte), `== != < > <= >=`,
`and or not`, and `+` to join strings.
Int literals can be hex (`0xFF`). `[v] * n` makes a list of n copies of plain values.
Float math is strict IEEE: never fused, so results are identical on every machine.
Comparisons can't be chained.

## Built-ins

`print(s)` prints a string and a newline; `print("x = {x}, e = {e:.9}")` interpolates.
Format specs follow Python: `{n:8}` width (at most 1000), `{e:.9}` decimals (at most 100),
`{b:02x}` zero-padded hex. A Float without a precision prints as the shortest text that
reads back as exactly the same number (`0.1`, `1e+21`, `0.30000000000000004`).
`write(x)` outputs a Str or `[Byte]` exactly as is; `eprint(s)` prints a Str and a newline
to standard error. `exit(code)` ends the program at once with that exit code, flushing
output first; like `panic`, it never returns, so a function may end with it. `args()`
returns all command-line arguments as a `[Str]` (index 0 is the program).
`swap(&a, &b)` exchanges two values of the same type. Also: `panic("...")`, `sqrt`, `abs`,
`min`, `max` (of two or more numbers, or of a list), `float`, `int`, `byte`, `str`, `bytes`.
A NaN always prints as `nan`, as in Python. `arg(i, 10)` reads command-line
argument i as an Int and `arg(i, "default")` as a Str, falling back to the default when it's
missing.

`float(s)` and `int(s)` on a Str read a number from text and can fail, so they're handled
with `?`, `else` or `match`: `let n = int(s) else 0`. The whole string must be the number
(no spaces, no hex, no `inf`/`nan`), and `float(s)` rounds correctly.

The common Python helpers, with Python's names and behavior:

```
let parts = line.strip().split(",")     # s.split(sep); s.split() splits on runs of whitespace
let csv = ", ".join(parts)              # sep.join(items), items a [Str]
if name.startswith("vu_"): ...          # also s.endswith(suffix)
let t = s.strip()                       # also s.lstrip(), s.rstrip(); s.strip("xy") strips those bytes
let ys = sorted(xs)                     # a sorted copy; sorted(xs, reverse: true)
xs.sort()                               # in place; xs.sort(reverse: true)
let lo = min(xs)                        # min/max of a list, or of two or more numbers: max(a, b, c)
```

Text: strings are bytes, and these read them as UTF-8 characters, with Python's names and results:

```
"straße".upper()          # "STRASSE": Python's full Unicode case mapping (also s.lower())
"aé中😀".char_count()     # 4 (s.len is 10: bytes)
for c in s.chars(): ...    # each character as a Str
ord("é")                   # 233; chr(233) is "é"
s.find("é")                # the byte index of the first "é" (for s[a..b]), or -1
s.count("ab")              # how many times, not overlapping
s.replace("a", "b")        # every "a" replaced
if "ab" in s: ...          # whether s contains "ab"
s.is_utf8()                # whether s is valid UTF-8
```

- Bytes that aren't UTF-8 are read as Python's `decode(errors="replace")` reads them: each bad
  stretch is one character, U+FFFD in `chars()`, counted once by `char_count()`; `upper()` and
  `lower()` leave them as they are. `ord` of such a string, of `""` or of more than one character
  stops the program, and so does `chr` of a number that isn't a code point (0 to 0x10FFFF, not a
  surrogate).
- `upper()` and `lower()` match Python's, from tables of Unicode 15.1 (Python 3.13), except that
  `lower()` always turns `Σ` into `σ` (Python uses `ς` at the end of a word). `tests/run_text.sh`
  checks every function here against Python on random text.
- `find`, `count` and `replace` with `""` work as in Python: `find` gives 0, `count` one more than
  the number of characters, and `replace` puts the new text between every two characters.

- Whitespace means ASCII whitespace (space, tab, newline, carriage return, vertical tab, form
  feed). `strip(chars)` removes bytes, which is the same as Python's characters for ASCII.
- `s.split(sep)` with an empty `sep` stops the program, as Python raises an error.
- `sorted`, `.sort`, `min(xs)` and `max(xs)` work on lists of Int, Float, Byte and Str (and
  sorting also on Bool). Sorting is stable, including with `reverse: true`. Strings compare
  byte by byte, which for UTF-8 is the same as Python's order. A NaN sorts after every number
  (before them when reversed). `min` or `max` of an empty list stops the program.

## Tooling

```
vu check file.vu            # errors only: no binary, no C compiler (milliseconds)
vu run file.vu [args]       # quick -O0 build, then run with args
vu run --release file.vu    # optimized build, then run (options go before the file;
                            #   everything after it goes to the program)
vu build file.vu [-o out]   # optimized native binary
  --debug    -O0 build for fast iteration
  --malloc   use malloc/free instead of the node free list
  --san      build with AddressSanitizer + UBSan (implies --malloc)
  --san-pool same sanitizers with Vu's own node allocator (freed nodes are poisoned)
  --tsan     build with ThreadSanitizer (use CC=clang and run with
             OMP_TOOL_LIBRARIES=.../libarcher.so; see CHANGELOG.md)
  --emit-c F write the generated C to F
  --time     report front-end and C compiler time
```

Every compile error comes from Vu's own front end, before the C compiler runs, so `vu check`
gives the same errors as a build. For an edit-and-fix loop, `check` while fixing errors and
`run` to test; keep `build` (or `run --release`) for timing and shipping.

### When something goes wrong

A panic prints what went wrong and where. In quick builds (`vu run`, `--debug`) it also
prints the chain of calls that led there; optimized builds give the panic's own line:

```
panic: index 3 out of bounds for a list of length 3
  at deep.vu:5 in third
  called from deep.vu:9 in second
  called from deep.vu:14 in first
  called from deep.vu:19 in main
```

Deep recursion is collapsed (`at f.vu:2 in f (74841 times in a row)`), and long chains show
their first 12 calls and the outermost one. A panic inside a `par` loop leads back to the line
of the loop. When several threads panic at once, exactly one report is printed.

With `--json` (on `check`, `run` or `build`), compile errors and panics are printed to standard
error as one JSON object per line, for tools and agents:

```
{"type": "error", "file": "x.vu", "line": 4, "message": "...", "source": "    xs.push(1)"}
{"type": "panic", "message": "...", "file": "x.vu", "line": 5,
 "backtrace": [{"function": "third", "file": "x.vu", "line": 5}, ...]}
{"type": "error", "message": "..."}      # main returned an error
```

A collapsed frame has `"times": N`; frames left out of a long backtrace are counted in
`"more_calls"`. Setting `VU_PANIC=json` when running any Vu binary does the same for panics.
Strings in JSON are valid UTF-8: bytes that aren't become U+FFFD.

The generated C carries `#line` directives, so gdb, sanitizer reports and core dumps point at
Vu source lines: `gdb -ex "break deep.vu:5" ./prog`.

Source files must be UTF-8 (a file that isn't gets an error naming the line). Windows line
endings (`\r\n`) are accepted, and so is a byte-order mark at the start. A file can have at
most 16,777,215 lines.

## Modules

Each file is a module. `import geo` reads `geo.vu` from the folder of the file that imports
it; `from geo import area, Point` imports names to use bare:

```
import geo
from util import describe

fn total(shapes: [geo.Shape]) -> Float:
  var t = 0.0
  for s in shapes: t += geo.area(s)
  return t

fn main():
  let shapes = [geo.unit(), geo.Circle(geo.Point(1.0, 2.0), 2.0)]
  match shapes[0]:
    Circle(c, r): print(describe(1))      # arms name variants bare (or geo.Circle(c, r))
    _: print("other")
```

- Everything a module defines can be used from outside: functions, types, variants and
  constants, written `geo.name`. Names never clash between modules.
- Imports go at the top level, anywhere in the file. Each module is read once; modules may
  import each other in a cycle. A program can have up to 127 modules, and a module's name
  starts with a letter. A local variable can't be named like a module the file imports.
- Constants are evaluated in the order they use each other, across modules.
- Errors, panics and backtraces name the file each line is in (`at geo.vu:12 in geo.area`).
- Names can't contain `__` except as leading underscores: Vu uses it for names from modules.
- When there is no `geo.vu` next to the importing file, `import geo` looks in the standard
  library: the folder named by the environment variable `VU_STD`, or else `std/` next to the
  compiler (one level up from `compiler/vuc`).

## The standard library

Modules in `std/`, written in Vu, imported like any other module.

**`time`**: dates in UTC from `os.time()` seconds.

```
import time
print(time.iso(os.time()))                # 2026-10-26T21:30:05.123Z
print(time.http_date(os.time()))          # Mon, 26 Oct 2026 21:30:05 GMT
let d = time.utc(t)                       # d.year, d.month, d.day, d.hour, d.minute, d.second, d.ms, d.weekday
let t = time.parse_iso("2026-10-26T21:30:05+02:00")?    # RFC 3339 -> seconds; can fail
```

**`log`**: lines on standard error with the time and a level; `log.json` writes one JSON
object per line for machines.

```
import log
log.info(os, "listening on {port}")      # 2026-10-26T21:30:05.123Z info listening on 8080
log.warn(os, "slow")                      # also log.error
log.json(os, "info", "request", [log.Field("path", req.path), log.Field("ms", "{ms}")])
```

**`http`**: HTTP/1.1 servers and clients, over TCP or TLS. The simplest server gives a handler to
`http.serve`:

```
import http

fn route(req: http.Request) -> http.Response:
  if req.method == "GET" and req.path == "/": return http.text(200, "hi")
  return http.text(404, "not found")

fn main(net: Net, os: Os) throws:
  http.serve(net, os, 8080, route, 10.0)?   # returns after SIGTERM / SIGINT
```

`http.serve(net, os, port, handler, grace)` runs one task per connection, on every core, and calls
`handler` (any `fn(http.Request) -> http.Response`, a closure too) for each request. On SIGTERM or
SIGINT it stops accepting, lets the requests in progress finish (each connection closes after its
current request, idle ones within a second), and returns when every connection is done or `grace`
seconds have passed. An idle keep-alive connection is closed after 60 s.

A server can also keep its own accept loop and task per connection, and ask `http.next` for each
request:

```
import http

type Hello:
  msg: Str

fn handle(net: Net, own c: Conn):
  var r = http.reader()
  while true:
    let req = http.next(net, c, &r, 60.0) else return   # wait up to 60 s for each piece
    var resp = http.text(404, "not found")
    if req.method == "GET" and req.path == "/":
      resp = http.json(200, to_json(Hello("hi")))
    http.reply(net, c, req, resp) else return
    if not http.keep_alive(req): return

fn main(net: Net) throws:
  let l = net.listen(8080)?
  while true:
    let c = net.accept(l) else continue
    spawn handle(net, c)
```

- `http.next` fails with `http.Closed` (the client left or went quiet) or `http.Bad(status, why)`
  (a malformed or too large request, already answered with that status, after which the
  connection should be closed). Requests are read strictly: header sections up to 64 KB and
  100 lines, bodies up to 10 MB by `Content-Length` or chunked (not both, and only one of
  each), `Expect: 100-continue` answered, an HTTP/1.1 request must have exactly one `Host`.
- A `Request` has `method`, `path`, `query` (after `?`), `version`, `headers` (names in
  lowercase) and `body`. `http.header(req, "Content-Type")` and `http.query(req, "q")` return
  a `Str?`; query values are percent-decoded.
- `http.reply(net, c, req, resp)` adds `Content-Length` and `Connection` as needed and leaves
  the body out for `HEAD`. A header name or value containing a line break is an error, so
  request data can't inject headers. `http.text`, `http.json` and `http.response(status,
  content_type, body)` make responses; `http.Response(status, headers, body)` is the full form.
- Pipelined requests are answered in order; the server doesn't rescan what it has already
  read, so a request sent a byte at a time costs time in proportion to its size.
- The client: `http.get(net, url)`, `http.post(net, url, content_type, body)`, and
  `http.send(net, http.ClientRequest(method, url, headers, body, timeout, ca))` for the rest
  (`ca`: PEM certificates to trust for https, `""` for the system's). It sends one request per
  connection and reads bodies by length, chunked, or until the connection closes (up to 64 MB).
  It returns redirects instead of following them.

## Not in v0

Methods, and Unicode-aware strings.
