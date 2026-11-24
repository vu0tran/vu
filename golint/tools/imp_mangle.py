#!/usr/bin/env python3
# mangle.py SEED FRACTION FILES...: rewrites the import declarations of each file in place (a
# FRACTION of them; the rest stay untouched): shuffled, regrouped, split into several declarations,
# comments added, duplicate blank imports, aliases equal to the package name, empty blocks.
import sys, random, re

seed = int(sys.argv[1]); frac = float(sys.argv[2]); files = sys.argv[3:]
rng = random.Random(seed)
SPEC = re.compile(r'^\s*((?:[A-Za-z_][A-Za-z0-9_]*|\.)\s+)?("[^"]+")\s*(//.*|/\*.*\*/)?\s*$')

def parse(lines, i):
    """import decls starting at line i: returns (specs, end) or None. specs: [(name, path, trailing, docs)]"""
    specs = []; docs = []
    while i < len(lines):
        l = lines[i]
        if l.startswith('import ('):
            if l.strip() != 'import (': return None
            i += 1
            while i < len(lines) and lines[i].strip() != ')':
                s = lines[i].strip()
                if s == '': docs = []  # comment groups detached by a blank line are dropped from docs but kept
                elif s.startswith('//'): docs.append(s)
                else:
                    m = SPEC.match(lines[i])
                    if not m or '/*' in s and not s.endswith('*/'): return None
                    specs.append(((m[1] or '').strip(), m[2], m[3] or '', docs)); docs = []
                i += 1
            if i >= len(lines): return None
            i += 1
        elif l.startswith('import '):
            m = SPEC.match(l[len('import '):])
            if not m: return None
            specs.append(((m[1] or '').strip(), m[2], m[3] or '', docs)); docs = []
            i += 1
        elif l.strip() == '': i += 1
        elif l.startswith('//') and i + 1 < len(lines) and lines[i + 1].startswith('import'):
            docs.append(l.strip()); i += 1
        else: break
    return specs, i

def mangle(src):
    lines = src.split('\n')
    i = 0
    while i < len(lines) and not lines[i].startswith('import'):
        if lines[i].startswith(('func', 'var', 'const', 'type')): return None
        i += 1
    if i >= len(lines): return None
    if 'import "C"' in src or '"C"' in src: return None
    start = i
    r = parse(lines, i)
    if r is None or not r[0]: return None
    specs, end = r
    specs = [list(s) for s in specs]
    n = len(specs)
    ops = set(rng.sample(['shuffle', 'swap', 'blank', 'split', 'comment', 'doc', 'dupblank', 'alias', 'empty', 'join', 'block', 'standalone'], rng.randint(1, 5)))
    if 'shuffle' in ops: rng.shuffle(specs)
    if 'swap' in ops and n > 1:
        for _ in range(rng.randint(1, 3)):
            a, b = rng.randrange(n), rng.randrange(n); specs[a], specs[b] = specs[b], specs[a]
    if 'comment' in ops:
        for s in specs:
            if not s[2] and rng.random() < 0.3: s[2] = '// note %d' % rng.randint(0, 99)
    if 'block' in ops:
        for s in specs:
            if not s[2] and rng.random() < 0.3: s[2] = '/* b%d */' % rng.randint(0, 99)
    if 'doc' in ops:
        for s in specs:
            if rng.random() < 0.25: s[3] = s[3] + ['// doc %d' % rng.randint(0, 99)]
    paths = [s[1] for s in specs]
    if 'dupblank' in ops:
        for _ in range(rng.randint(1, 3)):
            p = rng.choice(['"embed"', '"unsafe"', rng.choice(paths)])
            specs.insert(rng.randint(0, len(specs)), ['_', p, rng.choice(['', '', '// dup']), []])
    if 'alias' in ops:
        for s in specs:
            p = s[1].strip('"')
            if not s[0] and '/' not in p and '.' not in p and rng.random() < 0.5: s[0] = p
    n = len(specs)
    # decl boundaries and blank lines
    cuts = set()
    if 'split' in ops and n > 1:
        cuts = set(rng.sample(range(1, n), rng.randint(1, min(3, n - 1))))
    blanks = set()
    if 'blank' in ops:
        blanks = set(k for k in range(1, n) if rng.random() < 0.3)
    if 'join' in ops: blanks = set()
    out = []
    groups = []; cur = []
    for k, s in enumerate(specs):
        if k in cuts: groups.append(cur); cur = []
        cur.append((k, s))
    groups.append(cur)
    def spec_text(s):
        t = (s[0] + ' ' if s[0] else '') + s[1]
        if s[2]: t += ' ' + s[2]
        return t
    for gi, g in enumerate(groups):
        if gi > 0: out.append('')
        if 'empty' in ops and gi == 0 and rng.random() < 0.5: out += ['import ()', '']
        if len(g) == 1 and rng.random() < 0.5 and not g[0][1][3]:
            out.append('import ' + spec_text(g[0][1]))
            continue
        out.append('import (')
        for k, s in g:
            if k in blanks and k != g[0][0]: out.append('')
            if 'standalone' in ops and rng.random() < 0.15: out += ['\t// standalone %d' % k, '']
            for d in s[3]: out.append('\t' + d)
            out.append('\t' + spec_text(s))
        out.append(')')
    new = lines[:start] + out + [''] + lines[end:]
    # (one blank line before the rest)
    while len(new) > start + len(out) + 1 and new[start + len(out) + 1] == '': del new[start + len(out) + 1]
    return '\n'.join(new)

changed = 0
for f in files:
    if rng.random() >= frac: continue
    src = open(f).read()
    m = mangle(src)
    if m and m != src:
        open(f, 'w').write(m); changed += 1
print("mangled", changed, "of", len(files))
