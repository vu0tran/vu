"""std/ws: tests/net/ws_echo.vu against Python's websockets library and hand-made (broken) frames, and
tests/net/ws_client.vu against a websockets server; plain and over TLS (wss). Extra arguments (--san)
go to the build."""
import os
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, counts, work, recv_exactly  # noqa: E402
import asyncio  # noqa: E402
# The asyncio client: websockets' threaded (sync) client reads and writes one TLS socket from two
# threads, and now and then loses its handshake request over TLS (it hangs the same way against
# websockets' own server), so the threaded one is only used as a server here.
from websockets.asyncio.client import connect  # noqa: E402
from websockets.sync.server import serve  # noqa: E402
from websockets.exceptions import ConnectionClosed  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
echo = build(os.path.join(HERE, 'net', 'ws_echo.vu'))
client = build(os.path.join(HERE, 'net', 'ws_client.vu'))

# certificates for wss: a CA and a server certificate for localhost
D = os.path.join(work, 'certs')
os.makedirs(D)


def openssl(*args):
    subprocess.run(['openssl', *args], cwd=D, check=True, capture_output=True)


openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '30',
        '-subj', '/CN=Vu Test CA', '-addext', 'basicConstraints=critical,CA:TRUE',
        '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.csr', '-subj', '/CN=localhost')
open(os.path.join(D, 'san.ext'), 'w').write('subjectAltName=DNS:localhost,IP:127.0.0.1\n'
                                           'extendedKeyUsage=serverAuth\n')
openssl('x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
        '-out', 'server.pem', '-days', '30', '-extfile', 'san.ext')
CA = os.path.join(D, 'ca.pem')


