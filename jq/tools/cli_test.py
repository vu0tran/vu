# Command-line differential test: python3 cli_test.py JQ VJQ [CASES]. Each case line is an
# argument list (standard input from in1.json, or "<FILE args"; "ENV:K=V" sets a variable), run
# in tests/cli by jq and vjq under the program name "jq"; stdout, stderr and status must match.
import os, subprocess, sys, shlex
J, V = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "cli")
if len(sys.argv) < 4: sys.argv.append(os.path.join(d, "cases.txt"))
cases = [l.rstrip("\n") for l in open(sys.argv[3]) if l.strip() and not l.startswith("##")]
same = 0
for c in cases:
    stdin_file = "in1.json"
    env = dict(os.environ)
    if c.startswith("<"):
        stdin_file, c = c[1:].split(" ", 1)
    while c.startswith("ENV:"):
        kv, c = c[4:].split(" ", 1)
        k, v = kv.split("=", 1); env[k] = v
    args = shlex.split(c)
    res = []
    for x in ("a", "b"):
        with open(f"{d}/{stdin_file}", "rb") as fin:
            r = subprocess.run(["jq"] + args, executable=(J if x == "a" else V), stdin=fin, capture_output=True, cwd=d, env=env, timeout=10)
        res.append((r.returncode, r.stdout, r.stderr))
    if res[0] == res[1]: same += 1
    else:
        print("=== " + c); print(" jq: ", str(res[0])[:600]); print(" vjq:", str(res[1])[:600])
print(f"{same}/{len(cases)} same")
