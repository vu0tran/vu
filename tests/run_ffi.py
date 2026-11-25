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
# The build cache (VU_CACHE) keeps programs that call C too, keyed by their C files as well: the
# same build again is a copy, and an edit to the glue is built again.
import shutil
cache = os.path.join(work, 'cache')
cdir = os.path.join(work, 'cached')
shutil.copytree(os.path.join(D, '03_handles_drop'), os.path.join(cdir, 'prog'))
shutil.copytree(os.path.join(D, 'glue'), os.path.join(cdir, 'glue'))
env = {'VU_CACHE': cache}
exe = os.path.join(work, 'cached_exe')
rc1, _, e1 = run(VU + ['build', 'main.vu', '-o', exe], cwd=os.path.join(cdir, 'prog'), env=env)
n1 = len(os.listdir(cache)) if os.path.isdir(cache) else 0
rc2, _, e2 = run(VU + ['build', 'main.vu', '-o', exe], cwd=os.path.join(cdir, 'prog'), env=env)
n2 = len(os.listdir(cache)) if os.path.isdir(cache) else 0
glue = os.path.join(cdir, 'glue', 't.c')
gtxt = open(glue).read()
open(glue, 'w').write(gtxt.replace('static int64_t box_live(void) { return live; }', 'static int64_t box_live(void) { return live + 100; }'))
rc3, _, e3 = run(VU + ['build', 'main.vu', '-o', exe], cwd=os.path.join(cdir, 'prog'), env=env)
n3 = len(os.listdir(cache)) if os.path.isdir(cache) else 0
rc4, out4, _ = run([exe]) if rc3 == 0 else (rc3, '', e3)
check('the build cache keeps a program that calls C, and an edit to its C file builds again',
      rc1 == 0 and rc2 == 0 and n1 == 1 and n2 == 1 and n3 == 2 and rc4 == 0 and out4.strip() == 'live 105 -> 100',
      f'{rc1} {rc2} {rc3} entries {n1} {n2} {n3}, output {out4!r} {e1[:200]} {e3[:200]}')
# vu check never runs the C compiler, so a broken C file is only found by build.
rc, out, err = run(VU + ['check', 'main.vu'], cwd=os.path.join(D, '17_bad_signature'))
check('check passes a program whose C file is broken (only build compiles C)', rc == 0, err)
# A glue header in a split build: every part includes it and inlines its functions, and the parts
# kept between builds are keyed by its text, so an edit to the header builds them again.
hdir = os.path.join(work, 'hdr')
shutil.copytree(os.path.join(D, '36_glue_header'), os.path.join(hdir, 'prog'))
shutil.copytree(os.path.join(D, 'glue'), os.path.join(hdir, 'glue'))
henv = {'VU_SPLIT': 'always', 'VU_SPLIT_LINES': '20', 'XDG_CACHE_HOME': os.path.join(work, 'hxdg'), 'VU_CACHE': ''}
exe = os.path.join(work, 'hdr_exe')
rc1, _, e1 = run(VU + ['build', '--release', 'main.vu', '-o', exe], cwd=os.path.join(hdir, 'prog'), env=henv)
r1 = run([exe]) if rc1 == 0 else (rc1, '', e1)
hfile = os.path.join(hdir, 'glue', 'cols.h')
htxt = open(hfile).read()
open(hfile, 'w').write(htxt.replace('#define COL_SCALE 1', '#define COL_SCALE 2'))
rc2, _, e2 = run(VU + ['build', '--release', 'main.vu', '-o', exe], cwd=os.path.join(hdir, 'prog'), env=henv)
r2 = run([exe]) if rc2 == 0 else (rc2, '', e2)
parts = os.path.join(work, 'hxdg', 'vu', 'parts')
nparts = sum(len(fs) for _, _, fs in os.walk(parts)) if os.path.isdir(parts) else 0
check('a glue header in a split build: inlined in every part, and an edit to it builds the parts again',
      r1[0] == 0 and r1[1].strip() == '10 45 285 9 3' and r2[0] == 0 and r2[1].strip() == '10 90 1140 18 3' and nparts > 4,
      f'{r1} {r2} parts {nparts}')
print(f'{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
