"""std/pg with tls on, against a fake PostgreSQL server: it answers the TLS request with 'S' and
then speaks TLS with a certificate from a test CA. The client must check the certificate (the CA
it was given, the host name), refuse a server that says 'N' or sends anything but 'S', and refuse
bytes sent ahead of the handshake (they'd be read as if they came over TLS). Extra arguments
(--san) go to the build."""
import os
import socket
import ssl
import struct
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, check, counts, work  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'pg', 'tls.vu'))
D = os.path.join(work, 'certs')
os.makedirs(D)


def openssl(*args):
    subprocess.run(['openssl', *args], cwd=D, check=True, capture_output=True)


openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '30',
        '-subj', '/CN=Vu Test CA', '-addext', 'basicConstraints=critical,CA:TRUE',
        '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
open(os.path.join(D, 'san.ext'), 'w').write('subjectAltName=DNS:localhost,IP:127.0.0.1\n'
                                           'keyUsage=critical,digitalSignature,keyEncipherment\n'
                                           'extendedKeyUsage=serverAuth\nauthorityKeyIdentifier=keyid\n')
open(os.path.join(D, 'other.ext'), 'w').write('subjectAltName=DNS:example.com\nextendedKeyUsage=serverAuth\n')
for name, ext in (('server', 'san.ext'), ('other', 'other.ext')):
    openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', f'{name}.key', '-out', f'{name}.csr', '-subj', '/CN=x')
    openssl('x509', '-req', '-in', f'{name}.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
            '-out', f'{name}.pem', '-days', '30', '-extfile', ext)
openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'self.key', '-out', 'self.pem', '-days', '30',
        '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost')
CA = os.path.join(D, 'ca.pem')


def m(kind, body=b''):
    return kind + struct.pack('>I', len(body) + 4) + body


def exactly(c, n):
    out = b''
    while len(out) < n:
        got = c.recv(n - len(out))
        if not got:
            break
        out += got
    return out


def recv_msg(c, startup=False):
    if startup:
        n = struct.unpack('>I', exactly(c, 4))[0]
        return b'', exactly(c, n - 4)
    h = exactly(c, 5)
    if len(h) < 5:
        return None, b''
    n = struct.unpack('>I', h[1:])[0]
    return h[:1], exactly(c, n - 4)


READY = m(b'Z', b'I')
OK = m(b'R', struct.pack('>I', 0))
seen = {}


def talk(c):
    """After the handshake: trust sign-in, one query answered with one row."""
    k, body = recv_msg(c, startup=True)
    seen['startup'] = body
    c.sendall(OK + READY)
    for _ in range(5):
        if recv_msg(c)[0] is None:
            return
    row_d = m(b'T', struct.pack('>H', 1) + b'a\0' + b'\0' * 18)
    c.sendall(m(b'1') + m(b'2') + row_d + m(b'D', struct.pack('>Hi', 1, 1) + b'1') + m(b'C', b'SELECT 1\0') + READY)


def tls_with(cert):
    def go(c):
        req = c.recv(8, socket.MSG_WAITALL)
        seen['request'] = req
        c.sendall(b'S')
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(os.path.join(D, f'{cert}.pem'), os.path.join(D, f'{cert}.key'))
        s = ctx.wrap_socket(c, server_side=True)
        talk(s)
        s.recv(1 << 16)
    return go


def answer_raw(data):
    def go(c):
        c.recv(8, socket.MSG_WAITALL)
        c.sendall(data)
        c.recv(1 << 16)
    return go


def plain_server(c):
    """A server that ignores the TLS request and starts talking in the clear."""
    c.recv(8, socket.MSG_WAITALL)
    c.sendall(OK + READY)
    c.recv(1 << 16)


SCENARIOS = {
    'good, with the test CA': (tls_with('server'), CA, 'query 1: 1 rows'),
    'the system CAs (the test CA is not among them)': (tls_with('server'), '', "error: network: tls: localhost: can't verify the server's certificate"),
    'a certificate for another host': (tls_with('other'), CA, "error: network: tls: localhost: can't verify the server's certificate"),
    'a self-signed certificate': (tls_with('self'), CA, "error: network: tls: localhost: can't verify the server's certificate"),
    "the server says 'N'": (answer_raw(b'N'), CA, "error: network: the server doesn't accept TLS connections (tls is on)"),
    "'S' with bytes after it (buffer stuffing)": (answer_raw(b'S' + OK + READY), CA,
                                                  'error: protocol: an unexpected answer to the TLS request'),
    'an error message instead of an answer': (answer_raw(m(b'E', b'SFATAL\0Mno\0\0')), CA,
                                              'error: protocol: an unexpected answer to the TLS request'),
    'a plain-text server': (plain_server, CA, 'error: protocol: an unexpected answer to the TLS request'),
    'closed at once': (lambda c: c.close(), CA, 'error: network: the server closed the connection'),
}

for name, (behave, ca, want) in SCENARIOS.items():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    seen.clear()

    def serve():
        c, _ = srv.accept()
        try:
            behave(c)
        except (OSError, ssl.SSLError):
            pass
        finally:
            c.close()
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    r = subprocess.run([exe, str(port), ca], capture_output=True, text=True, timeout=60)
    out = r.stdout + r.stderr
    ok = r.returncode in (0, 1) and want in out and 'ERROR' not in r.stderr and 'runtime error' not in r.stderr
    if name.startswith('good'):
        ok = ok and seen.get('request') == struct.pack('>II', 8, 80877103) and b'user\0app' in seen.get('startup', b'')
    check(f'pg tls: {name}', ok, f'exit {r.returncode}\n{r.stdout}{r.stderr[-500:]}')
    t.join(5)
    srv.close()
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
