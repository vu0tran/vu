# Vu 0.1

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
| `[T]` | growable list: `xs.len`, `xs.push(v)`, `xs.pop()` (removes and returns the last element; stops the program if empty), `xs.truncate(n)` (keeps the first n), `xs.copy_within(to, from, n)` (as memmove; plain values only), `xs[i]` (bounds-checked), `xs[a..b]` (a slice, below), `xs.reserve(n)` |
| `T?` | optional: either a `T` or `nil` (`Int?`, `Str?`, `[T]?`, a struct or enum...; not a capability or another optional). Recursive types must use it (or a list or map). Read it with `if x = opt:` or `opt else default` (see Errors). |
| `{K: V}` | map from Int, Byte, Bool or Str keys to any value (see Maps) |
| `type Name:` | a struct, fields listed below it (`x, y: Float` declares two fields) |
| `type Name:` with variants | an enum (see Enums) |
| `Fs` | the capability to read and write files (see Capabilities) |

A list slice `xs[a..b]` (bounds-checked) reads part of a list without copying it: `let v = xs[1..4]`
is a read-only view (the list can't change while it lives, as with `let` of a field), and
`for x in xs[2..n]` loops over the range. `var v = xs[1..4]` makes a copy that's yours to change.

Structs are built with positional or named arguments: `Body(1, 2)` or `Body(x: 1, y: 2)`.
`s.reserve(n)` and `xs.reserve(n)` make room for `n` more bytes or elements up front, so a
string or list built in a loop of known length grows without reallocating (a negative `n`
stops the program).
Bytes in bulk, each checked once: `s.read_le(at, n)` and `s.read_be(at, n)` read n bytes (1 to 8) of a
`Str` or `[Byte]` as an Int, least or most significant first (8 bytes give all 64 bits, so the Int
may be negative), and `bs.take_str()` turns a `[Byte]` list into a `Str` without copying it,
leaving the list empty.
Integer literals become a Float or Byte where one is expected. Other conversions are explicit:
`float(i)`, `int(f)`, `int(b)`, `byte(i)` (stops the program if i isn't 0..255).

String literals are `Str` values and can interpolate: `let msg = "{n} items"`. Escapes are
`\n \t \r \0 \\ \"`, and Byte literals take the same ones (`'\r'`). An interpolation can hold
any expression, including other strings, as in Python 3.12: `"{m["k"]} {", ".join(xs)}"`. Every
Vu string interpolates, so a literal brace is always doubled, inside nested strings too (`{{`).
A string that is nothing but one interpolation of a string literal (`"{"x"}"`) is an error: it's
almost always a brace meant literally (`s.startswith("{") and s.endswith("}")` is one string), and
the message says to double it. With other text around it (`"a{"\0"}b"`) it's fine.
Strings are
immutable byte strings; the text functions in Built-ins read them as UTF-8. `bytes(s)` copies one
into a `[Byte]` list, and `str(bs)` copies back.

Text over several lines goes in a `"""` string. Its text starts on the line after the opening `"""`
and ends before the closing one, which stands on a line of its own; the closing `"""`'s indentation
is removed from every line (a line indented less is an error), and so is the last line break. Quotes
need no escaping; escapes, interpolation and `{{ }}` work as in any string (an interpolation closes on
the line it opens).

```
let page = """
  <h1 class="title">{title}</h1>
  <p>{n} items</p>
  """                                  # "<h1 class=\"title\">...</h1>\n<p>... items</p>"
```

Constants are numbers, `true`/`false`, or text: `const MAX = 64`, `const SCALE = 2.5 * MAX`,
`const GREETING = "hello"`, `const PAGE = """...""" + FOOTER`. A text constant can't interpolate, and
using it is the same as writing its text, so it can be passed to a `const` parameter (a SQL query, a
template). Constants are evaluated in the order they use each other, across modules (`geo.ORIGIN`).

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
- **Const parameters.** A `Str` parameter declared `const` takes only text written into the
  program: a string literal (without `{...}`), literals joined with `+`, or the caller's own
  `const` parameter. Text built at run time doesn't compile there, so an API can make injection
  impossible: `pg.query(net, &db, "select * from users where id = $1", [id])` takes values only as
  parameters. A function with a `const` parameter can't be used as a value.

  ```
  fn run_sql(var db: Db, const sql: Str, args: [Str]) ...
  run_sql(&db, "delete from t where id = $1", [id])       # fine
  run_sql(&db, "delete from t where id = " + id, [])       # error: built at run time
  ```

- **Locals may shadow** a function, a constant or a built-in: `let text = ...` and
  `let max = 10` are fine. Calling the shadowed function in that scope is an error that says
  so. Type and variant names stay reserved.
- **Strings are copied unless moving is free.** Taking a `Str` from a field, a list element, a
  parameter, a loop binding, or a frozen variable copies it (`let name = p.name`). A `Str` variable
  given away (`xs.push(s)`, `m[k] = s`, a struct field, `let t = s`) is moved only when that's its
  last use in the block that declared it; anywhere else it's copied, so using it again is always
  fine. Other owned values (lists, structs, enums) are never copied implicitly.
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
- **Generic interfaces** take type parameters, used in their functions' other parameters and
  results:

  ```
  interface Store[T]:
    fn get(s: Self, i: Int) -> T
    fn put(var s: Self, x: T)

  impl Store[Int] for Ints: ...           # each instance is implemented like an interface
  fn total[S: Store[Int]](s: S) -> Int: ...
  fn first[S: Store[T], T](s: S) -> T:    # T comes from the instance S implements
    return get(s, 0)
  let all: [Store[Str]] = [Words(["a"])]  # values of an instance
  ```

  A type implements one instance of a generic interface (`Store[Int]` or `Store[Str]`, not both),
  so `get(x, 0)` always knows which.

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
  `fn(T)` for one that returns nothing. `(fn(Int) -> Int)?` is an optional one. `fn(own Conn)`
  takes ownership of that argument: a call moves it in, as for an `own` parameter, and a closure of
  that type names it `own` (`fn(own c) => serve(c)`), or gets that from where it goes. A named
  function with `own` parameters is a value of such a type.
- **Closures**: `fn(x: Int) -> Int => x * k` is an expression. Parameter and return types can be
  left out when the context gives them (an argument, a typed `let`, a field). `fn name(...): ...`
  inside a function is a nested function with a block body, bound to `name`; it can't call
  itself (make it top-level to recurse). Closure parameters are read-only, except `own` ones
  (there is no `var`).
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
  with `var` parameters, or one that fails with typed errors (`throws E`), can't be a value; wrap
  it in a closure. A generic function becomes a value given a type:
  `let f: fn(Int) -> Int = identity`.
- A closure that captures a capability (`os`, `net`) carries it: whoever holds the closure can
  use that capability through it.
- Function values can't be compared, printed or converted to JSON. A call through one is an
  indirect C call; a closure's captured variables live in an env (on the stack for a borrowing
  closure, on the heap for an own one).

## Methods

`x.f(args)` is another way to write `f(x, args)`: any function whose first parameter takes `x`
can be called on it.

```
fn dist(a: Point, b: Point) -> Float: ...
fn grow(var s: Stack, v: Int): ...

a.dist(b)                 # dist(a, b)
st.grow(3)                # grow(&st, 3): a var first parameter changes the receiver, as xs.push does
"hi".shout().len          # chains; works on Int, Str, lists, enums, interface values too
xs.largest(fn(a, b) => a > b)   # generic functions infer from the receiver
```

- The function is looked up where the call is written (its own functions and `from` imports), then
  in the module that defines the receiver's type, so `p.norm()` works for a `geo.Point` without
  importing `norm` by name. Locals never hide a method.
- Built-in methods come first (`s.split()`, `xs.push(v)`, `m.get(k, d)`), and a struct field holding
  a function is called by `h.handler(x)` as before. Capabilities, channels, optionals and function
  values have only their built-in methods.
- The receiver is passed exactly as the first argument would be: borrowed, `&x` for a `var`
  parameter (so it must be a variable, field or list element, and every rule about `&` applies:
  not while it's borrowed, not twice in one call, not inside an index), or moved for `own`.
  A failing method is handled like any failing call (`x.f()?`, `else`, `match`).

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
- In `match f(x):`, what `ok(v)` and `err(e)` bind is the arm's own: it can be moved on
  (`ok(c): spawn serve(c)`, `ok(v): result = v`).
- If `main` is marked `throws` and an error reaches it, the program prints `error: <message>`
  to standard error and exits with code 1. (`panic` exits with 101.)
- File operations and reading numbers from text can fail the same way (see Built-ins).

`else` also reads an optional (`T?`): the value inside, or the fallback when it's `nil`, with the
same ways to leave:

```
let name = user.nickname else "anon"          # a Str? field: the text is copied, the field stays
let port = find_port(cfg) else 8080           # a call returning Int?
let row = first_row(rows) else return         # or else break / continue / fail "..." / panic(...)
print((lookup(k) else "?") + "!")             # else binds loosest: parentheses inside a larger expression
```

- An optional held in a field or list element whose value isn't plain data or a `Str` (a list, a
  struct) can't be taken out by `else` (that would move it out of its owner): unwrap it in place
  with `if x = ...:`. A whole local variable is moved out, as `let` would.

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
counts[w] = counts.get(w, 0) + 1     # .get(key, default) for plain-data and Str values
if "the" in counts: ...
let n = counts["the"]                # a missing key stops the program; check with 'in' first
counts.remove("the")                 # returns true if the key was there
print("{counts.len}")                # how many keys
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
code 101. It never reads or writes memory it shouldn't. In hot loops the checks are cheap: indexes
whose range the loop shows (`xs[i + k]` with `i` the counter, `xs[0]`, `t[x & 255]`, the two
ends of `while lo < hi`) are checked once before it starts, and so are sums that can only grow
so much (`s += int(b)`); a loop that only computes numbers runs first with its checks recorded
instead of stopping it (so the C compiler can vectorize it), then again checked if any failed. Either way the program stops at the
same check, with the same message, as when each operation is checked in order. Recursion too deep for the stack
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
they are handled like calls to a `throws` function: with `?`, `else` or `match`. So can
`fs.list(dir)` (the names in a folder, sorted, each folder's ending in `/`), `fs.mkdir(path)` (with
any missing parents), `fs.remove(path)` (a file or an empty folder) and `fs.rename(from, to)`;
`fs.exists(path)` returns a Bool.

An `Fs` can't be created anywhere else, so a function that isn't handed one has no way to
read or write files, and its signature shows that. To hand out less than all of it,
`dir.open(fs, path)` (the `dir` module) opens one folder as a `Dir`, which reaches only what's inside
it: code given a `Dir` and no `Fs` can't touch any other file. `main` may only take capabilities as
parameters (`Fs`, `Os`, `Net` and `Ffi`, see Calling C). Printing to standard
output needs no capability. `fs.temp_dir()` creates a new private directory under `$TMPDIR`
(or `/tmp`) and returns its path; it can fail.

The operating-system capability `Os` (`fn main(os: Os)`, alone or next to `fs: Fs`)
covers the rest of the outside world:

- `os.run(["gcc", "-O2", "x.c"])` runs a program (found on `PATH`) with those arguments,
  waits, and returns its exit code (128 + the signal number if a signal killed it). Output
  goes to the program's own standard output and error. It fails if the list is empty, an
  argument contains a zero byte, or the program can't be started.
- `os.output(["git", "rev-parse", "HEAD"])` runs a program the same way and returns what it wrote
  to standard output and standard error together, whatever its exit code.
- `os.read_stdin()` reads all of standard input, to its end (it can fail, so `?` or `else`).
  Reading it a line at a time with the `stdio` module needs no capability: standard input and
  output are the program's own streams.
- `os.read_stdin(n)` reads up to n bytes of standard input as they arrive (`""` at its end); it
  can fail. (`print` and `write` need no capability; reading input does.)
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

- `net.listen(port) -> Listener` (IPv6 and IPv4 where the system has IPv6, else IPv4), `net.accept(l) -> Conn`, `net.connect(host, port) -> Conn`,
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
- `net.resolve(host) -> [Str]` (it can fail; takes `timeout:`) gives the addresses a name stands
  for, as text (`"127.0.0.1"`, `"::1"`), in the order `connect` tries them. An address resolves to
  itself, and the C library's older spellings of one are read as it reads them (`"0x7f.1"` is
  `127.0.0.1`), so check the addresses it returns, not the text. A program that must refuse some addresses (a fetcher that stays off the local network)
  resolves first, checks, then connects to the address it checked.
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
  `ch.send(v)` on a closed channel stops the program; `ch.send(v, timeout: s)` instead fails (the
  channel stayed full that long, or is closed: `v` is then freed), so it's handled like `recv`.
  `ch.close()` wakes every task waiting on it.
