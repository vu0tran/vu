"""std/time's zones against Python's zoneinfo, which reads the same tz database files with its own
parser: the local time, abbreviation and DST flag at random instants and at instants around every
offset change found, and from_local on wall-clock times around those changes (the gaps when clocks
go forward and the repeated hour when they go back, which Python resolves with fold=0), across
years 1800-2200 (after 2037 most zones run on the file's POSIX rule). Then broken and hostile TZif
files. Extra arguments (--san) go to the build."""
import datetime as dt
import os, random, struct, subprocess, sys, zoneinfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, check, counts, work  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'time', 'zones.vu'))
rng = random.Random(int(os.environ.get('SEED', '7')))
names = sorted(n for n in zoneinfo.available_timezones() if os.path.exists('/usr/share/zoneinfo/' + n))
if not names:
    print('skipped: no tz database'); print('0 passed, 0 failed'); sys.exit(0)
pick = rng.sample(names, min(len(names), int(os.environ.get('ZONES', '100000'))))
for must in ['America/New_York', 'Europe/London', 'Europe/Dublin', 'Australia/Lord_Howe', 'Pacific/Apia',
             'Asia/Kolkata', 'America/St_Johns', 'Africa/Casablanca', 'America/Sao_Paulo', 'Antarctica/Troll',
             'Pacific/Chatham', 'Australia/Sydney', 'Pacific/Auckland', 'UTC', 'Etc/GMT+5', 'America/Godthab', 'Asia/Tehran', 'Europe/Moscow']:
    if must in names and must not in pick:
        pick.append(must)

LO, HI = int(dt.datetime(1800, 1, 1, tzinfo=dt.timezone.utc).timestamp()), int(dt.datetime(2200, 1, 1, tzinfo=dt.timezone.utc).timestamp())


def off(z, t):
    return int(dt.datetime.fromtimestamp(t, z).utcoffset().total_seconds())


def changes(z):
    """Instants where the offset changes, found by stepping 20 days and bisecting."""
    out = []
    step = 20 * 86400
    t = LO
    o = off(z, t)
    while t < HI:
        u = min(t + step, HI)
        ou = off(z, u)
        if ou != o:
            a, b = t, u
            while b - a > 1:
                m = (a + b) // 2
                if off(z, m) == o: a = m
                else: b = m
            out.append((b, o, ou))
        t, o = u, ou
    return out


def local_line(z, t):
    d = dt.datetime.fromtimestamp(t, z)
    return f'{d.isoformat(timespec="milliseconds")} {d.tzname()} {1 if d.dst() else 0}'


cmds, want = [], []
for name in pick:
    z = zoneinfo.ZoneInfo(name)
    ch = changes(z)
    ts = [rng.randint(LO, HI) for _ in range(30)]
    for (T, a, b) in rng.sample(ch, min(len(ch), 25)):
        ts += [T - 1, T, T + 1, T + rng.randint(-7200, 7200)]
        for _ in range(3):
            wall = T + rng.randint(min(a, b) - 3600, max(a, b) + 3600)
            w = dt.datetime(1970, 1, 1) + dt.timedelta(seconds=wall)
            cmds.append(f'F {name} {w.year} {w.month} {w.day} {w.hour} {w.minute} {w.second}')
            want.append(str(int(w.replace(tzinfo=z).timestamp())))
    for t in ts:
        cmds.append(f'L {name} {t}')
        want.append(local_line(z, t))

r = subprocess.run([exe], input='\n'.join(cmds) + '\n', capture_output=True, text=True, timeout=600)
got = r.stdout.rstrip('\n').split('\n')
check('zones ran', r.returncode == 0 and len(got) == len(want), f'exit {r.returncode}, {len(got)} lines for {len(want)}\n{r.stderr[-400:]}')
by_kind = {}
for c, w, g in zip(cmds, want, got):
    k = c[0]
    by_kind.setdefault(k, [0, []])
    by_kind[k][0] += 1
    if w != g:
        by_kind[k][1].append(f'{c}: want [{w}] got [{g}]')
