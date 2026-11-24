#!/usr/bin/env python3
# gofmt_mangle2.py SEED OUTDIR FILELIST: like gofmt_mangle.py, and also puts comments between tokens: /* */ on a
# line, // at line ends, multi-line /* */ where a line break is, and generated doc comments
# (paragraphs, lists, code, headings, links, quotes) above top-level declarations.
import sys, os, random, importlib.util
spec = importlib.util.spec_from_file_location("mg", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gofmt_mangle.py"))
mg = importlib.util.module_from_spec(spec); spec.loader.exec_module(mg)

WORDS = "the a value of returns Foo bar baz ``quoted'' x y z http://example.com/a(b) [Link] [fmt.Println] [io] it's".split()

def doc_comment(rnd):
    lines = []
    for _ in range(rnd.randint(1, 4)):
        k = rnd.random()
        if k < 0.4:
            for _ in range(rnd.randint(1, 3)):
                lines.append(" ".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 8))))
        elif k < 0.55:
            mark = rnd.choice(["-", "*", "+", "1.", "2)", "•"])
            for _ in range(rnd.randint(1, 3)):
                lines.append(rnd.choice(["", " ", "  ", "\t"]) + mark + " " + " ".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 5))))
        elif k < 0.7:
            for _ in range(rnd.randint(1, 3)):
                lines.append(rnd.choice(["\t", "  ", "    "]) + "code(" + rnd.choice(WORDS) + ")")
        elif k < 0.8:
            lines.append(rnd.choice(["# Heading", "Old Heading", "#  Spaced heading"]))
        elif k < 0.9:
            lines.append("[Link]: https://example.com/" + rnd.choice(["x", "y"]))
        else:
            lines.append("")
        if rnd.random() < 0.6: lines.append("")
    style = rnd.random()
    if style < 0.8:
        return "".join("//" + rnd.choice([" ", "", "  "]) + l + "\n" if l else "//\n" for l in lines)
    return "/*\n" + "\n".join(lines) + "\n*/\n"

def mangle2(src, rnd):
    m = mg.mangle(src, rnd)
    if m is None: return None
    toks = mg.lex(m)
    if toks is None: return None
    out = []
    prev = None
    depth = 0
    for i, t in enumerate(toks):
        k, s = t
        if k == "op" and s in "({[": depth += 1
        if k == "op" and s in ")}]": depth -= 1
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if k == "nl":
            r = rnd.random()
            if prev is not None and prev[0] not in ("lcomment",) and r < 0.04:
                out.append(rnd.choice([" // c", "\t// trailing", "  /* b */", " //x"]))
            out.append(s)
            if r > 0.97 and prev is not None:
                out.append(rnd.choice(["/* m\n  more */\n", "  /*\n * star\n */\n", "\t// own line\n"]))
            # doc comment above a top-level declaration
            if depth == 0 and nxt is not None and nxt[0] == "word" and nxt[1] in ("func", "type", "var", "const") and rnd.random() < 0.3:
                out.append(doc_comment(rnd))
            prev = t
            continue
        if k == "ws" and prev is not None and prev[0] not in ("lcomment", "nl") and rnd.random() < 0.03:
            out.append(s + rnd.choice(["/* i */", "/*x*/ ", "/* */"]))
            prev = t
            continue
        out.append(s)
        if k not in ("ws",): prev = t
    return "".join(out)

def main():
    seed, outdir, flist = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    files = [l.strip() for l in open(flist) if l.strip()]
    rnd = random.Random(seed)
    lst = []
    for i, f in enumerate(files):
        try: src = open(f, encoding="utf-8").read()
        except Exception: continue
        m = mangle2(src, rnd)
        if m is None: continue
        p = os.path.join(outdir, "%d.go" % i)
        open(p, "w", encoding="utf-8").write(m)
        lst.append(p)
    open(outdir + ".files", "w").write("".join(x + "\n" for x in lst))
    print(len(lst), "mangled")
if __name__ == "__main__": main()
