"""Vu's text functions against Python's on random strings: s.upper(), s.lower(), s.chars(),
s.char_count(), s.is_utf8(), s.find(a), s.find(a, start), s.count(a), s.replace(a, b), ord, chr and `a in s`.
Strings mix ASCII, Latin, Greek, Cyrillic, CJK, emoji, combining marks and characters whose case
changes length (ß, ŉ, ǰ), and some aren't UTF-8 at all (Vu reads those as Python's
decode(errors="replace") does). Run under the sanitizers too."""
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
N = int(os.environ.get('N', '3000'))
rng = random.Random(int(os.environ.get('SEED', '7')))
POOL = ('abcxyzABCXYZ 019,.-' 'àéîõüÀÉÎÕÜßÿŸ' 'ŉǰΐΰ' 'αβγδΩΣσςάέ' 'жЖщЩёЁ' 'ﬁﬃǅǈǋ' 'İı'
        '中文字日本語' '😀🎉👍🏽' 'éä' 'ǆǇǉ' 'ⅰⅱⅲⅠ' 'ẞ')
BAD = [b'\xff', b'\xc3', b'\xe2\x82', b'\xf0\x9f\x98', b'\xed\xa0\x80', b'\xc0\xaf', b'\xf8\x88\x80\x80\x80', b'\x80']


def rand_str(maxlen, bad_ok):
    parts = []
    for _ in range(rng.randint(0, maxlen)):
        if bad_ok and rng.random() < 0.08:
            parts.append(rng.choice(BAD))
        else:
            parts.append(rng.choice(POOL).encode())
    return b''.join(parts)


def py(s, a, b):
    t = s.decode('utf-8', 'replace')
    valid = True
    try:
        s.decode('utf-8')
    except UnicodeDecodeError:
        valid = False
    up = s.upper() if False else None
    # case: Python's str methods on valid text (Vu leaves invalid bytes as they are; Σ always lowers to σ)
    if valid:
        up = t.upper().encode()
        lo = t.lower().replace('ς', '\x00')  # (placeholder, see below)
        lo = ''.join('σ' if ch == 'Σ' else ch.lower() for ch in t).encode() if 'Σ' in t else t.lower().encode()
    chars = [c.encode() for c in t]
    ords = [ord(c) for c in t]
    rt = ''.join(chr(o) for o in ords).encode()
    find = s.find(a)
    if a == b'':
        cnt = len(t) + 1
        rep = (b.decode('utf-8', 'replace').join([''] + list(t) + [''])).encode() if valid and b.decode('utf-8', 'replace').encode() == b else None
    else:
        cnt = s.count(a)
        rep = s.replace(a, b)
    return up if valid else None, lo if valid else None, chars, len(t), valid, find, cnt, rep, ords, rt, a in s


def main():
    work = tempfile.mkdtemp()
    prog = os.path.join(work, 'ops')
    flags = sys.argv[1:]
    r = subprocess.run(VU + ['build', f'{HERE}/text/ops.vu', '-o', prog] + flags, capture_output=True, text=True)
    if r.returncode:
        print('FAIL  build', r.stderr[:500]); sys.exit(1)
    cases = []
    for i in range(N):
        bad_ok = i % 3 == 0
        s = rand_str(12, bad_ok)
        if rng.random() < 0.6 and len(s) > 0:
            x = rng.randrange(len(s)); y = min(len(s), x + rng.randint(0, 3))
            a = s[x:y]
        else:
            a = rand_str(2, False)
        b = rand_str(3, False)
        cases.append((s, a, b))
    inp = os.path.join(work, 'in.txt')
    with open(inp, 'w') as f:
        for s, a, b in cases:
            f.write(f'{s.hex() or "-"} {a.hex() or "-"} {b.hex() or "-"}\n'.replace('-', ''))
    r = subprocess.run([prog, inp], capture_output=True, text=True, timeout=300)
    if r.returncode or 'ERROR' in r.stderr or 'runtime error' in r.stderr:
        print('FAIL  run', r.returncode, r.stderr[:800]); sys.exit(1)
    lines = r.stdout.split('\n')
    bad = 0
    for (s, a, b), line in zip(cases, lines):
        f = line.split(' ')
        up, lo, chars, n, valid, find, cnt, rep, ords, rt, has = py(s, a, b)
        got_chars = [bytes.fromhex(x) for x in f[2].split(',')] if f[2] else []
        problems = []
        if valid and bytes.fromhex(f[0]) != up: problems.append(f'upper {bytes.fromhex(f[0])!r} != {up!r}')
        if valid and bytes.fromhex(f[1]) != lo: problems.append(f'lower {bytes.fromhex(f[1])!r} != {lo!r}')
        if got_chars != chars: problems.append(f'chars {got_chars!r} != {chars!r}')
        if int(f[3]) != n: problems.append(f'char_count {f[3]} != {n}')
        if (f[4] == '1') != valid: problems.append(f'is_utf8 {f[4]} != {valid}')
        if int(f[5]) != find: problems.append(f'find {f[5]} != {find}')
        if int(f[6]) != cnt: problems.append(f'count {f[6]} != {cnt}')
        if rep is not None and bytes.fromhex(f[7]) != rep: problems.append(f'replace {bytes.fromhex(f[7])!r} != {rep!r}')
        if f[8] != ','.join(map(str, ords)): problems.append(f'ord {f[8]} != {ords}')
        if bytes.fromhex(f[9]) != rt: problems.append(f'chr {bytes.fromhex(f[9])!r} != {rt!r}')
        if (f[10] == '1') != has: problems.append(f'in {f[10]} != {has}')
        starts = [-3, -1, 0, 1, len(s) // 2, len(s) - 1, len(s), len(s) + 2]
        want_finds = ','.join(str(s.find(a, st)) for st in starts)   # (bytes.find: byte offsets, as Vu's)
        if f[11] != want_finds: problems.append(f'find with a start {f[11]} != {want_finds}')
        if problems:
            bad += 1
            if bad <= 8: print(f'FAIL  s={s!r} a={a!r} b={b!r}: ' + '; '.join(problems))
    total = len(cases)
    print(f'{total - bad} of {total} strings agree with Python ({" ".join(flags) or "optimized"})')
    sys.exit(1 if bad else 0)


main()
