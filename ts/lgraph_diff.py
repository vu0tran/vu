#!/usr/bin/env python3
# Differential test of oxlint's default (graphical) output: oxlint vs vlint on the same paths, run
# as a person would (no agent variables), output to a pipe (oxlint's ASCII theme). Reports are
# compared as blocks, per file and in order; the summary lines are compared apart from the time.
#   lgraph_diff.py [-x 'extra args'] PATH...
import subprocess, sys, os, re, collections
S = os.environ.get("VLINT_WORK", "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad")
OX = os.environ.get("OXLINT", S + "/tsbench/node_modules/.bin/oxlint")
VL = os.environ.get("VLINT", S + "/vlint")
args = sys.argv[1:]
extra = []
if args and args[0] == "-x": extra = args[1].split(); args = args[2:]
cfg = os.environ.get("OXCFG", "/tmp/oxempty.json")
base = [] if cfg == "none" else ["-c", cfg, "--disable-nested-config"]
env = {k: v for k, v in os.environ.items() if k not in ("AI_AGENT", "CLAUDECODE", "CLAUDE_CODE")}
def run(cmd):
    p = subprocess.run(cmd + base + extra + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return p.stdout.decode("utf-8", "replace"), p.returncode
def blocks(out):
    lines = out.split("\n")
    bl, cur, tail = [], None, []
    for i, l in enumerate(lines):
        if re.match(r"^  [x!>] ", l) and i > 0 and lines[i - 1] == "":
            if cur is not None: bl.append(cur)
            cur = [l]
        elif l.startswith("Found ") or l.startswith("Finished in ") or l.startswith("Exceeded "):
            if cur is not None: bl.append(cur); cur = None
            tail.append(re.sub(r"Finished in [0-9.]+m?s", "Finished in T", l))
        elif cur is not None: cur.append(l)
    if cur is not None: bl.append(cur)
    per = collections.OrderedDict()
    for b in bl:
        while b and b[-1] == "": b.pop()
        m = re.search(r"\[(.*?):\d+:\d+\]", "\n".join(b))
        per.setdefault(m.group(1) if m else "", []).append("\n".join(b))
    return per, tail
o, orc = run([OX]); v, vrc = run([VL])
po, to = blocks(o); pv, tv = blocks(v)
same = order = 0; bad = []
for f in sorted(set(po) | set(pv)):
    a, b = po.get(f, []), pv.get(f, [])
    if a == b: same += 1
    elif collections.Counter(a) == collections.Counter(b): order += 1
    else: bad.append((f, a, b))
print(f"files: oxlint {len(po)}, vlint {len(pv)}; identical {same}, order differs {order}, different {len(bad)}; exit {orc} {vrc}")
print("summary oxlint:", to); print("summary vlint: ", tv)
for f, a, b in bad[:int(os.environ.get("SHOW", "3"))]:
    ca, cb = collections.Counter(a), collections.Counter(b)
    for x in list((ca - cb).elements())[:2]: print("--- oxlint only:\n" + x)
    for x in list((cb - ca).elements())[:2]: print("--- vlint only:\n" + x)
