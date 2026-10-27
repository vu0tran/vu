"""Modules: each tests/modules/<case>/ is a program (main.vu plus the files it imports). main.vu's
header says what must happen, as in the targeted attacks:
  reject MSG   compilation fails with MSG
  output TEXT  the program prints TEXT, with no AddressSanitizer/LeakSanitizer/UBSan report
  panic MSG    the program stops with exit code 101 and MSG
Then some generated cases: the module limit, and reports that name files."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
work = tempfile.mkdtemp()
passed = failed = 0


def check(name, ok, detail=''):
    global passed, failed
    if ok:
        passed += 1
        print(f'ok    {name}')
    else:
        failed += 1
        print(f'FAIL  {name}\n      {detail[:600]}')


def run(args, cwd=None, env=None, timeout=300):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run(args, cwd=cwd, capture_output=True, env=e, timeout=timeout)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


for case in sorted(os.listdir(os.path.join(HERE, 'modules'))):
    d = os.path.join(HERE, 'modules', case)
    head = open(os.path.join(d, 'main.vu')).read().split('\n')
    attack = head[0].removeprefix('# attack: ')
    kind, _, want = head[1].removeprefix('# expect: ').partition(' ')
    exe = os.path.join(work, case)
    rc, out, err = run(VU + ['build', '--san', 'main.vu', '-o', exe], cwd=d)
    name = f'{case}: {attack}'
    if kind == 'reject':
        check(name, rc == 1 and want in err, f'exit {rc}: {err}')
        continue
    if rc != 0:
        check(name, False, f'failed to compile: {err}')
        continue
    rc, out, err = run([exe], cwd=d, env={'ASAN_OPTIONS': 'detect_leaks=1'})
    if kind == 'panic':
        check(name, rc == 101 and want in err, f'exit {rc}: {err}')
    else:
        check(name, rc == 0 and out.rstrip('\n') == want and 'ERROR' not in err and 'runtime error' not in err,
              f'exit {rc}, output [{out}], {err[:300]}')

# A panic inside a module: the report names the module's file and function.
rc, out, err = run(VU + ['run', '--json', 'main.vu'], cwd=os.path.join(HERE, 'modules', '12_panic_in_module'))
try:
    j = json.loads(err.strip())
except ValueError:
    j = None
check('JSON panic inside a module names its file and function', rc == 101 and j and j['file'] == 'util.vu'
      and j['backtrace'][0] == {'function': 'util.pick', 'file': 'util.vu', 'line': 2}
      and j['backtrace'][1]['file'] == 'main.vu', err)
rc, out, err = run(VU + ['check', '--json', 'main.vu'], cwd=os.path.join(HERE, 'modules', '13_syntax_error_in_module'))
try:
    j = json.loads(err.strip())
except ValueError:
    j = None
check('JSON compile error inside a module names its file', rc == 1 and j and j['file'] == 'util.vu' and j['line'] == 2, err)

# gdb: breakpoints by module file and line; frames in the module show its file.
if shutil.which('gdb'):
    exe = os.path.join(work, 'gdbmod')
    d = os.path.join(HERE, 'modules', '12_panic_in_module')
    run(VU + ['build', '--debug', 'main.vu', '-o', exe], cwd=d)
    rc, out, err = run(['gdb', '-batch', '-ex', 'break util.vu:2', '-ex', 'run', '-ex', 'bt', exe], cwd=d)
    bt = [l for l in out.splitlines() if l.startswith('#')]
    check('gdb: a breakpoint in a module file; the backtrace shows the module and the main file',
          len(bt) >= 2 and bt[0].endswith('util.vu:2') and bt[1].endswith('main.vu:7'), out[-500:])

# Paths: a program in a folder, compiled from elsewhere, finds its modules next to it.
sub = os.path.join(work, 'proj')
os.makedirs(sub)
with open(os.path.join(sub, 'app.vu'), 'w') as f:
    f.write('import helper\n\nfn main():\n  print("{helper.two()}")\n')
with open(os.path.join(sub, 'helper.vu'), 'w') as f:
    f.write('fn two() -> Int:\n  return 2\n')
rc, out, err = run(VU + ['run', os.path.join('proj', 'app.vu')], cwd=work)
check('modules are found next to the importing file, not the current folder', rc == 0 and out == '2\n', err)

# The module limit: the file index lives in the top bits of a 32-bit location, so 127 modules at most.
for n, ok in [(127, True), (128, False)]:
    big = os.path.join(work, f'many{n}')
    os.makedirs(big)
    with open(os.path.join(big, 'main.vu'), 'w') as f:
        f.write(''.join(f'import m{i}\n' for i in range(n)) + '\nfn main():\n  var t = 0\n'
                + ''.join(f'  t += m{i}.v()\n' for i in range(n)) + '  print("{t}")\n')
    for i in range(n):
        with open(os.path.join(big, f'm{i}.vu'), 'w') as f:
            f.write(f'fn v() -> Int:\n  return {i}\n')
    rc, out, err = run(VU + ['run', 'main.vu'], cwd=big)
    if ok:
        check(f'{n} modules: allowed', rc == 0 and out == f'{n * (n - 1) // 2}\n', err[:300])
    else:
        check(f'{n} modules: a clear error', rc == 1 and 'at most 127 modules' in err, err[:300])

shutil.rmtree(work)
print(f'{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
