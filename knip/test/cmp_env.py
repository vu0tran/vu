#!/usr/bin/env python3
# Runs knip and vknip on projects with extra environment variables (FORCE_COLOR=1: knip's colors on a
# pipe) and command lines, and compares stdout, stderr and the exit code. knip's results are cached
# in OUT (delete a file to run knip again).
#   KNIP=.../knip.js VKNIP=.../vknip OUT=dir ENV='FORCE_COLOR=1' python3 cmp_env.py PROJECT... -- ARGS...
import os, sys, json, subprocess, hashlib
KNIP = os.environ['KNIP']; VK = os.environ['VKNIP']; OUT = os.environ['OUT']
extra = dict(kv.split('=', 1) for kv in os.environ.get('ENV', '').split() if '=' in kv)
argv = sys.argv[1:]
cut = argv.index('--') if '--' in argv else len(argv)
projects, cmdline = argv[:cut], argv[cut + 1:]
os.makedirs(OUT, exist_ok=True)
env = dict(os.environ); env.update(extra)
same = 0
for d in projects:
    key = hashlib.md5(json.dumps([os.path.abspath(d), cmdline, extra]).encode()).hexdigest()[:12]
    rp = os.path.join(OUT, f'{os.path.basename(d)}-{key}.json')
    if not os.path.exists(rp):
        r = subprocess.run(['node', KNIP] + cmdline, cwd=d, capture_output=True, text=True, env=env)
        json.dump({'out': r.stdout, 'err': r.stderr, 'code': r.returncode}, open(rp, 'w'))
    ref = json.load(open(rp))
    r = subprocess.run([VK] + cmdline, cwd=d, capture_output=True, text=True, env=env)
    ok = (r.stdout, r.stderr, r.returncode) == (ref['out'], ref['err'], ref['code'])
    same += ok
    if not ok:
        what = [n for n, a, b in (('stdout', ref['out'], r.stdout), ('stderr', ref['err'], r.stderr), ('code', ref['code'], r.returncode)) if a != b]
        print(f'DIFF {os.path.basename(d)}: {" ".join(what)}')
        if os.environ.get('V'):
            import difflib
            for a, b in (('out', r.stdout), ('err', r.stderr)):
                for l in list(difflib.unified_diff(ref[a].splitlines(), b.splitlines(), lineterm=''))[:30]: print(repr(l))
print(f'{" ".join(cmdline) or "(default)"} {" ".join(f"{k}={v}" for k, v in extra.items())}: identical: {same}/{len(projects)}')
