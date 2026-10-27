"""std/re against Python's re (with re.ASCII) on random patterns and texts: search, match (prefix),
fullmatch spans and groups, findall, sub and split; texts include non-ASCII characters and newlines.
Also: patterns that take exponential time in backtracking engines run in linear time here."""
import os
import random
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
N = int(os.environ.get('N', '2500'))
rng = random.Random(int(os.environ.get('SEED', '5')))
ATOMS = ['a', 'b', 'c', '.', '[ab]', '[^a]', '[a-c]', r'\d', r'\w', r'\s', r'\W', 'é', '1', r'\.', ' ', '[é1]', r'[\d_]', r'[^\s]']


def gen(depth=0):
    r = rng.random()
    if depth > 2 or r < 0.35:
        x = rng.choice(ATOMS)
    elif r < 0.5:
        x = '(' + gen(depth + 1) + ')'
    elif r < 0.6:
        x = '(?:' + gen(depth + 1) + ')'
    elif r < 0.75:
        x = gen(depth + 1) + gen(depth + 1)
    else:
        x = gen(depth + 1) + '|' + gen(depth + 1)
        if depth > 0:
            x = '(' + x + ')'
    q = rng.random()
    if x[-1] in '*+?}' and not x.endswith('\\' + x[-1]) and rng.random() < 0.9:
        x = '(?:' + x + ')'   # mostly no repeat right after a repeat (Python: possessive, or an error)
    if q < 0.12: x = '(?:' + x + ')*' if '|' in x and not x.startswith('(') else x + '*'
    elif q < 0.2: x = '(?:' + x + ')+' if '|' in x and not x.startswith('(') else x + '+'
    elif q < 0.27: x = '(?:' + x + ')?' if '|' in x and not x.startswith('(') else x + '?'
    elif q < 0.31: x = '(?:' + x + '){1,2}' if '|' in x and not x.startswith('(') else x + '{1,2}'
    elif q < 0.35: x = '(?:' + x + ')*?' if '|' in x and not x.startswith('(') else x + '*?'
    elif q < 0.38: x = '(?:' + x + ')+?' if '|' in x and not x.startswith('(') else x + '+?'
    return x


def pattern():
    p = gen()
    if rng.random() < 0.15: p = '^' + p
    if rng.random() < 0.15: p = p + '$'
    if rng.random() < 0.1: p = r'\b' + p
    return p


def text():
    return ''.join(rng.choice('abc1 é\n_.') for _ in range(rng.randint(0, 10)))


def bspan(s, a, b):
    if a < 0: return '-1:-1'
    return f'{len(s[:a].encode())}:{len(s[:b].encode())}'


def spans(s, m):
    parts = [bspan(s, m.start(), m.end())]
    for k in range(1, len(m.groups()) + 1):
        parts.append(bspan(s, m.start(k), m.end(k)) if m.start(k) >= 0 else '-1:-1')
    return ','.join(parts)


def py(p, s):
    try:
        r = re.compile(p, re.ASCII)
    except re.error:
        return 'error'
    if 'POSSESSIVE_REPEAT' in str(re._parser.parse(p)):
        return 'error'   # std/re refuses possessive repeats (they need backtracking)
    a = spans(s, m) if (m := r.search(s)) else '-'
    b = spans(s, m) if (m := r.match(s)) else '-'
    c = spans(s, m) if (m := r.fullmatch(s)) else '-'
    fa = []
    for x in r.findall(s):
        fa.append('\t'.join(x) if isinstance(x, tuple) else x)
    repl = r'<\1>' if r.groups >= 1 else '<>'
    sb = r.sub(repl, s)
    sp = [x if x is not None else '' for x in r.split(s)]
    return ' '.join([a, b, c, '\n'.join(fa).encode().hex(), sb.encode().hex(), '\n'.join(sp).encode().hex()])


def main():
    work = tempfile.mkdtemp()
    flags = sys.argv[1:]
    prog = os.path.join(work, 'ops')
    r = subprocess.run(VU + ['build', f'{HERE}/re/ops.vu', '-o', prog] + flags, capture_output=True, text=True)
    if r.returncode:
        print('FAIL  build', r.stderr[:500]); sys.exit(1)
    cases = [(pattern(), text()) for _ in range(N)]
    inp = os.path.join(work, 'in.txt')
    with open(inp, 'w') as f:
        for p, s in cases:
            f.write(p.encode().hex() + ' ' + s.encode().hex() + '\n')
    r = subprocess.run([prog, inp], capture_output=True, text=True, timeout=600)
    if r.returncode or 'ERROR' in r.stderr or 'runtime error' in r.stderr:
        print('FAIL  run', r.returncode, r.stderr[:800]); sys.exit(1)
    bad = 0
    for (p, s), got in zip(cases, r.stdout.split('\n')):
        want = py(p, s)
        if got != want:
            bad += 1
            if bad <= 8: print(f'FAIL  pattern {p!r} text {s!r}\n      got  {got}\n      want {want}')
    # linear time: (a|a)*b and (a*)*b on 30,000 a's (exponential for backtracking matchers)
    big = 'a' * 30000
    slow_in = os.path.join(work, 'slow.txt')
    with open(slow_in, 'w') as f:
        for p in ['(a|a)*b', '(a*)*b', '(a+)+$x']:
            f.write(p.encode().hex() + ' ' + big.encode().hex() + '\n')
    t = time.time()
    r2 = subprocess.run([prog, slow_in], capture_output=True, text=True, timeout=120)
    dt = time.time() - t
    ok_slow = r2.returncode == 0 and dt < 60 and r2.stdout.count('\n') == 3
    if not ok_slow: bad += 1; print(f'FAIL  linear time: {dt:.1f} s, exit {r2.returncode}')
    print(f'{N + 1 - bad} of {N + 1} agree with Python ({" ".join(flags) or "optimized"}; pathological patterns took {dt:.2f} s)')
    sys.exit(1 if bad else 0)


main()
