"""WebSocket routes in std/web: tests/web/sockets.vu against the websockets package (an independent
client), over plain TCP and TLS: echo, a route with parameters and middleware values, middleware
that refuses, origins (cross-site refused, allowed ones and the app's own accepted), a chat whose
messages reach every socket (from tasks other than the socket's own), a client that drops out, a
frame sent in the same packet as the handshake, and broken handshakes. Extra arguments (--san) go to
the build."""
import asyncio
import os
import socket
import ssl
import struct
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, counts, work, recv_exactly  # noqa: E402
import websockets  # noqa: E402
from websockets.asyncio.client import connect  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'web', 'sockets.vu'))
D = os.path.join(work, 'certs')
os.makedirs(D)


def openssl(*args):
    subprocess.run(['openssl', *args], cwd=D, check=True, capture_output=True)


openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '30',
        '-subj', '/CN=Vu Test CA', '-addext', 'basicConstraints=critical,CA:TRUE',
        '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
open(os.path.join(D, 'san.ext'), 'w').write('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.csr', '-subj', '/CN=localhost')
openssl('x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
        '-out', 'server.pem', '-days', '30', '-extfile', 'san.ext')


def run(coro):
    try:
        return asyncio.run(asyncio.wait_for(coro, 30))
    except Exception as e:
        return f'{type(e).__name__}: {e}'


def status_of(e):
    s = str(e)
    for code in ('401', '403', '404', '400', '200'):
        if code in s:
            return code
    return s


def suite(tls):
    tag = 'wss' if tls else 'ws'
    srv = Server(exe, D) if tls else Server(exe)
    ctx = None
    if tls:
        ctx = ssl.create_default_context(cafile=os.path.join(D, 'ca.pem'))
    host = f'localhost:{srv.port}'
    base = f'{tag}://{host}'

    async def echo():
        async with connect(base + '/echo', ssl=ctx, max_size=None) as w:
            out = []
            for m in ['hi', 'ünïcode', 'x' * 70000]:
                await w.send(m)
                out.append(await w.recv())
            await w.send(b'\x00\x01\xff' * 400000)
            b = await w.recv()
            return out == ['echo: hi', 'echo: ünïcode', 'echo: ' + 'x' * 70000] and b == b'\x00\x01\xff' * 400000
    check(f'{tag}: echo of text, unicode, 70 KB and a 1.2 MB binary message', run(echo()) is True, run(echo()))

    async def room():
        async with connect(base + '/room/ada%20l', ssl=ctx, additional_headers={'x-user': 'bob'}) as w:
            m = await w.recv()
            try:
                await w.recv()
            except websockets.ConnectionClosedOK as e:
                return m, e.rcvd.code
            return m, 'not closed'
    check(f'{tag}: a route parameter and a middleware value reach the handler, which closes with 1000',
          run(room()) == ('hello ada l from bob', 1000), run(room()))

    async def refused(path, **kw):
        try:
            async with connect(base + path, ssl=ctx, **kw) as w:
                return 'opened'
        except websockets.InvalidStatus as e:
            return e.response.status_code
        except Exception as e:
            return f'{type(e).__name__}: {e}'
    check(f'{tag}: middleware that answers 401 stops the upgrade', run(refused('/room/x?deny=1')) == 401, run(refused('/room/x?deny=1')))
    check(f'{tag}: a page from another origin is refused (403)', run(refused('/echo', origin='https://evil.example')) == 403)
    check(f'{tag}: an origin the app allows, and its own, are accepted',
          run(refused('/echo', origin='https://friend.example')) == 'opened' and
          run(refused('/echo', origin=('https://' if tls else 'http://') + host)) == 'opened')
    check(f'{tag}: no WebSocket route at that path: 404', run(refused('/nope')) == 404)
    check(f'{tag}: a WebSocket handshake to a plain GET route gets its plain answer (200)', run(refused('/')) == 200)

    async def chat():
        ws_ = [await connect(base + '/chat', ssl=ctx) for _ in range(5)]
        for w in ws_:
            assert await w.recv() == 'joined'
        await asyncio.sleep(0.3)
        # one drops out without a close frame
        drop = await connect(base + '/chat', ssl=ctx)
        await drop.recv()
        drop.transport.abort()
        await asyncio.sleep(0.2)
        for i, w in enumerate(ws_):
            for k in range(3):
                await w.send(f'{i}.{k}')
        got = []
        for w in ws_:
            mine = [await w.recv() for _ in range(15)]
            got.append(mine)
        for w in ws_:
            await w.close()
        want = {f'{i}.{k}' for i in range(5) for k in range(3)}
        in_order = all([m for m in g if m.startswith(f'{i}.')] == [f'{i}.{k}' for k in range(3)] for g in got for i in range(5))
        return all(set(g) == want for g in got) and in_order
    check(f'{tag}: chat: 15 messages from 5 sockets reach all 5 (in order per sender), after one dropped out',
          run(chat()) is True, run(chat()))

    if not tls:
        # the handshake and a first frame in one packet: the frame must not be lost
        s = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
        key = os.urandom(4)
        payload = b'early'
        fr = bytes([0x81, 0x80 | len(payload)]) + key + bytes(b ^ key[i % 4] for i, b in enumerate(payload))
        s.sendall(b'GET /echo HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                  b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n' + fr)
        head = b''
        while b'\r\n\r\n' not in head:
            d = s.recv(1)
            if not d:
                break
            head += d
        h = recv_exactly(s, 2)
        body = recv_exactly(s, h[1] & 127) if len(h) == 2 else b''
        check('ws: a frame in the same packet as the handshake is read', head.startswith(b'HTTP/1.1 101') and body == b'echo: early', (head, body))
        s.close()
        for name, req, want in [
            ('no Sec-WebSocket-Key', b'GET /echo HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\n\r\n', b'HTTP/1.1 400'),
            ('version 8', b'GET /echo HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 8\r\n\r\n', b'HTTP/1.1 400'),
            ('a key that isn\'t 16 bytes', b'GET /echo HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: YWJj\r\nSec-WebSocket-Version: 13\r\n\r\n', b'HTTP/1.1 400'),
            ('POST with Upgrade', b'POST /echo HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nContent-Length: 0\r\n\r\n', b'HTTP/1.1 404'),
        ]:
            s = socket.create_connection(('127.0.0.1', srv.port), timeout=10)
            s.sendall(req)
            got = s.recv(100)
            check(f'ws: a broken handshake ({name}) is refused', got.startswith(want), got)
            s.close()
        got = urllib.request.urlopen(f'http://{host}/').read()
        check('ws: plain requests are still served while sockets are open', got == b'page', got)
    srv.p.terminate()
    rc, out, err = srv.finish()
    check(f'{tag}: the server stops cleanly', rc == 0 and 'ERROR' not in err and 'runtime error' not in err, f'{rc} {err[-600:]}')


suite(False)
suite(True)
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
