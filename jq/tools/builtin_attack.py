# Every builtin on inputs and arguments of every type (wrong ones included): one jq program per
# builtin, each call in try/catch; jq 1.7.1 and vjq must print the same.
#   python3 builtin_attack.py JQ VJQ
import itertools, json, os, subprocess, sys, tempfile
J, V = sys.argv[1], sys.argv[2]
names = json.loads(subprocess.run([J, "-nc", "builtins"], capture_output=True).stdout)
skip = {"input/0", "inputs/0", "halt/0", "halt_error/0", "halt_error/1", "now/0", "debug/0", "debug/1",
        "stderr/0", "input_line_number/0", "get_jq_origin/0", "get_prog_origin/0", "localtime/0",
        "strflocaltime/1", "builtins/0", "input_filename/0", "env/0"}
inputs = ['null', 'false', 'true', '0', '-1', '1.5', '1e300', '-0', '"abc"', '""', '"a,b"', '"2015-03-05T23:51:47Z"',
          '[]', '[1,2,"a",null]', '[[1,2],[3]]', '[3,1,2]', '{}', '{"a":1,"b":[2]}', '[{"a":1},{"a":2}]', '(nan)', '(infinite)']
args = ['.', '1', '"a"', 'null', '[1,2]', '{"a":1}', 'empty', '(1,2)', '"x", 3', '-1', '"%Y-%m-%d"', '"a|b"', '[["a"]]', '0']
total = same = 0
for nm in sorted(names):
    if nm in skip: continue
    name, ar = nm.split("/"); ar = int(ar)
    if ar == 0: arg_sets = [()]
    elif ar == 1: arg_sets = [(a,) for a in args]
    elif ar == 2: arg_sets = [(a, b) for a in args[:8] for b in args[:8]]
    else: arg_sets = [(a, b, c) for a in args[:5] for b in args[:5] for c in args[:5]]
    exprs = []
    for x in inputs:
        for a in arg_sets:
            call = name if ar == 0 else name + "(" + "; ".join(a) + ")"
            exprs.append(f'(try ([limit(5; {x} | {call})] | tojson) catch ("ERR: " + tostring))')
    for c0 in range(0, len(exprs), 150):
        chunk = exprs[c0:c0 + 150]
        prog = ",\n".join(chunk)
        pf = tempfile.NamedTemporaryFile("w", suffix=".jq", delete=False); pf.write(prog); pf.close()
        r = []
        try:
            for b in (J, V):
                p = subprocess.run([b, "-nr", "-f", pf.name], capture_output=True, timeout=60)
                r.append((p.returncode, p.stdout.split(b"\n"), p.stderr))
        except subprocess.TimeoutExpired:
            print("=== " + nm + " timeout (chunk %d)" % c0)
            os.unlink(pf.name)
            continue
        os.unlink(pf.name)
        total += len(chunk)
        if r[0] == r[1]:
            same += len(chunk); continue
        if len(r[0][1]) != len(r[1][1]) or r[0][0] != r[1][0] or r[0][2] != r[1][2]:
            print("=== " + nm, "rc", r[0][0], r[1][0], r[0][2][:300], r[1][2][:300], len(r[0][1]), len(r[1][1]))
            continue
        k = 0
        for e, a, b in zip(chunk, r[0][1], r[1][1]):
            if a == b: same += 1
            else:
                k += 1
                if k <= 3: print("=== " + nm + ": " + e.replace("\n", " ")); print(" jq: ", a[:300]); print(" vjq:", b[:300])
print(f"{same}/{total} same")
