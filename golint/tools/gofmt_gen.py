#!/usr/bin/env python3
# gofmt_gen.py NAME FLAGS FILELIST: runs gofmt FLAGS on each file into ./NAME/exp/N.go and writes
# NAME/list (SRC<tab>EXPECTED lines for fmttest cmp); GOFMT names the gofmt binary
import sys, os, subprocess, concurrent.futures as cf
S = os.getcwd()
GOFMT = os.environ.get("GOFMT", "gofmt")
name, flags, flist = sys.argv[1], sys.argv[2].split() if sys.argv[2] else [], sys.argv[3]
files = [l.strip() for l in open(flist) if l.strip()]
out = os.path.join(S, name, "exp"); os.makedirs(out, exist_ok=True)
def run(i):
    f = files[i]
    try:
        r = subprocess.run([GOFMT] + flags + [f], capture_output=True, timeout=60)
    except Exception:
        return None
    if r.returncode != 0: return None
    p = os.path.join(out, "%d.go" % i)
    open(p, "wb").write(r.stdout)
    return (f, p)
with cf.ThreadPoolExecutor(int(os.environ.get("J", "6"))) as ex:
    res = list(ex.map(run, range(len(files))))
ok = [r for r in res if r]
open(os.path.join(S, name, "list"), "w").write("".join("%s\t%s\n" % r for r in ok))
print(len(files), "files,", len(ok), "formatted by gofmt")
