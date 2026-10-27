"""TLS (net.tls_listen, net.tls_connect): tests/net/tls_echo.vu and tls_client.vu against Python's ssl
module, with certificates made by the openssl command for each run. Runs against the compiler named
by VU (default: ../vu, the compiler); extra arguments (--san) go to the build."""
import os
import socket
import ssl
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, free_port, work, counts  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(work, 'certs')
os.makedirs(D)


def openssl(*args):
    subprocess.run(['openssl', *args], cwd=D, check=True, capture_output=True)


# A CA, a server certificate for localhost and 127.0.0.1 signed by it, a self-signed certificate, a key
# that belongs to neither, and a password-protected key.
openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '30',
        '-subj', '/CN=Vu Test CA', '-addext', 'basicConstraints=critical,CA:TRUE',
        '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.csr', '-subj', '/CN=localhost')
open(os.path.join(D, 'san.ext'), 'w').write('subjectAltName=DNS:localhost,IP:127.0.0.1\n'
                                           'keyUsage=critical,digitalSignature,keyEncipherment\n'
                                           'extendedKeyUsage=serverAuth\nauthorityKeyIdentifier=keyid\n')
openssl('x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
        '-out', 'server.pem', '-days', '30', '-extfile', 'san.ext')
openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'self.key', '-out', 'self.pem', '-days', '30',
        '-subj', '/CN=localhost')
# a chain: root CA -> intermediate CA -> server (the server sends its certificate and the intermediate)
open(os.path.join(D, 'inter.ext'), 'w').write('basicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\n'
                                             'authorityKeyIdentifier=keyid\n')
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'inter.key', '-out', 'inter.csr', '-subj', '/CN=Vu Intermediate')
openssl('x509', '-req', '-in', 'inter.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial', '-out', 'inter.pem',
        '-days', '30', '-extfile', 'inter.ext')
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'leaf.key', '-out', 'leaf.csr', '-subj', '/CN=localhost')
openssl('x509', '-req', '-in', 'leaf.csr', '-CA', 'inter.pem', '-CAkey', 'inter.key', '-CAcreateserial', '-out', 'leaf.pem',
        '-days', '30', '-extfile', 'san.ext')
open(os.path.join(D, 'chain.pem'), 'w').write(open(os.path.join(D, 'leaf.pem')).read() + open(os.path.join(D, 'inter.pem')).read())
# ECDSA (P-256), signed by the root
openssl('req', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:P-256', '-nodes', '-keyout', 'ec.key', '-out', 'ec.csr',
        '-subj', '/CN=localhost')
openssl('x509', '-req', '-in', 'ec.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial', '-out', 'ec.pem',
        '-days', '30', '-extfile', 'san.ext')
openssl('genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048', '-out', 'other.key')
openssl('genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048', '-aes-128-cbc', '-pass', 'pass:pw',
        '-out', 'locked.key')
for d, files in [('good', ('server.pem', 'server.key')), ('mismatch', ('server.pem', 'other.key')),
                 ('locked', ('server.pem', 'locked.key')), ('self', ('self.pem', 'self.key')),
                 ('chain', ('chain.pem', 'leaf.key')), ('ec', ('ec.pem', 'ec.key'))]:
    os.makedirs(os.path.join(D, d))
    for src, dst in zip(files, ('server.pem', 'server.key')):
        os.symlink(os.path.join(D, src), os.path.join(D, d, dst))
os.makedirs(os.path.join(D, 'garbage'))
open(os.path.join(D, 'garbage', 'server.pem'), 'w').write('not a certificate\n')
os.symlink(os.path.join(D, 'server.key'), os.path.join(D, 'garbage', 'server.key'))

echo = build(os.path.join(HERE, 'net', 'tls_echo.vu'))
client = build(os.path.join(HERE, 'net', 'tls_client.vu'))
ca = os.path.join(D, 'ca.pem')


def tls_conn(port, host='localhost'):
    ctx = ssl.create_default_context(cafile=ca)
    raw = socket.create_connection(('127.0.0.1', port), timeout=10)
    return ctx.wrap_socket(raw, server_hostname=host)


def recv_n(s, n):
    buf = b''
    while len(buf) < n:
        d = s.recv(1 << 20)
        if not d:
            break
        buf += d
    return buf


