#!/usr/bin/env python3
# Runs `knip --watch` and `vknip --watch` in a terminal (a pty) on a generated project, makes the
# same file edits under each, and compares what each shows after every step (the screen after the
# last clear, the summary line's time and memory left out), and how many times each redrew.
#   KNIP=.../knip.js VKNIP=.../vknip python3 cmp_watch.py OUT_DIR [-v]
import os, sys, pty, select, time, shutil, subprocess, json, re, signal

KNIP = os.environ['KNIP']; VK = os.environ['VKNIP']
out = os.path.abspath(sys.argv[1]); verbose = '-v' in sys.argv
CLEAR = '\x1b[2J\x1b[1;1f'

def pkg(name='app', deps=None, dev=None, extra=None):
    m = {'name': name, 'version': '1.0.0'}
    if deps: m['dependencies'] = {d: '1' for d in deps}
    if dev: m['devDependencies'] = {d: '1' for d in dev}
    if extra: m.update(extra)
    return json.dumps(m, indent=2) + '\n'

BASE = {
    'package.json': pkg(deps=['dep-a'], extra={'main': 'src/index.ts'}),
    'node_modules/dep-a/package.json': json.dumps({'name': 'dep-a', 'version': '1.0.0', 'main': 'index.js'}),
    'node_modules/dep-a/index.js': 'module.exports = {};\n',
    'src/index.ts': "import { used } from './lib';\nimport x from 'dep-a';\nconsole.log(used, x);\n",
    'src/lib.ts': 'export const used = 1;\nexport const unusedExport = 2;\n',
    'src/orphan.ts': 'export const o = 1;\n',
    'README.md': '# app\n',
}

# each step: (label, action) where action edits the project folder
def w(path, text):
    def f(d):
        p = os.path.join(d, path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(text)
    return f
def rm(path):
    return lambda d: os.remove(os.path.join(d, path))
def touch_same(path):
    def f(d):
        p = os.path.join(d, path); t = open(p).read(); open(p, 'w').write(t)
    return f

STEPS = [
    ('add an unused export', w('src/lib.ts', 'export const used = 1;\nexport const unusedExport = 2;\nexport const another = 3;\n')),
    ('use an export', w('src/index.ts', "import { used, another } from './lib';\nimport x from 'dep-a';\nconsole.log(used, x, another);\n")),
    ('the same contents written again', touch_same('src/lib.ts')),
    ('add a file nothing imports', w('src/new.ts', 'export const n = 1;\n')),
    ('import the new file', w('src/index.ts', "import { used, another } from './lib';\nimport './new';\nimport x from 'dep-a';\nconsole.log(used, x, another);\n")),
    ('delete the orphan', rm('src/orphan.ts')),
    ('a README edit', w('README.md', '# app\n\nmore\n')),
    ('an unlisted import', w('src/lib.ts', "import 'not-listed';\nexport const used = 1;\nexport const unusedExport = 2;\nexport const another = 3;\n")),
    ('add the dependency', w('package.json', pkg(deps=['dep-a', 'not-listed'], extra={'main': 'src/index.ts'}))),
    ('a knip.json', w('knip.json', json.dumps({'ignore': ['src/lib.ts']}))),
    ('a new folder with a file', w('src/sub/deep.ts', 'export const d = 1;\n')),
    ('remove every issue', w('knip.json', json.dumps({'ignore': ['src/**'], 'ignoreDependencies': ['not-listed']}))),
]

def write_project(d):
    shutil.rmtree(d, ignore_errors=True)
    for p, t in BASE.items():
        f = os.path.join(d, p); os.makedirs(os.path.dirname(f), exist_ok=True); open(f, 'w').write(t)
    kdir = os.path.dirname(os.path.dirname(KNIP))
    os.symlink(kdir, os.path.join(d, 'node_modules', 'knip'))
    subprocess.run(['git', 'init', '-q'], cwd=d)
    open(os.path.join(d, '.gitignore'), 'w').write('node_modules\n')

def read_until_idle(fd, buf, idle=1.5, limit=30.0):
    start = time.time(); last = time.time()
    while time.time() - start < limit:
        r, _, _ = select.select([fd], [], [], 0.1)
        if r:
            try: data = os.read(fd, 65536)
            except OSError: break
            if not data: break
            buf.append(data.decode('utf-8', 'replace')); last = time.time()
        elif time.time() - last > idle and buf: break
    return buf

def screen(text):
    s = text.split(CLEAR)[-1]
    # (the time and memory of the summary line vary)
    return re.sub(r'(\d+ files) \([^)]*\)', r'\1 (…)', s).replace('\r\n', '\n')

def session(cmd, d):
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(d)
        env = dict(os.environ); env.pop('CI', None); env['COLUMNS'] = '120'
        os.execvpe(cmd[0], cmd, env)
    buf = read_until_idle(fd, [], idle=2.0, limit=60.0)
    shots = [(screen(''.join(buf)), ''.join(buf).count(CLEAR))]
    for label, act in STEPS:
        n0 = len(buf)
        act(d)
        read_until_idle(fd, buf, idle=2.5, limit=30.0)
        new = ''.join(buf[n0:])
        shots.append((screen(''.join(buf)), new.count(CLEAR)))
    os.kill(pid, signal.SIGTERM)
    try: os.waitpid(pid, 0)
    except OSError: pass
    return shots

def main():
    os.makedirs(out, exist_ok=True)
    res = {}
    for tag, cmd in (('knip', ['node', KNIP, '--watch']), ('vknip', [VK, '--watch'])):
        d = os.path.join(out, tag); write_project(d)
        res[tag] = session(cmd, d)
    same = 0
    labels = ['start'] + [s[0] for s in STEPS]
    for k, label in enumerate(labels):
        a, b = res['knip'][k], res['vknip'][k]
        ok = a[0] == b[0]
        # (redraws: knip clears the screen for its progress messages too, so only whether one came)
        redraw_same = (a[1] > 0) == (b[1] > 0)
        if ok and redraw_same: same += 1
        print(('SAME ' if ok and redraw_same else 'DIFF ') + label + ('' if redraw_same else f' (redraws {a[1]} vs {b[1]})'))
        if not ok and verbose:
            import difflib
            for l in difflib.unified_diff(a[0].split('\n'), b[0].split('\n'), 'knip', 'vknip', lineterm=''): print('   ', l)
    print(f'identical: {same}/{len(labels)}')

main()
