"""std/zlib's compression (zlib.compress, gzip, deflate at levels 0-9): Python's zlib and gzip must read back
exactly the input, on edge cases, random and compressible data; prints the size next to Python's (C
zlib) at the same level, which it should stay close to."""
import zlib, gzip, subprocess, random, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'zlib', 'compress.vu'))
rng = random.Random(5)
def corpus():
    yield 'empty', b''
    yield 'one', b'a'
    yield 'two', b'ab'
    yield 'zeros', b'\0' * 100000
    yield 'random', bytes(rng.randrange(256) for _ in range(70000))
    words = [b'the', b'quick', b'brown', b'fox', b'vu', b'compiler', b'\n', b' ', b'lorem', b'ipsum']
    yield 'words', b' '.join(rng.choice(words) for _ in range(60000))
    yield 'aaab', (b'a' * 300 + b'b') * 500
    yield 'src', open(os.path.join(HERE, '..', 'compiler', 'c3_expr.vu'), 'rb').read()
    yield 'seed', open(os.path.join(HERE, '..', 'compiler', 'vuc_seed.c'), 'rb').read()[:3000000]
    yield 'mixed', bytes(rng.choice(b'ab') if rng.random() < 0.9 else rng.randrange(256) for _ in range(200000))
bad = 0; n = 0
for name, data in corpus():
    for lvl in ([0, 1, 4, 6, 9] if len(data) < 1000000 else [1, 6]):
        for mode in 'zgr':
            t = time.time()
            p = subprocess.run([exe, str(lvl), mode], input=data, capture_output=True)
            dt = time.time() - t
            out = p.stdout
            try:
                if mode == 'z': back = zlib.decompress(out)
                elif mode == 'g': back = gzip.decompress(out)
                else: back = zlib.decompress(out, -15)
                ok = back == data
            except Exception as e:
                ok = False; back = str(e)
            n += 1
            if not ok:
                bad += 1; print('FAIL', name, lvl, mode, p.returncode, p.stderr[-300:], str(back)[:100])
            elif mode == 'z' and lvl in (1, 6, 9):
                py = len(zlib.compress(data, lvl))
                t2 = time.time(); zlib.compress(data, lvl); pdt = time.time() - t2
                print(f'{name:7} L{lvl}: {len(data):8} -> vu {len(out):8}  python/C zlib {py:8}  ({(len(out)/max(py,1)-1)*100:+.1f}%)  {dt*1000:.0f} ms vs {pdt*1000:.0f} ms')
print(f'{n - bad} passed, {bad} failed')
sys.exit(1 if bad else 0)