for k, (n, bad) in sorted(by_kind.items()):
    what = {'L': 'local time, abbreviation, DST', 'F': 'from_local (gaps and repeats by fold=0)'}[k]
    check(f'{what}: {n} cases over {len(pick)} zones', not bad, f'{len(bad)} differ:\n' + '\n'.join(bad[:8]))

# Broken and hostile TZif files: each must give an error, never a crash.
good = open('/usr/share/zoneinfo/America/New_York', 'rb').read()
files = {
    'empty': b'',
    'not TZif': b'XXXX' + good[4:],
    'version 9': good[:4] + b'9' + good[5:],
    'cut in the header': good[:30],
    'cut in the data': good[:200],
    'cut before the footer': good[:-30],
    'no footer newline': good[:-1],
    'a huge count': good[:32] + struct.pack('>I', 0xFFFFFFFF) + good[36:],
    'counts past the end': good[:36] + struct.pack('>I', 1 << 20) + good[40:],
}
v1len = 44 + sum(struct.unpack('>6I', good[20:44])[i] * w for i, w in zip(range(6), [1, 1, 8, 5, 6, 1]))
h2 = v1len
cnt = struct.unpack('>6I', good[h2 + 20:h2 + 44])
tstart = h2 + 44
files['transitions out of order'] = good[:tstart] + good[tstart + 8:tstart + 16] + good[tstart:tstart + 8] + good[tstart + 16:]
istart = tstart + cnt[3] * 8
files['a type index past the types'] = good[:istart] + bytes([200]) + good[istart + 1:]
ty = istart + cnt[3]
files['an offset of a week'] = good[:ty] + struct.pack('>i', 7 * 86400) + good[ty + 4:]
files['an abbreviation index past the text'] = good[:ty + 5] + bytes([250]) + good[ty + 6:]
foot = good.rindex(b'\n', 0, len(good) - 1)
for bad_rule in [b'EST', b'E5', b'EST5EDT,M13.1.0,M11.1.0', b'EST5EDT,M3.2.0', b'EST99', b'<+03', b'EST5EDT,J0,J365', b'EST5EDT,M3.2.0/200,M11.1.0']:
    files[f'rule {bad_rule.decode()}'] = good[:foot + 1] + bad_rule + b'\n'
okfiles = {'rule <+0330>-3:30': good[:foot + 1] + b'<+0330>-3:30\n',
           'rule with no dates': good[:foot + 1] + b'EST5EDT\n',
           'rule DST all year': good[:foot + 1] + b'EST5EDT,0/0,J365/25\n',
           'version 1 only': good[:4] + b'\0' + good[5:v1len]}
for i in range(300):
    b = bytearray(good)
    for _ in range(rng.randint(1, 6)):
        b[rng.randrange(len(b))] = rng.randrange(256)
    files[f'fuzz {i}'] = bytes(b)
cmds = []
for k, data in list(files.items()) + list(okfiles.items()):
    p = os.path.join(work, f'tz{len(cmds)}')
    open(p, 'wb').write(data)
    cmds.append((k, f'P {p}'))
r = subprocess.run([exe], input='\n'.join(c for _, c in cmds) + '\n', capture_output=True, text=True, errors='replace', timeout=300)
got = r.stdout.rstrip('\n').split('\n')
check('hostile files ran', r.returncode == 0 and len(got) == len(cmds) and 'ERROR' not in r.stderr and 'runtime error' not in r.stderr,
      f'exit {r.returncode}, {len(got)} lines\n{r.stderr[-600:]}')
bad = [f'{k}: {g}' for (k, _), g in zip(cmds, got) if not k.startswith('fuzz') and (k in files) != ('is not a valid time zone file' in g)]
check(f'{len(files) - 300} broken files refused, {len(okfiles)} unusual ones read', not bad, '\n'.join(bad))
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
