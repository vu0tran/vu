"""std/path against Python's posixpath on random paths (made of /, ., .., names with dots, and empty
parts): join, dirname, basename, splitext, normpath, isabs, relpath; and within() against a
definition through normpath. Extra arguments (--san) go to the build."""
import os
import posixpath
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
N = int(os.environ.get('N', '20000'))
rng = random.Random(int(os.environ.get('SEED', '7')))
PARTS = ['a', 'b', 'c.txt', '.', '..', '', '.hidden', 'x.tar.gz', 'é.vu', '...', 'a..b', '.a.b']


def rand_path():
    p = '/'.join(rng.choice(PARTS) for _ in range(rng.randint(0, 6)))
    r = rng.random()
    if r < 0.3:
        p = '/' + p
    elif r < 0.35:
        p = '//' + p
    elif r < 0.4:
        p = '///' + p
    if rng.random() < 0.2:
        p += '/'
    return p


def h(s):
    return s.encode().hex()


def splitext(p):
    return posixpath.splitext(p)


def py_rel(t, s):
    if posixpath.isabs(t) != posixpath.isabs(s):
        return 'error'
    sp = posixpath.normpath(s)
    if not posixpath.isabs(sp) and (sp == '..' or sp.startswith('../')):
        return 'error'
    # relpath on two relative paths goes through the current folder; anchor both at a fixed one
    if not posixpath.isabs(t):
        anchor = '/r1/r2/r3/r4/r5/r6/r7/'   # deeper than any run of '..' here, so none reaches the root
        return h(posixpath.relpath(anchor + t, anchor + s))
    return h(posixpath.relpath(t, s))


def py_within(folder, p):
    f = posixpath.normpath(folder) if folder else '.'
    full = posixpath.normpath(p) if p else '.'
    if not posixpath.isabs(full) and posixpath.isabs(f):
        full = posixpath.normpath(posixpath.join(f, full))
    if f == '.' and not posixpath.isabs(full):
        return full != '..' and not full.startswith('../')
    if full == f:
        return True
    if f in ('/', '//'):
        return posixpath.isabs(full)
    return full.startswith(f + '/')


def py(a, b):
    root, e = splitext(a)
    parts = (['/'] if a.startswith('/') else []) + [x for x in a.split('/') if x]
    return ' '.join([h(posixpath.join(a, b) if a else b), h(posixpath.dirname(a)), h(posixpath.basename(a)), h(e),
                     h(posixpath.basename(root)) if posixpath.basename(a) else '', h(root), h(posixpath.normpath(a) if a else '.'),
                     '1' if posixpath.isabs(a) else '0', h('\n'.join(parts)), py_rel(a, b), '1' if py_within(b, a) else '0'])


work = tempfile.mkdtemp()
exe = os.path.join(work, 'ops')
r = subprocess.run(VU + ['build', f'{HERE}/path/ops.vu', '-o', exe] + sys.argv[1:], capture_output=True, text=True)
if r.returncode:
    print('FAIL  build', r.stderr[:500])
    sys.exit(1)
cases = [(rand_path(), rand_path()) for _ in range(N)]
cases += [('', ''), ('/', '/'), ('//', 'a'), ('a/b/', 'c'), ('/srv/www/../etc/passwd', '/srv/www'), ('/srv/www2/x', '/srv/www'),
          ('x/../../y', '.'), ('/a/b/c', '/a'), ('/a/x', '/a/b')]
inp = os.path.join(work, 'in.txt')
with open(inp, 'w') as f:
    for a, b in cases:
        f.write(h(a) + ' ' + h(b) + '\n')
r = subprocess.run([exe, inp], capture_output=True, text=True, timeout=600)
if r.returncode or 'ERROR' in r.stderr or 'runtime error' in r.stderr:
    print('FAIL  run', r.returncode, r.stderr[:800])
    sys.exit(1)
names = ['join', 'dir', 'base', 'ext', 'stem', 'without_ext', 'clean', 'is_abs', 'parts', 'rel', 'within']
bad = 0
for (a, b), got in zip(cases, r.stdout.split('\n')):
    want = py(a, b)
    if got != want:
        bad += 1
        if bad <= 8:
            g, w = got.split(' '), want.split(' ')
            which = [names[i] for i in range(len(names)) if i >= len(g) or g[i] != w[i]]
            print(f'FAIL  {a!r} {b!r}: {which}\n      got  {got}\n      want {want}')
print(f'{len(cases) - bad} of {len(cases)} agree with Python ({" ".join(sys.argv[1:]) or "optimized"})')
print(f'{len(cases) - bad} passed, {bad} failed')
sys.exit(1 if bad else 0)
