"""Debugging support: panic reports (text and JSON), backtraces, JSON compile errors, #line for gdb.
Runs every check against the compiler named by VU (default: ../vu, the compiler), in quick builds (vu run), optimized
builds, and quick builds under AddressSanitizer/UBSan and ThreadSanitizer."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
D = os.path.join(HERE, 'debug')
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


def run(args, cwd=D, env=None, timeout=120):
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run(args, cwd=cwd, capture_output=True, env=e, timeout=timeout)
    # surrogateescape keeps invalid bytes recoverable, so one_json can insist on strict UTF-8
    return r.returncode, r.stdout.decode('utf-8', 'surrogateescape'), r.stderr.decode('utf-8', 'surrogateescape')


def vu(*args, **kw):
    return run(VU + list(args), **kw)


def frames(err):
    return [l.strip() for l in err.splitlines() if l.startswith('  at ') or l.startswith('  called from ')]


def one_json(err):
    """stderr must be exactly one JSON object (one line)."""
    lines = [l for l in err.splitlines() if l.strip()]
    if len(lines) != 1:
        return None
    try:
        return json.loads(lines[0].encode('utf-8', 'surrogateescape').decode('utf-8'))   # JSON must be UTF-8
    except ValueError:
        return None


# ---- text reports in quick builds
rc, out, err = vu('run', '30_task_panic.vu')
check('task panic: the trace goes through the task to the line that spawned it', rc == 101 and frames(err) == [
    'at 30_task_panic.vu:2 in boom', 'called from 30_task_panic.vu:5 in worker', 'called from 30_task_panic.vu:8 in spawn'], err)
rc, out, err = vu('run', '03_par_panic.vu')
check('par worker panic: the trace reaches the loop in main', rc == 101 and frames(err) == [
    'at 03_par_panic.vu:2 in boom', 'called from 03_par_panic.vu:7 in main'], err)
rc, out, err = vu('run', '04_par_overflow.vu')
f = frames(err)
check('stack overflow in a par worker: one collapsed line, then main', rc == 101 and len(f) == 2
      and f[0].startswith('at 04_par_overflow.vu:2 in down (') and f[0].endswith(' times in a row)')
      and f[1] == 'called from 04_par_overflow.vu:6 in main', err)
rc, out, err = vu('run', '05_stale_frames_after_fail.vu')
check('frames of functions that failed with ? are gone', rc == 101 and frames(err) == ['at 05_stale_frames_after_fail.vu:16 in main'], err)
rc, out, err = vu('run', '06_stale_frames_after_return.vu')
check('frames of functions that returned from inside loops are gone', rc == 101 and frames(err) == ['at 06_stale_frames_after_return.vu:13 in main'], err)
rc, out, err = vu('run', '12_frames_balanced.vu')
check('100,000 calls later the stack is balanced', rc == 101 and frames(err) == ['at 12_frames_balanced.vu:10 in main'], err)
rc, out, err = vu('run', '07_mutual_json.vu')
f = frames(err)
check('mutual recursion: 12 lines, a count of the rest, then main', rc == 101 and len(f) == 13
      and err.count('more calls') == 1 and f[-1] == 'called from 07_mutual_json.vu:9 in main', err)
rc, out, err = vu('run', '09_overflow_json.vu')
f = frames(err)
check('stack overflow: one line with a count, then main', rc == 101 and len(f) == 2 and 'times in a row' in f[0], err)
rc, out, err = vu('run', '11_exit_mid_trace.vu')
check('exit() deep in calls: output kept, no report', rc == 0 and out == 'bye\n' and err == '', err)
rc, out, err = vu('run', '02_huge_panic.vu')
first = err.split('\n', 1)[0]
check('a 3 MB panic message is reported (capped at 1,000,000 bytes), then the location',
      rc == 101 and len(first) == len('panic: ') + 1000000 and frames(err) == ['at 02_huge_panic.vu:4 in main'], f'{len(first)}')
rc, out, err = vu('run', '08_uncaught_json.vu')
check('main returning an error: "error: ..." and exit 1', rc == 1 and err == "error: not an Int: 'not \"a\" number'\n", err)

rc, out, err = vu('run', '19_recursion_below_top.vu')
check('recursion below a top frame on another line: exact counts', rc == 101 and err ==
      'panic: index 9 out of bounds for a list of length 1\n  at 19_recursion_below_top.vu:2 in f\n'
      '  called from 19_recursion_below_top.vu:3 in f (1000 times in a row)\n  called from 19_recursion_below_top.vu:6 in main\n', err)
rc, out, err = vu('run', '--json', '18_all_bytes.vu')
j = one_json(err)
check('panic() with all 256 byte values: zero bytes kept (printf once cut the message at the first)',
      rc == 101 and j and j['message'] == bytes(range(256)).decode('utf-8', 'replace'), err[:200])
# messages around the 512-byte formatting buffer and the 4,096-byte output buffer
bad = []
for n in [504, 505, 506, 4080, 4081, 4082, 4083, 8170, 8171]:
    src = os.path.join(work, f'len{n}.vu')
    with open(src, 'w') as fh:
        fh.write(f'fn main():\n  var s = ""\n  for i in 0..{n}: s += "x"\n  panic(s)\n')
    rc, out, err = vu('run', src, cwd=work)
    if err != 'panic: ' + 'x' * n + f'\n  at {src}:4 in main\n':
        bad.append(n)
check('panic messages around the buffer sizes come out exactly', not bad, str(bad))

# ---- optimized builds: the panic's own line only
rc, out, err = vu('run', '--release', '06_stale_frames_after_return.vu')
check('--release: location without a backtrace', rc == 101 and frames(err) == ['at 06_stale_frames_after_return.vu:13'], err)
rc, out, err = vu('run', '--release', '09_overflow_json.vu')
check('--release stack overflow: message, no frames', rc == 101 and err == 'panic: stack overflow (recursion too deep)\n', err)

# ---- JSON reports
rc, out, err = vu('run', '--json', '01_json_escapes.vu')
j = one_json(err)
check('JSON panic: quotes, backslash, newline, tab and control bytes survive exactly',
      rc == 101 and j and j['type'] == 'panic' and j['message'] == 'bad "quote" and "\\\n\t\x01\x7f end'
      and j['file'] == '01_json_escapes.vu' and j['line'] == 3 and j['backtrace'] == [
          {'function': 'main', 'file': '01_json_escapes.vu', 'line': 3}], err)
rc, out, err = vu('run', '--json', '13_invalid_utf8_panic.vu')
j = one_json(err)
check('JSON panic with invalid UTF-8 bytes: still valid UTF-8 JSON, bad bytes as U+FFFD',
      rc == 101 and j and j['message'] == '\U0001F600\u20ac' + '\ufffd' * 12, err.encode('utf-8', 'surrogateescape')[:200])
rc, out, err = vu('run', '--json', '07_mutual_json.vu')
j = one_json(err)
check('JSON mutual recursion: at most 48 frames plus more_calls', rc == 101 and j and len(j['backtrace']) == 48
      and j['more_calls'] > 0 and j['backtrace'][0] == {'function': 'g', 'file': '07_mutual_json.vu', 'line': 2}, err[:300])
rc, out, err = vu('run', '--json', '09_overflow_json.vu')
j = one_json(err)
check('JSON stack overflow: collapsed frame carries times', rc == 101 and j and j['backtrace'][0]['times'] > 1000
      and j['backtrace'][-1] == {'function': 'main', 'file': '09_overflow_json.vu', 'line': 5}, err[:300])
rc, out, err = vu('run', '--json', '08_uncaught_json.vu')
check('JSON uncaught error', rc == 1 and one_json(err) == {'type': 'error', 'message': "not an Int: 'not \"a\" number'"}, err)
rc, out, err = vu('check', '--json', '10_tab_source.vu')
check('JSON compile error: file, line, message, source (with its tab)', rc == 1 and one_json(err) == {
    'type': 'error', 'file': '10_tab_source.vu', 'line': 3, 'message': 'expected Int, found Str',
    'source': '  let x: Int = s'}, err)
rc, out, err = vu('run', '--release', '03_par_panic.vu', env={'VU_PANIC': 'json'})
j = one_json(err)
check('VU_PANIC=json at run time switches any binary to JSON', rc == 101 and j and j['type'] == 'panic' and j['line'] == 2, err)
odd = os.path.join('odd"dir\\x', 'we"ird\\name.vu')
rc, out, err = vu('run', '--json', odd)
j = one_json(err)
check('a path with quotes and backslashes: valid C (#line) and valid JSON', rc == 101 and j and j['file'] == odd
      and j['backtrace'][0]['line'] == 2, err)

# ---- quick builds under the sanitizers: the shadow stack and reporter make no memory or thread errors
for name in ['03_par_panic.vu', '05_stale_frames_after_fail.vu', '07_mutual_json.vu', '01_json_escapes.vu', '12_frames_balanced.vu']:
    exe = os.path.join(work, 'san')
    rc, out, err = vu('build', '--debug', '--san', name, '-o', exe)
    rc2, out2, err2 = run([exe]) if rc == 0 else (rc, out, err)
    check(f'--debug --san {name}: reports cleanly, no sanitizer findings',
          rc == 0 and rc2 == 101 and 'Sanitizer' not in err2 and 'runtime error' not in err2 and 'panic:' in err2, err + err2)
archer = os.environ.get('ARCHER', '/usr/lib/llvm-18/lib/libarcher.so')
if os.path.exists(archer) and shutil.which('clang'):
    exe = os.path.join(work, 'tsan')
    src = os.path.join(work, 'par_ok.vu')
    with open(src, 'w') as fh:
        fh.write('fn work(i: Int) -> Int:\n  var t = 0\n  for k in 0..100: t += k * i\n  return t\n\n'
                 'fn main():\n  var out = [0] * 2000\n  par for i in 0..2000:\n    out[i] = work(i)\n  print("{out[1999]}")\n')
    rc, out, err = vu('build', '--debug', '--tsan', src, '-o', exe, env={'CC': 'clang'})
    rc2, out2, err2 = run([exe], env={'OMP_TOOL_LIBRARIES': archer, 'OMP_NUM_THREADS': '4',
                                      'TSAN_OPTIONS': f'suppressions={HERE}/tsan.supp'}) if rc == 0 else (rc, out, err)
    check('--debug --tsan: par workers sharing the loop frame race-free', rc == 0 and rc2 == 0 and out2 == '9895050\n'
          and 'data race' not in err2, err + err2[:400])

# ---- many par workers panicking at once: exactly one report, no races in the reporter
for i in range(5):
    rc, out, err = vu('run', '14_simultaneous_panics.vu', env={'OMP_NUM_THREADS': '8'})
    if not (rc == 101 and err.count('panic:') == 1):
        break
check('4,000 par iterations panicking at once: exactly one report (5 runs)', rc == 101 and err.count('panic:') == 1, err[:400])
if os.path.exists(archer) and shutil.which('clang'):
    exe = os.path.join(work, 'tsan2')
    rc, out, err = vu('build', '--debug', '--tsan', '14_simultaneous_panics.vu', '-o', exe, env={'CC': 'clang'})
    rc2, out2, err2 = run([exe], env={'OMP_TOOL_LIBRARIES': archer, 'OMP_NUM_THREADS': '8',
                                      'TSAN_OPTIONS': f'suppressions={HERE}/tsan.supp'}) if rc == 0 else (rc, out, err)
    check('--tsan: simultaneous panics race-free', rc == 0 and rc2 == 101 and 'data race' not in err2
          and err2.count('panic:') == 1, err + err2[:400])
# Every worker overflowing its stack at once: the report must stay whole (the signal handler once
# cleared the buffer before taking the lock, wiping another thread's half-written report).
exe = os.path.join(work, 'ovf')
vu('build', '--debug', '15_simultaneous_overflows.vu', '-o', exe)
bad = ''
for i in range(20):
    rc, out, err = run([exe], env={'OMP_NUM_THREADS': '8'})
    lines = err.splitlines()
    if not (rc == 101 and len(lines) == 3 and lines[0] == 'panic: stack overflow (recursion too deep)'
            and 'times in a row' in lines[1] and lines[2] == '  called from 15_simultaneous_overflows.vu:6 in main'):
        bad = err
        break
check('64 workers overflowing at once: one whole report (20 runs)', not bad, bad[:400])
exe = os.path.join(work, 'mix')
vu('build', '--debug', '16_overflow_and_panic.vu', '-o', exe)
bad = ''
for i in range(20):
    rc, out, err = run([exe], env={'OMP_NUM_THREADS': '8'})
    if not (rc == 101 and err.count('panic:') == 1 and err.startswith('panic: ')):
        bad = err
        break
check('stack overflows and ordinary panics racing: one whole report (20 runs)', not bad, bad[:400])
# exit() in one worker while another panics: whichever wins, the output and the exit code agree.
exe = os.path.join(work, 'exr')
vu('build', '--debug', '17_exit_vs_panic.vu', '-o', exe)
bad = ''
for i in range(30):
    rc, out, err = run([exe], env={'OMP_NUM_THREADS': '8'})
    if not ((rc == 3 and 'panic' not in err) or (rc == 101 and err.count('panic:') == 1)):
        bad = f'rc={rc} {err}'
        break
check('exit(3) racing a panic: exit code and report always agree (30 runs)', not bad, bad[:400])
if os.path.exists(archer) and shutil.which('clang'):
    exe = os.path.join(work, 'tsan3')
    rc, out, err = vu('build', '--debug', '--tsan', '17_exit_vs_panic.vu', '-o', exe, env={'CC': 'clang'})
    rc2, out2, err2 = run([exe], env={'OMP_TOOL_LIBRARIES': archer, 'OMP_NUM_THREADS': '8',
                                      'TSAN_OPTIONS': f'suppressions={HERE}/tsan.supp'}) if rc == 0 else (rc, out, err)
    check('--tsan: exit racing a panic is race-free', rc == 0 and rc2 in (3, 101) and 'data race' not in err2, err + err2[:600])
rc, out, err = vu('run', os.path.join('..', 'selfhost', 'r27_bom.vu'))
check('a UTF-8 byte-order mark at the start of a file is skipped', rc == 0 and out == 'bom\n', err)

# ---- gdb sees Vu source lines
if shutil.which('gdb'):
    exe = os.path.join(work, 'g')
    vu('build', '--debug', '06_stale_frames_after_return.vu', '-o', exe)
    rc, out, err = run(['gdb', '-batch', '-ex', 'break 06_stale_frames_after_return.vu:4', '-ex', 'run', '-ex', 'bt', exe])
    bt = [l for l in out.splitlines() if l.startswith('#')]
    check('gdb: breakpoint by Vu line; frames show Vu lines', len(bt) >= 2 and bt[0].endswith('06_stale_frames_after_return.vu:4')
          and bt[1].endswith('06_stale_frames_after_return.vu:11'), out[-600:])

# ---- the line limit: a location keeps the line in 24 bits, so 16,777,215 lines is the most a file can have
big = os.path.join(work, 'lastline.vu')
with open(big, 'w') as fh:
    fh.write('fn main():\n' + '\n' * 16777213 + '  print("{[1][5]}")\n')     # 16,777,215 lines, final newline
rc, out, err = vu('run', '--json', 'lastline.vu', cwd=work, timeout=600)
j = one_json(err)
check('a panic on line 16,777,215 (the last allowed) is reported on that line', rc == 101 and j and j['line'] == 16777215, err[:300])
with open(big, 'w') as fh:
    fh.write('fn main():\n' + '\n' * 16777214 + '  print("x")\n')            # 16,777,216 lines
rc, out, err = vu('check', 'lastline.vu', cwd=work, timeout=600)
check('16,777,216 lines: a clear error', rc == 1 and 'can have at most 16,777,215 lines' in err, err[:300])
with open(big, 'w') as fh:
    fh.write('fn main():\n' + '\n' * 16777213 + '  print("x")')             # 16,777,215 lines, no final newline
rc, out, err = vu('check', 'lastline.vu', cwd=work, timeout=600)
check('16,777,215 lines without a final newline: accepted', rc == 0, err[:300])

shutil.rmtree(work)
print(f'{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