- Passing a channel to an `own` parameter shares it (both sides keep using it); `ch.share()`
  makes another handle to store in a struct or list. The channel is freed, with any values still
  in it, when its last handle goes.
- `os.sleep(seconds)` waits without blocking other tasks.
- **`select`** waits for whichever of several things happens first, then runs that arm:

  ```
  select:
    let job = jobs.recv():          # a value from jobs
      run(job)
    results.send(r):                # room in results: r goes in (a variable moves only if this arm runs)
      sent += 1
    net.readable(conn):             # data (or the other side's close) on a connection; a nil Conn? sits out
      let d = net.recv(conn)?
    stop.closed():                  # stop is closed and empty
      return
    timeout 5.0:                    # nothing else within 5 seconds
      print("idle")
  ```

  An arm followed by `if condition` takes part only when that's true (`jobs.closed() if not
  jobs_done:`), which is how a loop stops waiting on a channel it has seen closed; a closed channel's
  arm would otherwise be ready on every pass. When several arms are ready, one is picked at random,
  so a busy channel can't keep the others waiting. A select waits on one connection at most, and its
  channels must be variables or fields. A select with no timeout waiting on channels nothing will
  feed isn't reported as a deadlock: it waits.
- `ch.closed()` says whether the channel was closed: closing one channel is how one task tells
  many to stop (each checks `closed()` between the things it waits for).
- If every task is waiting on a channel and nothing (a connection, a timer) can wake any of
  them, the program stops with "deadlock".
- Each task has its own stack (8 MB of address space, used as it grows), so a stack overflow in a
  task is reported like one in `main`. A thread with nothing to do takes new tasks (ones that
  haven't started) from a busy thread's queue, so a task that never waits doesn't hold up the new
  tasks queued behind it. A task that has started stays on its thread, and main always stays on
  the first thread.
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
  locks. It's freed when its last handle goes. A channel inside is still a channel: tasks send and
  receive through it (a pool of connections in a `Chan[pg.Db]` inside a `Shared` value works).
- Passing a `Shared` value to an `own` parameter (or `spawn`) gives the callee another handle, as
  for channels; `s.share()` makes one to store. `let t = s` moves the handle.
- A `Shared` value can't hold a connection, a listener or a C handle (using one from several tasks
  at once isn't safe), nor a closure that borrows local variables. Channels inside are fine,
  whatever they carry: a task takes a value out of a channel to own, so a `Chan[Conn]` is too.
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
  `Int`, `Float`, `Bool`, `Byte`, `Str`, `[Byte]`, `[Int]`, `[Float]` or an extern type; it returns
  one of the scalars, `Str`, an extern type or nothing.
- A `[Byte]`, `[Int]` or `[Float]` reaches C as a pointer to its elements and their count, without a
  copy. A `var` one C may change in place (not its length): to get bytes back, make a buffer of the
  size C needs and have C return how many it wrote.

  ```
  extern "z_glue.c":
    link "z"
    fn crc(ffi: Ffi, data: [Byte]) -> Int        # C: int64_t crc(const uint8_t *p, int64_t n)
    fn scale(ffi: Ffi, var xs: [Float], k: Float)  # C: void scale(double *p, int64_t n, double k)
  ```
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
| `[Byte]` / `[Int]` / `[Float]` | `const uint8_t *p, int64_t n` / `const int64_t *` / `const double *` (`var`: without `const`); `p` may be NULL when `n` is 0 | (not a result) |
| an extern type | `void *` | `void *` (never NULL) |
| `throws` | after the others: `T *out` (if it returns a value), then `vu_str *err` | `bool`: true on success; on failure set `*err = vu_errf("fmt", ...)` |

`vu_cstr(s)` makes a NUL-terminated copy (free it with `free`), or returns NULL when the string
contains a zero byte. The compiler declares each function's expected C signature before
including the file, so a definition that doesn't match is a compile error. C names can't be C
keywords or start with `vu_`, `fn_` or `drop_`. (`par` is a keyword only right before `for`;
elsewhere it's an ordinary name.)

C code is outside Vu's checks: the glue must not keep a borrowed `vu_str` or list pointer after the
call, write past a list's count,
free a borrowed handle, or return a handle that is still owned elsewhere.

## Libraries for C and Python

`export fn` makes a function a plain C function of the same name too, and `vu build --lib` builds
the file's exported functions into a shared library (`libNAME.so`, or `.dylib` on macOS) with a
header declaring them (`NAME.h`):

```
export fn count_words(text: Str) -> Int:
  return text.split().len

