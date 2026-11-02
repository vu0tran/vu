# Module differential test: python3 mod_test.py JQ VJQ [CASES]. Each case line is a shell-quoted
# argument list run in tests/mods (HOME=tests/mods/home; "ENV:K=V" sets a variable, $WD
# standing for tests/mods, "UNSET:K" removes one) by jq and vjq under the name "jq";
# stdout, stderr and exit status must match.
import os, shlex, subprocess, sys
d = os.path.dirname(os.path.abspath(__file__))
J, V = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
cf = sys.argv[3] if len(sys.argv) > 3 else os.path.join(d, "../tests/mods/cases.txt")
wd = os.path.join(d, "../tests/mods")
env = dict(os.environ, HOME=os.path.join(wd, "home"))
same = tot = 0
for line in open(cf, encoding="utf-8"):
    if not line.strip() or line.startswith("##"): continue
    args = shlex.split(line)
    e = dict(env)
    while args and (args[0].startswith("ENV:") or args[0].startswith("UNSET:")):
        a = args.pop(0)
        if a.startswith("ENV:"):
            k, v = a[4:].split("=", 1); e[k] = v.replace("$WD", wd)
        else: e.pop(a[6:], None)
    tot += 1
    r = []
    for b in (J, V):
        p = subprocess.run(["jq"] + args, executable=b, cwd=wd, env=e, capture_output=True, timeout=10, stdin=subprocess.DEVNULL)
        r.append((p.returncode, p.stdout, p.stderr))
    if r[0] == r[1]: same += 1
    else:
        print("=== " + line.rstrip())
        for n, x in zip(("jq: ", "vjq:"), r): print(n, x[0], x[1][:400], x[2].decode(errors="replace")[:1500])
print(f"{same}/{tot} same")
