#!/usr/bin/env python3
"""The eval's table, from eval/run.py's results: per model and language, how often the first program
compiled, how often it passed every test first time, how often it passed within the attempts, and the
median output tokens of a passing program.
  eval/report.py [eval/results] [--markdown]"""
import glob, json, os, statistics, sys

d = next((a for a in sys.argv[1:] if not a.startswith("--")), os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
md = "--markdown" in sys.argv
rows = {}
for p in glob.glob(os.path.join(d, "*.jsonl")):
    for line in open(p):
        r = json.loads(line)
        rows.setdefault((r["model"], r["lang"]), []).append(r)

def pct(n, d): return "%d%%" % round(100 * n / d) if d else "-"

head = ["model", "language", "tasks", "compiles first try", "passes first try", "passes in 3", "tokens (median, passing)"]
out = []
for (m, l), rs in sorted(rows.items()):
    n = len(rs)
    c1 = sum(1 for r in rs if r["attempts"] and r["attempts"][0]["compiled"])
    p1 = sum(1 for r in rs if r["attempts"] and r["attempts"][0]["passed"])
    pk = sum(1 for r in rs if r["attempts"] and r["attempts"][-1]["passed"])
    toks = [r["attempts"][-1]["tokens"] for r in rs if r["attempts"] and r["attempts"][-1]["passed"]]
    out.append([m, l, str(n), pct(c1, n), pct(p1, n), pct(pk, n), str(int(statistics.median(toks))) if toks else "-"])
if md:
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in out: print("| " + " | ".join(r) + " |")
else:
    w = [max(len(x[i]) for x in out + [head]) for i in range(len(head))]
    for r in [head] + out: print("  ".join(x.ljust(w[i]) for i, x in enumerate(r)))