export fn mean(xs: [Float]) -> Float throws:
  if xs.len == 0: fail "mean of no numbers"
  var t = 0.0
  for x in xs: t += x
  return t / float(xs.len)
```

```
vu build --lib words.vu           # libwords.so and words.h
```

```c
int64_t count_words(const char *text, int64_t text_len);
double mean(const double *xs, int64_t xs_len, char **vu_err);
```

From Python, with ctypes:

```python
import ctypes
lib = ctypes.CDLL("./libwords.so")
lib.count_words.restype = ctypes.c_int64
lib.count_words.argtypes = [ctypes.c_char_p, ctypes.c_int64]
print(lib.count_words(b"the quick brown fox", -1))   # 4
```

- Parameters can be `Int`, `Float`, `Bool`, `Byte` (as for extern functions), `Str` (a pointer
  and a length; a negative length reads up to the first zero byte) and `[Byte]`, `[Int]` or
  `[Float]` (a pointer and a count). Both are read in place, during the call only.
- Results are those scalars, nothing, or a `Str` or list: a copy made with `malloc` (a Str's with
  a zero byte after it), with its length in `*vu_out_len` when that isn't NULL. The caller frees
  it with `free`.
- A function that `throws` takes `char **vu_err` last: a message (free it) when it fails, with a
  result of 0 or NULL, and NULL when it succeeds. Typed errors (`throws E`) can't be exported.
- An exported function gets no capabilities, so a library can't reach files, the network or
  programs, whatever it's called with. It can use `par` loops, not tasks or channels (yet).
- It's called on the caller's threads, from as many at once as the caller likes.
- A panic prints its report and ends the process (exit 101), as it does a program.
- Only the main file's functions can be exported, without type parameters, and with names that
  aren't C keywords or already the C library's (the C compiler names a clash). Exported functions
  are ordinary Vu functions too, and a library may have a `main` (it isn't run).

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
`and or not` (`and` and `or` stop as soon as the answer is known, so `i < xs.len and xs[i] > 0` is
safe), and `+` to join strings. Arithmetic stops the program on overflow; for hashes, checksums and
random number generators, `+% -% *%` wrap around at 64 bits instead (and `+%= -%= *%=`), and `>>>`
shifts right filling with zeros (`>>` keeps the sign). A shift by less than 0 or more than 63 stops
the program. A Byte literal holds one character, any character: `'{'` is a brace, not an interpolation.
Int literals can be hex (`0xFF`). `[v] * n` makes a list of n copies of plain values.
Float math is strict IEEE: never fused, so results are identical on every machine. To fuse,
ask for it: `fma(a, b, c)` is `a * b + c` rounded once (one instruction on most CPUs, and the same
result on every machine).
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
`swap(&a, &b)` exchanges two values of the same type. Also: `panic("...")`, `sqrt`, `fma`, `abs`,
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
xs.sort(by: fn(a, b) => a.n > b.n)     # any element type: by says whether a goes first (stable)
xs.sort(key: fn(p) => p.age)            # by what the function gives for each (Int, Float, Byte, Bool or Str)
xs.swap(i, j)                           # exchange two elements in place
let lo = min(xs)                        # min/max of a list, or of two or more numbers: max(a, b, c)
if 3 in xs: ...                         # whether an element == 3 (lists of Int, Float, Byte, Bool, Str)
```

Text: strings are bytes, and these read them as UTF-8 characters, with Python's names and results:

```
"straße".upper()          # "STRASSE": Python's full Unicode case mapping (also s.lower())
"aé中😀".char_count()     # 4 (s.len is 10: bytes)
for c in s.chars(): ...    # each character as a Str
s.normalize("NFC")          # Unicode normalization: "NFC", "NFD", "NFKC" or "NFKD", as Python's
s.is_alpha()                # and is_digit, is_space, is_alnum, is_upper, is_lower, is_decimal: Python's isalpha()...
ord("é")                   # 233; chr(233) is "é"
s.find("é")                # the byte index of the first "é" (for s[a..b]), or -1
s.find("é", 10)            # the first at or after byte 10 (a negative start counts from the end)
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

Hashing and encoding, on bytes (a `Str`); no capability needed:

```
sha256(data)                       # the 32-byte digest; sha256(data).hex() for hex text
hmac_sha256(key, data)             # HMAC-SHA256
pbkdf2_sha256(password, salt, n)   # PBKDF2-HMAC-SHA256 with n iterations, 32 bytes
random_bytes(16)                   # from the kernel's generator (for keys and nonces)
b64encode(data)                    # standard base64 with padding
let raw = b64decode(text)?         # fails on text that isn't base64 (like Python's validate=True)
let k = from_hex("00ff")?          # fails on anything but hex digits in pairs; s.hex() makes them
```

`tests/run_crypto.sh` checks each against Python's `hashlib`, `hmac` and `base64`.

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
vu check --checks file.vu   # also: the index and overflow checks each loop still makes on every pass
vu check --index file.vu    # also: what the language server knows (items, fields, variables' types), as JSON lines
vu check --caps file.vu     # what the program can reach: the capabilities main asks for (fs, os, net, ffi)
vu run file.vu [args]       # quick -O0 build, then run with args
vu run --release file.vu    # optimized build, then run (options go before the file;
                            #   everything after it goes to the program)
#!/usr/bin/env -S vu run     # first line of a script: run it as ./script.vu
vu build file.vu [-o out]   # optimized native binary
vu build --lib file.vu      # a shared library of its export fn functions, and a C header
  --profile  report where the CPU time went, at exit (also for run)
  --debug    -O0 build for fast iteration
  --malloc   use malloc/free instead of the node free list
  --san      build with AddressSanitizer + UBSan (implies --malloc)
  --san-pool same sanitizers with Vu's own node allocator (freed nodes are poisoned)
  --tsan     build with ThreadSanitizer (use CC=clang and run with
             OMP_TOOL_LIBRARIES=.../libarcher.so; see CHANGELOG.md)
  --emit-c F write the generated C to F
  --time     report front-end and C compiler time
  --static   link every library in (no shared libraries needed where it runs; with glibc,
             host name lookups still need glibc's libraries there)
  --wasm     a WebAssembly (WASI) module, out.wasm, with zig's C compiler (see WebAssembly)
vu fmt file.vu... [--check] # rewrite spacing the one way (--check: list files it would change)
vu test file.vu...          # run each fn test_... in its own process; report which pass
vu get [file.vu]            # fetch the packages in vu.pkg, write vu.lock (see Packages)
vu search WORDS / vu add NAME  # the package registry (see Packages); vu publish NAME VERSION
vu version                  # the release: vu 0.2.0
vu new web NAME             # a folder NAME with a web app: main.vu, public/, Dockerfile, fly.toml, railway.json
vu new api NAME             # a JSON API on PostgreSQL with accounts and sessions: main.vu, Dockerfile, railway.json
vu lsp                      # a language server for editors (diagnostics, formatting, hover, definition, completion)
```

