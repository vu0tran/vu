# Writes generated projects, runs knip on each command line of each (cached), then vknip, and compares
# standard output, standard error and the exit code.
#   KNIP=.../knip/bin/knip.js VKNIP=.../vknip python3 gen_cmp.py CASES.py OUT_DIR [-r] [-v] [NAME...]
import os, sys, json, shutil, subprocess, importlib.util, difflib
here = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
rerun = '-r' in args; verbose = '-v' in args
args = [a for a in args if a not in ('-r', '-v')]
spec = importlib.util.spec_from_file_location("cases", os.path.abspath(args[0])); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = os.path.abspath(args[1]); names = args[2:] or list(m.CASES)
KNIP = os.environ.get("KNIP", "/dev/shm/knip/ref/node_modules/knip/bin/knip.js")
VK = os.environ.get("VKNIP")
refdir = os.path.join(out, "_ref"); os.makedirs(refdir, exist_ok=True)
same = total = 0
def write(d, c, links):
    shutil.rmtree(d, ignore_errors=True)
    for p, txt in c.items():
        f = os.path.join(d, p); os.makedirs(os.path.dirname(f), exist_ok=True); open(f, "w").write(txt)
    for p, t in links.items():
        f = os.path.join(d, p); os.makedirs(os.path.dirname(f), exist_ok=True); os.symlink(t, f)
    # knip next to the project, as when it's a devDependency (vknip finds jiti through it)
    kdir = os.path.dirname(os.path.dirname(KNIP))
    nm = os.path.join(d, "node_modules"); os.makedirs(nm, exist_ok=True)
    if not os.path.exists(os.path.join(nm, "knip")): os.symlink(kdir, os.path.join(nm, "knip"))
    subprocess.run(["git", "init", "-q"], cwd=d)
def tree(d):  # the project's files after a run (for --fix)
    out = {}
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in ("node_modules", ".git")]
        for f in files:
            p = os.path.join(root, f); out[os.path.relpath(p, d)] = open(p, errors="replace").read()
    return out
for name in names:
    c = dict(m.CASES[name])
    cmdlines = c.pop("__args__", [[]]); links = c.pop("__links__", {}); fresh = c.pop("__fresh__", False)
    d = os.path.join(out, name)
    write(d, c, links)
    for k, cl in enumerate(cmdlines):
        rp = os.path.join(refdir, f"{name}.{k}.json")
        if rerun or not os.path.exists(rp):
            if fresh: write(d, c, links)
            r = subprocess.run(["node", KNIP] + cl, cwd=d, capture_output=True, text=True)
            json.dump({"args": cl, "out": r.stdout, "err": r.stderr, "code": r.returncode, "tree": tree(d) if fresh else None}, open(rp, "w"))
        ref = json.load(open(rp))
        if not VK: continue
        total += 1
        if fresh: write(d, c, links)
        r = subprocess.run([VK] + cl, cwd=d, capture_output=True, text=True)
        tdiff = []
        if fresh:
            got = tree(d); want = ref.get("tree") or {}
            tdiff = sorted(f for f in set(got) | set(want) if got.get(f) != want.get(f))
        ok = r.stdout == ref["out"] and r.stderr == ref["err"] and r.returncode == ref["code"] and not tdiff
        same += ok
        if not ok:
            what = []
            if r.stdout != ref["out"]: what.append("stdout")
            if r.stderr != ref["err"]: what.append("stderr")
            if r.returncode != ref["code"]: what.append(f"exit {ref['code']} vs {r.returncode}")
            if tdiff: what.append("files after: " + " ".join(tdiff))
            print(f"DIFF {name} {' '.join(cl)}: {', '.join(what)}")
            if verbose:
                for l in difflib.unified_diff(ref["out"].split("\n"), r.stdout.split("\n"), "knip", "vknip", lineterm="", n=1): print("   ", l)
                for l in difflib.unified_diff(ref["err"].split("\n"), r.stderr.split("\n"), "knip.err", "vknip.err", lineterm="", n=1): print("   ", l)
                for f in tdiff:
                    for l in difflib.unified_diff((ref["tree"].get(f) or "").split("\n"), (got.get(f) or "").split("\n"), "knip:" + f, "vknip:" + f, lineterm="", n=1): print("   ", l)
if VK: print(f"identical: {same}/{total}")
