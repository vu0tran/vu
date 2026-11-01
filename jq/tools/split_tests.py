# Runs each test of a jq .test file separately (with a timeout) and reports failures.
import subprocess, sys, os, tempfile
binary, path = sys.argv[1], sys.argv[2]
cwd = sys.argv[3] if len(sys.argv) > 3 else None
lines = open(path, encoding='utf-8', errors='surrogateescape').read().split('\n')
blocks = []; i = 0; pending_fail = []
while i < len(lines):
    l = lines[i]
    if l.strip() == '' or l.startswith('#'):
        i += 1; continue
    if l.startswith('%%FAIL'):
        pending_fail = [l]; i += 1; continue
    blk = pending_fail + [l]; pending_fail = []
    i += 1
    while i < len(lines) and lines[i].strip() != '':
        blk.append(lines[i]); i += 1
    blocks.append(blk)
passed = 0; fails = []
tmpd = tempfile.mkdtemp()
for n, blk in enumerate(blocks):
    f = os.path.join(tmpd, 't.test')
    open(f, 'w', encoding='utf-8', errors='surrogateescape').write('\n'.join(blk) + '\n')
    try:
        r = subprocess.run([binary] + (['-L', 'modules'] if cwd else []) + ['--run-tests', f], capture_output=True, timeout=10, cwd=cwd)
        out = r.stdout.decode('utf-8', 'replace')
        if '\n1 of 1 tests passed' in '\n' + out:
            passed += 1
        else:
            msg = [x for x in out.split('\n') if x.startswith('***')]
            err = r.stderr.decode('utf-8', 'replace').strip().split('\n')[:3]
            fails.append((n + 1, blk[0] if not blk[0].startswith('%%') else blk[1], (msg + err)[:3]))
    except subprocess.TimeoutExpired:
        fails.append((n + 1, blk[0], ['TIMEOUT']))
for n, prog, msg in fails:
    print(f'#{n}: {prog[:120]}')
    for m in msg: print('    ' + m[:300])
print(f'{passed} of {len(blocks)} passed')
