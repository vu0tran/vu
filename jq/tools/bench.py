# bench.py RUNS FILE 'OPTIONS::FILTER' ... : runs each tool on each filter, best-of-RUNS wall time and peak RSS,
# and checks that every tool's output is byte-identical to jq's (sha256).
import os, sys, time, hashlib, subprocess, shlex
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the binaries: VJQ, JQ, GOJQ, JAQ (default: next to this folder, and on PATH)
TOOLS = {'vjq': os.environ.get('VJQ', W + '/vjq'), 'jq': os.environ.get('JQ', 'jq'),
         'gojq': os.environ.get('GOJQ', 'gojq'), 'jaq': os.environ.get('JAQ', 'jaq')}
runs = int(sys.argv[1]); infile = sys.argv[2]; cases = sys.argv[3:]
only = os.environ.get('TOOLS', 'vjq,jq,gojq,jaq').split(',')
def run(cmd, out):
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, stdout=out, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    _, status, ru = os.wait4(p.pid, 0)
    # CPU time (user + system): steadier than wall time on a shared machine
    return ru.ru_utime + ru.ru_stime, ru.ru_maxrss, status
print(f"{'case':38s} " + " ".join(f"{t:>16s}" for t in only))
for case in cases:
    opts, _, filt = case.rpartition('::')
    args = shlex.split(opts) + [filt]
    res = []; ref = None
    for tool in only:
        cmd = [TOOLS[tool]] + args + [infile]
        h = hashlib.sha256()
        with open('/dev/null', 'w') as dn:
            best = None; rss = 0
            for i in range(runs):
                t, r, st = run(cmd, dn)
                best = t if best is None else min(best, t); rss = max(rss, r)
        # output check (one more run, hashed)
        p = subprocess.run(cmd, capture_output=True)
        dig = hashlib.sha256(p.stdout).hexdigest()
        if ref is None: ref = dig
        mark = '' if dig == ref else '*'
        res.append(f"{best:6.2f}s {rss/1024:6.0f}MB{mark}")
    print(f"{case:38s} " + " ".join(f"{r:>16s}" for r in res), flush=True)
