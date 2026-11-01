#!/usr/bin/env python3
# Differential test: golangci-lint (saved baselines in want/REPO.txt) vs vgolint, per check.
# usage: gd.py [-r key,key] [-n N] [-a] [REPO...]     (-a: show every check, not just implemented ones)
import subprocess, sys, re, collections, os
S = "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad"
C = S + "/gocorpus"
args = sys.argv[1:]
only = None; show = 8; allk = False
while args and args[0].startswith("-"):
    if args[0] == "-r": only = set(args[1].split(",")); args = args[2:]
    elif args[0] == "-n": show = int(args[1]); args = args[2:]
    elif args[0] == "-a": allk = True; args = args[1:]
repos = args or sorted(os.listdir(C))
impl = set(open(S + "/golint/impl.txt").read().split())
pat = re.compile(r"^(.*?):(\d+):(\d+): (.*) \((\w+)\)$")
def key(msg, linter):
    if linter == "staticcheck":
        m = re.match(r"^(\w+\d+):", msg); return "staticcheck/" + (m.group(1) if m else "?")
    if linter == "govet":
        m = re.match(r"^(\w+):", msg); return "govet/" + (m.group(1) if m else "?")
    if linter == "unused":
        m = re.match(r"^(\w+) ", msg); return "unused/" + (m.group(1) if m else "?")
    return linter
want = collections.Counter(); got = collections.Counter(); parse_err = []
for r in repos:
    for l in open(f"{S}/golint/want/{r}.txt"):
        l = l.rstrip("\n")
        m = pat.match(l)
        if not m: continue
        path = m.group(1)
        pre = f"../gocorpus/{r}/"
        if path.startswith(pre): path = path[len(pre):]
        want[(r, path + l[len(m.group(1)):], key(m.group(4), m.group(5)))] += 1
    out = subprocess.run([S + "/vgolint", "./..."], cwd=f"{C}/{r}", capture_output=True, text=True).stdout.splitlines()
    for l in out:
        if l.startswith("PARSE ERROR"): parse_err.append(r + ": " + l); continue
        m = pat.match(l)
        if not m: print("??", r, l); continue
        got[(r, l, key(m.group(4), m.group(5)))] += 1
def keep(k):
    if only is not None: return k in only
    return allk or k in impl
byk = collections.defaultdict(lambda: [0, 0, 0])
miss = want - got; extra = got - want
for (r, l, k), c in want.items():
    if keep(k): byk[k][0] += c
for (r, l, k), c in miss.items():
    if keep(k): byk[k][1] += c
for (r, l, k), c in extra.items():
    if keep(k): byk[k][2] += c
for e in parse_err[:10]: print(e)
tw = tm = te = 0
for k, (n, m, e) in sorted(byk.items()):
    flag = "" if m == 0 and e == 0 else "  <--"
    tw += n; tm += m; te += e
    print(f"{k:28} want {n:5}  missing {m:4}  extra {e:4}{flag}")
print(f"{'TOTAL':28} want {tw:5}  missing {tm:4}  extra {te:4}  matched {tw - tm}")
for name, d in (("MISSING", miss), ("EXTRA", extra)):
    items = sorted((k, r, l) for (r, l, k), c in d.items() if keep(k) for _ in range(c))
    if items:
        print(f"== {name} ({len(items)})")
        cnt = collections.Counter()
        for k, r, l in items:
            cnt[k] += 1
            if cnt[k] <= show: print(f"  {r}/{l}"[:300])