`vu run` keeps each program's binary (in `$XDG_CACHE_HOME/vu/run`, or `~/.cache/vu/run`), so running
it again, unchanged and with the same options, starts it without the C compiler: a script that
takes 234 ms the first time takes 9 ms after (measured on Linux x86-64). A change to the program or
a module it imports builds it again. It keeps the 64 programs used last and forgets one whose file
is gone; `VU_RUN_CACHE=off` builds every time.

Quick builds (`vu run`, `vu build --debug`) use clang when it's installed and `CC` isn't set: it
compiles Vu's C about 3 times as fast as gcc. A build of a big program (more than about 6,000 lines
of C in its functions) is split: its functions are compiled as several C files, as many at once as
there are cores, and each one's object file is kept (in `~/.cache/vu/parts`), so a rebuild after an
edit compiles only the part that changed. On a 20,000-line program, an edit and `vu run` takes
0.64 s (Rust's `cargo run`: 0.70 s), and an optimized rebuild 2.4 s (`cargo build --release`:
14.0 s; see `bench/rebuild`). An optimized split build doesn't inline a function into a caller in
another part: functions are grouped by source file, so calls within a module still can be.
`VU_SPLIT=off` builds one C file; `VU_SPLIT=always` splits any program.

- **`vu fmt`**: blocks indented 2 spaces per level, one space around binary operators and after
  commas and colons, none inside brackets or before a call's `(`, and runs of blank lines down to
  one. Comments and the spacing before a comment at the end of a line are kept, and strings are
  never touched. Formatting doesn't change what a program does: `tests/run_fmt.sh` checks that every
  `.vu` file here compiles to the same C before and after, and that formatting twice changes
  nothing more.
- **`vu test`**: a test is a top-level function named `test_...` that takes nothing but
  capabilities (`fn test_save(fs: Fs) throws:`). Each runs in its own process, so a panic or a
  failed `assert` fails that test only. `assert(cond)` stops the program (exit 101) naming the
  assertion's text; `assert(cond, message)` gives the message instead.
- **`vu build --profile`** (or `vu run --profile`): an optimized build that, at exit, prints where the
  CPU time went: by function (self, and total with what it calls) and by line, from a sample of each
  thread's call stack at every tick of the kernel's CPU timer (often 250 a second, across all
  threads). `vu-profile.txt` has all of it, and `vu-profile.folded` one stack per sample for
  `flamegraph.pl` or speedscope (`VU_PROF_OUT=prefix` moves them). The profiled program keeps every
  call's frame and the line it's at, which made the benchmarks 1.0x (`par` loops) to 2.5x
  (spectralnorm) slower, and the optimizer moves work between neighbouring lines, so shares by line
  are approximate; by function they're the program's.
- **`vu lsp`** speaks the Language Server Protocol on standard input and output: the compiler's
  error for each open file (re-checked on every change), and formatting with `vu fmt`.
- **Other machines**: Vu runs on Linux on x86-64 and ARM64 (`tests/run_arm64.sh` runs the test
  programs under qemu); `CC=aarch64-linux-gnu-gcc VU_MARCH= vu build ...` cross-compiles. The runtime
  also has a macOS port (kqueue in place of epoll) that compiles and links for macOS on x86-64 and
  ARM64 but hasn't been run on a Mac; `par` loops there need clang with libomp.
- **WebAssembly**: `tools/wasm.sh` builds the compiler itself for WASI (with zig): `vuc.wasm` runs
  `check` and `fmt` in a browser or any WASI runtime, with the standard library given as `/std`
  (`VU_STD=/std`). It's what the playground on vulang.org runs. `tests/run_wasm.sh` checks that it
  gives the same errors and formatting as the native compiler on every targeted test. Building
  programs there isn't possible (no C compiler), and a program nested more than a few hundred
  levels deep runs out of a browser's stack.
  `vu build --wasm app.vu` makes `app.wasm` for WASI (run it with `wasmtime app.wasm ARGS`, with
  `--dir .` for files). It needs zig's C compiler (`pip install ziglang`, or `zig` on the PATH;
  `VU_WASM_CC` names another). WASI has one thread and no sockets or processes, so a program that
  uses tasks, channels, `Net`, `os.signals`, TLS or C files is refused (exit 2, with the reason);
  `os.run` fails with "not available in WebAssembly", and too-deep recursion stops with the
  runtime's trap instead of the "stack overflow" panic. `tests/run_wasm.sh` builds every example
  and targeted output and panic test this way and checks they print what the native builds do.

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

### Packages

Code from other repositories comes in as packages, listed in `vu.pkg` next to the main file (or in
a folder above it):

```
need github.com/vu0tran/pg v0.2.0 net            # source, version (a git tag), what it may receive
need git+file:///srv/git/util.git v1.0.0          # any git URL
need ../shared                                    # a local folder (no version)
need github.com/someone/log v1.1.0 as slog        # imported as slog instead of log
```

- `vu get` fetches every package (with git) into the cache (`$VU_PKG_DIR`, else `~/.cache/vu/pkg`),
  then the packages those need (from each package's own `vu.pkg`), picking the highest version
  anyone asks for, and writes `vu.lock`: each package's version, commit, and the SHA-256 of its
  files. Every `build`, `run` and `check` hashes the packages again and stops if one changed since
  `vu.lock` was written (in the cache, or a tag that moved); `vu get` accepts the change.
- `import pg` finds the package's `pg.vu` (the last part of its source; `as` changes the import
  name, not the file). A file next to the importing one comes first, then the packages, then `std`.
  Inside a package, imports see its own files and the packages its `vu.pkg` lists.
- **A package receives only the capabilities its line grants** (`fs`, `net`, `os`, `ffi`): one of
  its functions taking a capability it wasn't granted (directly, or inside a struct, list or
  optional), or an `extern` block without `ffi`, is a compile error naming the package. A package
  can pass on only what it was granted itself. So a dependency that starts reading files or calling
  C in a new version stops the build until someone edits `vu.pkg` to allow it.
- Two different modules can't have the same name (a package and a local file, say); import a
  package under another name with `as`.
- **The registry** names packages: `need clock v1.2.0 os` (a name instead of a source) is the
  package the registry lists as `clock`. Its index (`https://vulang.org/registry/index.txt`, or
  `VU_REGISTRY`) records each version's commit and the SHA-256 of its files when it was published,
  and `vu get` refuses a fetch that differs from them (a tag moved, or the host changed the files),
  as Go's checksum database does. `vu search WORDS` lists packages; `vu add NAME [VERSION]` adds the
  line to `vu.pkg`, granting the capabilities the registry says the package takes (it prints them),
  then fetches it. `vu publish NAME VERSION [DIR] [fs net os ffi]`, in a package's repository, prints
  the index lines for a tag; they go in by pull request to the index (github.com/vu0tran/vulang-web).