def handshake(port, key='dGhlIHNhbXBsZSBub25jZQ=='):
    s = socket.create_connection(('127.0.0.1', port), timeout=10)
    s.sendall((f'GET /chat HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
               f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
    head = b''
    while b'\r\n\r\n' not in head:
        d = s.recv(1)
        if not d:
            break
        head += d
    return s, head


def frame(opcode, payload, fin=True, mask=True, rsv=0, length=None):
    b0 = (0x80 if fin else 0) | rsv | opcode
    n = len(payload) if length is None else length
    mbit = 0x80 if mask else 0
    if n < 126:
        h = bytes([b0, mbit | n])
    elif n < 65536:
        h = bytes([b0, mbit | 126]) + struct.pack('>H', n)
    else:
        h = bytes([b0, mbit | 127]) + struct.pack('>Q', n)
    if not mask:
        return h + payload
    key = os.urandom(4)
    return h + key + bytes(b ^ key[i % 4] for i, b in enumerate(payload))


def read_frame(s):
    h = recv_exactly(s, 2)
    if len(h) < 2:
        return None, b''
    n = h[1] & 127
    if n == 126:
        n = struct.unpack('>H', recv_exactly(s, 2))[0]
    elif n == 127:
        n = struct.unpack('>Q', recv_exactly(s, 8))[0]
    return h[0] & 15, recv_exactly(s, n)


def close_code(s):
    op, body = read_frame(s)
    if op != 8:
        return f'opcode {op}'
    return struct.unpack('>H', body[:2])[0] if len(body) >= 2 else 1005


async def recv(w, t=10):
    return await asyncio.wait_for(w.recv(), t)


def still_serves(port, label):
    async def go():
        async with connect(f'ws://127.0.0.1:{port}/') as w:
            await w.send('alive')
            return await recv(w) == 'alive'
    check(f'{label}: the next client is served', asyncio.run(go()))


async def library_tests(url, ctx, tag):
    async with connect(url, ssl=ctx, max_size=None) as w:
        await w.send('hello')
        check(f'{tag}: text echoed', await recv(w) == 'hello')
        await w.send('héllo wörld 中 🎉')
        check(f'{tag}: UTF-8 text echoed', await recv(w) == 'héllo wörld 中 🎉')
        await w.send(b'\x00\xff\x80binary')
        check(f'{tag}: binary echoed', await recv(w) == b'\x00\xff\x80binary')
        big = os.urandom(3 << 20)
        await w.send(big)
        check(f'{tag}: 3 MB binary echoed', await recv(w, 30) == big)
        await w.send(['frag', 'mented ', 'message'])   # one message in three frames
        check(f'{tag}: fragmented message joined', await recv(w) == 'fragmented message')
        for i in range(200):
            await w.send(f'm{i}')
        got = [await recv(w) for _ in range(200)]
        check(f'{tag}: 200 messages in order', got == [f'm{i}' for i in range(200)])
        pong = await w.ping(b'pp')
        await asyncio.wait_for(pong, 10)
        check(f'{tag}: ping answered', True)
        await w.send('')
        check(f'{tag}: empty message', await recv(w) == '')
        await w.send('close')
        try:
            await recv(w)
            check(f'{tag}: server-started close', False, 'got a message')
        except ConnectionClosed as e:
            check(f'{tag}: server-started close (4000 bye)', e.rcvd is not None and e.rcvd.code == 4000 and e.rcvd.reason == 'bye', e)
    async with connect(url, ssl=ctx) as w:
        await w.send('x')
        await recv(w)
    check(f'{tag}: client-started close', True)
    # many at once
    socks = [await connect(url, ssl=ctx) for _ in range(100)]
    for i, w in enumerate(socks):
        await w.send(f'c{i}')
    ok = True
    for i, w in enumerate(socks):
        ok = ok and await recv(w, 20) == f'c{i}'
    for w in socks:
        await w.close()
    check(f'{tag}: 100 connections at once', ok)


async def send_quit(url, ctx):
    async with connect(url, ssl=ctx) as w:
        await w.send('quit')


def server_tests(tls):
    srv = Server(echo, *([D] if tls else []))
    scheme = 'wss' if tls else 'ws'
    ctx = ssl.create_default_context(cafile=CA) if tls else None
    url = f'{scheme}://localhost:{srv.port}/chat'
    tag = 'wss' if tls else 'ws'
    try:
        asyncio.run(library_tests(url, ctx, tag))

        # the Vu client against this Vu server
        r = subprocess.run([client, url, CA if tls else '-', 'one', 'två'], capture_output=True, text=True, timeout=60)
        check(f'{tag}: Vu client to Vu server', r.stdout == 'text one\ntext två\nbinary 1048576 true\nclosed 1000\n',
              r.stdout + r.stderr)

        if not tls:
            # protocol errors close the connection with the right code; the server goes on
            s, head = handshake(srv.port)
            check('101 with the RFC accept key', b' 101 ' in head and b's3pPLMBiTxaQ9kYGzzhZRbK+xOo=' in head, head)
            s.sendall(frame(1, b'unmasked', mask=False))
            check('unmasked client frame: close 1002', close_code(s) == 1002)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(1, b'\xff\xfe bad utf-8'))
            check('text that isn\'t UTF-8: close 1007', close_code(s) == 1007)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(2, b'', length=17 << 20)[:14])   # announces 17 MB
            check('17 MB frame: close 1009', close_code(s) == 1009)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(9, b'p' * 126))
            check('control frame over 125 bytes: close 1002', close_code(s) == 1002)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(1, b'x', rsv=0x40))
            check('reserved bit set: close 1002', close_code(s) == 1002)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(0, b'cont'))
            check('continuation with nothing to continue: close 1002', close_code(s) == 1002)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(1, b'a', fin=False) + frame(1, b'b'))
            check('new message inside a fragmented one: close 1002', close_code(s) == 1002)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(3, b'x'))
            check('unknown opcode: close 1002', close_code(s) == 1002)
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(1, b'a', fin=False) + frame(9, b'mid') + frame(0, b'b'))
            op, body = read_frame(s)
            op2, body2 = read_frame(s)
            check('ping between fragments answered, message joined', (op, body, op2, body2) == (10, b'mid', 1, b'ab'),
                  (op, body, op2, body2))
            s.close()
            # bad handshakes get 400
            for name, req in [('no key', 'GET / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\n\r\n'),
                              ('version 8', 'GET / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 8\r\n\r\n'),
                              ('POST', 'POST / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n'),
                              ('short key', 'GET / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: c2hvcnQ=\r\nSec-WebSocket-Version: 13\r\n\r\n')]:
                s = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
                s.sendall(req.encode())
                check(f'bad handshake ({name}): 400', s.recv(100).startswith(b'HTTP/1.1 400'))
                s.close()
            # a 70 KB header section, and a connection cut mid-frame
            s = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
            try:
                s.sendall(b'GET / HTTP/1.1\r\nX: ' + b'a' * 70000)
            except OSError:
                pass
            s.close()
            s, _ = handshake(srv.port)
            s.sendall(frame(2, os.urandom(5000))[:3000])
            s.close()
            # a client that never finishes the handshake doesn't hold up the others
            silent = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
            still_serves(srv.port, 'after protocol errors, a cut frame and a silent client')
            silent.close()
        asyncio.run(send_quit(url, ctx))
        code, out, err = srv.finish()
        check(f'{tag}: server stops on quit, no sanitizer report', code == 0 and 'ERROR' not in err and 'runtime error' not in err,
              f'exit {code} {err[-400:]}')
    finally:
        if srv.p.poll() is None:
            srv.kill()


