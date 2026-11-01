#!/usr/bin/env python3
# Compares format.vu's printing of expressions with go/printer's, on the given folders.
import subprocess, sys, collections
S = "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad"
files = subprocess.run(["find"] + sys.argv[1:] + ["-name", "*.go", "-not", "-path", "*/testdata/*"], capture_output=True, text=True).stdout.split()
def load(out):
    d = {}; cur = None
    for l in out.splitlines():
        if l.startswith("FILE "): cur = l[5:]; continue
        a, b, t = l.split(" ", 2)
        d[(cur, int(a), int(b))] = t
    return d
g = {}; v = {}
for i in range(0, len(files), 200):
    chunk = files[i:i+200]
    g.update(load(subprocess.run([S + "/astdump", "-fmt"] + chunk, capture_output=True, text=True).stdout))
    v.update(load(subprocess.run([S + "/gpt", "--fmt"] + chunk, capture_output=True, text=True).stdout))
bad = [(k, g[k], v[k]) for k in g if k in v and g[k] != v[k] and "{...}" not in v[k]]
print(len(g), "go exprs,", sum(1 for k in g if k in v), "compared,", len(bad), "differ")
for k, a, b in bad[:15]: print(k[0].split("scratchpad/")[-1], k[1], "\n   go:", a, "\n   vu:", b)
