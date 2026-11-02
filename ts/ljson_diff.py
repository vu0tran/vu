#!/usr/bin/env python3
# Differential test of whole diagnostics: oxlint -f json vs vlint -f json on the same paths (run from
# the corpus folder). Compares each file's diagnostics (rule, message, help, severity, every label's
# span and text) and their order; prints a table by rule and examples.
#   ljson_diff.py [-n N] [-x 'extra args'] PATH...
# Environment: OXLINT (default: the tsbench copy), VLINT (default: $VLINT_WORK/vlint), OXCFG (default
# /tmp/oxempty.json; "none" to let both discover configurations).
import subprocess, sys, json, collections, os
S = os.environ.get("VLINT_WORK", "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad")
OX = os.environ.get("OXLINT", S + "/tsbench/node_modules/.bin/oxlint")
VL = os.environ.get("VLINT", S + "/vlint")
args = sys.argv[1:]
show = 6
extra = []
while args and args[0].startswith("-"):
    if args[0] == "-n": show = int(args[1]); args = args[2:]
    elif args[0] == "-x": extra = args[1].split(); args = args[2:]
    else: break
cfg = os.environ.get("OXCFG", "/tmp/oxempty.json")
if cfg == "none": base = []
else:
    if cfg == "/tmp/oxempty.json" and not os.path.exists(cfg): open(cfg, "w").write("{}")
    base = ["-c", cfg, "--disable-nested-config"]
def run(cmd):
    p = subprocess.run(cmd + base + extra + ["-f", "json"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out = p.stdout
    try:
        i = out.index("{")
        return json.loads(out[i:])["diagnostics"], p.returncode
    except Exception as e:
        print("can't read the output of", cmd[0], e, out[:300], p.stderr[:300]); sys.exit(1)
o, orc = run([OX])
v, vrc = run([VL])
def key(d):
    labs = tuple((l.get("label"), l["span"]["offset"], l["span"]["length"]) for l in d["labels"])
    return (d.get("code", "error"), d["message"], d.get("help"), d["severity"], labs)
def byfile(ds):
    m = collections.OrderedDict()
    for d in ds: m.setdefault(d.get("filename", ""), []).append(d)
    return m
of, vf = byfile(o), byfile(v)
bad_parse = set(f for f, ds in vf.items() if any(d.get("code") == "vlint(parse)" for d in ds))
stats = collections.defaultdict(lambda: [0, 0, 0])
miss_ex, extra_ex = collections.defaultdict(list), collections.defaultdict(list)
order_bad = []
same_files = 0
for f in sorted(set(of) | set(vf)):
    if f in bad_parse: continue
    ok = [key(d) for d in of.get(f, [])]
    vk = [key(d) for d in vf.get(f, [])]
    for k in ok: stats[k[0]][0] += 1
    oc, vc = collections.Counter(ok), collections.Counter(vk)
    for k, c in (oc - vc).items():
        stats[k[0]][1] += c
        miss_ex[k[0]].append((f, k))
    for k, c in (vc - oc).items():
        stats[k[0]][2] += c
        extra_ex[k[0]].append((f, k))
    if oc == vc:
        if ok == vk: same_files += 1
        else: order_bad.append(f)
print(f"files: oxlint {len(of)}, vlint {len(vf)}, vlint parse errors {len(bad_parse)}; identical {same_files}, order differs {len(order_bad)}; exit codes {orc} {vrc}")
for r, (n, m, e) in sorted(stats.items()):
    flag = "" if m == 0 and e == 0 else "  <--"
    print(f"{r:55} ox {n:6}  missing {m:5}  extra {e:5}{flag}")
for name, d in (("MISSING", miss_ex), ("EXTRA", extra_ex)):
    for r, items in sorted(d.items()):
        print(f"== {name} {r} ({len(items)})")
        for f, k in items[:show]:
            print(f"   {f}: {k[1][:80]!r} labels={k[4]}")
for f in order_bad[:show]:
    print("== ORDER", f)
    print("   ox:", [(d.get("code"), d["labels"][0]["span"]["offset"] if d["labels"] else None) for d in of[f]][:12])
    print("   vl:", [(d.get("code"), d["labels"][0]["span"]["offset"] if d["labels"] else None) for d in vf[f]][:12])
