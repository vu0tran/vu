# Programs differential test (jq -n): python3 cmp_programs.py JQ VJQ FILE, one program per line
# ("\\n" for a newline); e.g. ../tests/syntax_errors.txt.
import subprocess, sys
J, V, F = sys.argv[1], sys.argv[2], sys.argv[3]
same = 0; tot = 0
for line in open(F, encoding="utf-8", errors="surrogateescape"):
    prog = line.rstrip("\n").replace("\\n", "\n")
    if not prog.strip(): continue
    tot += 1
    a = subprocess.run(["jq", "-n", prog], executable=J, capture_output=True, timeout=10)
    b = subprocess.run(["jq", "-n", prog], executable=V, capture_output=True, timeout=10)
    if (a.returncode, a.stdout, a.stderr) == (b.returncode, b.stdout, b.stderr): same += 1
    else:
        print("=== " + repr(prog)); print("jq: ", a.returncode, a.stdout[:300], a.stderr.decode(errors="replace")[:1500]); print("vjq:", b.returncode, b.stdout[:300], b.stderr.decode(errors="replace")[:1500])
print(f"{same}/{tot} same")
