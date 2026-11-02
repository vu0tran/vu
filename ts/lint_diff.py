#!/usr/bin/env python3
# Differential test: oxlint vs vlint on the given paths, for the rules vlint implements.
# usage: ld.py [-r rule,rule] [-n N] PATH...   (run from the corpus dir)
import subprocess, sys, re, collections, os
S = os.environ.get("VLINT_WORK", "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad")
args = sys.argv[1:]
only = None; show = 8
while args and args[0].startswith("-"):
    if args[0] == "-r": only = set(args[1].split(",")); args = args[2:]
    elif args[0] == "-n": show = int(args[1]); args = args[2:]
impl = set(open(S + "/lint/impl.txt").read().split())
ox = subprocess.run([S + "/tsbench/node_modules/.bin/oxlint", "-c", "/tmp/oxempty.json", "--disable-nested-config"] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.splitlines()
vl = subprocess.run([S + "/vlint"] + args, capture_output=True, text=True).stdout.splitlines()
pat = re.compile(r"^(.*?):(\d+):(\d+): (\w+)(?: ([\w-]+\([\w-]+\)|vlint\(parse\)))?: (.*)$")
bad = set(); oxbad = set()
def parse(lines, who):
    out = []
    for l in lines:
        m = pat.match(l)
        if not m: continue
        f, ln, col, sev, rule, rest = m.groups()
        if rule == "vlint(parse)": bad.add(f); continue
        if sev == "error" and who == "ox": oxbad.add(f); out.append((f, rule or "error", l)); continue
        if sev == "error": out.append((f, "error", l)); continue
        out.append((f, rule, l))
    return out
o = parse(ox, "ox"); v = parse(vl, "vl")
def keep(f, rule):
    if f in bad: return False
    if f in oxbad and rule != "error": return False
    if rule == "error" and f not in oxbad: return True
    r = (rule or "").replace("(", "/").rstrip(")")
    if only is not None: return r in only
    return r in impl or rule == "error"
oc = collections.Counter(l for f, r, l in o if keep(f, r))
vc = collections.Counter(l for f, r, l in v if keep(f, r))
miss = oc - vc; extra = vc - oc
byrule = collections.defaultdict(lambda: [0, 0, 0])
for l, c in oc.items(): byrule[pat.match(l).group(5) or "error"][0] += c
for l, c in miss.items(): byrule[pat.match(l).group(5) or "error"][1] += c
for l, c in extra.items(): byrule[pat.match(l).group(5) or "error"][2] += c
print(f"files vlint can't parse: {len(bad)}; oxlint error files: {len(oxbad)}")
for r, (n, m, e) in sorted(byrule.items()):
    flag = "" if m == 0 and e == 0 else "  <--"
    print(f"{r:55} ox {n:5}  missing {m:4}  extra {e:4}{flag}")
for name, d in (("MISSING", miss), ("EXTRA", extra)):
    items = sorted(d.elements())
    if items:
        print(f"== {name} ({len(items)})")
        byr = collections.defaultdict(list)
        for l in items: byr[pat.match(l).group(5)].append(l)
        for r, ls in byr.items():
            for l in ls[:show]: print("  " + l[:300])
