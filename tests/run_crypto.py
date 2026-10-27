"""sha256, hmac_sha256, pbkdf2_sha256, b64encode/b64decode and hex/from_hex against Python's hashlib,
hmac and base64 on random inputs (lengths around the 64-byte block and padding edges), optimized and
under the sanitizers; random_bytes gives different bytes each time; malformed base64 and hex fail."""
import base64
import hashlib
import hmac
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
rng = random.Random(11)
work = tempfile.mkdtemp()
cases = []
lengths = [0, 1, 2, 3, 55, 56, 57, 63, 64, 65, 119, 120, 127, 128, 129, 1000, 4096]
for i in range(300):
    n = lengths[i % len(lengths)] if i < 100 else rng.randint(0, 300)
    data = bytes(rng.randrange(256) for _ in range(n))
    key = bytes(rng.randrange(256) for _ in range(rng.choice([0, 1, 16, 32, 63, 64, 65, 100, 200])))
    salt = bytes(rng.randrange(256) for _ in range(rng.choice([0, 8, 16, 64])))
    iters = rng.choice([1, 2, 3, 10, 100, 4096])
    cases.append((key, data, salt, iters))
inp = os.path.join(work, 'in.txt')
with open(inp, 'w') as f:
    for key, data, salt, iters in cases:
        f.write(f'{key.hex()} {data.hex()} {salt.hex()} {iters}\n')
ok = True
for flags in ([], ['--san']):
    prog = os.path.join(work, 'ops')
    r = subprocess.run(VU + ['build', f'{HERE}/crypto/ops.vu', '-o', prog] + flags, capture_output=True, text=True)
    if r.returncode:
        print('FAIL  build', r.stderr[:400]); sys.exit(1)
    r = subprocess.run([prog, inp], capture_output=True, text=True, timeout=600)
    lines = r.stdout.split('\n')
    bad = 0
    if r.returncode or 'ERROR' in r.stderr or 'runtime error' in r.stderr:
        print('FAIL  run', r.returncode, r.stderr[:500]); ok = False; continue
    for (key, data, salt, iters), line in zip(cases, lines):
        want = ' '.join([hashlib.sha256(data).hexdigest(), hashlib.sha1(data).hexdigest(), hmac.new(key, data, 'sha256').hexdigest(),
                         hashlib.pbkdf2_hmac('sha256', key, salt, iters).hex(), base64.b64encode(data).decode(), 'same'])
        if line != want:
            bad += 1
            if bad < 5: print(f'FAIL  key={key.hex()} data={data.hex()} salt={salt.hex()} i={iters}\n      got  {line}\n      want {want}')
    tail = lines[len(cases):len(cases) + 2]
    if tail != ['32 true', '11 rejected']:
        print('FAIL  random/malformed:', tail); bad += 1
    print(f'{len(cases) + 1 - bad} of {len(cases) + 1} agree with Python ({" ".join(flags) or "optimized"})')
    ok = ok and bad == 0
sys.exit(0 if ok else 1)
