#!/usr/bin/env python3
# golangci-lint findings (DIR/CFG/REPO.txt, from `run -c DIR/CFG.yml` with no limits) vs vgolint, per linter.
# usage: cmp_cfg.py DIR CFG [REPO...]
import subprocess, sys, re, os, collections
S = "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad"
W = S + "/golint-work"
VG = os.environ.get("VG", W + "/vgolint")
d, cf = sys.argv[1], sys.argv[2]
repos = sys.argv[3:] or sorted(os.listdir(S + "/gocorpus"))
pat = re.compile(r"^(.*?):(\d+):(\d+): (.*) \(([\w-]+)\)$")
want = collections.Counter(); got = collections.Counter()
for r in repos:
    f = f"{d}/{cf}/{r}.txt"
    if not os.path.exists(f): continue
    for l in open(f):
        l = l.rstrip("\n"); m = pat.match(l)
        if m: want[(r, l, m.group(5))] += 1
    p = subprocess.run([VG, "run", "--no-cache", "-c", f"{d}/{cf}.yml", "--max-issues-per-linter", "0", "--max-same-issues", "0", "--output.text.print-issued-lines=false", "--show-stats=false", "./..."], cwd=f"{S}/gocorpus/{r}", capture_output=True, text=True, env=dict(os.environ, VGOLINT_QUIET="1"))
    for l in p.stdout.splitlines():
        m = pat.match(l)
        if m: got[(r, l, m.group(5))] += 1
        else: print("??", r, l[:200])
byk = collections.defaultdict(lambda: [0, 0, 0])
for (r, l, k), c in want.items(): byk[k][0] += c
miss = want - got; extra = got - want
for (r, l, k), c in miss.items(): byk[k][1] += c
for (r, l, k), c in extra.items(): byk[k][2] += c
tw = tm = te = 0
for k, (n, m, e) in sorted(byk.items()):
    tw += n; tm += m; te += e
    print(f"{k:16} want {n:5}  missing {m:4}  extra {e:4}{'' if m == 0 and e == 0 else '  <--'}")
print(f"{'TOTAL':16} want {tw:5}  missing {tm:4}  extra {te:4}  matched {tw - tm}")
for name, dd in (("MISSING", miss), ("EXTRA", extra)):
    items = sorted((k, r, l) for (r, l, k), c in dd.items() for _ in range(c))
    cnt = collections.Counter()
    if items: print(f"== {name} ({len(items)})")
    for k, r, l in items:
        cnt[k] += 1
        if cnt[k] <= 8: print(f"  {r}: {l}"[:260])