def quit_server(srv):
    try:
        s = tls_conn(srv.port)
        s.sendall(b'quit')
        s.close()
    except OSError:
        pass
    return srv.finish()


# ---- the server
srv = Server(echo, os.path.join(D, 'good'))
try:
    s = tls_conn(srv.port)
    s.sendall(b'hello')
    check('echo over TLS (Python client)', recv_n(s, 5) == b'hello')
    check('TLS 1.2 or later', s.version() in ('TLSv1.2', 'TLSv1.3'), s.version())
    s.close()

    # 3 MB echoed while the client sends and reads at the same time
    data = os.urandom(3 << 20)
    s = tls_conn(srv.port)
    t = threading.Thread(target=s.sendall, args=(data,))
    t.start()
    back = recv_n(s, len(data))
    t.join()
    check('3 MB echoed', back == data, f'{len(back)} bytes back')
    s.close()

    # a slow reader: the server must wait (WANT_WRITE) without spinning or failing
    s = tls_conn(srv.port)
    s.sendall(os.urandom(1 << 20))
    time.sleep(1.5)
    back = recv_n(s, 1 << 20)
    check('slow reader gets all 1 MB', len(back) == 1 << 20, len(back))
    s.close()

    # plain TCP to a TLS server: that connection fails, the server goes on
    p = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
    p.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
    try:
        reply = p.recv(100)
    except OSError:
        reply = b''
    p.close()
    s = tls_conn(srv.port)
    s.sendall(b'after')
    check('plain HTTP to the TLS port is refused, next client served', recv_n(s, 5) == b'after', reply[:40])
    s.close()

    # a client that connects and says nothing: its task times out, others are served meanwhile
    silent = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
    s = tls_conn(srv.port)
    s.sendall(b'busy')
    check('served while another connection is silent', recv_n(s, 4) == b'busy')
    s.close()

    # a handshake cut off halfway, and a client that resets the connection after sending
    half = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
    half.sendall(b'\x16\x03\x01\x02\x00\x01\x00\x01\xfc\x03\x03')   # the start of a ClientHello
    half.close()
    s = tls_conn(srv.port)
    s.sendall(os.urandom(2 << 20))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x01\x00\x00\x00\x00\x00\x00\x00')   # RST on close
    s.close()   # the server is still echoing 2 MB into a connection that is gone (SIGPIPE if unprotected)
    time.sleep(0.5)
    s = tls_conn(srv.port)
    s.sendall(b'alive')
    check('server survives a cut-off handshake and a reset while sending', recv_n(s, 5) == b'alive')
    s.close()

    # many connections at once, each its own task
    conns = [tls_conn(srv.port) for _ in range(200)]
    for i, c in enumerate(conns):
        c.sendall(b'%05d' % i)
    check('200 TLS connections at once', all(recv_n(c, 5) == b'%05d' % i for i, c in enumerate(conns)))
    for c in conns:
        c.close()

    # the Vu client against the Vu server
    r = subprocess.run([client, str(srv.port), 'localhost', ca, 'quit-not'], capture_output=True, text=True, timeout=30)
    # the server's idle timeout (3 s) closes the connection, which ends the client's read loop
    check('Vu client, Vu server', r.returncode == 0 and 'got 8: quit-not' in r.stdout, r.stdout + r.stderr)
    time.sleep(3.5)   # let the silent connection's timeout fire
    silent.close()
finally:
    code, out, err = quit_server(srv)
check('server quits cleanly', code == 0 and out.strip() == 'quit', f'{code} {out!r} {err[-300:]!r}')
check('failed connections reported (plain HTTP, silent, cut-off)',
      'recv: the TLS handshake failed' in err and 'recv: timed out' in err, err[-600:])
check('no sanitizer report', 'ERROR' not in err and 'runtime error' not in err, err[-600:])