## The standard library

Modules in `std/`, written in Vu, imported like any other module.

**`time`**: dates from `os.time()` seconds, in UTC and in time zones.

```
import time
print(time.iso(os.time()))                # 2026-10-26T21:30:05.123Z
print(time.http_date(os.time()))          # Mon, 26 Oct 2026 21:30:05 GMT
let d = time.utc(t)                       # d.year, d.month, d.day, d.hour, d.minute, d.second, d.ms, d.weekday
let t = time.parse_iso("2026-10-26T21:30:05+02:00")?    # RFC 3339 -> seconds; can fail
let ny = time.zone(fs, "America/New_York")?             # from /usr/share/zoneinfo; can fail
let l = time.local(ny, t)                 # l.date (a Date), l.offset (-14400), l.abbrev ("EDT"), l.dst
print(time.iso_in(ny, t))                 # 2026-10-26T15:30:05.000-04:00
let u = time.from_local(ny, time.Date(2026, 11, 1, 1, 30, 0, 0, 0))   # wall clock -> seconds
```

- Zones come from the system's tz database files (TZif): `time.zone(fs, name)`, `time.local_zone(fs)`
  for `/etc/localtime`, or `time.parse_tzif(name, bytes)` for a file you have (no capability).
  `time.fixed(seconds, "ABC")` and `time.utc_zone()` need no file. After a file's last change
  (usually 2037) its POSIX rule (`EST5EDT,M3.2.0,M11.1.0`) gives the changes.
- `from_local` reads a wall-clock time that happens twice (clocks going back) as the first one, and
  one that never happens (clocks going forward) with the offset from before the change: Python's
  `fold=0`. Fields out of range roll over (month 13 is January of the next year).
- `tests/run_time_zones.py` checks every zone against Python's `zoneinfo` around every change from
  1800 to 2200, and broken files (refused with "is not a valid time zone file").

**`heap`**: a priority queue kept in a list, ordered by a function that says whether a comes first.

```
import heap
let first = fn(a: Job, b: Job) -> Bool => a.due < b.due
heap.push(&q, Job(3, "c"), first)       # q[0] is always the first
let next = heap.pop(&q, first)          # removes and returns it (stops the program if q is empty)
heap.heapify(&xs, first)                # a list made into a heap in place
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
- `client.fetch_all(net, requests)` sends a list of requests and gives an `http.Fetched` for each
  (`ok`, `resp`, `error`), in order: those to an HTTP/2 server go out at once on one connection, as
  many streams as the server allows, and their answers come back interleaved.
- A `Client` keeps connections open between requests and speaks HTTP/2 to https servers that
  offer it (ALPN), else HTTP/1.1 with keep-alive:

  ```
  var client = http.client()
  let r = client.fetch(net, http.req("GET", "https://api.example.com/items"))?
  var post = http.req("POST", "https://api.example.com/items")
  post.body = to_json(item)
  post.headers.push(http.Header("Content-Type", "application/json"))
  let r2 = client.fetch(net, post)?        # on the same connection
  ```

  It keeps up to `client.max_idle` open connections (8; the least recently used is closed first);
  `client.http2 = false` turns HTTP/2 off, and `client.opened` and `client.reused` count. A kept
  connection the server has closed or is closing (GOAWAY) is noticed before use; a request that
  still fails because of it, or that an HTTP/2 server refused, goes once more on a new connection
  if it's safe to repeat (GET, HEAD, OPTIONS, TRACE, PUT, DELETE, or with an `Idempotency-Key`
  header). One request at a time per client (several tasks: one client each).
  `net.tls_connect(..., alpn: "h2,http/1.1")` and `net.protocol(conn)` are what it uses.

**`web`**: an app on top of `http`: routes, middleware, forms, cookies, static files and HTML
templates.

```
import http
import web

fn show(req: http.Request, c: web.Ctx) -> http.Response:
  let who = web.val(c, "user") else "nobody"
  return web.html(200, web.render("<h1>{{id}}</h1><p>for {{who}}</p>", [web.v("id", web.param(c, "id")), web.v("who", who)]))

fn auth(req: http.Request, c: web.Ctx, next: fn(http.Request, web.Ctx) -> http.Response) -> http.Response:
  if s = web.get_cookie(req, "sid"):
    if u = web.verify("a secret: 32 random bytes", s): return next(req, web.with(c, "user", u))  # signed
  return next(req, c)

fn main(net: Net, os: Os, fs: Fs) throws:
  var app = web.app()
  web.use(&app, web.logger(os))          # middleware runs in the order added, around what follows
  web.use(&app, web.same_origin)
  web.use(&app, auth)
  web.get(&app, "/items/:id", show)      # also post, put, patch, delete, and web.route(&app, METHOD, ...)
  web.get(&app, "/static/*file", web.files(fs, "public"))
  web.serve(net, os, app, 8080)?         # http.serve with the app; stops on SIGTERM / SIGINT
```

- A handler is a `fn(http.Request, web.Ctx) -> http.Response`. The first route that matches the
  method and path answers (HEAD runs a GET route); a path that matches only other methods' routes
  gets 405 with `Allow`, any other 404. `:name` matches one non-empty part of the path, `*name` the
  rest (last only); `web.param(c, name)` gives it percent-decoded. A bad pattern panics when it's
  added.
- Middleware is a `fn(http.Request, web.Ctx, next) -> http.Response`: it can answer itself, call
  `next`, or call it with `web.with(c, name, value)` for handlers to read with `web.val`.
  `web.logger(os)` logs each request; `web.same_origin` refuses requests that change things (not GET,
  HEAD or OPTIONS) that a browser marks as coming from another site (`Sec-Fetch-Site`, else `Origin`).
- **Templates escape.** `web.render(template, values)` replaces each `{name}` (written `{{name}}` in a
  Vu string) with a value: `web.v(name, text)` is escaped (`& < > " '`), `web.h(name, html)` is a
  `web.Html` inserted as it is (made by `render`, `web.join(list)`, or `web.trust(text)`, which says
  the text is HTML already). The template is a `const` parameter, so it's written in the program;
  values are never read as templates, and a `{name}` with no value panics. `web.html(status, h)`
  sends it with `nosniff`, `X-Frame-Options: DENY` and a referrer policy; there is no way to send a
  `Str` as HTML except through `trust`. (Escaping is for text and quoted attributes: a URL in an
  `href` still needs checking.)
- Forms: `web.form(req)` gives the fields of an `application/x-www-form-urlencoded` body as a map (the
  first of a name wins), `web.field(req, name)` one of them.
- File uploads: `web.parts(req)?` reads a `multipart/form-data` body (a form with
  `enctype="multipart/form-data"`) into `web.Part`s (`name`, `filename`, `content_type`, `data`), and
  fails on a malformed one (at most 1,000 parts). `web.file(parts, name)` is the first file of that
  name, `web.part_value(parts, name)` a plain field. The browser's `filename` is never safe as a path:
  `web.safe_filename(p.filename)` keeps its last part without control characters, quotes or leading
  dots.
- Cookies: `web.get_cookie(req, name)`; `web.set_cookie(&resp, web.cookie(name, value))`, whose
  defaults are `Path=/`, `HttpOnly`, `Secure` and `SameSite=Lax` (a `web.Cookie`'s fields change
  them: `max_age`, `same_site`...); `web.clear_cookie(&resp, name)`. Values are percent-encoded, so
  any text is safe in one. `web.sign(secret, value)` and `web.verify(secret, signed)` (HMAC-SHA256,
  compared in constant time) make a cookie the client can read but not change.
