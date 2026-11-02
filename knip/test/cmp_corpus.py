# cmp_corpus.py [-r] [-v] [--args "ARGS"] DIR...: knip (its output cached in $WORK/ref/) vs vknip on
# each project folder: stdout, stderr, exit code, and the issues per type. -r re-runs knip.
#   WORK=dir KNIP=.../knip/bin/knip.js VKNIP=.../vknip python3 cmp_corpus.py corpus/*
import sys, os, re, subprocess, collections, hashlib, shlex, json
W = os.environ.get('WORK', os.getcwd())
KNIP = os.environ.get('KNIP', '/dev/shm/knip/ref/node_modules/knip/bin/knip.js')
VK = os.environ.get('VKNIP', os.path.join(W, 'vknip'))
def parse(text):
    cats = collections.OrderedDict(); cur = None
    for line in text.split('\n'):
        m = re.match(r'^([A-Z][A-Za-z ]+) \((\d+)\)$', line)
        if m: cur = m.group(1); cats[cur] = []; continue
        if cur and line.strip(): cats[cur].append(' '.join(line.split()))
    return cats
def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1800)
    return p.stdout, p.stderr, p.returncode
def main():
    a = sys.argv[1:]; rerun = False; extra = []; verbose = False
    while a and a[0].startswith('-'):
        if a[0] == '-r': rerun = True; a = a[1:]
        elif a[0] == '-v': verbose = True; a = a[1:]
        elif a[0] == '--args': extra = shlex.split(a[1]); a = a[2:]
        else: break
    tot = collections.Counter(); same_n = 0; rows = []
    for d in a:
        d = os.path.abspath(d)
        name = os.path.basename(d.rstrip('/'))
        tag = name + ('' if not extra else '__' + hashlib.md5(' '.join(extra).encode()).hexdigest()[:8])
        rp = os.path.join(W, 'ref', tag)
        if rerun or not os.path.exists(rp + '.json'):
            o, e, c = run(['node', KNIP] + extra, d)
            json.dump({'out': o, 'err': e, 'code': c, 'args': extra}, open(rp + '.json', 'w'))
        ref = json.load(open(rp + '.json'))
        o, e, c = run([VK] + extra, d)
        same = o == ref['out'] and e == ref['err'] and c == ref['code']
        same_n += same
        A = parse(ref['out']); B = parse(o); det = []
        for k in sorted(set(A) | set(B)):
            ra = collections.Counter(A.get(k, [])); rb = collections.Counter(B.get(k, []))
            tot[(k, 'ref')] += sum(ra.values()); tot[(k, 'same')] += sum((ra & rb).values())
            mi = sum((ra - rb).values()); ex = sum((rb - ra).values())
            tot[(k, 'missing')] += mi; tot[(k, 'extra')] += ex
            if mi or ex: det.append(f"{k}: -{mi} +{ex}")
        if ref['err'] != e: det.append('stderr differs')
        if ref['code'] != c: det.append(f"exit {ref['code']} vs {c}")
        if o == ref['out'] and not det: pass
        elif o != ref['out'] and not det: det.append('order/format')
        print(f"{name:20} {'IDENTICAL' if same else 'DIFF'} {'; '.join(det)}", flush=True)
        if verbose and not same:
            import difflib
            for l in difflib.unified_diff(ref['out'].split('\n'), o.split('\n'), 'knip', 'vknip', lineterm='', n=0): print('   ', l)
            for l in difflib.unified_diff(ref['err'].split('\n'), e.split('\n'), 'knip.err', 'vknip.err', lineterm='', n=0): print('   ', l)
    print(f"identical: {same_n}/{len(a)}")
    for k in sorted(set(c for c, _ in tot)):
        print(f"  {k:36} ref={tot[(k,'ref')]:5} same={tot[(k,'same')]:5} missing={tot[(k,'missing')]:4} extra={tot[(k,'extra')]:4}")
main()
