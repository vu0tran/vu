"""Programs built with `vu build --wasm` and run under wasmtime: every targeted output and panic test
(against the output its header expects) and every example (against the native build's output).
A program WebAssembly can't build (tasks, the network, TLS, C files) must be refused with exit 2
and a reason; those are counted as skipped.
  python3 wasm_programs.py VU FILE.vu..."""
import concurrent.futures as cf
import os, subprocess, sys, tempfile
import wasmtime

vu = sys.argv[1].split()
files = sys.argv[2:]
tmp = tempfile.mkdtemp(prefix='vu-wasmp-')
eng = wasmtime.Engine()
# Differences WebAssembly is expected to have: os.run can't start programs there (it fails, with
# "not available in WebAssembly"); the runtime stops a too-deep recursion itself (a trap); WASI
# reports an empty path as "Bad file descriptor"; and clang turns 465's endless recursion into a
# loop, so it ends with the integer overflow its counter reaches instead of a stack overflow.
KNOWN = {'180_os_run_bad_args', '30_empty_path', '465_closure_recursion_overflow'}
counts = {'passed': 0, 'failed': 0, 'skipped': 0, 'known': 0}


def header(f):
    lines = open(f).read().split('\n')[:3]
    kind = want = ''
    args = []
    if len(lines) > 1 and lines[1].startswith('# expect: '):
        kind, _, want = lines[1][len('# expect: '):].partition(' ')
    if len(lines) > 2 and lines[2].startswith('# args: '):
        args = lines[2][len('# args: '):].split()
    return kind, want, args


def build(f):
    name = os.path.basename(f)[:-3]
    d = os.path.join(tmp, name)
    os.makedirs(d)
    r = subprocess.run(vu + ['build', '--wasm', f, '-o', os.path.join(d, 'prog.wasm')], capture_output=True, text=True, timeout=300)
    return d, r


def run(d, args):
    store = wasmtime.Store(eng)
    cfg = wasmtime.WasiConfig()
    cfg.argv = ['prog'] + args
    cfg.preopen_dir(d, '.')
    cfg.stdout_file = os.path.join(d, '.out')
    cfg.stderr_file = os.path.join(d, '.err')
    store.set_wasi(cfg)
    linker = wasmtime.Linker(eng)
    linker.define_wasi()
    inst = linker.instantiate(store, wasmtime.Module.from_file(eng, os.path.join(d, 'prog.wasm')))
    rc = 0
    try:
        inst.exports(store)['_start'](store)
    except wasmtime.ExitTrap as e:
        rc = e.code
    except wasmtime.Trap as e:
        rc = 'trap: ' + ('call stack exhausted' if 'call stack exhausted' in str(e) else str(e)[-300:])
    return rc, open(os.path.join(d, '.out'), errors='replace').read(), open(os.path.join(d, '.err'), errors='replace').read()


def native(f):
    exe = os.path.join(tmp, os.path.basename(f)[:-3] + '.native')
    subprocess.run(vu + ['build', f, '-o', exe], check=True, capture_output=True)
    r = subprocess.run([exe], capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout


def check(name, ok, detail):
    if ok:
        counts['passed'] += 1
        print(f'ok    {name}')
    else:
        counts['failed'] += 1
        print(f'FAIL  {name}\n      {detail[:600]}')


jobs = []
for f in files:
    kind, want, args = header(f)
    if '/targeted/' in f and kind not in ('output', 'panic'):
        continue
    jobs.append((f, kind, want, args))
with cf.ThreadPoolExecutor(os.cpu_count() or 2) as pool:
    built = list(pool.map(lambda j: build(j[0]), jobs))
for (f, kind, want, args), (d, r) in zip(jobs, built):
    if r.returncode == 2 and r.stderr.startswith('vu: ') and 'WebAssembly' in r.stderr:
        counts['skipped'] += 1
        continue
    if r.returncode:
        check(f, False, f'build failed (exit {r.returncode}): {r.stderr}')
        continue
    rc, out, err = run(d, args)
    base = os.path.basename(f)[:-3]
    if base in KNOWN:
        counts['known'] += 1
        continue
    if kind == 'output':
        check(f, rc == 0 and out.replace('\0', '').rstrip('\n') == want, f'exit {rc}, output [{out[:300]}] {err[:300]}')
    elif kind == 'panic':
        check(f, (rc == 101 and want in out + err) or ('stack overflow' in want and rc == 'trap: call stack exhausted'), f'exit {rc}, output [{out[:200]}] {err[:300]}')
    else:
        nrc, nout = native(f)
        check(f, rc == nrc and out == nout, f'exit {rc} (native {nrc}), output [{out[:200]}] native [{nout[:200]}] {err[:200]}')
print(f'{counts["passed"]} passed, {counts["failed"]} failed, {counts["skipped"]} refused as they should be, {counts["known"]} known differences')
sys.exit(1 if counts['failed'] else 0)
