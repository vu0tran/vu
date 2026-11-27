#!/usr/bin/env python3
# fix_mangle.py SEED FRACTION FILES...: changes a FRACTION of the files (in place) so that goimports'
# fix.go has work: an import deleted (its references then missing), an unused one added (from the
# pool of every path the files import, or the standard library), a block made one line, all of a
# file's imports deleted, comments beside the specs, a second import declaration. Files stay
# parseable (a change gofmt can't parse is dropped; GOFMT names it); most no longer compile.
import sys, random, re, subprocess, os
GOFMT = os.environ.get("GOFMT", "gofmt")
seed = int(sys.argv[1]); frac = float(sys.argv[2]); files = sys.argv[3:]
rng = random.Random(seed)
SPEC = re.compile(r'^(\s*)((?:[A-Za-z_][A-Za-z0-9_]*|\.)\s+)?("[^"]+")(\s*//.*)?$')
pool = set(["fmt", "os", "strings", "bytes", "io", "sort", "errors", "context", "time", "sync", "math/rand", "crypto/rand", "html/template", "text/template", "log"])
srcs = {}
for f in files:
    s = open(f).read()
    srcs[f] = s
    for blk in re.findall(r'^import \((.*?)^\)', s, re.M | re.S):
        for m in re.finditer(r'^\s*(?:[A-Za-z_.]\w*\s+)?"([a-z0-9/._-]+)"', blk, re.M):
            pool.add(m.group(1))
    for m in re.finditer(r'^import (?:[A-Za-z_.]\w*\s+)?"([a-z0-9/._-]+)"', s, re.M):
        pool.add(m.group(1))
# (FIXPOOL=std: only standard library paths are added, so no import makes the package unloadable,
# which golangci-lint reports alone)
if os.environ.get("FIXPOOL") == "std":
    pool = set(p for p in pool if "." not in p.split("/")[0] and "internal" not in p)
pool = sorted(pool)
def block(lines):
    """the first import block's line range (start, end) of `import (`...`)`, or a single import's"""
    for i, l in enumerate(lines):
        if l.startswith("import ("):
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == ")": return i, j
            return None
        if l.startswith("import \"") or re.match(r'import [A-Za-z_.]\w* "', l): return i, i
        if l.startswith("func ") or l.startswith("type ") or l.startswith("var ") or l.startswith("const "): return None
    return None
for f in files:
    if rng.random() > frac: continue
    lines = srcs[f].split("\n")
    b = block(lines)
    ops = rng.sample(["del", "del", "add", "add", "oneline", "delall", "comment", "second", "addnamed"], k=rng.randint(1, 3))
    pk = None
    for i, l in enumerate(lines):
        if l.startswith("package "): pk = i; break
    if pk is None: continue
    for op in ops:
        b = block(lines)
        if op == "del" and b and b[0] != b[1]:
            cand = [k for k in range(b[0] + 1, b[1]) if SPEC.match(lines[k])]
            if cand: del lines[rng.choice(cand)]
        elif op == "delall" and b:
            del lines[b[0]:b[1] + 1]
        elif op in ("add", "addnamed"):
            p = rng.choice(pool)
            spec = '"%s"' % p
            if op == "addnamed": spec = rng.choice(["x", "_", ".", p.split("/")[-1]]) + " " + spec
            if b and b[0] != b[1]: lines.insert(rng.randint(b[0] + 1, b[1]), "\t" + spec)
            else: lines.insert(pk + 1, "\nimport " + spec)
        elif op == "oneline" and b and b[0] != b[1]:
            specs = [lines[k].strip() for k in range(b[0] + 1, b[1]) if SPEC.match(lines[k]) and "//" not in lines[k]]
            if specs and len(specs) == b[1] - b[0] - 1: lines[b[0]:b[1] + 1] = ["import (" + "; ".join(specs) + ")"]
        elif op == "comment" and b and b[0] != b[1]:
            cand = [k for k in range(b[0] + 1, b[1]) if SPEC.match(lines[k])]
            if cand:
                k = rng.choice(cand)
                if rng.random() < 0.5: lines[k] = lines[k] + " // c%d" % k
                else: lines.insert(k, "\t// doc %d" % k)
        elif op == "second" and b:
            lines.insert(b[1] + 1, '\nimport "%s"' % rng.choice(pool))
    out = "\n".join(lines)
    # (only changes that still parse: gofmt -e reports syntax errors)
    if subprocess.run([GOFMT, "-e"], input=out.encode(), capture_output=True).returncode == 0:
        open(f, "w").write(out)
