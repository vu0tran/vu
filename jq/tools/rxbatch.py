# Regex differential fuzzing in batches: many [pattern, flags, string] cases run by one jq and
# one vjq process (each case in try/catch), so tens of thousands of patterns are cheap.
#   python3 rxbatch.py JQ VJQ N SEED [BATCH]
import json, os, random, subprocess, sys, tempfile
J, V, N, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
BATCH = int(sys.argv[5]) if len(sys.argv) > 5 else 500
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

PROG = '.[] | . as [$s, $p, $f] | try ([$s | match($p; $f)] | tojson) catch ("ERR " + tostring)'
env = dict(os.environ); env["VJQ_NO_ONIG"] = "1"
last_err = b""
def run(b, data, e=None):
    global last_err
    try:
        p = subprocess.run([b, "-r", PROG], input=data, capture_output=True, env=e, timeout=120)
    except subprocess.TimeoutExpired:
        last_err = b"timeout"
        return ["timeout"]
    last_err = p.stderr
    return p.stdout.decode("utf-8", "surrogateescape").split("\n")
fails = unsup = tot = 0
shown = 0
done = 0
while done < N:
    n = min(BATCH, N - done)
    cases = []
    for _ in range(n):
        p = pat(); f = rnd.choice(FLAGS); s = string()
        cases.append([s, p, f])
    done += n
    data = json.dumps(cases).encode()
    a = run(J, data); b = run(V, data, env)
    if len(a) != len(b):
        print("batch length differs", len(a), len(b), last_err[:300])
        bad = os.path.join(tempfile.gettempdir(), f"rxbatch_bad_{SEED}.json")
        open(bad, "wb").write(data); print("  batch written to", bad)
        fails += n; continue
    for c, x, y in zip(cases, a, b):
        tot += 1
        if "unsupported by vjq" in y: unsup += 1; continue
        if x != y:
            fails += 1
            if shown < 30:
                shown += 1
                print("=== " + json.dumps(c, ensure_ascii=False)); print(" jq: ", x[:400]); print(" vjq:", y[:400])
print(f"{tot - fails - unsup} same, {fails} differ, {unsup} unsupported of {tot} (seed {SEED})")
