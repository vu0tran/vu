import sys, os, json, subprocess, yaml, tomllib
def dump(v):
    if v is None: return "null"
    if isinstance(v, bool): return '"' + ("true" if v else "false") + '"'
    if isinstance(v, (int, float)): return '"' + str(v) + '"'
    if isinstance(v, str): return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, list): return "[" + ", ".join(dump(x) for x in v) + "]"
    if isinstance(v, dict): return "{" + ", ".join('"%s": %s' % (k, dump(x)) for k, x in v.items()) + "}"
    return '"' + str(v) + '"'
bad = 0; n = 0
for p in sys.argv[1:]:
    try:
        if p.endswith(".toml"): v = tomllib.load(open(p, "rb"))
        elif p.endswith(".json"): v = json.load(open(p))
        else: v = yaml.load(open(p), Loader=yaml.BaseLoader)
    except Exception as e:
        continue
    n += 1
    want = dump(v)
    got = subprocess.run([sys.argv[0].rsplit("/",1)[0] + "/doctest", p], capture_output=True, text=True).stdout.rstrip("\n")
    if got != want:
        bad += 1
        print("DIFF", p)
        if bad <= 3:
            for i,(a,b) in enumerate(zip(got, want)):
                if a != b: print("  got ", got[max(0,i-100):i+100]); print("  want", want[max(0,i-100):i+100]); break
            else: print("  len", len(got), len(want))
print(n, "files", bad, "differ")
