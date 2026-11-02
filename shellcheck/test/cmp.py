# cmp.py REFDIR FILELIST VSCOUT [codes-spec] [--show N] [--code C]
# Compares vsc's gcc-format output with the reference per-file outputs, for the given codes
# (a comma list; "1" means every SC1xxx; "all" every code).
import sys, re, collections
refdir, flist, vout = sys.argv[1:4]
spec = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 'all'
show = 0; only = None
a = sys.argv
if '--show' in a: show = int(a[a.index('--show')+1])
if '--code' in a: only = a[a.index('--code')+1]
def want(code):
    if only: return code == only
    if spec == 'all': return True
    for s in spec.split(','):
        if s == code or (len(s) == 1 and code.startswith(s)): return True
    return False
pat = re.compile(r'^(.*?):(\d+):(\d+): (\w+): (.*) \[SC(\d+)\]$')
def parse(lines):
    d = collections.defaultdict(list)
    for l in lines:
        m = pat.match(l)
        if not m: continue
        if want(m.group(6)): d[m.group(1)].append(l)
    return d
files = [l.rstrip('\n') for l in open(flist)]
ref = {}
skipped = 0
for f in files:
    k = refdir + '/' + f.replace('/', '%')
    try:
        st = open(k + '.st').read().split()[0]
    except FileNotFoundError:
        continue
    if st not in ('0', '1'):
        skipped += 1; continue
    ref[f] = [l for l in parse(open(k + '.out', errors='surrogateescape').read().split('\n')).get(f, [])]
vs = parse(open(vout, errors='surrogateescape').read().split('\n'))
per = collections.defaultdict(lambda: [0, 0, 0])  # ref, vsc, matched
miss = []; extra = []
files_same = 0
for f, rl in ref.items():
    vl = vs.get(f, [])
    rc = collections.Counter(rl); vc = collections.Counter(vl)
    same = True
    for l in set(rl) | set(vl):
        code = pat.match(l).group(6)
        r, v = rc[l], vc[l]
        per[code][0] += r; per[code][1] += v; per[code][2] += min(r, v)
        if r > v: miss.extend([l] * (r - v)); same = False
        if v > r: extra.extend([l] * (v - r)); same = False
    if same: files_same += 1
print(f"files compared: {len(ref)} (skipped {skipped} where the reference failed); identical: {files_same}")
print(f"{'code':>8} {'ref':>6} {'vsc':>6} {'match':>6} {'miss':>6} {'extra':>6}")
tr = tv = tm = 0
for code in sorted(per, key=lambda c: -per[c][0]):
    r, v, m = per[code]
    tr += r; tv += v; tm += m
    print(f"{'SC'+code:>8} {r:>6} {v:>6} {m:>6} {r-m:>6} {v-m:>6}")
print(f"{'total':>8} {tr:>6} {tv:>6} {tm:>6} {tr-tm:>6} {tv-tm:>6}")
if show:
    print("--- missing (in reference, not vsc):")
    for l in miss[:show]: print("  " + l)
    print("--- extra (in vsc, not reference):")
    for l in extra[:show]: print("  " + l)
