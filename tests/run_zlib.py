"""std/zlib against Python's zlib: random data of many kinds, compressed by zlib at every level and
strategy into the zlib, gzip (with every optional header field) and raw formats, and some of it then
damaged (bits flipped, cut short, header bytes changed, junk appended). For each case std/zlib must
succeed exactly when Python's zlib.decompress does, with the same bytes, and fail otherwise; how
often the messages agree too is reported. Also crc32 and adler32, and the result-size limit.
  python3 tests/run_zlib.py [SEEDS] [CASES_PER_SEED]"""
import os
import random
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
per = int(sys.argv[2]) if len(sys.argv) > 2 else 400
WBITS = {0: 15, 1: 31, 2: -15, 4: 15, 5: 31, 6: -15}


def sample(r, depth=0):
    k = r.random() * (0.8 if depth else 1)
    n = r.choice([0, 1, 2, 7, 100, 1000, 5000, 40000, 70000, 200000]) if r.random() < 0.9 else r.randint(0, 400000)
    if k < 0.15:
        return bytes(r.getrandbits(8) for _ in range(min(n, 50000)))
    if k < 0.45:
        words = [bytes(r.choice(b'etaoinshrdlu  ,.\n') for _ in range(r.randint(1, 9))) for _ in range(r.randint(1, 400))]
        out = bytearray()
        while len(out) < n:
            out += r.choice(words) + b' '
        return bytes(out[:n])
    if k < 0.6:
        return bytes([r.getrandbits(8)]) * n
    if k < 0.8:
        pat = bytes(r.getrandbits(8) for _ in range(r.randint(1, 300)))
        return (pat * (n // len(pat) + 1))[:n]
    # pieces of all of the above
    out = b''
    while len(out) < n:
        out += sample(random.Random(r.random()), 1)[:r.randint(1, 30000)] or b'x'
    return out[:n]


def compress(r, data, mode):
    level = r.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, -1])
    strategy = r.choice([zlib.Z_DEFAULT_STRATEGY] * 3 + [zlib.Z_FILTERED, zlib.Z_HUFFMAN_ONLY, zlib.Z_RLE, zlib.Z_FIXED])
    if mode == 1 and r.random() < 0.5:
        return gzip_by_hand(r, data, level, strategy)
    wb = r.randint(9, 15)
    wbits = {0: wb, 1: 16 + wb, 2: -wb}[mode]
    c = zlib.compressobj(level, zlib.DEFLATED, wbits, r.randint(1, 9), strategy)
    if r.random() < 0.2:   # flushes in the middle make empty stored blocks and partial-byte boundaries
        out = b''
        at = 0
        while at < len(data):
            step = r.randint(1, 20000)
            out += c.compress(data[at:at + step]) + c.flush(r.choice([zlib.Z_SYNC_FLUSH, zlib.Z_FULL_FLUSH, zlib.Z_NO_FLUSH]))
            at += step
        return out + c.flush()
    return c.compress(data) + c.flush()


def gzip_by_hand(r, data, level, strategy):
    flags = 0
    extra = b''
    if r.random() < 0.5:
        flags |= 4
        x = bytes(r.getrandbits(8) for _ in range(r.randint(0, 40)))
        extra += struct.pack('<H', len(x)) + x
    if r.random() < 0.5:
        flags |= 8
        extra += bytes(r.choice(b'abc.txt') for _ in range(r.randint(0, 20))) + b'\0'
    if r.random() < 0.5:
        flags |= 16
        extra += b'a comment' * r.randint(0, 3) + b'\0'
    if r.random() < 0.3:
        flags |= 1   # FTEXT: just a hint
    head = bytes([31, 139, 8, flags]) + struct.pack('<I', r.getrandbits(32)) + bytes([0, 3]) + extra
    if r.random() < 0.4:
        head = bytes([31, 139, 8, flags | 2]) + head[4:]
        head += struct.pack('<H', zlib.crc32(head) & 0xFFFF)
    c = zlib.compressobj(level, zlib.DEFLATED, -15, 8, strategy)
    body = c.compress(data) + c.flush()
    return head + body + struct.pack('<II', zlib.crc32(data), len(data) & 0xFFFFFFFF)


def damage(r, blob):
    k = r.random()
    b = bytearray(blob)
    if k < 0.35 and b:
        for _ in range(r.randint(1, 4)):
            i = r.randrange(len(b))
            b[i] ^= 1 << r.randrange(8)
    elif k < 0.6 and b:
        del b[r.randrange(len(b)):]
    elif k < 0.75 and b:
        b[r.randrange(min(len(b), 12))] = r.getrandbits(8)
    elif k < 0.85:
        b += bytes(r.getrandbits(8) for _ in range(r.randint(1, 30)))
    else:
        b = bytearray(r.getrandbits(8) for _ in range(r.randint(0, 300)))   # junk
    return bytes(b)


def python(mode, blob, limit):
    try:
        out = zlib.decompress(blob, WBITS[mode])
    except zlib.error as e:
        return 'err', str(e).split(': ', 1)[-1]
    if limit and len(out) > limit:
        return 'err', 'the result is longer than'
    if mode >= 4:   # streamed: also the input after the end of the stream
        d = zlib.decompressobj(WBITS[mode])
        d.decompress(blob)
        return 'ok', f'{len(out)} {zlib.crc32(out)} {len(d.unused_data)}'
    return 'ok', f'{len(out)} {zlib.crc32(out)}'


