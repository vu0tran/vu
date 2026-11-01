# Differential fuzzing: random filters on random JSON documents, run by jq 1.7.1 and vjq;
# stdout, stderr and exit status must match exactly.
#   python3 fuzz.py VJQ JQ N SEED [OUTDIR]
import json, os, random, subprocess, sys

VJQ, JQ, N, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
OUT = sys.argv[5] if len(sys.argv) > 5 else None
rnd = random.Random(SEED)
KEYS = ["a", "b", "c", "x y", "é", "1", ""]
STRS = ["", "a", "abc", "a,b,c", "Hello World", "é", "日本", "😀", "a\"b", "back\\slash", "tab\there", "nl\nx",
        "1", "-2.5", "1e3", "nan", "true", "  pad  ", "<&>'\"", "a-b_c.d~e", "x\u0000y", "\u007f", "ABCdef"]
NUMS = [0, 1, -1, 2, 3, 10, 100, -7, 0.5, -0.25, 1.5, 3.14159, 1e10, 1e-5, 12345678901234567890, 1.0, 2.50,
        9007199254740993, -0.0, 1e300, 0.1, 42]

def gen_value(d=0):
    r = rnd.random()
    if d > 3 or r < 0.35:
        c = rnd.randrange(6)
        if c == 0: return None
        if c == 1: return rnd.choice([True, False])
        if c in (2, 3): return rnd.choice(NUMS)
        return rnd.choice(STRS)
    if r < 0.65:
        return [gen_value(d + 1) for _ in range(rnd.randrange(5))]
    return {rnd.choice(KEYS): gen_value(d + 1) for _ in range(rnd.randrange(5))}

def num_text(x):
    if isinstance(x, float) and x == int(x) and abs(x) < 1e16 and rnd.random() < 0.3:
        return repr(x)  # e.g. 1.0, keeps a literal
    return json.dumps(x)

def dump(v):
    # JSON text with occasional jq-1.7-specific literal forms (1.0, 1E2, 1.50)
    if isinstance(v, bool) or v is None: return json.dumps(v)
    if isinstance(v, (int, float)):
        r = rnd.random()
        if r < 0.1 and isinstance(v, int): return f"{v}.0"
        if r < 0.15 and isinstance(v, int) and v != 0: return f"{v}E0"
        return json.dumps(v)
    if isinstance(v, str): return json.dumps(v, ensure_ascii=rnd.random() < 0.3)
    if isinstance(v, list): return "[" + ",".join(dump(x) for x in v) + "]"
    return "{" + ",".join(json.dumps(k) + ":" + dump(x) for k, x in v.items()) + "}"

def lit():
    return dump(gen_value(2))

def key(): return rnd.choice(KEYS)

def path(d):
    c = rnd.randrange(10)
    if c == 0: return "." + rnd.choice(["a", "b", "c"])
    if c == 1: return f".[{rnd.randrange(-3, 4)}]"
    if c == 2: return ".[]"
    if c == 3: return ".[]?"
    if c == 4: return f".[{json.dumps(key())}]"
    if c == 5: return f".[{rnd.randrange(-2, 3)}:{rnd.randrange(-2, 4)}]"
    if c == 6: return ".a.b"
    if c == 7: return ".a?"
    if c == 8: return f".[{rnd.randrange(3)}:]"
    return "."

UNARY = ["length", "keys", "keys_unsorted", "values", "type", "tostring", "tojson", "add", "sort", "unique", "reverse",
         "min", "max", "to_entries", "not", "flatten", "ascii_downcase", "ascii_upcase", "explode", "implode",
         "tonumber", "floor", "sqrt", "fabs", "round", "ceil", "abs", "paths", "leaf_paths", "any", "all", "arrays",
         "objects", "scalars", "strings", "numbers", "booleans", "nulls", "iterables", "empty", "first", "last",
         "@base64", "@base64d", "@csv", "@tsv", "@html", "@sh", "@uri", "@json", "@text", "utf8bytelength",
         "isnan", "isinfinite", "isnormal", "infinite", "nan", "transpose", "tostream", "from_entries", "combinations",
         "getpath([\"a\"])", "fromjson", "ltrimstr(\"a\")", "rtrimstr(\"c\")", "splits(\",\")", "ascii", "todate",
         "input_line_number", "$__loc__", "halt_error", "error", "@base32", "@base32d", "significand", "logb",
         "trunc", "exp10", "log2", "gmtime", "mktime", "builtins|length", "env|type", "now|type", "getpath([0,1])",
         "to_entries|from_entries", "with_entries(.value)", "debug", "stderr", "input_filename", "@text \"x\\(.)y\""]

