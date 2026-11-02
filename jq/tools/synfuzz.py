# Syntax fuzzing: valid-looking jq programs mutated at the token level (delete, duplicate,
# insert, swap tokens), run with -n by jq and vjq; stdout, stderr, status must match.
import random, re, subprocess, sys
J, V, N, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
rnd = random.Random(SEED)
BASE = [
 '.a | .b', '{a: 1, "b": 2, (.c): 3, $__loc__, @base64: 1}', 'if . then 1 elif . then 2 else 3 end',
 'try error("x") catch .', 'reduce range(3) as $x (0; . + $x)', 'foreach .[] as [$a, $b] (0; 1; 2)',
 'def f(g; $x): g + $x; f(1; 2)', '[.[] | select(. > 1)]', '"a\\(1 + 2)b" | @base64 "x\\(.)y"',
 'label $out | 1, break $out', '. as {a: $x, $y, "z": [$w]} ?// [$x] | $x', '.[1:2], .[:3], .[2:]?',
 'import "m" as m; include "n"; .', 'module {a: 1}; def f: 1; .', '.a.b?.c[0]."d"', '$__loc__ | .file',
 'path(..) | length', '.x |= . + 1 | .y += 2 | .z //= 3', 'not, -1, 1 - -2, .a and .b or .c',
 '{(1, 2): 3}', '[limit(3; .[])]', 'reduce .[] as {a: $a} ({}; .[$a] = 1)', 'def f: def g: 3; g; f',
 '"\\u00e9\\n\\t" | test("a"; "g")', '.[] as $x | $x * 2 // empty', '..|numbers', '@json "a\\(.)"',
]
TOK = re.compile(r'"(?:[^"\\]|\\.)*"|\$__loc__|\?//|//=|\|=|\+=|-=|\*=|/=|%=|==|!=|<=|>=|//|\.\.|[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*|\$[A-Za-z_][A-Za-z0-9_]*|@[A-Za-z0-9_]+|\.[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?|\S')
EXTRA = ['(', ')', '[', ']', '{', '}', ',', ':', ';', '|', 'if', 'then', 'else', 'end', 'try', 'catch', 'as', 'def',
         '.', '..', '$x', '"s"', '"\\(', '1', 'reduce', 'foreach', 'import', 'module', 'label', 'break', '?', '=',
         '+', '-', '*', '/', '%', 'and', 'or', '$', '@text', '\\', '!', '#', '"\\q"', 'elif', '?//', 'include',
         '.a', 'f', 'x::y', '$__loc__', '==', '//', '|=']
def mutate(p):
    t = TOK.findall(p)
    for _ in range(rnd.randrange(1, 4)):
        c = rnd.randrange(5)
        i = rnd.randrange(len(t) + 1)
        if c == 0 and t: del t[min(i, len(t) - 1)]
        elif c == 1 and t: t.insert(i, t[min(i, len(t) - 1)])
        elif c == 2: t.insert(i, rnd.choice(EXTRA))
        elif c == 3 and len(t) > 1:
            j = rnd.randrange(len(t)); k = rnd.randrange(len(t)); t[j], t[k] = t[k], t[j]
        else:
            t = t[:i]
    sep = rnd.choice([' ', '', ' ', '\n'])
    return sep.join(t)
fails = 0; e3 = 0; multi = 0
for n in range(N):
    p = mutate(rnd.choice(BASE))
    a = subprocess.run([J, '-n', p], capture_output=True, timeout=10)
    b = subprocess.run([V, '-n', p], capture_output=True, timeout=10)
    e3 += a.returncode == 3; multi += b"compile errors" in a.stderr
    if (a.returncode, a.stdout, a.stderr) != (b.returncode, b.stdout, b.stderr):
        fails += 1
        if fails <= 25:
            print('=== ' + repr(p)); print('jq: ', a.returncode, a.stdout[:200], a.stderr.decode(errors='replace')[:1200]); print('vjq:', b.returncode, b.stdout[:200], b.stderr.decode(errors='replace')[:1200])
print(f"{N - fails}/{N} same (seed {SEED}); {e3} compile errors, {multi} with several")