def client_tests(tls):
    tag = 'wss' if tls else 'ws'
    ctx = None
    if tls:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(os.path.join(D, 'server.pem'), os.path.join(D, 'server.key'))
    seen = []

    def handler(w):
        for m in w:
            seen.append(m)
            if m == 'ping me':
                w.ping(b'hi').wait(5)   # the Vu client answers pings inside recv
            w.send(m)

    with serve(handler, '127.0.0.1', 0, ssl=ctx, max_size=None) as server:
        port = server.socket.getsockname()[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        scheme = 'wss' if tls else 'ws'
        r = subprocess.run([client, f'{scheme}://localhost:{port}/x', CA if tls else '-', 'a', 'ping me', 'ünï'],
                           capture_output=True, text=True, timeout=60)
        check(f'{tag}: Vu client to websockets server',
              r.stdout == 'text a\ntext ping me\ntext ünï\nbinary 1048576 true\nclosed 1000\n' and 'ERROR' not in r.stderr,
              r.stdout + r.stderr)
        if tls:
            r = subprocess.run([client, f'wss://localhost:{port}/x', '-', 'a'], capture_output=True, text=True, timeout=60)
            check('wss: an unknown certificate authority is refused', r.returncode != 0 and 'text a' not in r.stdout,
                  r.stdout + r.stderr)
        server.shutdown()


def hostile_server(reply):
    """A one-shot TCP server: reads the client's handshake, then reply(sock, key). Returns its port."""
    import base64
    import hashlib
    srv = socket.socket()
    srv.bind(('127.0.0.1', 0))
    srv.listen(1)

    def run():
        c, _ = srv.accept()
        try:
            head = b''
            while b'\r\n\r\n' not in head:
                d = c.recv(4096)
                if not d:
                    return
                head += d
            key = [l.split(b':', 1)[1].strip() for l in head.split(b'\r\n') if l.lower().startswith(b'sec-websocket-key:')][0]
            accept = base64.b64encode(hashlib.sha1(key + b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
            reply(c, accept)
            time.sleep(0.5)
        except OSError:
            pass
        finally:
            c.close()
            srv.close()
    threading.Thread(target=run, daemon=True).start()
    return srv.getsockname()[1]


def ok101(accept):
    return b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + accept + b'\r\n\r\n'


HOSTILE = {
    'a wrong Sec-WebSocket-Accept': (lambda c, a: c.sendall(ok101(b'AAAAAAAAAAAAAAAAAAAAAAAAAAA=')), "the server's Sec-WebSocket-Accept is wrong"),
    'no 101': (lambda c, a: c.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'), "didn't switch to WebSocket: HTTP/1.1 200 OK"),
    'a masked frame from the server': (lambda c, a: c.sendall(ok101(a) + frame(1, b'hi', mask=True)), 'closed 1002'),
    'a 17 MB frame': (lambda c, a: c.sendall(ok101(a) + frame(2, b'', mask=False, length=17 << 20)[:10]), 'closed 1009'),
    "text that isn't UTF-8": (lambda c, a: c.sendall(ok101(a) + frame(1, b'\xc3\x28', mask=False)), 'closed 1007'),
    'closed mid-frame': (lambda c, a: c.sendall(ok101(a) + frame(2, b'x' * 100, mask=False)[:50]), 'the connection closed'),
    'a header section over 64 KB': (lambda c, a: c.sendall(b'HTTP/1.1 101 OK\r\nX: ' + b'a' * 70000), 'over 64 KB'),
}
for name, (reply, want) in HOSTILE.items():
    port = hostile_server(reply)
    r = subprocess.run([client, f'ws://127.0.0.1:{port}/', '-', 'a'], capture_output=True, text=True, timeout=60)
    out = r.stdout + r.stderr
    check(f'client, hostile server: {name}', want in out and 'ERROR' not in r.stderr and 'runtime error' not in r.stderr, out[-400:])

for tls in (False, True):
    server_tests(tls)
    client_tests(tls)
r = subprocess.run([client, 'http://localhost:1/', '-'], capture_output=True, text=True, timeout=30)
check('a URL that isn\'t ws:// or wss://', 'starts with ws://' in r.stderr, r.stderr)
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
