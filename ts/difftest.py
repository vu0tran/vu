"""Compares vtsc with tsc on generated programs: python3 difftest.py SEED COUNT [VTSC] [TSC]
Prints the files whose errors differ (first lines only) and a summary."""
import subprocess, sys, os, collections, tempfile, shutil, time
here = os.path.dirname(os.path.abspath(__file__))
seed, count = int(sys.argv[1]), int(sys.argv[2])
pos = [a for a in sys.argv[1:] if not a.startswith("--")]
vtsc = pos[2] if len(pos) > 2 else "vtsc"
tsc = pos[3] if len(pos) > 3 else "tsc"
d = tempfile.mkdtemp()
subprocess.run([sys.executable, os.path.join(here, "gen.py"), str(seed), str(count), d] + [a for a in sys.argv if a in ("--modules", "--classes")], check=True)
files = sorted(os.path.join(d, f) for f in os.listdir(d))
def run(cmd):
    t = time.time()
    p = subprocess.run(cmd + files, capture_output=True, text=True)
    return p.stdout, p.stderr, time.time() - t
tout, terr, tt = run([tsc, "--noEmit", "--strict", "--pretty", "false"])
vout, verr, vt = run([vtsc])
def by_file(out):
    m = collections.defaultdict(list)
    for line in out.splitlines():
        if line.startswith(" ") or "): error TS" not in line: continue
        f = os.path.basename(line.split("(")[0])
        m[f].append(os.path.basename(line))
    return m
want, got = by_file(tout), by_file(vout)
skipped = set()
for line in verr.splitlines():
    if ": not checked: " in line: skipped.add(os.path.basename(line.split(": ")[1]))
bad = 0
reasons = collections.Counter()
for line in verr.splitlines():
    if ": not checked: uses " in line: reasons[line.split("uses ")[1].rsplit(" at ", 1)[0]] += 1
for path in files:
    f = os.path.basename(path)
    if f in skipped: continue
    if want.get(f, []) != got.get(f, []):
        bad += 1
        if bad <= int(os.environ.get("SHOW", "6")):
            print("==", f)
            print(open(path).read())
            for l in want.get(f, []):
                if l not in got.get(f, []): print("  tsc only: ", l)
            for l in got.get(f, []):
                if l not in want.get(f, []): print("  vtsc only:", l)
checked = len(files) - len(skipped)
nerr = sum(len(want.get(os.path.basename(f), [])) for f in files if os.path.basename(f) not in skipped)
print(f"{checked} of {len(files)} programs checked ({nerr} errors expected), {checked - bad} identical, {bad} differ; {len(skipped)} not checked")
for r, n in reasons.most_common(5): print(f"   not checked: {n} use {r}")
print(f"time: tsc {tt:.2f} s, vtsc {vt:.2f} s")
if "--keep" not in sys.argv: shutil.rmtree(d)
sys.exit(1 if bad else 0)