- `web.redirect(status, to)` goes only to a path on the same site: anything else (`//host`, a
  scheme, a backslash, a control character) goes to `/`.
- Static files: `web.files(fs, folder)` is a handler for a `*name` route. Names that would leave the
  folder (`..`, encoded or not), hidden files (a part starting with `.`), a NUL or a backslash get 404;
  a name ending in `/` gets its `index.html`. Each file has a `Content-Type` by its extension, `nosniff`,
  and an ETag, and `If-None-Match` gets 304. Symbolic links inside the folder are followed.
- WebSockets: `web.websocket(&app, path, handler)` (the same patterns as `get`). The handshake passes
  the middleware like any request (which can refuse it: 401...), then the handler gets the open
  socket to own, with the request and the context, and has the connection until it returns:

  ```
  fn chat(net: Net, own inbox: Chan[Str], own s: ws.Socket, req: http.Request, c: web.Ctx):
    var sock = s
    ws.send_text(net, &sock, "hello " + web.param(c, "room")) else return
    while true:
      var incoming = ws.buffered(sock)            # part of the next message read already
      if not incoming:
        select:
          let t = inbox.recv():                   # from other tasks: send it on
            ws.send_text(net, &sock, t) else return
          net.readable(sock.conn):
            incoming = true
      if incoming:
        let m = ws.recv(net, &sock) else return
        # ... handle m
  app.websocket("/rooms/:room", own fn(own s, req, c) => chat(net, inbox.share(), s, req, c))
  app.allow_origin("https://other.example")    # pages there may open these sockets too
  ```

  A browser page from another origin is refused (403), since any site's page could otherwise
  open a socket that carries the user's cookies; requests with no `Origin` (not from a browser)
  are let in. `web.serve_tls` serves an app over TLS (HTTP/2 for browsers that offer it;
  WebSockets use HTTP/1.1). `http.Site` is what makes this work: a handler, and a function that
  takes over the connection when the handler answers 101 (`http.serve_site`).
- `tests/run_web.sh` checks routes, forms, escaping and cookies against a Python model on random
  input, and an app against hostile requests (including 400 random paths that try to leave the
  static folder), under the sanitizers and ThreadSanitizer.

**`re`**: regular expressions with Python's syntax and results (`re.compile`, `re.search`,
`re.prefix` for Python's `re.match`, `re.fullmatch`, `re.findall`, `re.finditer`, `re.sub`,
`re.split`, `re.group`), run as RE2 does: time linear in the text whatever the pattern, so no
pattern can be made to take exponential time. A DFA built when the pattern is compiled finds where
each match ends, another run backwards finds where it starts, and only groups need more work; patterns
the DFAs can't express (loops whose body can match nothing), or would make too big, run on a Pike VM. Backreferences and lookaround aren't
supported (they can't run in linear time); `\d \w \s` are ASCII. Offsets are byte offsets.
`tests/run_re.sh` compares it with Python's `re` on thousands of random patterns.

```
import re
let r = re.compile("(\\w+)@(\\w+)\\.com")?
if m = re.search(r, text): print(re.group(m, text, 2) else "")   # nil if group 2 didn't take part
let parts = re.split(re.compile(",\\s*")?, line)
```

Loops whose body can match nothing (`(a*)*`) give the groups Python gives. Possessive repeats
(`a*+`) are refused like backreferences: they need backtracking.

**`zlib`**: decompression of DEFLATE data in the zlib and gzip formats or raw, and `crc32` and
`adler32`. It answers what Python's `zlib.decompress` answers for the same bytes (data after the
stream is ignored, as there) and fails with zlib's messages on anything else; `tests/run_zlib.py`
compares the two, damaged data included. It takes no capability, so whatever it is given, it can't
touch a file or the network. The `_max` forms fail once the result would pass a size, before using
the memory for it (a zip bomb).

```
import zlib
let page = zlib.gunzip_max(body, 50 << 20)?   # Content-Encoding: gzip, at most 50 MB
let text = zlib.decompress(data)?             # zlib.compress's format; zlib.inflate(raw) for raw DEFLATE
print("{zlib.crc32(text)}")
```

Compression, as zlib does it (hash chains over a 32 KB window, lazy matching from level 4, each block
written with its own Huffman codes, the fixed ones or none, whichever is smallest): the output is
within a few percent of C zlib's size at the same level, and Python's `zlib` and `gzip` read it back
(`tests/run_zlib_compress.py`).

```
let z = zlib.compress(text)            # zlib format, level 6; compress_level(text, 0..9)
let gz = zlib.gzip(body)               # Content-Encoding: gzip; gzip_level(body, n)
let raw = zlib.deflate(data)           # raw DEFLATE; deflate_level(data, n)
```

Data that arrives in pieces (a download, a socket) decompresses as it comes, in at most 32 KB plus the
piece's output of memory:

```
var z = zlib.stream("gzip", 0)?        # "zlib", "gzip" or "raw"; a size limit, 0 for none
let part = zlib.feed(&z, piece)?       # the output so far (fails on bad data)
let rest = zlib.finish(&z)?            # after the last piece (fails if the stream stopped short)
zlib.unused(z)                         # input after the end of the stream
```

