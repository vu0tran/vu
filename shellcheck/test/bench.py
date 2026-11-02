# bench.py TOOL REPS: runs TOOL (sc, vsc1, vsc2) over the three corpora, the parity file lists minus
# the files shellcheck runs out of memory on. Prints wall, user and sys seconds and max RSS per run.
import sys, os, time, subprocess, resource
# SCW: the work directory (shellcheck, vsc, corpus/, corpus2/, files.txt, ...)
W = os.environ['SCW']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tool, reps = sys.argv[1], int(sys.argv[2])
cmd = {'sc': [W + '/shellcheck', '-f', 'gcc'], 'vsc1': [W + '/vsc', '-f', 'gcc'], 'vsc2': [W + '/vsc', '-f', 'gcc', '--jobs', '2'],
       'sctty': [W + '/shellcheck'], 'vsctty': [W + '/vsc']}[tool]
for r in range(reps):
    for c, d, lst in ((1, 'corpus', 'bench1.txt'), (2, 'corpus2', 'files2.txt'), (3, 'corpus3', 'files3_ok.txt')):
        files = [l.rstrip('\n') for l in open(W + '/' + lst)]
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        t = time.monotonic()
        p = subprocess.run(cmd + files, cwd=W + '/' + d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wall = time.monotonic() - t
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        print(f'{tool} corpus{c} wall {wall:.2f} user {after.ru_utime - before.ru_utime:.2f} sys {after.ru_stime - before.ru_stime:.2f} maxrss_mb {after.ru_maxrss / 1024:.0f} exit {p.returncode}', flush=True)
