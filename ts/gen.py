"""Random TypeScript programs for checking vtsc against tsc: python3 gen.py SEED COUNT OUTDIR
Each program uses only what vtsc models, mixes right and wrong code, and suffixes every name it
declares with its number, so many programs can be checked in one tsc run."""
import random, sys, os

def split_union(t):
    out, d, cur = [], 0, ""
    i = 0
    while i < len(t):
        ch = t[i]
        if ch in "({[": d += 1
        elif ch in ")}]": d -= 1
        if d == 0 and t.startswith(" | ", i):
            out.append(cur.strip()); cur = ""; i += 3; continue
        cur += ch; i += 1
    out.append(cur.strip())
    return out

class G:
    def __init__(self, r, k):
        self.r = r; self.k = k
        self.vars = []      # (name, type text)
        self.ifaces = []    # (name, [(prop, type, optional)])
        self.aliases = []   # (name, type text)
        self.funcs = []     # (name, [param types], return type)
        self.n = 0
    def name(self, base):
        self.n += 1
        return f"{base}{self.n}_{self.k}"

    # ---- types
    def prim(self):
        return self.r.choice(["number", "string", "boolean"])
    def lit(self):
        c = self.r.random()
        if c < 0.4: return '"' + self.r.choice(["a", "b", "c", "on", "off"]) + '"'
        if c < 0.7: return str(self.r.choice([0, 1, 2, 3, 10, 42]))
        return self.r.choice(["true", "false"])
    def type_(self, depth=0):
        c = self.r.random()
        if c < 0.35 or depth > 1: return self.prim()
        if c < 0.45: return self.lit()
        if c < 0.6:
            ms = [self.type_(depth + 1) for _ in range(self.r.randint(2, 3))]
            return " | ".join(sorted(set(f"({m})" if "=>" in m and not m.startswith("((") else m for m in ms)))
        if c < 0.7: return self.prim() + "[]"
        if c < 0.78: return self.prim() + " | undefined"
        if c < 0.83: return self.prim() + " | null"
        if c < 0.9 and self.ifaces: return self.r.choice(self.ifaces)[0]
        if c < 0.95 and self.aliases: return self.r.choice(self.aliases)[0]
        if c < 0.98: return "{ " + "; ".join(f"{p}: {self.prim()}" for p in self.r.sample(["x", "y", "id", "name", "ok"], self.r.randint(1, 3))) + " }"
        return f"({self.r.choice(['n', 's'])}: {self.prim()}) => {self.prim()}"

    # ---- expressions of (roughly) a type
    def value(self, t, depth=0):
        """an expression meant to have type t; sometimes deliberately something else"""
        r = self.r
        if r.random() < 0.12: t = self.type_()     # a wrong one, often
        t = t.strip()
        parts = split_union(t)
        if len(parts) > 1:
            m = r.choice(parts)
            if m.startswith("((") and m.endswith(")"): m = m[1:-1]
            return self.value(m, depth)
        if t == "number": return r.choice([str(r.randint(0, 99)), "1.5", "-3", self.var_of("number") or "7", self.var_of("number", True) or "2"]) if depth > 1 else r.choice([str(r.randint(0, 99)), self.arith(depth)])
        if t == "string": return r.choice(['"hi"', "`t`", '"x" + 1', self.var_of("string") or '"s"', '"abc".toUpperCase()'])
        if t == "boolean": return r.choice(["true", "false", "1 > 2", "!0"])
        if t == "undefined": return "undefined"
        if t == "null": return "null"
        if t.startswith('"') or t[0].isdigit() or t in ("true", "false"): return t
        if t.endswith("[]"):
            el = t[:-2]
            return "[" + ", ".join(self.value(el, depth + 1) for _ in range(r.randint(0, 3))) + "]"
        if t.startswith("{"):
            props = [p.strip() for p in t.strip("{} ").split(";") if p.strip()]
            parts = []
            for p in props:
                pn, pt = p.split(":", 1)
                pn = pn.strip().rstrip("?")
                if r.random() < 0.9: parts.append(f"{pn}: {self.value(pt, depth + 1)}")
            if r.random() < 0.1: parts.append(f"extra: {self.value('number', depth + 1)}")
            self.spread_in(parts)
            return "{ " + ", ".join(parts) + " }"
        if t.startswith("("):
            pn = t[1]
            ret = t.split("=>")[1].strip()
            return f"(({pn}) => ({self.value(ret, depth + 1)}))"
        for iname, props in self.ifaces:
            if iname == t:
                parts = []
                for (pn, pt, opt) in props:
                    if opt and r.random() < 0.5: continue
                    if r.random() < 0.93: parts.append(f"{pn}: {self.value(pt, depth + 1)}")
                if r.random() < 0.08: parts.append(f"zz: 1")
                self.spread_in(parts)
                return "{ " + ", ".join(parts) + " }"
        for aname, at in self.aliases:
            if aname == t: return self.value(at, depth)
        return "0"

    def spread_in(self, parts):
        """--spreads: sometimes spread a variable of an object type into an object literal"""
        if not getattr(self, "with_spreads", False) or self.r.random() > 0.5: return
        cands = [v for v, vt in self.vars if vt.startswith("{") or any(vt == i for i, _ in self.ifaces) or vt.endswith("| undefined") and (vt.startswith("{") or vt.split(" |")[0] in [i for i, _ in self.ifaces])]
        if not cands: return
        parts.insert(self.r.randint(0, len(parts)), "..." + self.r.choice(cands))

    def var_of(self, t, any_=False):
        cands = [v for v, vt in self.vars if vt == t or any_]
        return self.r.choice(cands) if cands else None

    def arith(self, depth):
        a = self.var_of("number") or str(self.r.randint(1, 9))
        b = self.var_of("number", True) or str(self.r.randint(1, 9))
        return f"{a} {self.r.choice(['+', '-', '*', '%'])} {b}"

    # ---- statements
    def iface(self):
        name = self.name("I")
        props = []
        for p in self.r.sample(["id", "name", "count", "tag", "on", "label"], self.r.randint(1, 4)):
            props.append((p, self.prim() if self.r.random() < 0.8 else self.lit(), self.r.random() < 0.25))
        self.ifaces.append((name, props))
        body = "; ".join(f"{p}{'?' if o else ''}: {t}" for p, t, o in props)
        return f"interface {name} {{ {body} }}"

    def alias(self):
        name = self.name("T")
        t = " | ".join(sorted(set(self.lit() if self.r.random() < 0.6 else self.prim() for _ in range(self.r.randint(2, 3)))))
        self.aliases.append((name, t))
        return f"type {name} = {t}"

    def decl(self):
        r = self.r
        kw = r.choice(["let", "const", "let"])
        name = self.name("v")
        if r.random() < 0.7:
            t = self.type_()
            line = f"{kw} {name}: {t} = {self.value(t)}"
            self.vars.append((name, t))
        else:
            t = self.prim()
            line = f"{kw} {name} = {self.value(t)}"
            self.vars.append((name, t if kw == "let" else "?"))
        return line

    def func(self):
        r = self.r
        name = self.name("f")
        params = []
        for i in range(r.randint(0, 3)):
            params.append((f"p{i}", self.type_()))
        ret = r.choice([self.prim(), "void", self.prim() + " | undefined"])
        body = []
        if params and r.random() < 0.5:
            p, pt = r.choice(params)
            body.append(self.narrow_stmt(p, pt))
        if ret == "void":
            body.append(f"console.log({params[0][0] if params else '1'})")
        else:
            base = ret.replace(" | undefined", "")
            if r.random() < 0.85: body.append(f"return {self.value(base)}")
        self.funcs.append((name, [pt for _, pt in params], ret))
        ps = ", ".join(f"{p}: {t}" for p, t in params)
        return f"function {name}({ps}): {ret} {{\n  " + "\n  ".join(body) + "\n}"

    def narrow_stmt(self, p, pt):
        r = self.r
        c = r.random()
        if "undefined" in pt or "null" in pt:
            if c < 0.5: return f"if ({p}) {{ console.log({p}) }}"
            if c < 0.8: return f"if ({p} !== undefined && {p} !== null) {{ console.log({p}) }}"
            return f"console.log({p})"
        if " | " in pt:
            if c < 0.6: return f'if (typeof {p} === "string") {{ console.log({p}.length) }} else {{ console.log({p}) }}'
            return f"console.log({p})"
        if pt == "string": return f"if ({p}.length > 2) {{ console.log({p}.toUpperCase()) }}"
        if pt.endswith("[]"): return f"console.log({p}.length, {p}.join(\",\"))"
        return f"console.log({p})"

    def gfunc(self):
        """a generic function: a constrained type parameter read, narrowed and used"""
        r = self.r
        name = self.name("g")
        con = r.choice(["", " extends string", " extends string | number", " extends number | undefined",
                        " extends { x: number } | null", " extends Date | number", " extends string | null",
                        " extends number", " extends { x: number }", " extends boolean | string"])
        pt = r.choice(["T", "T", "T | undefined", "T | number", "T | null"])
        body = []
        for _ in range(r.randint(1, 4)):
            c = r.random()
            tgt = r.choice(["boolean", "number", "string", "object", "{ x: number }"])
            if c < 0.15: body.append(f"const a{len(body)}: {tgt} = p")
            elif c < 0.3: body.append(f"if (p) {{ const b: {tgt} = p }}")
            elif c < 0.42: body.append(f"if (!p) {{ const b: {tgt} = p }}")
            elif c < 0.6:
                w = r.choice(["string", "number", "object", "function", "undefined", "boolean"])
                op = r.choice(["===", "!=="])
                body.append(f'if (typeof p {op} "{w}") {{ const b: {tgt} = p }}')
            elif c < 0.72:
                v = r.choice(["undefined", "null"])
                op = r.choice(["===", "!==", "==", "!="])
                body.append(f"if (p {op} {v}) {{ const b: {tgt} = p }}")
            elif c < 0.82: body.append(f"p.{r.choice(['toString()', 'length', 'x', 'valueOf()'])}")
            elif c < 0.9: body.append(f"const e{len(body)} = p\n  const f{len(body)}: {tgt} = e{len(body)}")
            else: body.append(f"take{self.k}(p)")
        ret = ""
        if r.random() < 0.4:
            ret = ": T"
            body.append("return p" if r.random() < 0.7 else "return 1")
        self.gfuncs = getattr(self, "gfuncs", []) + [(name, pt)]
        decl = "" if getattr(self, "took", False) else f"declare function take{self.k}(b: boolean): void\n"
        self.took = True
        return decl + f"function {name}<T{con}>(p: {pt}){ret} {{\n  " + "\n  ".join(body) + "\n}"

    def call(self):
        r = self.r
        if not self.funcs: return "console.log(0)"
        name, pts, ret = r.choice(self.funcs)
        args = [self.value(t) for t in pts]
        if r.random() < 0.1 and args: args.pop()
        elif r.random() < 0.08: args.append("1")
        e = f"{name}({', '.join(args)})"
        if r.random() < 0.4 and ret != "void":
            v = self.name("r")
            t = self.type_() if r.random() < 0.4 else ret
            self.vars.append((v, t))
            return f"const {v}: {t} = {e}"
        return e

    def misc(self):
        r = self.r
        c = r.random()
        if c < 0.2:
            v = self.var_of(r.choice(["number", "string", "boolean"]), True) or "0"
            w = self.var_of(r.choice(["number", "string"]), True) or '"x"'
            return f"if ({v} === {w}) {{ console.log(1) }}"
        if c < 0.35:
            arr = self.name("xs")
            el = self.prim()
            self.vars.append((arr, el + "[]"))
            return f"const {arr}: {el}[] = [{self.value(el)}]\n{arr}.push({self.value(el)})\nconst {arr}m = {arr}.map(x => x)"
        if c < 0.5:
            v = self.var_of("string") or '"q"'
            return f"const {self.name('n')}: number = {v}.{r.choice(['length', 'indexOf(\"a\")', 'charCodeAt(0)', 'toUpperCase()', 'nope'])}"
        if c < 0.6 and self.ifaces:
            iname, props = r.choice(self.ifaces)
            o = self.name("o")
            self.vars.append((o, iname))
            p = r.choice(props + [("missing", "number", False)])
            return f"const {o}: {iname} = {self.value(iname)}\nconsole.log({o}.{p[0]})"
        if c < 0.7:
            v = self.var_of("number", True) or "1"
            return f"let {self.name('s')} = {v} {r.choice(['+', '-', '<', '*'])} {self.value(self.prim())}"
        if c < 0.8:
            v = self.var_of("number") or None
            if v: return f"{v} = {self.value('number')}"
            return "console.log(2)"
        if c < 0.9:
            return f"const {self.name('c')} = {self.value(self.prim())} ? {self.value(self.prim())} : {self.value(self.prim())}"
        return f"const {self.name('u')}: string | undefined = undefined\nconsole.log({self.vars[-1][0] if self.vars else 'undefined'})"

    # ---- classes
    def klass(self):
        r = self.r
        name = self.name("C")
        if not hasattr(self, "classes"): self.classes = []
        base = r.choice(self.classes) if self.classes and r.random() < 0.3 else None
        impl = r.choice(self.ifaces) if self.ifaces and r.random() < 0.25 else None
        props = []   # (name, type, mods)
        lines = []
        head = f"class {name}"
        if base: head += f" extends {base['name']}"
        if impl: head += f" implements {impl[0]}"
        used = set(p[0] for p in (base["props"] if base else []))
        if impl:
            for (pn, pt, opt) in impl[1]:
                if r.random() < 0.85:
                    t = pt if r.random() < 0.85 else self.prim()
                    used.add(pn)
                    lines.append(f"  {pn}{'?' if opt and r.random() < 0.5 else ''}: {t} = {self.value(t, 1)}")
                    props.append((pn, t, ""))
        for _ in range(r.randint(0, 3)):
            pn = r.choice(["a", "b", "count", "label", "flag", "size"])
            if pn in used: continue
            used.add(pn)
            c = r.random()
            mods = r.choice(["", "", "", "private ", "readonly ", "protected ", "static "])
            t = self.prim()
            if c < 0.45: lines.append(f"  {mods}{pn}: {t} = {self.value(t, 1)}")
            elif c < 0.65: lines.append(f"  {mods}{pn} = {self.value(t, 1)}")
            elif c < 0.85: lines.append(f"  {mods}{pn}: {t}")
            else: lines.append(f"  {mods}{pn}{r.choice(['?', '!'])}: {t}")
            if "static" not in mods: props.append((pn, t, mods))
        ctor = []
        if r.random() < 0.6:
            ps = []
            for i in range(r.randint(0, 2)):
                pm = r.choice(["", "", "public ", "private ", "readonly "])
                t = self.prim()
                pn = f"q{i}"
                ps.append(f"{pm}{pn}: {t}")
                ctor.append(t)
                if pm: props.append((pn, t, pm))
            body = []
            if base and r.random() < 0.85: body.append("super(" + ", ".join(self.value(t, 1) for t in base["ctor"]) + ")")
            for (pn, t, mods) in props:
                if r.random() < 0.3 and "static" not in mods: body.append(f"this.{pn} = {self.value(t, 1)}")
            lines.append(f"  constructor({', '.join(ps)}) {{ " + "; ".join(body) + " }")
        elif base:
            ctor = list(base["ctor"])
        methods = []
        for _ in range(r.randint(0, 2)):
            mn = self.name("m")
            ret = self.prim()
            body_t = ret if r.random() < 0.8 else self.prim()
            ex = self.value(body_t, 1)
            if props and r.random() < 0.5:
                pn, pt, _m = r.choice(props)
                ex = f"this.{pn}"
                body_t = pt
            ann = f": {ret}" if r.random() < 0.6 else ""
            lines.append(f"  {mn}(){ann} {{ return {ex} }}")
            methods.append((mn, ret if ann else body_t))
        if r.random() < 0.2 and props:
            pn, pt, _m = r.choice(props)
            lines.append(f"  get g{pn}() {{ return this.{pn} }}")
        if r.random() < 0.15:
            lines.append(f"  static make() {{ return new {name}({', '.join(self.value(t, 1) for t in ctor)}) }}")
        allprops = list(props) + ([p for p in base["props"] if p[0] not in used] if base else [])
        self.classes.append({"name": name, "props": allprops, "ctor": ctor, "methods": methods + (base["methods"] if base else [])})
        return head + " {\n" + "\n".join(lines) + "\n}"

    def use_class(self):
        r = self.r
        k = r.choice(self.classes)
        o = self.name("o")
        args = [self.value(t) for t in k["ctor"]]
        if r.random() < 0.1 and args: args.pop()
        out = [f"const {o} = new {k['name']}({', '.join(args)})"]
        for _ in range(r.randint(1, 3)):
            c = r.random()
            if c < 0.35 and k["props"]:
                pn, pt, mods = r.choice(k["props"])
                want = pt if r.random() < 0.7 else self.prim()
                out.append(f"const {self.name('p')}: {want} = {o}.{pn}")
            elif c < 0.55 and k["props"]:
                pn, pt, mods = r.choice(k["props"])
                out.append(f"{o}.{pn} = {self.value(pt)}")
            elif c < 0.8 and k["methods"]:
                mn, mt = r.choice(k["methods"])
                want = mt if r.random() < 0.7 else self.prim()
                out.append(f"const {self.name('v')}: {want} = {o}.{mn}()")
            elif self.ifaces:
                out.append(f"const {self.name('i')}: {r.choice(self.ifaces)[0]} = {o}")
            else:
                out.append(f"console.log({o}.zz)")
        return "\n".join(out)

    def program(self):
        out = []
        for _ in range(self.r.randint(0, 2)): out.append(self.iface())
        for _ in range(self.r.randint(0, 2)): out.append(self.alias())
        classes = getattr(self, "with_classes", False)
        for _ in range(self.r.randint(3, 9)):
            c = self.r.random()
            if classes and c < 0.2: out.append(self.klass())
            elif classes and c < 0.35 and getattr(self, "classes", None): out.append(self.use_class())
            elif getattr(self, "with_generics", False) and c < 0.3: out.append(self.gfunc())
            elif c < 0.35: out.append(self.decl())
            elif c < 0.55: out.append(self.func())
            elif c < 0.75: out.append(self.call())
            else: out.append(self.misc())
        return "\n".join(out) + "\n"