**`path`**: file paths as text, as Python's `os.path` gives them on Linux and macOS (`tests/run_path.py`
compares them): `path.join(a, b)`, `join_all(parts)`, `dir`, `base`, `ext` (".gz" of "a.tar.gz"),
`stem`, `without_ext`, `clean` (normpath), `is_abs`, `parts`, `rel(target, start)`, and
`within(folder, p)`, which says whether a path stays inside a folder once `..` is resolved (for names
from outside, like a URL's path: `path.within(root, path.join(root, name))`). Text only: symbolic
links aren't followed.

**`cli`**: command-line arguments (named `cli`, since `args()` is the built-in that gives them):

```
import cli
var p = cli.parser("serve", "Serves a folder over HTTP.")
cli.flag(&p, "verbose", "v", "print each request")
cli.option(&p, "port", "p", "8080", "the port to listen on")    # a default
cli.required(&p, "root", "r", "where the files are")             # must be given
cli.positional(&p, "mode", "dev or prod")
cli.rest(&p, "files", "files to preload")                        # zero or more
let a = cli.parse(p, args())?          # a mistake fails with the message and the usage
if a.help: print(cli.usage(p))         # -h or --help
let port = int(cli.get(a, "port"))?    # cli.has(a, "verbose"), cli.all(a, "files")
```

It takes `--name value`, `--name=value`, `-n value`, `-nvalue`, `-abc` (short flags together) and
`--` (the rest is positional); an option given twice keeps both (`cli.all`; `get` gives the last).

**`ws`**: WebSockets (RFC 6455), server (`ws.accept(net, c)` on a connection from `net.accept`) and
client (`ws.connect(net, "ws://..." or "wss://...")`); `ws.recv` returns whole messages (`Text`,
`Binary` or `Closed`), answering pings and closes itself; `ws.send_text`, `ws.send_binary`,
`ws.ping`, `ws.close`; `ws.poll(net, &s, seconds)` is `recv` that gives nil if no message starts
arriving in that time, so a handler can do other work in between (`ws.accept_request` does the
handshake for a request http already read). Text is checked to be UTF-8; messages are limited to 16 MB. `ws.connect_ca`
checks a `wss://` server against given certificates instead of the system's. Over TLS, give
`ws.accept` connections from a `net.tls_listen` listener. `tests/run_ws.py` tests it against
Python's `websockets` and against broken frames.

**HTTP/2**: `http.serve` also speaks HTTP/2 to clients that open with its preface (prior
knowledge, as `curl --http2-prior-knowledge`), and `http.serve_tls(net, os, port, cert, key,
handler, grace)` offers it to browsers through ALPN; the same handler answers both versions. The
`h2` module does it (HPACK, flow control, the frame types, request trailers); requests on one
connection are answered in turn. `net.tls_listen(..., alpn: "h2,http/1.1")` offers protocols for
other uses. Against clients that try to use up the server: a header list decodes to at most 64 KB
however it's compressed (no "HPACK bomb"), a header block comes in at most 32 frames, 100 streams at
once, 10 MB per request body and 20 MB of unfinished bodies per connection, and since requests are
answered in turn, cancelling streams ("rapid reset") starts no more work than sending requests
would. `tests/run_h2.py` runs these attacks, and checks against `httpx`.

**`pg`**: a PostgreSQL client over `Net`: SCRAM-SHA-256 or plain-password sign-in, TLS,
parameterized queries, text results.

```
import pg
var db = pg.connect(net, pg.config("localhost", 5432, "app", password, "appdb"))?   # fails with a message
let rows = pg.query(net, &db, "select id, name from users where age > $1", ["30"])?
let name = pg.text(rows, 0, "name") else ""       # row 0's name, nil for NULL
let n = pg.exec(net, &db, "delete from users where id = $1", ["{id}"])?   # rows affected
```

- The SQL is a `const` parameter, so values reach the server only as parameters (`$1`...), as text
  (`nil` is NULL); the server converts them to each column's type. `pg.get_int`, `get_float` and
  `get_bool` read a column as a number or Bool. For typed rows, have the server make JSON
  (`select row_to_json(u)::text from users u`) and read it with `from_json`.
- `query` and `exec` fail with a `pg.Error`: `Server(code, message, detail)` (code is the SQLSTATE,
  such as `23505` for a unique violation), `Network`, `Auth` or `Protocol`; `pg.describe(e)` makes
  a message. After a server error the connection is still usable; after a network error it isn't.
- TLS: set `cfg.tls = true` (as `sslmode=verify-full`: the server's certificate must be valid and
  for `cfg.host`), and `cfg.ca` to PEM text to trust instead of the system's certificates
  (`cfg.ca = fs.read("server-ca.pem")?`). A server that says it doesn't do TLS is refused, and so
  are bytes it sends before the handshake (they'd be read as if they came over TLS). `tests/run_pg_tls.py`
  runs a fake server with a test CA, a certificate for another host, a self-signed one, and these.
  `net.start_tls(&conn, host, ca:, timeout:)` is what it uses: TLS on a connection already open.
- `pg.from_url(os.env("DATABASE_URL"))?` reads the URL hosting platforms give
  (`postgresql://user:password@host:port/db?sslmode=require`): %-escapes are decoded, the port
  defaults to 5432 and the database to the user, an IPv6 host goes in brackets, and `sslmode`
  `require`, `verify-ca` or `verify-full` turns on TLS (always checking the certificate).
- One query at a time per connection. For several tasks, `pg.pool(net, cfg, n)?` opens n connections
  in a `Chan[pg.Db]`: take one with `recv()`, and return it with `pg.give_back(net, pool, db, cfg)`,
  which replaces a connection that broke (a database restart) with a new one. Not yet: `COPY`,
  `LISTEN`/`NOTIFY`, MD5 passwords.
  `tests/run_pg.sh` runs it against a real PostgreSQL.

**`auth`**: passwords, sessions and CSRF tokens, for apps with accounts.

```
import auth
let stored = auth.hash_password(password)           # "pbkdf2_sha256$600000$SALT$HASH" (Django's format)
if auth.check_password(attempt, stored): ...        # compares in constant time; false for a malformed hash
auth.setup(net, &db)?                                # the sessions table (PostgreSQL)
let token = auth.login(net, &db, os, user_id, 30)?   # a session for 30 days
auth.set_session(&resp, token, 30)                   # its cookie: HttpOnly, Secure, SameSite=Lax
let who = auth.current_user(net, &db, os, req)?      # the user id (a Str?), from the cookie or a Bearer token
auth.logout(net, &db, req)?                          # and auth.clear_session(&resp); auth.logout_all(net, &db, id)
```

- Hashes are PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP's number) and a random 22-character
  salt, written as Django writes them, so users can move between a Django app and a Vu app with their
  passwords. `auth.needs_rehash(stored)` says when to hash again at sign-in (fewer iterations than now).
  `check_password` refuses hashes asking for more than 10 million iterations. A hash takes about half
  a second; in a program with tasks it lets the other tasks on its thread run every 10 ms or so.
- Session tokens are 32 random bytes in URL-safe base64 (`auth.new_token()`, also for reset links and
  API keys); the table keeps only their SHA-256 (`auth.token_hash`), so a copy of it can't sign
  anyone in. `auth.session_token(req)` reads `Authorization: Bearer TOKEN`, else the `session` cookie.
  `auth.prune(net, &db, os)?` deletes ended sessions.
- `auth.csrf_token(secret, session)` is an HMAC of the session token for a hidden form field
  (`csrf_token`) or an `X-CSRF-Token` header; `auth.csrf_ok(req, secret, session)` checks it.
  (`web.same_origin` refuses most cross-site requests already.)
- `vu new api NAME` writes an app that uses all of this: sign-up, sign-in, sign-out and per-user data.
- `tests/run_auth.sh` checks the hashes against Django (both ways), malformed hashes, tokens, CSRF and
  cookies, the sessions in a real PostgreSQL, and that app over HTTP, plain and under the sanitizers.

**`stripe`**: payments with Stripe: Checkout sessions, any API call, and webhooks with their
signatures checked.

```
import stripe
var s = stripe.new(os.env("STRIPE_SECRET_KEY"))
let c = stripe.Checkout("price_123", 1, "payment", "https://example.com/thanks", "https://example.com/cart", user_id, email)
let session = stripe.checkout(net, &s, c)?          # session.id, session.url: redirect the buyer there
let v = stripe.call(net, &s, "GET", "/v1/customers", [stripe.Field("email", email)], "")?   # a json.Value
let e = stripe.verify_webhook(os.env("STRIPE_WEBHOOK_SECRET"), req, os.time())?   # e.kind, e.object (JSON)
```

- `call(net, &s, method, path, fields, idempotency_key)` sends form fields (nested names as Stripe
  writes them: `line_items[0][price]`) with the secret key, to a `/v1/` path only, keeping the
  connection open between calls. A refusal fails with Stripe's message and code (`stripe: Your card
  was declined. (card_declined)`).
- `verify_webhook` checks the `Stripe-Signature` header as Stripe's libraries do (HMAC-SHA256 of
  `TIMESTAMP.BODY`, any of several `v1` signatures, in constant time), and refuses a timestamp more
  than 5 minutes old, or (stricter than Stripe's libraries) more than 5 minutes ahead. Answer 400
  when it fails; Stripe tries again. `stripe.sign_payload(secret, body, t)` makes a header for tests.
- `tests/run_stripe.sh` checks the calls against a fake Stripe server and 86 webhook cases against
  what Stripe's Python library decides.

**`s3`**: objects in Amazon S3 and the services that speak its API (Cloudflare R2, MinIO, Backblaze
B2, DigitalOcean Spaces), with requests signed by AWS Signature Version 4.

```
import s3
var b = s3.bucket("https://s3.us-east-1.amazonaws.com", "us-east-1", "my-bucket", key_id, secret)
s3.put(net, os, &b, "avatars/42.png", data, "image/png")?
let data = s3.get(net, os, &b, "avatars/42.png")?     # fails with s3.NotFound(key), Denied, Failed or Network
let there = s3.exists(net, os, &b, key)?; s3.delete(net, os, &b, key)?
let url = s3.presign(b, "PUT", "uploads/" + name, 600, os.time())   # a browser uploads there for 10 minutes
```

- Keys are any text, encoded in the URL as S3 expects. Amazon's endpoints get virtual-hosted URLs
  (`bucket.host`) when the bucket's name allows it; other endpoints get path-style URLs, which they
  all accept. R2's region is `"auto"`.
- `tests/run_s3.sh` compares 120 random requests per run (keys with every reserved character and
  Unicode, six endpoints, bodies up to 5,000 bytes, times up to 2100) with botocore's signatures and
  presigned URLs, and runs put, get, exists, delete and a wrong secret against moto's S3, which
  checks signatures.

**`mail`**: sending email over SMTP or through Resend's API.

```
import mail
var m = mail.message("App <hello@example.com>", "ada@example.com", "Your sign-in link", text)
m.html = page                                            # optional; also m.cc, m.bcc, m.reply_to
mail.send_smtp(net, os, mail.smtp("smtp.example.com", 587, user, password), m)?
let id = mail.send_resend(net, os.env("RESEND_API_KEY"), m)?
```

- SMTP: TLS from the start on port 465 (`cfg.implicit_tls`), else STARTTLS, which is required except
  for a server at `localhost` (a local relay); sign-in with PLAIN or LOGIN, only over TLS. A server
  that sends anything between its answer to STARTTLS and the handshake is refused (that's how a man
  in the middle would slip a command into the encrypted session).
- An address, name or subject with a line break is refused, so headers can't be injected. Names and
  subjects that aren't ASCII are RFC 2047 encoded words; bodies are UTF-8 in base64; with `html`, the
  message is `multipart/alternative`. Bcc recipients get it without appearing in the headers.
- `tests/run_mail.sh` sends through aiosmtpd (STARTTLS with sign-in, TLS from the start, a local
  relay) and a fake Resend, and reads what arrived with Python's `email` package.

**`sqlite`**: SQLite databases (a file, or `":memory:"`) through the sqlite3 C library, so it takes
the `Ffi` capability, and libsqlite3 where the program is built.

```
import sqlite
var db = sqlite.open(ffi, "app.db")?
sqlite.exec(ffi, &db, "create table if not exists users (id integer primary key, name text)", [])?
let n = sqlite.exec(ffi, &db, "insert into users (name) values (?)", ["ada"])?   # rows changed
let id = sqlite.last_id(ffi, db)
let rows = sqlite.query(ffi, &db, "select id, name from users where id > ?", ["0"])?
for r in 0..rows.count:
  print(sqlite.text(rows, r, "name") else "")     # nil for NULL
```

- As with `pg`, the SQL is a `const` parameter and values go as parameters (`?`), as text (`nil`
  is NULL); `get_int` and `get_float` read a column as a number. One statement per call; errors
  are SQLite's message. `tests/run_sqlite.sh` checks it against Python's sqlite3 module.
- `sqlite.run_sql(ffi, &db, sql)` is for SQL that can't be written in the program (a console, a tool
  a model calls): one statement as given, with no parameters, and a `Result` of columns and typed
  values (`sqlite.Null`, `Integer(n)`, `Real(x)`, `Text(s)`, `Blob(b)`) and the rows changed. It
  refuses more than one statement, as Python's sqlite3 does ("You can only execute one statement
  at a time."). `sqlite.in_transaction(ffi, db)` says whether one is open. `mcp/sqlite` uses both.

**`dir`**: a folder as a capability. `dir.open(fs, path)` needs `Fs`; the `Dir` it returns resolves
every path inside the folder, in the kernel, so "..", symlinks that lead out (or absolute ones) and
folders swapped during an operation can't reach anything outside.

```
import dir
let d = dir.open(fs, "/srv/data")?
let text = d.read("notes/today.txt")?      # paths are relative to the folder
d.save("out/report.txt", text)?            # creates or replaces in place; never through a symlink
for e in d.list("notes")?: print(e.kind + " " + e.name)    # sorted; kind "dir", "file", "link", "other"
let i = d.info("notes/today.txt")?         # kind, size, mode, modified, accessed, changed, created
d.mkdir("a/b/c")?                          # with any missing parents
d.rename("a.txt", d, "b.txt")?             # fails if b.txt exists: never replaces it
d.remove("b.txt")?
let p = d.real("notes")?                   # the absolute path, symlinks resolved (inside the folder)
```

- Linux uses `openat2` with `RESOLVE_BENEATH` (5.6 and later). Elsewhere, or with `VU_DIR_WALK=1`
  (for tests), each name is opened in turn and any symlink or `..` is refused.
- Only regular files are read or written: a FIFO or a device is refused. `link_info` describes a
  symlink itself; `info` follows it (inside the folder only). Errors read like Node's:
  `ENOENT: no such file or directory`.

**`stdio`**: `stdio.line()` is the next line of standard input (without its `"\n"`), or `nil` once
it has ended; `stdio.flush()` writes out what `print` and `write` have buffered. No capability.

**`json`**: JSON whose shape isn't known ahead, as a tree (`from_json(text, Type)` reads into a declared
type, and is faster).

```
import json
let v = json.parse(text)?                  # a json.Value: Null, Flag, Whole, Num, Text, Arr or Obj
let id = json.int_at(v, "id") else 0       # also str_at, num_at, bool_at, strs_at, at (a copy), has, keys
print(json.kind(v) + " " + json.stringify(v))
```

- `stringify` writes what JavaScript's `JSON.stringify` writes: keys in their order, numbers as
  JavaScript prints them (`1e+21`, `1.5e-7`, `100000000000000000000`), the same escapes, and invalid
  UTF-8 as U+FFFD. A key given twice keeps its first place and its last value, as `JSON.parse` does.
  Nesting deeper than 1000 levels is an error.

**`mcp`**: a Model Context Protocol server over stdio. It answers the protocol itself (the 2026-07-28
revision, with the version in each request's `_meta`, and the earlier ones that start with
`initialize`) and hands the program each tool call:

```
import mcp
import stdio
let s = mcp.server("my-server", "1.0.0", TOOLS)?    # TOOLS: the tools/list array as JSON text
while true:
  let line = stdio.line() else break
  match mcp.handle(s, line):
    mcp.Reply(text): mcp.send(text)
    mcp.ToolCall(c): mcp.send(mcp.result(s, c, mcp.text("done")))   # or mcp.tool_error(msg)
    mcp.PromptGet(_): continue                  # (only for a server with prompts)
    mcp.Quiet: continue
```

A program can answer other methods itself (resources, say): it names them in `s.extra` and gets
`mcp.Request(c, method)` with the request's params in `c.args`, answered with `mcp.reply(s, c,
fields)`; `mcp.notify(method, params)` sends a notification. With `s.unknown_tool = ""`, a call to a
tool that isn't listed comes to the program too.

A server with prompts gives them as JSON too (`mcp.set_prompts(&s, PROMPTS)?`) and gets
`mcp.PromptGet(c)` for each `prompts/get`, answered with `mcp.prompt_result(s, c, description,
text)` or `mcp.error_reply(c, code, message)`.

`mcp/filesystem/main.vu` is a whole server on it: the reference MCP filesystem server's 14 tools,
reaching only the folders it was started with; `mcp/time`, `mcp/fetch`, `mcp/sqlite` and `mcp/git` are more.

The standard library's own C (`dir`, `stdio`) is part of Vu, like the runtime: its modules may make the
`Ffi` they pass to their extern functions (`Ffi()`), which no program or package can.

## Not in v0

A `\w` that's Unicode in `re` (it's ASCII).
