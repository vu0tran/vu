# cmpj.py REFDIR FILELIST VSCJSON1 [--codes FILE|all] [--show N] [--code C]
# Compares vsc's -f json1 output (all files in one run) with per-file reference json1 outputs:
# every field of every comment, the fix included, for the codes in FILE (default: all).
import sys, json, collections
refdir, flist, vout = sys.argv[1:4]
a = sys.argv
show = int(a[a.index('--show')+1]) if '--show' in a else 0
only = a[a.index('--code')+1] if '--code' in a else None
codes = None
if '--codes' in a and a[a.index('--codes')+1] != 'all':
    codes = set(int(x) for x in open(a[a.index('--codes')+1]).read().split())
def want(c):
    if only: return str(c['code']) == only
    return codes is None or c['code'] in codes
def key(c): return json.dumps(c, separators=(',', ':'), ensure_ascii=False)
def nofix(c):
    d = dict(c); d['fix'] = None; return key(d)
files = [l.rstrip('\n') for l in open(flist)]
vs = collections.defaultdict(list)
for c in json.load(open(vout, errors='surrogateescape'))['comments']:
    vs[c['file']].append(c)
per = collections.defaultdict(lambda: [0, 0, 0])
miss = []; extra = []; fixdiff = []
same_files = 0; n = 0; skipped = 0
for f in files:
    k = refdir + '/' + f.replace('/', '%')
    try: st = open(k + '.st').read().split()[0]
    except FileNotFoundError: continue
    if st not in ('0', '1'): skipped += 1; continue
    n += 1
    txt = open(k + '.out', errors='surrogateescape').read()
    rl = [c for c in json.loads(txt)['comments'] if want(c)] if txt.strip() else []
    vl = [c for c in vs.get(f, []) if want(c)]
    rc = collections.Counter(key(c) for c in rl); vc = collections.Counter(key(c) for c in vl)
    ok = True
    allc = {key(c): c for c in rl + vl}
    rnf = collections.Counter(nofix(c) for c in rl); vnf = collections.Counter(nofix(c) for c in vl)
    for s, c in allc.items():
        r, v = rc[s], vc[s]
        code = c['code']
        per[code][0] += r; per[code][1] += v; per[code][2] += min(r, v)
        if r != v: ok = False
        if r > v:
            (fixdiff if rnf[nofix(c)] == vnf[nofix(c)] else miss).extend([s] * (r - v))
        if v > r and rnf[nofix(c)] != vnf[nofix(c)]: extra.extend([s] * (v - r))
    if ok: same_files += 1
print(f"files compared: {n} (skipped {skipped}); identical: {same_files}")
tr = tv = tm = 0
for code in sorted(per, key=lambda c: -per[c][0]):
    r, v, m = per[code]; tr += r; tv += v; tm += m
    if r != m or v != m: print(f"  SC{code}: ref {r} vsc {v} match {m}")
print(f"total ref {tr} vsc {tv} match {tm}; missing {len(miss)}, extra {len(extra)}, fix differs {len(fixdiff)}")
if show:
    for name, l in (('missing', miss), ('extra', extra), ('fix differs (reference shown)', fixdiff)):
        print('--- ' + name)
        for s in l[:show]: print('  ' + s)
