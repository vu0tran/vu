"""Calling C: each tests/ffi/<case>/ is a program whose extern blocks name glue files in tests/ffi/glue/.
main.vu's header says what must happen (reject MSG / output TEXT / panic MSG), as in the module tests;
programs are built with AddressSanitizer/LeakSanitizer/UBSan, so a handle freed twice or never is a
failure. Then generated checks: a program built from another directory, and a release build."""
import os
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


D = os.path.join(HERE, 'ffi')
for case in sorted(os.listdir(D)):
    if case == 'glue':
        continue
    d = os.path.join(D, case)
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
        check(name, rc == 101 and want in err and 'ERROR' not in err, f'exit {rc}: {err}')
    else:
        got = out.rstrip('\n')
        check(name, rc == 0 and got == want and 'ERROR' not in err and 'runtime error' not in err,
              f'exit {rc}, output [{got}], {err[:300]}')

# From another directory: the C file is found next to the Vu file that names it.
exe = os.path.join(work, 'from_elsewhere')
rc, out, err = run(VU + ['build', 'ffi/01_sqlite/main.vu', '-o', exe], cwd=HERE)
rc2, out2, err2 = run([exe]) if rc == 0 else (rc, '', err)
check('built from another directory', rc2 == 0 and out2.startswith('1 ada|'), err2)
# Optimized, without sanitizers.
exe = os.path.join(work, 'release')
rc, out, err = run(VU + ['build', '--release', 'main.vu', '-o', exe], cwd=os.path.join(D, '03_handles_drop'))
rc2, out2, err2 = run([exe]) if rc == 0 else (rc, '', err)
check('release build', rc2 == 0 and out2.strip() == 'live 5 -> 0', out2 + err2)
# vu check never runs the C compiler, so a broken C file is only found by build.
rc, out, err = run(VU + ['check', 'main.vu'], cwd=os.path.join(D, '17_bad_signature'))
check('check passes a program whose C file is broken (only build compiles C)', rc == 0, err)
print(f'{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
