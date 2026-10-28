"""std/sqlite against Python's sqlite3: the same random inserts, updates, deletes and selects (names
with quotes, semicolons, NUL-free bytes, NULLs), text round-tripped through parameters, an invalid
statement, a database file reopened, and the const-SQL rule. Skipped without libsqlite3's header."""
import os, random, sqlite3, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, check, counts, work  # noqa: E402

if not os.path.exists('/usr/include/sqlite3.h'):
    print('skipped: no sqlite3.h'); print('0 passed, 0 failed'); sys.exit(0)
HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'sqlite', 'driver.vu'))
rng = random.Random(4)

def model(dbpath, ops):
    con = sqlite3.connect(dbpath)
    con.execute('create table if not exists people (id integer primary key, name text, age integer)')
    out = []
    for op in ops:
        p = op.split(' ')
        if p[0] == 'I':
            name = None if p[1] == '-' else bytes.fromhex(p[1]).decode('utf-8', 'surrogateescape')
            c = con.execute('insert into people (name, age) values (?, ?)', (name, p[2]))
            out.append(f'I {c.rowcount} {c.lastrowid}')
        elif p[0] == 'U':
            out.append(f"U {con.execute('update people set age = ? where id = ?', (p[2], p[1])).rowcount}")
        elif p[0] == 'D':
            out.append(f"D {con.execute('delete from people where id = ?', (p[1],)).rowcount}")
        elif p[0] == 'S':
            rows = con.execute('select id, name, age from people where age >= ? order by id', (p[1],)).fetchall()
            out.append('S ' + ','.join(f"{i}:{'NULL'.encode().hex() if n is None else n.encode('utf-8', 'surrogateescape').hex()}:{'NULL' if a is None else a}" for i, n, a in rows))
        elif p[0] == 'B':
            t = bytes.fromhex(p[1]).decode('utf-8', 'surrogateescape')
            out.append('B ' + con.execute('select ? as v', (t,)).fetchone()[0].encode('utf-8', 'surrogateescape').hex())
        elif p[0] == 'X':
            out.append('X err')
    con.commit(); con.close()
    return '\n'.join(out) + '\n'

PIECES = ["ada", "o'neil", "a;b", "--", '"q"', "é", "中文", " ", "x" * 50, "NULL", "1; drop table people"]
def ops(n):
    out = []
    for _ in range(n):
        k = rng.random()
        if k < 0.4:
            name = '-' if rng.random() < 0.1 else ''.join(rng.choice(PIECES) for _ in range(rng.randint(1, 3))).encode().hex()
            out.append(f'I {name} {rng.randint(0, 99)}')
        elif k < 0.55: out.append(f'U {rng.randint(1, 60)} {rng.randint(0, 99)}')
        elif k < 0.7: out.append(f'D {rng.randint(1, 60)}')
        elif k < 0.9: out.append(f'S {rng.randint(0, 99)}')
        elif k < 0.98: out.append('B ' + ''.join(rng.choice(PIECES) for _ in range(rng.randint(0, 3))).encode().hex())
        else: out.append('X')
    return out

for trial in range(5):
    seq = ops(300)
    d = tempfile.mkdtemp(dir=work)
    a, b = os.path.join(d, 'vu.db'), os.path.join(d, 'py.db')
    r = subprocess.run([exe, a], input='\n'.join(seq) + '\n', capture_output=True, text=True)
    want = model(b, seq)
    got = r.stdout
    bad = [(x, y) for x, y in zip(got.split('\n'), want.split('\n')) if x != y]
    check(f'trial {trial}: 300 random operations give what Python\'s sqlite3 gives', r.returncode == 0 and got == want, (r.returncode, r.stderr[-300:], bad[:3]))
    # the file persists: reopen it and read everything
    r2 = subprocess.run([exe, a], input='S 0\n', capture_output=True, text=True)
    con = sqlite3.connect(a)
    rows = con.execute('select count(*) from people').fetchone()[0]
    con.close()
    check(f'trial {trial}: the database file reopens with its {rows} rows', r2.returncode == 0 and (r2.stdout.count(':') == 2 * rows), r2.stdout[:200])

# SQL built at run time doesn't compile
bad_src = os.path.join(work, 'inject.vu')
open(bad_src, 'w').write('import sqlite\nfn main(ffi: Ffi) throws:\n  var db = sqlite.open(ffi, ":memory:")?\n  let id = args()[0]\n  sqlite.exec(ffi, &db, "delete from t where id = " + id, [])?\n')
r = subprocess.run([os.environ.get('VU', os.path.join(HERE, '..', 'vu')), 'check', bad_src], capture_output=True, text=True)
check('SQL built at run time is refused at compile time', r.returncode != 0 and 'const' in r.stderr, r.stderr)
# without Ffi there is no way in
nf = os.path.join(work, 'noffi.vu')
open(nf, 'w').write('import sqlite\nfn main() throws:\n  var db = sqlite.open(":memory:")?\n')
r = subprocess.run([os.environ.get('VU', os.path.join(HERE, '..', 'vu')), 'check', nf], capture_output=True, text=True)
check('opening a database needs the Ffi capability', r.returncode != 0, r.stderr)
print(f"{counts['passed']} passed, {counts['failed']} failed")
sys.exit(1 if counts['failed'] else 0)
