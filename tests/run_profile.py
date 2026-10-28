"""vu build --profile: the report names the functions where the CPU time went, in the right order and
roughly the right shares (hot.vu spends about 4/5 of its time in hot(), 1/5 in warm()); stacks and
files are written; and sampling doesn't break a program with tasks on every thread, a par loop, a
sleep and a network connection (the timer signal interrupts system calls). Shares are checked
with wide margins: they come from a few hundred samples."""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
work = tempfile.mkdtemp()
counts = {'passed': 0, 'failed': 0}


def check(name, ok, detail=''):
    counts['passed' if ok else 'failed'] += 1
    print(('ok    ' if ok else 'FAIL  ') + name + ('' if ok else '\n      ' + str(detail)[:800]))


def build(name):
    exe = os.path.join(work, name)
    r = subprocess.run(VU + ['build', '--profile', os.path.join(HERE, 'profile', name + '.vu'), '-o', exe], capture_output=True, text=True)
    if r.returncode:
        print(f'FAIL  build {name}\n{r.stderr}')
        sys.exit(1)
    return exe


def run(exe, *args):
    env = dict(os.environ, VU_PROF_OUT=os.path.join(work, os.path.basename(exe)))
    return subprocess.run([exe, *args], capture_output=True, text=True, env=env, timeout=120)


def shares(err):
    out = {}
    for m in re.finditer(r'^\s+([\d.]+)\s+([\d.]+)\s+(\S+)$', err, re.M):
        out[m.group(3)] = (float(m.group(1)), float(m.group(2)))
    return out


hot = build('hot')
r = run(hot, '60')
s = shares(r.stderr)
check('hot.vu runs as without the profiler', r.returncode == 0 and r.stdout.strip().isdigit(), r.stdout + r.stderr)
n = int(re.search(r'vu profile: (\d+) samples', r.stderr).group(1)) if 'vu profile:' in r.stderr else 0
check(f'a report with samples ({n}: the kernel\'s timer tick, often 250 a second)', n >= 150, r.stderr)
ok = 'hot' in s and 'warm' in s and 60 <= s['hot'][1] <= 95 and 5 <= s['warm'][1] <= 35 and s['hot'][1] > s['warm'][1] and s.get('main', (0, 0))[0] >= 99
check(f'hot() has most of the self time and warm() some (hot {s.get("hot")}, warm {s.get("warm")}, main {s.get("main")})', ok, r.stderr)
check('cold() is too quick to appear, or close to 0%', s.get('cold', (0, 0))[1] < 2, s.get('cold'))
lines = re.findall(r'^\s+([\d.]+)\s+hot\.vu:(\d+) in (\S+)$', r.stderr, re.M)
check('the lines named are in hot() (4 to 6) and warm() (9 to 12)', lines and all((4 <= int(l) <= 6 and f == 'hot') or (9 <= int(l) <= 12 and f == 'warm') or f == 'main' for _, l, f in lines), lines)
txt = open(os.path.join(work, 'hot.txt')).read() if os.path.exists(os.path.join(work, 'hot.txt')) else ''
check('vu-profile.txt has every function and line', 'hot' in txt and 'warm' in txt and 'hot.vu:' in txt, txt[:300])
folded = open(os.path.join(work, 'hot.folded')).read().split('\n') if os.path.exists(os.path.join(work, 'hot.folded')) else []
stacks = [l for l in folded if l]
check('vu-profile.folded has one stack per sample, from main down', len(stacks) == n and all(re.fullmatch(r'main(;\w+)* hot\.vu:\d+ 1', l) for l in stacks), stacks[:5])

tasks = build('tasks')
r = run(tasks)
s = shares(r.stderr)
check('tasks.vu (tasks on every thread, par, sleep, a connection) runs right while sampled',
      r.returncode == 0 and r.stdout.strip().startswith('ping ') and 'vu profile:' in r.stderr, r.stdout + r.stderr[-800:])
check(f'its CPU time is in burn(), called from the tasks and the par loop (burn {s.get("burn")}, worker {s.get("worker")})',
      s.get('burn', (0, 0))[1] > 80 and s.get('worker', (0, 0))[0] > 50, r.stderr)
for i in range(20):
    r = run(tasks)
    if r.returncode != 0 or not r.stdout.startswith('ping'):
        break
check('20 more runs of tasks.vu: none fails', r.returncode == 0 and r.stdout.startswith('ping'), r.stdout + r.stderr[-500:])
r = subprocess.run(VU + ['build', '--profile', '--wasm', os.path.join(HERE, 'profile', 'hot.vu'), '-o', os.path.join(work, 'x.wasm')], capture_output=True, text=True)
check('--profile with --wasm is refused', r.returncode == 2 and 'timer signal' in r.stderr, r.stderr)
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
