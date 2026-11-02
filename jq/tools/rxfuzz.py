# Regex differential fuzzing: random Oniguruma (Perl_NT) patterns and strings, [match(re; flags)]
# by jq 1.7.1 (its bundled Oniguruma) and by vjq with its own engine only (VJQ_NO_ONIG=1).
import json, os, random, subprocess, sys
J, V, N, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
rnd = random.Random(SEED)
ALPHA = "abcAB01 _\n-.é日Éß"
def lit():
    return rnd.choice(["a", "b", "c", "A", "B", "0", "1", " ", "_", "-", "é", "日", "\\.", "\\-", "\\n", "\\t", "x", "É", "ß", "\\x41", "\\x{e9}", "\\u", "\\101", "\\cA", "k", "\\*", "\\$"])
def cls():
    items = []
    for _ in range(rnd.randrange(1, 4)):
        c = rnd.randrange(8)
        if c == 0: items.append("a-c")
        elif c == 1: items.append("\\d")
        elif c == 2: items.append("\\w")
        elif c == 3: items.append("[:alpha:]")
        elif c == 4: items.append("\\s")
        elif c == 5: items.append(rnd.choice(["é", "日", "A-Z", "0-9", "_", "\\-", "-", "]", "^", "\\]", "\\p{L}", "\\P{Ll}", "[:^digit:]", "\\n"]))
        else: items.append(rnd.choice("abcAB01 "))
    neg = "^" if rnd.random() < 0.3 else ""
    return "[" + neg + "".join(items) + "]"
def atom(d):
    a = atom0(d)
    return a
def atom0(d):
    c = rnd.randrange(16)
    if c < 5 or d > 3: return lit()
    if c == 5: return cls()
    if c == 6: return rnd.choice([".", "\\w", "\\W", "\\d", "\\D", "\\s", "\\S", "\\p{Lu}", "\\p{^L}", "\\N", "\\O", "\\R", "\\h"])
    if c == 7: return rnd.choice(["^", "$", "\\b", "\\B", "\\A", "\\z", "\\Z", "\\G"]) + ("" if rnd.random() < 0.9 else "*")
    if c == 8: return "(" + pat(d + 1) + ")"
    if c == 9: return "(?:" + pat(d + 1) + ")"
    if c == 10: return "(?<" + rnd.choice(["x", "y", "n1"]) + ">" + pat(d + 1) + ")"
    if c == 11: return rnd.choice(["(?=", "(?!", "(?<=", "(?<!"]) + seqfixed() + ")"
    if c == 12: return "(?>" + pat(d + 1) + ")"
    if c == 13: return rnd.choice(["\\1", "\\2", "\\k<x>"])
    if c == 14: return rnd.choice(["(?i)", "(?-i)", "(?m)", "(?s)", "(?i:" + pat(d + 1) + ")", "(?x: a b )", "\\Qa.b\\E", "\\K"])
    return lit()
def seqfixed():
    return "".join(rnd.choice(["a", "b", ".", "\\d", "[ab]", "é", "\\b", "^"]) for _ in range(rnd.randrange(1, 3)))
def quant():
    return quant0()
def quant0():
    c = rnd.randrange(14)
    if c < 7: return ""
    if rnd.random() < 0.05: return rnd.choice(["{3,1}", "{,2}", "{0}"])
    return rnd.choice(["*", "+", "?", "*?", "+?", "??", "*+", "++", "{2}", "{1,2}", "{0,}", "{2,}?", "{1,3}+"])
def pat(d=0):
    alts = []
    for _ in range(1 if rnd.random() < 0.7 else rnd.randrange(2, 4)):
        parts = []
        for _ in range(rnd.randrange(1, 4)):
            a = atom(d)
            q = quant()
            if (a.startswith("(?=") or a.startswith("(?!") or a.startswith("(?<=") or a.startswith("(?<!") or a in ("^", "$", "\\b", "\\B", "\\A", "\\z", "\\Z", "\\G", "\\K", "(?i)", "(?-i)", "(?m)", "(?s)")) and rnd.random() < 0.9:
                q = ""
            parts.append(a + q)
        alts.append("".join(parts))
    return "|".join(alts)
def string():
    return "".join(rnd.choice(ALPHA) for _ in range(rnd.randrange(0, 9)))
FLAGS = [None, "g", "gi", "gx", "gn", "gs", "gp", "gl", "i", "gil", "gin"]
def run(b, prog, env=None):
    try:
        p = subprocess.run([b, "-nc", prog], capture_output=True, timeout=10, env=env)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return "timeout", b"", b""
env = dict(os.environ); env["VJQ_NO_ONIG"] = "1"
fails = unsup = 0
for i in range(N):
    p = pat()
    f = rnd.choice(FLAGS)
    strs = [string() for _ in range(3)]
    fl = "null" if f is None else json.dumps(f)
    prog = f"{json.dumps(strs)} | map([match({json.dumps(p)}; {fl})])"
    a = run(J, prog)
    b = run(V, prog, env)
    if b"unsupported by vjq" in b[2]:
        unsup += 1
        continue
    if a != b:
        fails += 1
        if fails <= 20:
            print("=== " + prog); print(" jq: ", a[0], a[1][:600], a[2][:300]); print(" vjq:", b[0], b[1][:600], b[2][:300])
print(f"{N - fails - unsup} same, {fails} differ, {unsup} unsupported of {N} (seed {SEED})")
