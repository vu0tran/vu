#!/usr/bin/env python3
# Why vtsc didn't type files, weighted by the tsgolint diagnostics those files hold: each file
# charged to its root (the file whose own construct isn't modeled, following "an import of X" and
# "(in X)"), then by reason and by package.
# usage: roots.py ERR REF [N]
import os, re, sys, collections
err, ref = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 25
P = os.environ['VLINT_CORPUS'].rstrip('/') + '/'
why = {}
for l in open(err, errors='replace'):
    m = re.match(r'vlint: vtsc: NOT (\S+): (.*?)(; rules .*)?$', l.rstrip('\n'))
    if m: why[m.group(1)] = m.group(2)
cnt = collections.Counter()
for l in open(ref, errors='replace'):
    f = l.split(':', 1)[0]
    cnt[f if f.startswith('/') else P + f] += 1
def root(f, seen=()):
    w = why.get(f, '')
    m = re.match(r'an import of (\S+), which', w) or re.match(r".*\(in (\S+?)\)$", w)
    if m and m.group(1) in why and m.group(1) not in seen and m.group(1) != f: return root(m.group(1), seen + (f,))
    return f
byroot, files, reason, nr, pkg = (collections.Counter() for _ in range(5))
for f in why:
    r = root(f); byroot[r] += cnt[f]; files[r] += 1
    w = re.sub(r' at \d+', '', why.get(r, '')); w = re.sub(r'\(in \S+\)', '(in X)', w); w = re.sub(r'\[[^\]]*\]', '', w)[:90]
    reason[w] += cnt[f]; nr[w] += 1
    pkg['/'.join(f.replace(P, '').split('/')[:2])] += cnt[f]
print('--- by reason (diagnostics, files)')
for w, n in reason.most_common(N): print(n, nr[w], w)
print('--- by root')
for f, n in byroot.most_common(N): print(n, files[f], f.replace(P, ''), '::', why.get(f, '')[:120])
print('--- by package')
for p, n in pkg.most_common(15): print(n, p)
