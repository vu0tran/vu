# Interleaving of standard output and standard error in one pipe (2>&1): jq's stdout is
# buffered by glibc, its stderr is not. python3 mix_test.py JQ VJQ
import os, pty, subprocess, sys
J, V = sys.argv[1], sys.argv[2]
cases = [
  (["-c", ".[] | (1 / .)"], b"[1,0,2,0,4]"),
  (["-c", ". + 1"], b'1 "a" 3 {} 5'),
  (["-n", '"out", ("err\\n" | halt_error)'], b""),
  (["-n", '"out", ({"a":1} | halt_error)'], b""),
  (["-n", '1, (2 | debug), 3, ("x" | stderr), 4'], b""),
  (["-n", '[range(300)] | .[] | if . == 150 then error("mid") else "x" * 40 end'], b""),
  (["-n", 'range(2000) | if . % 500 == 499 then debug else . end'], b""),
  (["-n", '"y" * 4095, ("e" | stderr), "z"'], b""),
  (["-n", '"y" * 4094, ("e" | stderr), "z"'], b""),
  (["-n", '"y" * 4096, ("e" | stderr), "z"'], b""),
  (["-rn", '"y" * 8191, ("e" | stderr), "z"'], b""),
  (["-jn", '"a", "b\\nc", ("e" | stderr), "d"'], b""),
  (["--unbuffered", "-c", ". + 1"], b'1 "a" 3'),
  (["-c", "."], b'1 2 [3'),
  (["-c", "."], b'1 2 {"a":'),
  (["--seq", "-c", "."], b'\x1e1\n\x1e[2\n\x1e3\n'),
  (["-n", '[limit(3; inputs)], input'], b"1 2 3"),
  (["-n", '"x", ("bad1" | modulemeta)', "-L", "../tests/mods"], b""),
  (["-n", 'range(5) | tostring | stderr'], b""),
  (["-c", "1, error"], b"5"),
  (["-e", "."], b"1 null"),
]
same = 0
for args, inp in cases:
    r = []
    for b in (J, V):
        p = subprocess.run(["jq"] + args, executable=b, input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        r.append((p.returncode, p.stdout))
    if r[0] == r[1]: same += 1
    else: print("===", args, inp); print(" jq: ", r[0][0], r[0][1][:300]); print(" vjq:", r[1][0], r[1][1][:300])
# on a terminal (stdout and stderr the same pty): glibc buffers stdout by lines
def tty_run(b, args):
    m, s = pty.openpty()
    p = subprocess.Popen(["jq"] + args, executable=b, stdin=subprocess.DEVNULL, stdout=s, stderr=s)
    os.close(s); out = b""
    while True:
        try: d = os.read(m, 65536)
        except OSError: break
        if not d: break
        out += d
    p.wait(); return p.returncode, out
tty_cases = [["-n", '1, (2|debug), 3'], ["-jn", '"a", "b\\nc", ("e"|stderr), "d"'], ["-n", '"x", error("boom")'],
             ["-Cn", '{"a":[1,"x",null,true]}'], ["-n", '"y"*3000, ("e"|stderr)'], ["-n", '"x"'], ["-rn", '"a\\nb", ("e"|stderr)']]
for args in tty_cases:
    a = tty_run(J, args); b = tty_run(V, args)
    if a == b: same += 1
    else: print("=== tty", args); print(" jq: ", a); print(" vjq:", b)
print(f"{same}/{len(cases) + len(tty_cases)} same")
