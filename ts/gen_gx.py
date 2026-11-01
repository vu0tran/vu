import random, sys
# Generic programs: conditional types, keyof, T[K] access, assertions with type parameters,
# Array.isArray on generic unions, overloads with callbacks, intersections against object types.
seed = int(sys.argv[1]); n = int(sys.argv[2]); random.seed(seed)
PRIM = ["string", "number", "boolean", "\"a\" | \"b\"", "1 | 2", "undefined", "null", "string[]", "readonly number[]", "{ a: number }", "{ a?: string; b: 1 }", "Record<string, number>", "{ 0: string; 1: string }"]
CONS = ["", " extends string", " extends number", " extends string | number", " extends \"a\" | \"b\"", " extends object", " extends {}", " extends { a: number }", " extends Record<string, number>", " extends unknown", " extends string | undefined"]
VALS = ["\"s\"", "1", "true", "undefined", "null", "{ a: 1 }", "[1]", "\"a\"", "{ a: 1, b: 2 }", "() => 1"]

def prim(): return random.choice(PRIM)

def cond_alias(name, tp):
    t = random.random()
    chk = tp if random.random() < 0.75 else f"[{tp}]"
    ext = random.choice(["string", "number", "undefined", "object", "unknown", "\"a\"", "any[]", "{ a: number }"])
    a = random.choice([prim(), "{ x: 1 }", "{ y: string }", f"{tp}[]", "never", tp if random.random() < 0.3 else prim()])
    b = random.choice([prim(), "{ x: 2 }", "{ z?: number }", "never"])
    if t < 0.3:
        b = f"{tp} extends {random.choice(['number', 'boolean'])} ? {prim()} : {prim()}"
    return f"type {name}<{tp}> = {chk} extends {ext} ? {a} : {b};"

for p in range(n):
    out = []
    out.append(cond_alias("C1", "T"))
    out.append(cond_alias("C2", "U"))
    out.append(f"type O = {random.choice(['{ a: number; b: string }', '{ [k: string]: number }', '{ 0: string; 1: number; x: boolean }', 'Record<\"a\" | \"b\", number>'])};")
    c1 = random.choice(CONS); c2 = random.choice(CONS)
    body = []
    k = random.random()
    # assertions between type parameters and concrete types
    for i in range(3):
        src = random.choice(["x", "y", VALS[random.randrange(len(VALS))]])
        dst = random.choice(["T", "K", prim(), "C1<T>", "keyof O", "O[keyof O]"])
        body.append(f"  const a{i} = {src} as {dst};")
    # element access with generic and concrete keys
    body.append(f"  const e1 = o[k];")
    body.append(f"  const e2: {prim()} = o[k];")
    body.append(f"  const e3 = x[{random.choice(['k', '\"a\"', '0', 'y'])}];")
    # conditional types against concrete values
    body.append(f"  const c1: C1<T> = {random.choice(VALS)};")
    body.append(f"  const c2: {prim()} = c;")
    body.append(f"  const c3 = c as {prim()};")
    # Array.isArray on a generic union
    body.append(f"  if (Array.isArray(u)) {{ const n1: {prim()} = u; }} else {{ const n2: {prim()} = u; }}")
    # overloads with callbacks
    body.append(f"  const r1: {prim()} = ov(x as any, (q) => q);")
    body.append(f"  const r2 = \"s\".replace(/a/g, (m) => m.{random.choice(['toUpperCase()', 'length', 'foo'])});")
    # intersections against object types
    body.append(f"  const i1: {random.choice(['{ a: number; b: string }', '{ z?: number }', '{ a: string }', '{ q: 1 }'])} = it;")
    out.append(f"declare function ov(a: string, f: (s: string) => string): string;")
    out.append(f"declare function ov(a: number, f: (n: number) => number): number;")
    out.append(f"declare const it: {random.choice(['{ a: number }', '{ a: number; c: 1 }'])} & {random.choice(['{ b: string }', '{ b: number }', '{}'])};")
    kc = random.choice([" extends keyof O", " extends keyof T", " extends string", "", " extends \"a\""])
    out.append(f"function f<T{c1}, K{kc}>(x: T, y: {prim()}, k: K, o: {random.choice(['O', 'T', 'Record<K & string, number>'])}, c: C1<T>, u: C1<T> | C2<T>) {{")
    out.extend(body)
    out.append("}")
    out.append("export {}")
    open(f"t{seed}_{p}.ts", "w").write("\n".join(out) + "\n")
