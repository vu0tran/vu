#!/usr/bin/env python3
# gofmt_mangle.py SEED OUTDIR FILELIST: writes a whitespace-mangled copy of each Go file to OUTDIR/N.go
# (tokens kept; spacing, line breaks, indentation, blank lines and comment alignment changed in
# ways that keep the program the same), and OUTDIR.files listing them.
import sys, os, random, re

OPS3 = ["<<=", ">>=", "&^=", "...", "&&=", "||="]
OPS2 = ["<<", ">>", "&^", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "&&", "||", "<-", "++", "--", "==", "!=", "<=", ">=", ":="]

def lex(src):
    toks = []  # (kind, text): kind in ws, nl, comment, str, word, op
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "\n":
            toks.append(("nl", c)); i += 1; continue
        if c in " \t\r":
            j = i
            while j < n and src[j] in " \t\r": j += 1
            toks.append(("ws", src[i:j])); i = j; continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            if j < 0: j = n
            toks.append(("lcomment", src[i:j])); i = j; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0: return None
            toks.append(("comment", src[i:j + 2])); i = j + 2; continue
        if c == "`":
            j = src.find("`", i + 1)
            if j < 0: return None
            toks.append(("str", src[i:j + 1])); i = j + 1; continue
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\": j += 1
                if j < n and src[j] == "\n": return None
                j += 1
            toks.append(("str", src[i:j + 1])); i = j + 1; continue
        if c.isalnum() or c == "_" or ord(c) > 127 or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] == "_" or ord(src[j]) > 127 or src[j] == "." and src[i].isdigit()
                             or (src[j] in "+-" and src[j - 1] in "eEpP" and src[i].isdigit() and not src[i:j].lower().startswith("0x") or src[j] in "+-" and src[j-1] in "pP" and src[i].isdigit())):
                j += 1
            toks.append(("word", src[i:j])); i = j; continue
        for op in OPS3 + OPS2:
            if src.startswith(op, i):
                toks.append(("op", op)); i += len(op); break
        else:
            toks.append(("op", c)); i += 1
    return toks

SEMI_AFTER = set(["break", "continue", "fallthrough", "return", "++", "--", ")", "]", "}"])
def ends_stmt(t):
    k, s = t
    if k == "str": return True
    if k == "word":
        return s not in ("if", "for", "switch", "select", "case", "default", "func", "go", "defer", "goto", "package", "import", "var", "const", "type", "struct", "interface", "map", "chan", "range", "else") or s in SEMI_AFTER
    return s in SEMI_AFTER

OPEN_SAFE = set(["(", "[", "{", ","])
BINOPS = set(["+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>", "&^", "&&", "||", "==", "!=", "<", "<=", ">", ">=", "=", ":=", "+=", "-=", "*=", "/=", ":"])
CLOSE = set([")", "]", "}"])
NOGLUE = set(["(", ")", "[", "]", "{", "}", ",", ";"])

def mangle(src, rnd):
    toks = lex(src)
    if toks is None: return None
    # significant tokens with the gaps between them
    sig = []   # list of (tok, gap) where gap = list of raw tokens before it (ws, nl, comments)
    gap = []
    for t in toks:
        if t[0] in ("ws", "nl", "comment", "lcomment"): gap.append(t)
        else:
            sig.append((t, gap)); gap = []
    tail = gap
    out = []
    prev = None
    mode = rnd.random()
    for idx, (t, g) in enumerate(sig):
        nls = sum(1 for x in g if x[0] == "nl")
        has_comment = any(x[0] in ("comment", "lcomment") for x in g)
        if has_comment or prev is None:
            # keep comments; mangle spacing around them a little
            for x in g:
                if x[0] == "ws" and rnd.random() < 0.3:
                    out.append(rnd.choice([" ", "  ", "\t", "\t\t", " \t"]))
                elif x[0] == "nl":
                    out.append("\n")
                    if rnd.random() < 0.15: out.append(rnd.choice(["", "  ", "\t\t\t", " "]))
                else: out.append(x[1])
        elif nls == 0:
            # same line: change the spacing; maybe break the line after a safe token
            if prev[1] in OPEN_SAFE and t[1] not in CLOSE and rnd.random() < 0.12:
                out.append("\n" + rnd.choice(["", "\t", "  ", "\t\t"]))
            elif prev[1] in BINOPS and prev[1] not in (":",) and rnd.random() < 0.05 and t[1] not in CLOSE:
                out.append("\n\t")
            else:
                ws = "".join(x[1] for x in g)
                r = rnd.random()
                if ws == "":
                    if r < 0.2 and not (prev[1] in ("/", "*") or t[1] in ("/", "*")): out.append(rnd.choice([" ", "  "]))
                elif r < 0.25 and (prev[1] in NOGLUE or t[1] in NOGLUE) and prev[1] not in ("/", "*", ".") and t[1] not in ("/", "*", "."):
                    pass  # remove the space
                elif r < 0.5:
                    out.append(rnd.choice([" ", "  ", "\t", "   ", " \t "]))
                else: out.append(ws)
        else:
            # line break(s) in between
            r = rnd.random()
            if prev[1] in OPEN_SAFE and r < 0.25 and not (prev[1] == "{" and t[1] == "}" and False):
                out.append(rnd.choice([" ", "", "  "]))   # join the lines
            else:
                k = nls
                if r < 0.15: k = nls + rnd.choice([1, 2])
                elif r < 0.3 and nls > 1: k = 1
                for _ in range(k):
                    out.append("\n")
                # indentation
                if mode < 0.3: ind = ""
                elif mode < 0.5: ind = " " * rnd.randint(0, 6)
                else: ind = rnd.choice(["", "\t", "\t\t", "  ", "    ", "\t \t"])
                out.append(ind)
        out.append(t[1])
        prev = t
    for x in tail: out.append(x[1] if x[0] != "ws" else x[1])
    res = "".join(out)
    if not res.endswith("\n") and rnd.random() < 0.8: res += "\n"
    return res

def main():
    seed, outdir, flist = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    files = [l.strip() for l in open(flist) if l.strip()]
    rnd = random.Random(seed)
    lst = []
    for i, f in enumerate(files):
        try: src = open(f, encoding="utf-8").read()
        except Exception: continue
        m = mangle(src, rnd)
        if m is None: continue
        p = os.path.join(outdir, "%d.go" % i)
        open(p, "w", encoding="utf-8").write(m)
        lst.append(p)
    open(outdir + ".files", "w").write("".join(x + "\n" for x in lst))
    print(len(lst), "mangled")
if __name__ == "__main__": main()
