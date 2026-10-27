"""The inputs for bench/zlib/compare.sh, in DIR: text (Python's own library source, up to 40 MB),
binary (the files in /usr/bin, up to 40 MB) and random (8 MB that doesn't compress), each compressed
by zlib at level 6 (FILE.z). What's in text and binary depends on the machine; the sizes are printed.
  python3 corpus.py DIR"""
import os
import random
import sys
import sysconfig
import zlib


def collect(root, pred, limit):
    out = bytearray()
    for d, _, fs in sorted(os.walk(root)):
        for f in sorted(fs):
            p = os.path.join(d, f)
            if pred(p) and os.path.isfile(p) and not os.path.islink(p):
                try:
                    out += open(p, 'rb').read()
                except OSError:
                    pass
            if len(out) >= limit:
                return bytes(out[:limit])
    return bytes(out)


d = sys.argv[1]
sets = [('text', collect(sysconfig.get_paths()['stdlib'], lambda p: p.endswith('.py'), 40 << 20)),
        ('binary', collect('/usr/bin', lambda p: True, 40 << 20)),
        ('random', random.Random(5).randbytes(8 << 20))]
for name, data in sets:
    z = zlib.compress(data, 6)
    open(os.path.join(d, name + '.z'), 'wb').write(z)
    print(f'{name}: {len(data)} bytes, {len(z)} compressed ({len(z) / len(data):.3f})')
