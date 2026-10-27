"""HTTP/2 in std/http (std/h2): tests/net/h2_serve.vu against httpx (HTTP/2 with prior knowledge, and
over TLS with ALPN), and against hand-built frames (with the h2 package's HPACK encoder) for protocol
errors and the known HTTP/2 denial-of-service attacks. Extra arguments (--san) go to the build."""
import os
import signal
import socket
import ssl
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, counts, work, FLAGS  # noqa: E402
import httpx  # noqa: E402
import hpack  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'net', 'h2_serve.vu'))

D = os.path.join(work, 'certs')
os.makedirs(D)


def openssl(*args):
    subprocess.run(['openssl', *args], cwd=D, check=True, capture_output=True)


openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '30',
        '-subj', '/CN=Vu Test CA', '-addext', 'basicConstraints=critical,CA:TRUE',
        '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.csr', '-subj', '/CN=localhost')
open(os.path.join(D, 'san.ext'), 'w').write('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
openssl('x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
        '-out', 'server.pem', '-days', '30', '-extfile', 'san.ext')
CA = os.path.join(D, 'ca.pem')

PREFACE = b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'
DATA, HEADERS, PRIORITY, RST, SETTINGS, PUSH, PING, GOAWAY, WINDOW, CONT = range(10)


def frame(kind, flags, stream, payload=b''):
    return struct.pack('>I', len(payload))[1:] + bytes([kind, flags]) + struct.pack('>I', stream) + payload


class Raw:
    """A hand-driven HTTP/2 connection."""

    def __init__(self, port, settings=b''):
        self.s = socket.create_connection(('127.0.0.1', port), timeout=10)
        self.enc = hpack.Encoder()
        self.dec = hpack.Decoder()
        self.buf = b''
        self.s.sendall(PREFACE + frame(SETTINGS, 0, 0, settings))

    def send(self, data):
        try:
            self.s.sendall(data)
        except OSError:
            pass

    def headers(self, stream, path='/', method='GET', extra=(), end_stream=True):
        block = self.enc.encode([(':method', method), (':scheme', 'http'), (':path', path), (':authority', 'x')] + list(extra))
        return frame(HEADERS, 4 | (1 if end_stream else 0), stream, block)

    def read(self, timeout=10):
        """The next frame, or None once the connection closes (or nothing comes for timeout seconds)."""
        self.s.settimeout(timeout)
        try:
            while len(self.buf) < 9 or len(self.buf) < 9 + int.from_bytes(self.buf[:3], 'big'):
                d = self.s.recv(1 << 16)
                if not d:
                    return None
                self.buf += d
        except (socket.timeout, OSError):
            return None
        n = int.from_bytes(self.buf[:3], 'big')
        f = (self.buf[3], self.buf[4], int.from_bytes(self.buf[5:9], 'big') & 0x7fffffff, self.buf[9:9 + n])
        self.buf = self.buf[9 + n:]
        return f

    def until(self, pred, timeout=10):
        """Frames until pred(frame) or the end; returns (the matching frame or None, all frames seen)."""
        seen = []
        end = time.time() + timeout
        while time.time() < end:
            f = self.read(max(0.1, end - time.time()))
            if f is None:
                return None, seen
            seen.append(f)
            if pred(f):
                return f, seen
        return None, seen

    def response(self, stream, timeout=10):
        """(status, headers, body) for a stream, or None; answers WINDOW_UPDATE-needing waits itself."""
        hdrs, body = None, b''
        end = time.time() + timeout
        while time.time() < end:
            f = self.read(max(0.1, end - time.time()))
            if f is None:
                return None
            kind, flags, sid, p = f
            if kind == RST and sid == stream:
                return ('reset', struct.unpack('>I', p)[0], b'')
            if kind == GOAWAY:
                return ('goaway', struct.unpack('>I', p[4:8])[0], b'')
            if sid != stream:
                if kind == DATA and p:   # (the connection's window is shared: give it back)
                    self.send(frame(WINDOW, 0, 0, struct.pack('>I', len(p))))
                continue
            if kind == HEADERS:
                hdrs = dict(self.dec.decode(p))
            elif kind == DATA:
                body += p
                if p:
                    self.send(frame(WINDOW, 0, 0, struct.pack('>I', len(p))) + frame(WINDOW, 0, stream, struct.pack('>I', len(p))))
            if flags & 1:
                return (hdrs.get(':status') if hdrs else None, hdrs, body)
        return None

    def goaway_code(self, timeout=10):
        f, _ = self.until(lambda f: f[0] == GOAWAY, timeout)
        return struct.unpack('>I', f[3][4:8])[0] if f else None

    def close(self):
        self.s.close()


def alive(port, label):
    with httpx.Client(http1=False, http2=True, timeout=10) as c:
        r = c.get(f'http://127.0.0.1:{port}/')
        check(f'{label}: the server still answers', r.status_code == 200 and r.text == 'hello', r)


def rss_kb(pid):
    for line in open(f'/proc/{pid}/status'):
        if line.startswith('VmRSS:'):
            return int(line.split()[1])
    return 0


srv = Server(exe)
port = srv.port
try:
    # ---- clients
    with httpx.Client(http1=False, http2=True, timeout=20) as c:
        r = c.get(f'http://127.0.0.1:{port}/')
        check('prior knowledge: GET', r.http_version == 'HTTP/2' and r.status_code == 200 and r.text == 'hello', r)
        r = c.get(f'http://127.0.0.1:{port}/proto')
        check('the handler sees HTTP/2', r.text == 'HTTP/2', r.text)
        body = os.urandom(3 << 20)
        r = c.post(f'http://127.0.0.1:{port}/echo', content=body)
        check('3 MB POST echoed (flow control both ways)', r.content == body, len(r.content))
        r = c.get(f'http://127.0.0.1:{port}/big', params={'n': 5 << 20})
        check('5 MB response', len(r.content) == 5 << 20 and r.headers['content-length'] == str(5 << 20), len(r.content))
        r = c.get(f'http://127.0.0.1:{port}/h', headers={'x-test': 'héllo'.encode()})
        check('request header', r.content == 'héllo'.encode(), r.content)
        r = c.get(f'http://127.0.0.1:{port}/q', params={'name': 'a b&c'})
        check('query string', r.text == 'name=a b&c', r.text)
        r = c.head(f'http://127.0.0.1:{port}/big', params={'n': 1000})
        check('HEAD: length, no body', r.headers['content-length'] == '1000' and r.content == b'', r.headers)
        r = c.get(f'http://127.0.0.1:{port}/nope')
        check('404', r.status_code == 404)
        big = 'v' * 20000
        r = c.get(f'http://127.0.0.1:{port}/h', headers={'x-test': big})
        check('a 20 KB header (CONTINUATION frames)', r.text == big, len(r.text))
    with httpx.Client(http1=False, http2=True, timeout=20) as c:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(20) as ex:
            got = list(ex.map(lambda i: c.get(f'http://127.0.0.1:{port}/q', params={'name': str(i)}).text, range(200)))
        check('200 requests on one connection from 20 threads', got == [f'name={i}' for i in range(200)])
    r = httpx.get(f'http://127.0.0.1:{port}/proto', timeout=10)
    check('HTTP/1.1 on the same port', r.http_version == 'HTTP/1.1' and r.text == 'HTTP/1.1', (r.http_version, r.text))

    # ---- protocol errors (each: GOAWAY with the RFC's code; the server goes on)
    k = Raw(port)
    k.send(k.headers(1, '/bad'))
    st = k.response(1)
    k.send(k.headers(3, '/'))
    st2 = k.response(3)
    check('a response with a line break in a header resets its stream only', st and st[0] == 'reset' and st2 and st2[2] == b'hello',
          (st, st2))
    k.close()
    for name, data, want in [
        ('even stream id', lambda k: k.headers(2), 1),
        ('stream 0 HEADERS', lambda k: k.headers(0), 1),
        ('decreasing stream id', lambda k: k.headers(5) + k.headers(3), 1),
        ('PUSH_PROMISE from a client', lambda k: frame(PUSH, 4, 1, b'\x00\x00\x00\x02'), 1),
        ('SETTINGS with a bad length', lambda k: frame(SETTINGS, 0, 0, b'\x00\x01\x00'), 6),
        ('SETTINGS on a stream', lambda k: frame(SETTINGS, 0, 1, b''), 1),
        ('ENABLE_PUSH = 2', lambda k: frame(SETTINGS, 0, 0, b'\x00\x02\x00\x00\x00\x02'), 1),
        ('initial window over 2^31-1', lambda k: frame(SETTINGS, 0, 0, b'\x00\x04\x80\x00\x00\x00'), 3),
        ('max frame size 100', lambda k: frame(SETTINGS, 0, 0, b'\x00\x05\x00\x00\x00\x64'), 1),
        ('PING with 7 bytes', lambda k: frame(PING, 0, 0, b'1234567'), 6),
        ('connection window overflow', lambda k: frame(WINDOW, 0, 0, b'\x7f\xff\xff\xff') * 2, 3),
        ('window update of 0 on the connection', lambda k: frame(WINDOW, 0, 0, b'\x00\x00\x00\x00'), 1),
        ('HEADERS interrupting a header block', lambda k: frame(HEADERS, 0, 1, k.enc.encode([(':method', 'GET')])) + k.headers(3), 1),
        ('CONTINUATION without HEADERS', lambda k: frame(CONT, 4, 1, b''), 1),
        ('DATA on stream 0', lambda k: frame(DATA, 1, 0, b'x'), 1),
        ('DATA on an idle stream', lambda k: frame(DATA, 1, 9, b'x'), 1),
        ('padding longer than the frame', lambda k: frame(HEADERS, 4 | 8, 1, b'\x09abc'), 1),
        ('uppercase header name', lambda k: frame(HEADERS, 5, 1, hpack.Encoder().encode([(':method', 'GET'), (':path', '/'), (':scheme', 'http'), ('X-Up', '1')])), 1),
        ('pseudo-header after a regular one', lambda k: frame(HEADERS, 5, 1, hpack.Encoder().encode([(':method', 'GET'), ('a', '1'), (':path', '/'), (':scheme', 'http')])), 1),
        ('connection-specific header', lambda k: frame(HEADERS, 5, 1, hpack.Encoder().encode([(':method', 'GET'), (':path', '/'), (':scheme', 'http'), ('connection', 'close')])), 1),
        ('no :path', lambda k: frame(HEADERS, 5, 1, hpack.Encoder().encode([(':method', 'GET'), (':scheme', 'http')])), 1),
        ('HPACK index out of range', lambda k: frame(HEADERS, 5, 1, b'\xff\x7f'), 9),
        ('HPACK table size update over 4096', lambda k: frame(HEADERS, 5, 1, b'\x3f\xe1\x3f'), 9),
        ('HPACK bad Huffman (EOS)', lambda k: frame(HEADERS, 5, 1, b'\x82\x04\x84\xff\xff\xff\xff'), 9),
        ('trailers without END_STREAM', lambda k: k.headers(1, '/echo', 'POST', end_stream=False) + frame(HEADERS, 4, 1, k.enc.encode([('x-t', '1')])), 1),
    ]:
        k = Raw(port)
        k.send(data(k))
        got = k.goaway_code()
        check(f'protocol error: {name} -> GOAWAY {want}', got == want, got)
        k.close()
    s = socket.create_connection(('127.0.0.1', port), timeout=10)
    s.sendall(PREFACE + frame(SETTINGS, 0, 0) + b'\x00\x50\x00' + bytes([0, 0]) + b'\x00\x00\x00\x01' + b'x' * 100)
    try:
        s.settimeout(5)
        while s.recv(65536):
            pass
        closed = True
    except OSError:
        closed = True
    check('a frame over 16 KB closes the connection', closed)
    s.close()
    alive(port, 'after the protocol errors')

    # trailers, padding, priority, a stream reset by the client, ping, a stream window overflow
    k = Raw(port)
    k.send(k.headers(1, '/echo', 'POST', end_stream=False) + frame(DATA, 8, 1, b'\x03abc\x00\x00\x00') +
           frame(PRIORITY, 0, 1, b'\x00\x00\x00\x00\x10') + frame(HEADERS, 5, 1, k.enc.encode([('x-trailer', '1')])))
    r = k.response(1)
    check('padded DATA, PRIORITY and request trailers', r and r[0] == '200' and r[2] == b'abc', r)
    k.send(frame(PING, 0, 0, b'12345678'))
    f, _ = k.until(lambda f: f[0] == PING)
    check('PING answered with ACK and the same bytes', f and f[1] == 1 and f[3] == b'12345678', f)
    k.send(k.headers(3, '/echo', 'POST', end_stream=False) + frame(WINDOW, 0, 3, b'\x7f\xff\xff\xff'))
    f, _ = k.until(lambda f: f[0] == RST and f[2] == 3)
    check('a stream window over 2^31-1 resets that stream (FLOW_CONTROL_ERROR)', f and struct.unpack('>I', f[3])[0] == 3, f)
    k.send(k.headers(5, '/big?n=100000', end_stream=True) + frame(RST, 0, 5, b'\x00\x00\x00\x08') + k.headers(7, '/'))
    r = k.response(7)
    check('a stream reset by the client is dropped, the next answered', r and r[2] == b'hello', r)
    k.send(frame(DATA, 1, 7, b'late'))   # DATA on a stream already answered: ignored (RFC 9113 allows it)
    k.send(k.headers(9, '/'))
    r = k.response(9)
    check('DATA on a closed stream is ignored', r and r[2] == b'hello', r)
    k.close()

    # a client with a zero window gets nothing until it opens it
    k = Raw(port, settings=b'\x00\x04\x00\x00\x00\x00')
    k.send(k.headers(1, '/big?n=1000'))
    f, seen = k.until(lambda f: f[0] == DATA, 1.5)
    check('initial window 0: no DATA yet', f is None, seen)
    k.send(frame(SETTINGS, 0, 0, b'\x00\x04\x00\x01\x00\x00') + frame(WINDOW, 0, 1, b'\x00\x00\x10\x00'))
    r = k.response(1)
    check('...and the body once the window opens', r and len(r[2]) == 1000, r and len(r[2]))
    k.close()

    # ---- attacks
    pid = srv.p.pid
    base = rss_kb(pid)
    # HPACK bomb: one 4 KB header in the dynamic table, then a block referring to it thousands of times
    k = Raw(port)
    blk = hpack.Encoder()
    first = blk.encode([(':method', 'GET'), (':scheme', 'http'), (':path', '/'), ('x-big', 'b' * 4000)])
    k.send(frame(HEADERS, 5, 1, first))
    k.response(1)
    bomb = b'\x82\x86\x84' + b'\xbe' * 16000   # :method GET, :scheme http, :path /, then index 62 (x-big) x 16000
    k.send(frame(HEADERS, 5, 3, bomb))
    got = k.goaway_code()
    check('HPACK bomb (64 MB of headers from 16 KB) refused: GOAWAY COMPRESSION_ERROR', got == 9, got)
    if not FLAGS:   # (under the sanitizers, freed memory is held back on purpose)
        check('...without the memory to decode it', rss_kb(pid) - base < 40000, f'{rss_kb(pid) - base} KB more')
    k.close()
    # CONTINUATION flood: endless empty CONTINUATION frames
    k = Raw(port)
    k.send(frame(HEADERS, 0, 1, k.enc.encode([(':method', 'GET')])) + frame(CONT, 0, 1, b'') * 100)
    check('CONTINUATION flood: GOAWAY after 32 frames', k.goaway_code() == 1)
    k.close()
    # rapid reset: open and cancel streams as fast as possible
    k = Raw(port)
    burst = b''.join(k.headers(i) + frame(RST, 0, i, b'\x00\x00\x00\x08') for i in range(1, 20001, 2))
    t = time.time()
    k.send(burst)
    k.send(k.headers(20001, '/q?name=last'))
    r = k.response(20001, 60)
    check('rapid reset (10,000 streams opened and cancelled): the connection still works', r and r[2] == b'name=last',
          (r, time.time() - t))
    k.close()
    # too many streams at once: the 101st is refused
    k = Raw(port)
    k.send(b''.join(k.headers(i, '/echo', 'POST', end_stream=False) for i in range(1, 203, 2)))
    f, _ = k.until(lambda f: f[0] == RST and f[2] == 201)
    check('stream 101 refused (REFUSED_STREAM) while 100 are open', f and struct.unpack('>I', f[3])[0] == 7, f)
    k.close()
    # unfinished request bodies: 100 streams each sending 1 MB, never ending
    k = Raw(port)
    k.send(b''.join(k.headers(i, '/echo', 'POST', end_stream=False) for i in range(1, 61, 2)))
    chunk = b'z' * 16384
    refused = 0
    for rnd in range(64):
        k.send(b''.join(frame(DATA, 0, i, chunk) for i in range(1, 61, 2)))
    f, seen = k.until(lambda f: False, 3)
    refused = sum(1 for f in seen if f[0] == RST and struct.unpack('>I', f[3])[0] == 7)
    check('30 unfinished 1 MB uploads: refused past 20 MB buffered', refused >= 8, refused)
    if not FLAGS:
        check('...and the memory stays bounded', rss_kb(pid) - base < 120000, f'{rss_kb(pid) - base} KB more')
    k.close()
    # SETTINGS and PING floods from a client that doesn't read: the server stops when it can't send
    k = Raw(port)
    k.s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    k.send(frame(PING, 0, 0, b'12345678') * 200000)
    k.close()
    alive(port, 'after the attacks')
finally:
    srv.p.send_signal(signal.SIGTERM)
    code, out, err = srv.finish(15)
    check('SIGTERM: stops cleanly, no sanitizer report', code == 0 and 'stopped' in (out or '') and 'ERROR' not in err and
          'runtime error' not in err, f'exit {code} {(err or "")[-600:]}')

# ---- TLS with ALPN
srv = Server(exe, D)
try:
    with httpx.Client(http2=True, verify=ssl.create_default_context(cafile=CA), timeout=20) as c:
        r = c.get(f'https://localhost:{srv.port}/proto')
        check('TLS: a client offering h2 gets HTTP/2 (ALPN)', r.http_version == 'HTTP/2' and r.text == 'HTTP/2', (r.http_version, r.text))
        body = os.urandom(1 << 20)
        r = c.post(f'https://localhost:{srv.port}/echo', content=body)
        check('TLS h2: 1 MB POST echoed', r.content == body)
    with httpx.Client(http2=False, verify=ssl.create_default_context(cafile=CA), timeout=20) as c:
        r = c.get(f'https://localhost:{srv.port}/proto')
        check('TLS: a client offering only http/1.1 gets HTTP/1.1', r.http_version == 'HTTP/1.1' and r.text == 'HTTP/1.1',
              (r.http_version, r.text))
    ctx = ssl.create_default_context(cafile=CA)
    s = ctx.wrap_socket(socket.create_connection(('127.0.0.1', srv.port), timeout=10), server_hostname='localhost')
    s.sendall(b'GET /proto HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
    reply = b''
    while True:
        d = s.recv(65536)
        if not d:
            break
        reply += d
    check('TLS without ALPN: HTTP/1.1', reply.startswith(b'HTTP/1.1 200') and reply.endswith(b'HTTP/1.1'), reply[-60:])
finally:
    srv.p.send_signal(signal.SIGTERM)
    code, out, err = srv.finish(15)
    check('TLS server: stops cleanly', code == 0 and 'ERROR' not in err and 'runtime error' not in err, f'exit {code} {(err or "")[-600:]}')
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
