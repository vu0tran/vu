# Compares knip's and vknip's --reporter json output, ignoring the order of files and of issues.
import json, subprocess, sys, os
vk, kn = sys.argv[1], sys.argv[2]
def norm(text):
    d = json.loads(text) if text.strip() else {"issues": []}
    out = {}
    for row in d["issues"]:
        f = row["file"]
        r = {}
        for k, v in row.items():
            if k == "file" or not isinstance(v, list): continue
            r[k] = sorted(json.dumps(x, sort_keys=True) for x in v)
        out[f] = r
    return out
same = 0
for d in sys.argv[3:]:
    a = subprocess.run(["node", kn, "--reporter", "json"], cwd=d, capture_output=True, text=True).stdout
    b = subprocess.run([vk, "--reporter", "json"], cwd=d, capture_output=True, text=True).stdout
    ok = norm(a) == norm(b)
    same += ok
    if not ok:
        na, nb = norm(a), norm(b)
        for f in sorted(set(na) | set(nb)):
            if na.get(f) != nb.get(f): print(d, f, "knip:", na.get(f), "vknip:", nb.get(f)); break
print(f"json identical (order aside): {same}/{len(sys.argv) - 3}")