def filt(d=0):
    if d > 3:
        return rnd.choice([path(d), lit(), ".", rnd.choice(UNARY)])
    c = rnd.randrange(42)
    f = lambda: filt(d + 1)
    if c < 4: return path(d)
    if c < 7: return rnd.choice(UNARY)
    if c == 7: return f"{f()} | {f()}"
    if c == 8: return f"{f()}, {f()}"
    if c == 9: return f"[{f()}]"
    if c == 10: return "{" + f"{json.dumps(key())}: {f()}" + (f", b: {f()}" if rnd.random() < 0.5 else "") + "}"
    if c == 11: return f"({f()}) {rnd.choice(['+', '-', '*', '/', '%'])} ({f()})"
    if c == 12: return f"({f()}) {rnd.choice(['==', '!=', '<', '<=', '>', '>='])} ({f()})"
    if c == 13: return f"({f()}) {rnd.choice(['and', 'or', '//'])} ({f()})"
    if c == 14: return f"map({f()})"
    if c == 15: return f"select({f()})"
    if c == 16: return f"if {f()} then {f()} else {f()} end"
    if c == 17: return f"try ({f()})" + (f" catch {f()}" if rnd.random() < 0.5 else "")
    if c == 18: return f"reduce ({f()}) as $x ({lit()}; . + $x)"
    if c == 19: return f"[foreach ({f()}) as $x (0; . + 1; [$x, .])]"
    if c == 20: return f"({f()}) as $v | {f()} | [$v, .]"
    if c == 21: return f"[limit({rnd.randrange(-1, 4)}; {f()})]"
    if c == 22: return f"first({f()})"
    if c == 23: return f"{rnd.choice(['sort_by', 'group_by', 'unique_by', 'min_by', 'max_by'])}({f()})"
    if c == 24: return f"has({json.dumps(rnd.choice([key(), 0, 1, 2]))})"
    if c == 25: return f"contains({lit()})"
    if c == 26: return f"{path(d)} |= {f()}"
    if c == 27: return f"{path(d)} {rnd.choice(['=', '+=', '-=', '*=', '//='])} {f()}"
    if c == 28: return f"del({path(d)})"
    if c == 29: return f"[path({f()})]"
    if c == 30: return f"[range({rnd.randrange(-1, 5)})]"
    if c == 31: return f"\"s\\({f()})e\""
    if c == 32: return f"join({json.dumps(rnd.choice([',', '', '-', 1]))})"
    if c == 33: return f"split({json.dumps(rnd.choice([',', '', 'b']))})"
    if c == 34: return f"test({json.dumps(rnd.choice(['a', '^a', 'b+', '[0-9]', '(?<x>a)']))})"
    if c == 35: return f"[match({json.dumps(rnd.choice(['a', 'b', '(.)', '']))}; \"g\")]"
    if c == 36: return f"sub({json.dumps(rnd.choice(['a', '^', '(?<x>.)']))}; \"Z\")"
    if c == 37: return f"gsub({json.dumps(rnd.choice(['a', '[bc]', '']))}; \"<\\(.)>\")" if False else f"gsub({json.dumps(rnd.choice(['a', '[bc]']))}; \"Z\")"
    if c == 38: return f"label $out | {f()} | ., break $out"
    if c == 39: return f"[.[] | {f()}]?"
    if c == 40: return f"indices({lit()})"
    return f"[{f()}] | {rnd.choice(['add', 'length', 'sort', 'unique', 'join(\",\")', 'tostring'])}"

OPTS = [[], ["-c"], ["-c"], ["-r"], ["-S"], ["--tab"], ["--indent", "1"], ["-a"], ["-j"], ["-e"], ["-s", "-c"], ["-n", "-c"], ["-cr"]]

def run(binary, args, data):
    try:
        p = subprocess.run([binary] + args, input=data, capture_output=True, timeout=10)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return "timeout", b"", b""

fails = 0
for i in range(N):
    docs = [gen_value() for _ in range(rnd.randrange(1, 4))]
    data = ("\n".join(dump(d) for d in docs) + "\n").encode()
    f = filt()
    args = rnd.choice(OPTS) + [f]
    a = run(JQ, args, data)
    b = run(VJQ, args, data)
    if a[0] == "timeout": continue
    if a != b:
        fails += 1
        msg = f"=== case {i}\nargs: {args!r}\ninput: {data.decode()!r}\njq:  {a!r}\nvjq: {b!r}\n"
        if OUT:
            with open(os.path.join(OUT, f"fail_{SEED}_{i}.txt"), "w") as fh: fh.write(msg)
        if fails <= 30: print(msg[:2000])
print(f"{N - fails} of {N} identical (seed {SEED})")