def main():
    work = tempfile.mkdtemp()
    exe = os.path.join(work, 'driver')
    builds = [('release', [])]
    if os.environ.get('ZLIB_SAN', '1') == '1':
        builds.append(('sanitizers', ['--san']))
    passed = failed = msg_same = msg_total = 0
    for name, flags in builds:
        b = subprocess.run(VU + ['build', f'{HERE}/zlib/driver.vu', '-o', exe] + flags, capture_output=True, text=True)
        if b.returncode:
            print('FAIL  driver does not build:', b.stderr[:500])
            sys.exit(1)
        n_seeds = seeds if name == 'release' else max(1, seeds // 3)
        for seed in range(n_seeds):
            r = random.Random(seed * 7919 + (name == 'sanitizers'))
            cases = []
            for _ in range(per):
                mode = r.choice([0, 1, 2, 3, 4, 5, 6, 4, 5, 6])
                data = sample(r)
                if mode == 3:
                    cases.append((3, 0, data, ('crc', f'{zlib.crc32(data)} {zlib.adler32(data)}'), 0))
                    continue
                blob = compress(r, data, mode if mode < 4 else mode - 4)
                if r.random() < 0.4:
                    blob = damage(r, blob)
                limit = 0
                if r.random() < 0.1:
                    limit = r.randint(1, max(1, len(data) * 2))
                piece = r.choice([1, 2, 7, 100, 4096, 65536, 1 << 20])
                if mode >= 4 and piece < 7 and len(blob) > 20000: piece = 13   # (a byte at a time is slow in Python's harness, not in Vu)
                cases.append((mode, limit, blob, python(mode, blob, limit), piece))
            path = os.path.join(work, 'cases')
            with open(path, 'wb') as f:
                for mode, limit, blob, _, piece in cases:
                    f.write(bytes([mode]) + struct.pack('<III', limit, piece, len(blob)) + blob)
            p = subprocess.run([exe, path], capture_output=True, timeout=600)
            lines = p.stdout.decode('latin-1').split('\n')
            if p.returncode != 0 or len(lines) < len(cases):
                failed += 1
                print(f'FAIL  {name} seed {seed}: exit {p.returncode}, {len(lines) - 1} of {len(cases)} answers\n      {p.stderr.decode("latin-1")[-600:]}')
                continue
            for i, (mode, limit, blob, want, piece) in enumerate(cases):
                kind, _, rest = lines[i].partition(' ')
                ok = kind == want[0] and (kind == 'err' or rest == want[1])
                if kind == 'err' and want[0] == 'err' and not limit:   # (with a limit, Vu may stop before the damage)
                    msg_total += 1
                    same = rest.startswith(want[1]) or want[1].startswith(rest)
                    msg_same += same
                    if not same and msg_total - msg_same <= 5:
                        print(f'note  message differs (mode {mode}): Vu {rest!r}, zlib {want[1]!r}')
                if ok:
                    passed += 1
                else:
                    failed += 1
                    if failed <= 15:
                        print(f'FAIL  {name} seed {seed} case {i} (mode {mode}, limit {limit}, {len(blob)} bytes): Vu {lines[i][:120]!r}, Python {want}')
    # a zip bomb: 200 MB of zeros (about 200 KB of gzip) with a 1 MB limit fails at once, in little memory
    import gzip
    import time
    bomb = gzip.compress(b'\0' * (200 << 20), 9)
    path = os.path.join(work, 'bomb')
    with open(path, 'wb') as f:
        f.write(bytes([5]) + struct.pack('<III', 1 << 20, 4096, len(bomb)) + bomb)
    b = subprocess.run(VU + ['build', f'{HERE}/zlib/driver.vu', '-o', exe], capture_output=True, text=True)
    t = time.perf_counter()
    # (started from a small helper: a process's peak memory survives fork and exec, and this one is big)
    helper = ('import os, subprocess, sys\n'
              'p = subprocess.Popen(sys.argv[1:], stdout=subprocess.PIPE)\n'
              '_, _, ru = os.wait4(p.pid, 0)\n'
              'sys.stdout.write(str(ru.ru_maxrss) + " " + p.stdout.read().decode())')
    r = subprocess.run([sys.executable, '-c', helper, exe, path], capture_output=True, text=True, timeout=60)
    took = time.perf_counter() - t
    kb, _, out = r.stdout.partition(' ')
    ok = out.startswith('err the result is longer than 1048576 bytes')
    rss = int(kb or 0) / 1024
    if ok and took < 2 and rss < 64:
        passed += 1
        print(f'ok    zip bomb ({len(bomb)} bytes of gzip for 200 MB) stopped at the 1 MB limit in {took:.3f} s, {rss:.0f} MB at most')
    else:
        failed += 1
        print(f'FAIL  zip bomb: {out[:100]!r} in {took:.2f} s, {rss:.0f} MB')
    print(f'error messages the same as zlib\'s: {msg_same} of {msg_total}')
    print(f'{passed} passed, {failed} failed')
    sys.exit(1 if failed else 0)


main()