def module_pair(r, k):
    """two files: b exports some of its declarations, a imports (some of) them and uses them"""
    b = G(r, k)
    b.n = 100
    out_b = []
    exported = []   # (kind, name, payload)
    for _ in range(r.randint(0, 2)): out_b.append(b.iface())
    for _ in range(r.randint(0, 2)): out_b.append(b.alias())
    for _ in range(r.randint(2, 6)):
        c = r.random()
        if c < 0.5: out_b.append(b.decl())
        elif c < 0.8: out_b.append(b.func())
        else: out_b.append(b.misc())
    # export some declarations by prefixing them
    lines = []
    for chunk in out_b:
        first = chunk.split("\n")[0]
        word = first.split(" ")[0]
        if word in ("interface", "type", "function", "let", "const") and r.random() < 0.75 and not first.startswith("const xs"):
            chunk = "export " + chunk
            name = first.split(" ")[1].split("(")[0].split(":")[0]
            exported.append(name)
        lines.append(chunk)
    a = G(r, k)
    a.n = 200
    for (n, props) in b.ifaces:
        if n in exported: a.ifaces.append((n, props))
    for (n, t) in b.aliases:
        if n in exported: a.aliases.append((n, t))
    for (n, ps, ret) in b.funcs:
        if n in exported: a.funcs.append((n, ps, ret))
    for (n, t) in b.vars:
        if n in exported: a.vars.append((n, t))
    names = list(exported)
    r.shuffle(names)
    specs = names[: r.randint(0, len(names))] if names else []
    # imported but not used names vanish from a's knowledge
    keep = set(specs)
    a.ifaces = [x for x in a.ifaces if x[0] in keep]
    a.aliases = [x for x in a.aliases if x[0] in keep]
    a.funcs = [x for x in a.funcs if x[0] in keep]
    a.vars = [x for x in a.vars if x[0] in keep]
    if r.random() < 0.2: specs.append(r.choice(["nope", "missing", (names[0] + "x") if names else "zz"]))
    if r.random() < 0.15 and b.vars: specs.append(b.vars[0][0])
    imp = []
    if specs: imp.append("import { " + ", ".join(specs) + f' }} from "./g{k:05d}_b"')
    elif r.random() < 0.5: imp.append(f'import * as ns{k} from "./g{k:05d}_b"')
    if r.random() < 0.08: imp.append(f'import {{ q }} from "./nowhere{k}"')
    body = []
    for _ in range(r.randint(2, 7)):
        c = r.random()
        if c < 0.35: body.append(a.decl())
        elif c < 0.55: body.append(a.func())
        elif c < 0.75: body.append(a.call())
        else: body.append(a.misc())
    if not imp: imp.append("export {}")
    return "\n".join(imp + body) + "\n", "\n".join(lines) + "\n"

def main():
    seed, count, outdir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    mods = "--modules" in sys.argv
    os.makedirs(outdir, exist_ok=True)
    for k in range(count):
        r = random.Random(seed * 100003 + k)
        if mods and r.random() < 0.5:
            pa, pb = module_pair(r, k)
            with open(os.path.join(outdir, f"g{k:05d}.ts"), "w") as f: f.write(pa)
            with open(os.path.join(outdir, f"g{k:05d}_b.ts"), "w") as f: f.write(pb)
            continue
        g = G(r, k)
        g.with_classes = "--classes" in sys.argv
        g.with_generics = "--generics" in sys.argv
        g.with_spreads = "--spreads" in sys.argv
        with open(os.path.join(outdir, f"g{k:05d}.ts"), "w") as f:
            f.write(g.program())

main()
