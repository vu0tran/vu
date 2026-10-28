"""Builds and tests the experiment's programs: python3 run.py DIR_VU DIR_RS [--label L]
For each task and language: does it compile (first error kept), and how many test inputs give exactly
the reference output (10 s limit each). Prints a table and writes results.json."""
import json, os, random, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', os.path.join(HERE, '..', '..', 'vu'))
TOK = os.path.join(HERE, '..', '..', 'tools', 'count_tokens.py')
dirs = {'vu': sys.argv[1], 'rs': sys.argv[2]}
work = tempfile.mkdtemp()
res = {}
for t in tasks.TASKS:
    ins = t.gen(random.Random(1))
    want = [t.ref(i) for i in ins]
    for lang in ('vu', 'rs'):
        src = os.path.join(dirs[lang], t.name + '.' + lang)
        exe = os.path.join(work, lang + '_' + t.name)
        r = {'exists': os.path.exists(src)}
        if r['exists']:
            if lang == 'vu': c = subprocess.run([VU, 'build', src, '-o', exe], capture_output=True, text=True)
            else: c = subprocess.run(['rustc', '-O', '--edition', '2021', src, '-o', exe], capture_output=True, text=True)
            r['compiles'] = c.returncode == 0
            r['error'] = '' if c.returncode == 0 else '\n'.join(l for l in (c.stderr + c.stdout).split('\n') if l.strip())[:600]
            passed, fails = 0, []
            if r['compiles']:
                for k, (i, w) in enumerate(zip(ins, want)):
                    try:
                        p = subprocess.run([exe], input=i, capture_output=True, text=True, timeout=10, errors='replace')
                        if p.stdout == w: passed += 1
                        else: fails.append((k, p.returncode, p.stdout[:120], w[:120], p.stderr[-200:]))
                    except subprocess.TimeoutExpired:
                        fails.append((k, 'timeout', '', '', ''))
            r['passed'], r['total'], r['fails'] = passed, len(ins), fails[:2]
            tk = subprocess.run(['python3', TOK, src], capture_output=True, text=True)
            import re
            m = re.search(r'(\d+) tokens', tk.stdout)
            r['tokens'] = int(m.group(1)) if m else '?'
        res[f'{t.name}/{lang}'] = r
json.dump(res, open(os.path.join(HERE, 'results_' + os.path.basename(dirs['vu'].rstrip('/')) + '.json'), 'w'), indent=1)
print(f"{'task':10} {'Vu':>22} {'Rust':>22}")
tot = {'vu': [0, 0, 0], 'rs': [0, 0, 0]}
for t in tasks.TASKS:
    cells = []
    for lang in ('vu', 'rs'):
        r = res[f'{t.name}/{lang}']
        if not r['exists']: cells.append('missing'); continue
        tot[lang][0] += r['compiles']
        tot[lang][1] += r['compiles'] and r['passed'] == r['total']
        if not r['compiles']: cells.append(f"no compile, {r['tokens']} tok")
        else: cells.append(f"{r['passed']}/{r['total']} pass, {r['tokens']} tok")
    print(f'{t.name:10} {cells[0]:>22} {cells[1]:>22}')
for lang in ('vu', 'rs'):
    print(f"{lang}: compiles {tot[lang][0]}/10, all tests pass {tot[lang][1]}/10")
