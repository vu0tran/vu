# Random projects: modules with random exports, imported in random ways.
import random, json
KINDS = ["const", "function", "class", "type", "interface", "enum", "default", "let"]
def gen(seed):
    r = random.Random(seed)
    nmod = r.randint(3, 14)
    files = {}
    mods = []
    for i in range(nmod):
        ext = r.choice([".ts", ".ts", ".ts", ".tsx", ".js", ".mts"])
        d = r.choice(["src", "src", "src/lib", "src/util", "lib"])
        isindex = r.random() < 0.15
        path = f"{d}/m{i}/index{ext}" if isindex else f"{d}/m{i}{ext}"
        exports = []
        for j in range(r.randint(1, 6)):
            k = r.choice(KINDS)
            if ext == ".js" and k in ("type", "interface", "enum"): k = "const"
            if k == "default" and any(e[0] == "default" for e in exports): k = "const"
            exports.append((k, f"e{i}_{j}"))
        mods.append({"path": path, "ext": ext, "exports": exports, "index": isindex, "dir": d, "i": i})
    deps = [f"dep{i}" for i in range(r.randint(0, 4))]
    listed = [d for d in deps if r.random() < 0.7]
    extra_listed = [f"extra{i}" for i in range(r.randint(0, 2))]
    def spec_from(a, b):
        # import specifier from module a to module b
        import os
        da = os.path.dirname(a["path"])
        target = b["path"]
        rel = os.path.relpath(target, da)
        if not rel.startswith("."): rel = "./" + rel
        base, ext = os.path.splitext(rel)
        if b["index"]:
            dirp = os.path.dirname(rel)
            if not dirp.startswith("."): dirp = "./" + dirp
            return r.choice([dirp, dirp + "/index"])
        style = r.random()
        if style < 0.5: return base
        if style < 0.8 and ext in (".ts", ".tsx"): return base + ".js"
        if ext == ".mts" and style < 0.9: return base + ".mjs"
        return base
    bodies = {}
    for m in mods:
        lines = []
        uses = []
        for _ in range(r.randint(0, 5)):
            b = r.choice(mods)
            if b is m: continue
            sp = spec_from(m, b)
            vals = [e for e in b["exports"] if e[0] not in ("default",)]
            style = r.random()
            if m["ext"] == ".js" and style < 0.3:
                if vals and r.random() < 0.5:
                    e = r.choice(vals)
                    if e[0] in ("type", "interface"): continue
                    lines.append(f"const {{ {e[1]} }} = require('{sp}');")
                else:
                    lines.append(f"const req{b['i']} = require('{sp}');")
                continue
            if style < 0.35 and vals:
                picks = r.sample(vals, r.randint(1, len(vals)))
                parts = []
                for e in picks:
                    tp = "type " if e[0] in ("type", "interface") and m["ext"] != ".js" and r.random() < 0.5 else ""
                    if tp and m["ext"] == ".js": tp = ""
                    if e[0] in ("type", "interface") and m["ext"] == ".js": continue
                    alias = f" as a{m['i']}_{e[1]}" if r.random() < 0.2 else ""
                    parts.append(tp + e[1] + alias)
                if parts: lines.append(f"import {{ {', '.join(parts)} }} from '{sp}';")
            elif style < 0.5:
                ns = f"ns{b['i']}"
                lines.append(f"import * as {ns} from '{sp}';")
                for e in r.sample(b["exports"], r.randint(0, len(b["exports"]))):
                    if e[0] == "default": continue
                    if e[0] in ("type", "interface"):
                        if m["ext"] != ".js": uses.append(f"export type U{m['i']}_{e[1]} = {ns}.{e[1]};")
                    elif e[0] == "enum":
                        uses.append(f"console.log({ns}.{e[1]}.A);")
                    else:
                        uses.append(f"console.log({ns}.{e[1]});")
                if r.random() < 0.15: uses.append(f"console.log({ns});")
            elif style < 0.6 and any(e[0] == "default" for e in b["exports"]):
                lines.append(f"import d{b['i']} from '{sp}';")
            elif style < 0.75 and vals:
                e = r.choice(vals)
                if m["ext"] == ".js" and e[0] in ("type", "interface"): continue
                lines.append(f"export {{ {e[1]} }} from '{sp}';")
            elif style < 0.82:
                lines.append(f"export * from '{sp}';")
            elif style < 0.88:
                lines.append(f"import '{sp}';")
            elif style < 0.94:
                uses.append(f"void import('{sp}');")
            elif vals:
                e = r.choice(vals)
                if e[0] == "enum":
                    lines.append(f"import {{ {e[1]} }} from '{sp}';")
                    uses.append(f"console.log({e[1]}.B);")
        for _ in range(r.randint(0, 2)):
            if deps:
                d = r.choice(deps)
                sub = r.choice(["", "", "/sub"])
                if m["ext"] == ".js" and r.random() < 0.5: lines.append(f"const x{r.randint(0,99)} = require('{d}{sub}');")
                else: lines.append(f"import '{d}{sub}';")
        if r.random() < 0.1: lines.append("import missing from './does-not-exist';")
        for k, name in m["exports"]:
            if k == "const": lines.append(f"export const {name} = 1;")
            elif k == "let": lines.append(f"export let {name} = 1;")
            elif k == "function": lines.append(f"export function {name}() {{ return 1; }}")
            elif k == "class": lines.append(f"export class {name} {{}}")
            elif k == "type": lines.append(f"export type {name} = number;")
            elif k == "interface": lines.append(f"export interface {name} {{ x: number }}")
            elif k == "enum": lines.append(f"export enum {name} {{ A, B, C }}")
            elif k == "default": lines.append(f"export default function {name}() {{}}")
        if m["ext"] == ".tsx": lines.append("export const View = () => <div />;")
        lines.extend(uses)
        files[m["path"]] = "\n".join(lines) + "\n"
    entry = r.choice(mods)
    # entry: src/index.ts importing a few modules
    imps = []
    for b in r.sample(mods, r.randint(1, min(4, len(mods)))):
        import os
        rel = os.path.relpath(b["path"], "src")
        if not rel.startswith("."): rel = "./" + rel
        base = os.path.splitext(rel)[0]
        if b["index"]: base = os.path.dirname(rel) if os.path.dirname(rel).startswith(".") else "./" + os.path.dirname(rel)
        imps.append(f"import * as entry{b['i']} from '{base}';\nconsole.log(entry{b['i']});")
    files["src/index.ts"] = "\n".join(imps) + "\n"
    pkgj = {"name": f"rnd{seed}", "version": "1.0.0", "dependencies": {d: "1" for d in listed + extra_listed}}
    if r.random() < 0.5: pkgj["devDependencies"] = {"typescript": "5", "vitest": "1"}
    if r.random() < 0.3: pkgj["scripts"] = {"test": "vitest run", "lint": "eslint ."}
    files["package.json"] = json.dumps(pkgj, indent=2) + "\n"
    if r.random() < 0.3:
        t = r.choice(mods)
        import os
        tp = os.path.splitext(t["path"])[0] + ".test.ts"
        rel = "./" + os.path.basename(os.path.splitext(t["path"])[0])
        files[tp] = f"import * as t from '{rel}';\nconsole.log(t);\n"
    return files
CASES = {f"rnd{s}": gen(s) for s in range(int(__import__('os').environ.get('RND_FROM', '0')), int(__import__('os').environ.get('RND_TO', '40')))}
