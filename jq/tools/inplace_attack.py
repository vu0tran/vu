# Attack round for values changed in place or shared: reduces whose updates keep their state
# owned from step to step, `+=` appends, new views over the tail of an array/object/string
# (a + b, .[k] = v past the end), big objects' key indexes shared by such views. Random
# programs keep references to earlier values (init variables, both sides of a sharing) and
# print them all; jq 1.7.1 and vjq must agree on stdout, stderr and status.
#   python3 inplace_attack.py JQ VJQ [N] [SEED]
import os, random, subprocess, sys, tempfile
J, V = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
N = int(sys.argv[3]) if len(sys.argv) > 3 else 500
rnd = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 1)

def key():
    return rnd.choice(['"a"', '"b"', '"k\\($i % 3)"', '"k\\($i % 60)"', '($i % 4 | tostring)', '"x"',
                       '(length % 3 | tostring)', '(keys_unsorted[0] // "a")', '([$i] | tojson)'])
def idx():
    return rnd.choice(['0', '1', '$i', '($i % 3)', '($i % 70)', '-1', '($i + 2)', '5', '(length % 4)', '([$i, 2] | min)'])
def path(d=0):
    p = "."
    for _ in range(rnd.randint(0 if d else 1, 3)):
        if rnd.random() < KEYS: p += "[" + key() + "]"
        else: p += "[" + idx() + "]"
    return p
def val():
    return rnd.choice(['($x | .[0])', '($i | [.] | .[0])', '$i', '[$i]', '{"v": $i}', '"s\\($i)"', 'null', '[$i, [$i]]', '$x', '$x[0]',
                       '[]', '{}', '($i * 2)', '{"k\\($i % 50)": $i}', '[range($i % 5)]'])
def upd():
    if rnd.random() < 0.15:
        return ". + " + rnd.choice(['[$i]', '{"k\\($i % 3)": $i}', '$x', '{}', '[]', '{"a": [$i]}', '$big', '[[$i]]', '{"k\\($i % 70)": [$i]}'])
    if rnd.random() < 0.5:
        # arrays only (few errors): appends, sets past the end, replacements
        p = "." + "".join("[" + key() + "]" for _ in range(rnd.randint(0, 2)))
        return rnd.choice([f"{p} += [$i]", f"{p} += [[$i], $x]", f"{p}[{idx()}] = $i", f"{p} |= . + [$i]",
                           f"{p} = [$i]", f"{p} += $x", f"{p}[{idx()}] += [$i]", f"{p}[{idx()}] |= [$i]"])
    op = rnd.choice(["=", "+=", "|=", "//=", "-=", "*="])
    if op == "|=":
        rhs = rnd.choice(['. + 1', '. + [$i]', '. + "z"', '$i', '[$i]', '. + {"q": $i}', '(. // 0) + 1',
                          '. + $x', '-(. // 0)', '"\\(.)"', '[., .]', '{"w": .}', '($i | [., .])', '($x | .[0])'])
    elif op in ("-=", "*="):
        rhs = rnd.choice(['1', '2', '[$i]', '{"q": 1}', '$x'])
    else:
        rhs = val()
    return f"{path()} {op} {rhs}"
def body():
    return " | ".join(upd() for _ in range(rnd.randint(1, 3)))
def init():
    return rnd.choice(['[]', '{}', 'null', '$x', '[range(5)]', '{"a": [1], "b": {"c": 2}}', '$big', '$x + [9]', '$big + {"zz": 1}'])
KEYS = 0.55
def prog():
    global KEYS
    KEYS = rnd.choice([0.0, 0.55, 1.0, 1.0])
    n = rnd.choice([3, 10, 60, 130])
    form = rnd.randint(0, 5)
    pre = ('[range(3) | [.]] as $x | ([range(55) | {key: "k\\(.)", value: .}] | from_entries) as $big | ')
    b = body()
    if form == 0:
        return pre + f"reduce range({n}) as $i ({init()}; {b}) | [., $x, $big]"
    if form == 1:
        return pre + f"({init()}) as $s | reduce range({n}) as $i ($s; {b}) | [., $s, $x]"
    if form == 2:
        return pre + f"[foreach range({n}) as $i ({init()}; {b})] | [.[-1], length, $x]"
    if form == 3:
        # shared tails: a + b views, then both extended
        return pre + (f"({init()}) as $a | [range({n})] as $r | ($a + [1]) as $p | ($a + [2]) as $q "
                      f"| [$a, $p, $q, ($p + $r | length), ($q | .[0] = 7)]")
    if form == 4:
        return pre + (f"($big + {{\"n1\": 1}}) as $p | ($big + {{\"n2\": 2}}) as $q | ($p | .n2 = 5) as $r "
                      f"| [($p | has(\"n2\")), ($q | has(\"n1\")), $r.n2, ($r | length), ($q | keys | length), $p.k3, "
                      f"(reduce range({n}) as $i ($p; .[\"k\\($i % 70)\"] = $i) | [.k3, .k69, length]), ($p | length)]")
    # a reduce inside a reduce's source and inside a function called again from its source
    return pre + (f"def f($k): reduce range($k) as $i ({init()}; {b}); "
                  f"reduce (range({n} % 7) | f(.)) as $j ([]; . += [$j]) | [., f(3), $x]")

def run(b, p):
    try:
        r = subprocess.run([b, "-nc", p], capture_output=True, timeout=20)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return "timeout", b"", b""
bad = 0
for t in range(N):
    p = prog()
    a = run(J, p); b = run(V, p)
    if a[0] == "timeout": continue
    if a != b:
        bad += 1
        if bad <= 8:
            print("DIFF:", p); print("  jq :", a[0], a[1][:300], a[2][:200]); print("  vjq:", b[0], b[1][:300], b[2][:200])
print(f"{N - bad}/{N} same")
