"""std/pg against a fake PostgreSQL server that misbehaves: sign-in tricks (skipping the server's
SCRAM proof, a wrong proof, asking for the password in clear text, absurd iteration counts) and
broken messages. The client must refuse or report each one, never crash, and never use a
connection whose stream it lost track of. Extra arguments (--san) go to the build."""
import base64
import hashlib
import hmac
import os
import socket
import struct
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, check, counts  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'pg', 'hostile.vu'))
PW = 'pw'


def m(kind, body=b''):
    return kind + struct.pack('>I', len(body) + 4) + body


def recv_msg(c, startup=False):
    if startup:
        n = struct.unpack('>I', c.recv(4, socket.MSG_WAITALL))[0]
        return b'', c.recv(n - 4, socket.MSG_WAITALL)
    h = c.recv(5, socket.MSG_WAITALL)
    if len(h) < 5:
        return None, b''
    n = struct.unpack('>I', h[1:])[0]
    return h[:1], c.recv(n - 4, socket.MSG_WAITALL) if n > 4 else b''


READY = m(b'Z', b'I')
OK = m(b'R', struct.pack('>I', 0))


def scram(c, final_mode):
    """Runs SCRAM with the client; final_mode: 'good', 'wrong' (a bad proof) or 'skip' (no proof)."""
    c.sendall(m(b'R', struct.pack('>I', 10) + b'SCRAM-SHA-256\0\0'))
    _, body = recv_msg(c)
    first = body[body.index(b'\0') + 5:].decode()
    bare = first[3:]
    cnonce = bare.split('r=')[1]
    salt = os.urandom(16)
    sfirst = f'r={cnonce}SRV,s={base64.b64encode(salt).decode()},i=4096'
    c.sendall(m(b'R', struct.pack('>I', 11) + sfirst.encode()))
    _, body = recv_msg(c)
    cfinal = body.decode()
    salted = hashlib.pbkdf2_hmac('sha256', PW.encode(), salt, 4096)
    auth = f'{bare},{sfirst},{cfinal.rsplit(",p=", 1)[0]}'
    v = base64.b64encode(hmac.new(hmac.new(salted, b'Server Key', 'sha256').digest(), auth.encode(), 'sha256').digest()).decode()
    if final_mode == 'wrong':
        v = base64.b64encode(os.urandom(32)).decode()
    if final_mode != 'skip':
        c.sendall(m(b'R', struct.pack('>I', 12) + f'v={v}'.encode()))
    c.sendall(OK + READY)


def answer(c, rows_msgs):
    """Reads one extended-protocol query (P B D E S) and sends rows_msgs, then CommandComplete and Ready."""
    for _ in range(5):
        k, _ = recv_msg(c)
        if k is None:
            return
    c.sendall(m(b'1') + m(b'2') + rows_msgs + m(b'C', b'SELECT 1\0') + READY)


def T(*names):
    return m(b'T', struct.pack('>H', len(names)) + b''.join(n.encode() + b'\0' + b'\0' * 18 for n in names))


def D(*vals):
    return m(b'D', struct.pack('>H', len(vals)) + b''.join(struct.pack('>i', len(v)) + v for v in vals))


SCENARIOS = {
    'good': (lambda c: (scram(c, 'good'), answer(c, T('a') + D(b'1')), answer(c, T('a') + D(b'2'))),
             'query 1: 1 rows\nquery 2: 1 rows'),
    'skip the server proof': (lambda c: scram(c, 'skip'), 'error: sign-in: the server accepted us without proving it knows the password'),
    'a wrong server proof': (lambda c: scram(c, 'wrong'), "error: sign-in: the server's SCRAM signature is wrong"),
    'clear-text password asked': (lambda c: c.sendall(m(b'R', struct.pack('>I', 3))), 'error: sign-in: the server asks for the password in clear text'),
    'MD5 asked': (lambda c: c.sendall(m(b'R', struct.pack('>I', 5) + b'salt')), 'error: sign-in: the server asks for an MD5 password'),
    'trust (no password)': (lambda c: (c.sendall(OK + READY), answer(c, T('a') + D(b'1'))), 'query 1: 1 rows'),
    'a 1 GB message': (lambda c: (c.sendall(OK + READY), answer(c, b'D' + struct.pack('>I', 1 << 30))),
                       "query 1: protocol: a message from the server says it's 1073741824 bytes long\nquery 2: protocol: this connection failed earlier"),
    'a data row shorter than it says': (lambda c: (c.sendall(OK + READY), answer(c, T('a') + m(b'D', struct.pack('>Hi', 1, 50) + b'x'))),
                                        'query 1: protocol: a short data row\nquery 2: protocol: this connection failed earlier'),
    'a one-byte data row': (lambda c: (c.sendall(OK + READY), answer(c, T('a') + m(b'D', b'\x01'))),
                            'query 1: protocol: a short data row\nquery 2: protocol: this connection failed earlier'),
    'more columns than described': (lambda c: (c.sendall(OK + READY), answer(c, T('a') + D(b'1', b'2'))),
                                    'query 1: protocol: a data row with 2 columns, after a description of 1'),
    'a row description cut short': (lambda c: (c.sendall(OK + READY), answer(c, m(b'T', struct.pack('>H', 3) + b'a\0'))),
                                    'query 1: protocol: a short row description'),
    'a message length under 4': (lambda c: (c.sendall(OK + READY), answer(c, b'D\x00\x00\x00\x01')),
                                 "query 1: protocol: a message from the server says it's 1 bytes long"),
    'closed mid-message': (lambda c: (c.sendall(OK + READY), [recv_msg(c) for _ in range(5)], c.sendall(b'T\x00\x00\x00\x40ab'), c.shutdown(socket.SHUT_RDWR)),
                           'query 1: network: the server closed the connection'),
    'an error, then usable': (lambda c: (c.sendall(OK + READY),
                                         [recv_msg(c) for _ in range(5)],
                                         c.sendall(m(b'E', b'SERROR\0C42P01\0Mno such table\0\0') + READY),
                                         answer(c, T('a') + D(b'2'))),
                              'query 1: server: no such table (SQLSTATE 42P01)\nquery 2: 1 rows'),
    'silence': (lambda c: threading.Event().wait(5), 'error: network: timed out'),
}

for name, (behave, want) in SCENARIOS.items():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        c, _ = srv.accept()
        try:
            recv_msg(c, startup=True)
            behave(c)
            c.recv(1 << 16)
        except OSError:
            pass
        finally:
            c.close()
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    r = subprocess.run([exe, str(port)], capture_output=True, text=True, timeout=60)
    out = r.stdout + r.stderr
    ok = r.returncode in (0, 1) and all(w in out for w in want.split('\n')) and 'ERROR' not in r.stderr and 'runtime error' not in r.stderr
    check(f'hostile server: {name}', ok, f'exit {r.returncode}\n{r.stdout}{r.stderr[-500:]}')
    srv.close()
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