# ---- a certificate chain and an ECDSA key; many Vu clients at once
for d in ('chain', 'ec'):
    srv = Server(echo, os.path.join(D, d))
    try:
        s = tls_conn(srv.port)   # trusts only the root
        s.sendall(b'chained')
        check(f'server with the {d} certificate, client trusting the root', recv_n(s, 7) == b'chained')
        s.close()
        if d == 'ec':
            many = build(os.path.join(HERE, 'net', 'tls_many.vu'))
            r = subprocess.run([many, str(srv.port), ca], capture_output=True, text=True, timeout=60)
            check('100 Vu client tasks, each its own TLS connection', r.returncode == 0 and r.stdout.strip() == '100 ok',
                  r.stdout + r.stderr[-400:])
    finally:
        code, out, err = quit_server(srv)
    check(f'{d}: no errors', code == 0 and 'ERROR' not in err, err[-400:])

# ---- certificates and keys the server can't use
for d, want in [('mismatch', "key: the private key doesn't match the certificate"),
                ('locked', 'key: no private key found in the PEM text (keys protected by a password'),
                ('garbage', 'cert: no certificate found in the PEM text')]:
    r = subprocess.run([echo, str(free_port()), os.path.join(D, d)], capture_output=True, text=True, timeout=30)
    check(f'tls_listen with {d} key or cert', r.returncode == 1 and want in r.stderr, r.stderr)


# ---- the client, against Python servers
sni = []


def py_server(certfile, keyfile, reply=b'hi from python', mode='tls'):
    """A one-connection server on a free port; returns (port, thread)."""
    ls = socket.socket()
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(('127.0.0.1', 0))
    ls.listen(1)
    port = ls.getsockname()[1]

    def run():
        try:
            c, _ = ls.accept()
            c.settimeout(10)
            if mode == 'plain':
                c.sendall(b'HTTP/1.0 200 OK\r\n\r\nnot tls')
                time.sleep(0.5)
            elif mode == 'silent':
                time.sleep(5)
            else:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ctx.load_cert_chain(certfile, keyfile)
                ctx.sni_callback = lambda sock, name, c: sni.append(name)
                t = ctx.wrap_socket(c, server_side=True)
                t.recv(100)
                t.sendall(reply)
                if mode == 'tls':
                    t.unwrap()   # close_notify
                c = t
            c.close()
        except (OSError, ssl.SSLError):
            pass
        ls.close()
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return port, th


def vu_client(port, host, cafile, timeout=30):
    r = subprocess.run([client, str(port), host, cafile], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


good = (os.path.join(D, 'server.pem'), os.path.join(D, 'server.key'))
self_signed = (os.path.join(D, 'self.pem'), os.path.join(D, 'self.key'))
port, th = py_server(*good)
code, out = vu_client(port, 'localhost', ca)
check('Vu client to a Python TLS server', code == 0 and 'got 14: hi from python' in out, out)
check('the client sends the host name (SNI)', sni == ['localhost'], sni)
port, th = py_server(*good, mode='noclose')
code, out = vu_client(port, '127.0.0.1', ca)
check('by IP address; the server closes without close_notify', code == 0 and 'got 14: hi from python' in out, out)
check('no SNI for an IP address', sni == ['localhost', None], sni)
port, th = py_server(*self_signed)
code, out = vu_client(port, 'localhost', ca)
check('untrusted certificate refused', code == 1 and "can't verify the server's certificate: self-signed certificate" in out, out)
port, th = py_server(*self_signed)
code, out = vu_client(port, '127.0.0.1', os.path.join(D, 'self.pem'))
check('certificate for another name refused', code == 1 and "can't verify the server's certificate: IP address mismatch" in out, out)
port, th = py_server(*good)
code, out = vu_client(port, 'localhost', '-')
check('system CAs only: a private CA is refused', code == 1 and 'unable to get local issuer certificate' in out, out)
port, th = py_server(*good, mode='plain')
code, out = vu_client(port, 'localhost', ca)
check('a server that isn\'t TLS', code == 1 and 'the TLS handshake failed' in out, out)
port, th = py_server(*good, mode='silent')
t0 = time.time()
code, out = vu_client(port, 'localhost', ca)
check('a server that never answers: timeout: applies to the handshake', code == 1 and 'timed out' in out
      and time.time() - t0 < 4.5, f'{time.time() - t0:.1f}s {out}')
code, out = vu_client(free_port(), 'localhost', ca)
check('nothing listening', code == 1 and 'Connection refused' in out, out)

print(f"{counts['passed']} passed, {counts['failed']} failed")
sys.exit(1 if counts['failed'] else 0)
