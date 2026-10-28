"""s.normalize() against Python's unicodedata.normalize, in all four forms: every code point (in lines
of 64, so neighbours interact too), and 30,000 random lines mixing characters that decompose,
combining marks in every class, Hangul syllables and jamo, and ASCII; then bytes that aren't UTF-8
(kept as they are). Extra arguments (--san) go to the build."""
import os, random, subprocess, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, check, counts  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'text', 'normalize.vu'))
rng = random.Random(int(os.environ.get('SEED', '5')))
cps = [c for c in range(1, 0x110000) if not (0xD800 <= c <= 0xDFFF) and c != 10 and c != 9 and unicodedata.category(chr(c)) != 'Cn']
lines = [''.join(chr(c) for c in cps[i:i + 64]) for i in range(0, len(cps), 64)]
decomp = [c for c in cps if unicodedata.decomposition(chr(c))]
marks = [c for c in cps if unicodedata.combining(chr(c))]
hangul = list(range(0xAC00, 0xD7A4, 7)) + list(range(0x1100, 0x1113)) + list(range(0x1161, 0x1176)) + list(range(0x11A8, 0x11C3))
pools = [decomp, marks, hangul, list(range(0x20, 0x7F)), cps]
for _ in range(30000):
    n = rng.randint(1, 12)
    lines.append(''.join(chr(rng.choice(rng.choice(pools))) for _ in range(n)))
forms = ['NFC', 'NFD', 'NFKC', 'NFKD']
data = '\n'.join(lines).encode('utf-8', 'surrogatepass') + b'\n'
r = subprocess.run([exe], input=data, capture_output=True, timeout=600)
got = r.stdout.decode('utf-8', 'surrogateescape').split('\n')[:-1]
check('ran', r.returncode == 0 and len(got) == len(lines), f'exit {r.returncode}, {len(got)} lines of {len(lines)}: {r.stderr[-300:]}')
bad = {f: [] for f in forms}
for line, g in zip(lines, got):
    parts = g.split('\t')
    for f, p in zip(forms, parts):
        want = unicodedata.normalize(f, line)
        if p != want:
            bad[f].append((line, p, want))
for f in forms:
    ex = bad[f][:3]
    check(f'{f}: {len(lines)} lines (every code point, and random mixes) as Python gives them', not bad[f],
          f'{len(bad[f])} differ, e.g. ' + '; '.join(f'{ascii(a)}: got {ascii(b)} want {ascii(c)}' for a, b, c in ex))
# bytes that aren't UTF-8 stay as they are, between normalized text
raw = b'e\xcc\x81\xff\xfe' + 'ﬁ'.encode() + b'\x80A\xcc\x8a\n'
r = subprocess.run([exe], input=raw, capture_output=True, timeout=60)
want = b'\t'.join([b'\xc3\xa9\xff\xfe' + 'ﬁ'.encode() + b'\x80\xc3\x85', b'e\xcc\x81\xff\xfe' + 'ﬁ'.encode() + b'\x80A\xcc\x8a',
                   b'\xc3\xa9\xff\xfefi\x80\xc3\x85', b'e\xcc\x81\xff\xfefi\x80A\xcc\x8a']) + b'\n'
check('bytes that aren\'t UTF-8 are kept, and nothing composes across them', r.stdout == want, f'{r.stdout!r} want {want!r}')
# character classes: one code point per line (all of them), then the random lines
cexe = build(os.path.join(HERE, 'text', 'classes.vu'))
clines = [chr(c) for c in range(1, 0x110000) if not (0xD800 <= c <= 0xDFFF) and c not in (10, 13, 0x85, 0x2028, 0x2029, 0x1C, 0x1D, 0x1E)] + lines[-30000:] + ['', 'ABC', 'Abc', 'ǅ', 'ǅA', 'a1', '１２', '²', '٣', ' \t']
r = subprocess.run([cexe], input='\n'.join(clines).encode('utf-8') + b'\n', capture_output=True, timeout=600)
cgot = r.stdout.decode().split('\n')[:-1][:len(clines)]   # (the input's last newline makes one more, empty line)
def bits(x):
    return ''.join('1' if f() else '0' for f in (x.isalpha, x.isdigit, x.isspace, x.isalnum, x.isupper, x.islower, x.isdecimal))
cbad = [(ascii(l), g, bits(l)) for l, g in zip(clines, cgot) if g != bits(l)]
check(f'is_alpha, is_digit, is_space, is_alnum, is_upper, is_lower, is_decimal on {len(clines)} lines (every code point alone, and mixes) as Python\'s',
      r.returncode == 0 and len(cgot) == len(clines) and not cbad, f'{len(cgot)} lines; {len(cbad)} differ: {cbad[:5]}')
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
