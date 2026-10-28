"""http.Client: keep-alive and HTTP/2. Against Python's http.server (HTTP/1.1 keep-alive, with the
connections counted), Vu's own server (tests/net/h2_serve.vu: HTTP/2 over TLS by ALPN, and HTTP/1.1),
a server on the h2 package (an independent HTTP/2 implementation, with a tiny flow-control window
and GOAWAY after some requests), and hand-built frames from servers that break HTTP/2. Each request's
status, length and body hash are checked against what was sent. Extra arguments (--san) go to the
build."""
import hashlib
import http.server
import os
import socket
import socketserver
import ssl
import struct
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, counts, work, free_port  # noqa: E402
import h2.config  # noqa: E402
import h2.connection  # noqa: E402
import h2.events  # noqa: E402
import h2.settings  # noqa: E402
import hpack  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
exe = build(os.path.join(HERE, 'http', 'client.vu'))
vu_server = build(os.path.join(HERE, 'net', 'h2_serve.vu'))
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
openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.csr', '-subj', '/CN=localhost')
openssl('x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
        '-out', 'server.pem', '-days', '30', '-extfile', 'san.ext')
CA = os.path.join(D, 'ca.pem')


def h(body):
    return hashlib.sha256(body).hexdigest()[:12]


def abc(n):
    return (b'abcdefghijklmnopqrstuvwxyz' * (n // 26 + 1))[:n]


def run(lines, *args):
    r = subprocess.run([exe, *args], input='\n'.join(lines) + '\n', capture_output=True, text=True, errors='replace', timeout=120)
    return r.returncode, r.stdout.rstrip('\n').split('\n'), r.stderr


def expect(name, lines, want, want_tail, *args):
    rc, got, err = run(lines, *args)
    tail_ok = want_tail(got[-1]) if callable(want_tail) else got[-1] == want_tail
    ok = rc == 0 and got[:-1] == want and tail_ok and 'ERROR' not in err and 'runtime error' not in err
    check(name, ok, f'exit {rc}\nwant {want} / {want_tail}\ngot  {got}\n{err[-500:]}')


# ---- HTTP/1.1 keep-alive against Python's http.server
conns = []


class H(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        super().setup()
        conns.append(1)

    def log_message(self, *a):
        pass

    def reply(self, body, close=False, length=True, chunked=False):
        self.send_response(200)
        if close:
            self.send_header('Connection', 'close')
        if chunked:
            self.send_header('Transfer-Encoding', 'chunked')
        elif length:
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command == 'HEAD':
            return
        if chunked:
            for i in range(0, len(body), 1000):
                part = body[i:i + 1000]
                self.wfile.write(b'%x\r\n' % len(part) + part + b'\r\n')
            self.wfile.write(b'0\r\n\r\n')
        else:
            self.wfile.write(body)
        if close or not length:
            self.close_connection = True

    def do_GET(self):
        p, _, q = self.path.partition('?')
        n = int(q or '0')
        if p == '/close': return self.reply(abc(n), close=True)
        if p == '/nolen': return self.reply(abc(n), length=False)
        if p == '/chunked': return self.reply(abc(n), chunked=True)
        if p == '/hang-up':
            # answers, then closes without saying so (a server's idle timeout)
            self.reply(abc(n))
            self.close_connection = True
            return
        return self.reply(abc(n))

    do_HEAD = do_GET

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        self.reply(body)

    do_PUT = do_POST


class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


hs = TS(('127.0.0.1', 0), H)
threading.Thread(target=hs.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{hs.server_address[1]}'


def once(name, lines, want, tail, *args):
    conns.clear()
    expect(name, lines, want, tail, *args)


once('keep-alive: 20 GETs, one connection', [f'GET {base}/?{i * 37} 0' for i in range(20)],
     [f'200 {i * 37} {h(abc(i * 37))}' for i in range(20)], 'opened 1 reused 19')
check('keep-alive: the server saw one connection', len(conns) == 1, f'{len(conns)} connections')
once('keep-alive: GET, POST, HEAD, chunked, PUT on one connection',
     [f'GET {base}/?5 0', f'POST {base}/ 70000', f'HEAD {base}/?99 0', f'GET {base}/chunked?5000 0', f'PUT {base}/ 3'],
     ['200 5 ' + h(abc(5)), '200 70000 ' + h(b'b' * 70000), '200 0 ' + h(b''), '200 5000 ' + h(abc(5000)), '200 3 ' + h(b'bbb')],
     'opened 1 reused 4')
once('Connection: close from the server: the next request opens a new connection',
     [f'GET {base}/close?10 0', f'GET {base}/?10 0', f'GET {base}/?11 0'],
     ['200 10 ' + h(abc(10))] + ['200 10 ' + h(abc(10)), '200 11 ' + h(abc(11))], 'opened 2 reused 1')
once('a body read to the close: not reused', [f'GET {base}/nolen?300 0', f'GET {base}/?3 0'],
     ['200 300 ' + h(abc(300)), '200 3 ' + h(abc(3))], 'opened 2 reused 0')
# (whether the close is seen before the next request or only when it fails, a GET goes through)
once('a server that hangs up after answering: a GET goes on a new connection',
     [f'GET {base}/hang-up?4 0', f'GET {base}/?9 0', f'GET {base}/hang-up?6 0', f'GET {base}/?7 0'],
     ['200 4 ' + h(abc(4)), '200 9 ' + h(abc(9)), '200 6 ' + h(abc(6)), '200 7 ' + h(abc(7))],
     lambda t: t.startswith('opened 3 '))

# ---- HTTP/2 against Vu's own server (TLS, ALPN)
vs = Server(vu_server, D)
vb = f'https://localhost:{vs.port}'
sizes = [0, 1, 26, 16384, 16385, 65535, 65536, 200000, 3000000]
expect('h2: GETs of 0 B to 3 MB on one connection (flow control, many DATA frames)',
       [f'GET {vb}/big?n={n} 0' for n in sizes] + [f'GET {vb}/proto 0'],
       [f'200 {n} {h(abc(n))}' for n in sizes] + ['200 6 ' + h(b'HTTP/2')], f'opened 1 reused {len(sizes)}', CA)
expect('h2: POST bodies up to 1 MB (the server\'s 64 KB window: the client waits for WINDOW_UPDATE)',
       [f'POST {vb}/echo {n} ' for n in [0, 5, 65535, 65536, 1048576]],
       [f'200 {n} {h(b"b" * n)}' for n in [0, 5, 65535, 65536, 1048576]], 'opened 1 reused 4', CA)
expect('h2: a header sent, and 404', [f'GET {vb}/h 0 X-Test=abc', f'GET {vb}/nope 0'],
       ['200 3 ' + h(b'abc'), '404 9 ' + h(b'not found')], 'opened 1 reused 1', CA)
expect('h2 turned off (http2 = false): HTTP/1.1 over TLS, kept alive', [f'GET {vb}/proto 0', f'GET {vb}/big?n=7 0'],
       ['200 8 ' + h(b'HTTP/1.1'), '200 7 ' + h(abc(7))], 'opened 1 reused 1', CA, 'h1')
rc, got, err = run([f'GET {vb}/ 0'], '-')
check('h2: a certificate from a CA the client doesn\'t trust is refused', rc == 0 and got[0].startswith('error: ') and 'certificate' in got[0], got)
vs.p.terminate()
vs.finish()

# ---- HTTP/2 against the h2 package: a 16-byte window, frames of 16 KB, GOAWAY every 3 streams,
# REFUSED_STREAM once, informational responses and trailers
stats = {'conns': 0, 'streams': 0, 'refused': False}


def h2_conn(s, opts):
    cfg = h2.config.H2Configuration(client_side=False, header_encoding=None)
    c = h2.connection.H2Connection(config=cfg)
    c.initiate_connection()
    c.update_settings({h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: 16})
    s.sendall(c.data_to_send())
    reqs = {}
    pending = {}     # stream -> body still to send
    served = 0

    def pump():
        for sid in list(pending):
            body = pending[sid]
            while body:
                room = min(c.local_flow_control_window(sid), c.max_outbound_frame_size, len(body))
                if room <= 0:
                    break
                c.send_data(sid, body[:room])
                body = body[room:]
            pending[sid] = body
            if not body:
                c.end_stream(sid)
                del pending[sid]
                if opts.get('trailers'):
                    pass
    while True:
        data = s.recv(65536)
        if not data:
            return
        for ev in c.receive_data(data):
            if isinstance(ev, h2.events.RequestReceived):
                reqs[ev.stream_id] = [dict(ev.headers), b'']
                stats['streams'] += 1
            elif isinstance(ev, h2.events.DataReceived):
                reqs[ev.stream_id][1] += ev.data
                c.acknowledge_received_data(ev.flow_controlled_length, ev.stream_id)
            elif isinstance(ev, h2.events.StreamEnded):
                hd, body = reqs.pop(ev.stream_id)
                path = hd[b':path'].decode()
                if path.startswith('/refuse') and not stats['refused']:
                    stats['refused'] = True
                    c.reset_stream(ev.stream_id, 7)
                    continue
                if hd[b':method'] == b'POST':
                    out = body
                else:
                    out = abc(int(path.split('?')[1]) if '?' in path else 0)
                if path.startswith('/info'):
                    c.send_headers(ev.stream_id, [(':status', '103'), ('link', '</a>')])
                c.send_headers(ev.stream_id, [(':status', '200'), ('content-length', str(len(out)))])
                pending[ev.stream_id] = out
                if not out:
                    c.end_stream(ev.stream_id)
                    del pending[ev.stream_id]
                served += 1
                if served % 3 == 0:
                    pump()
                    s.sendall(c.data_to_send())
                    while pending:
                        more = s.recv(65536)
                        if not more:
                            return
                        for e2 in c.receive_data(more):
                            pass
                        pump()
                        s.sendall(c.data_to_send())
                    c.close_connection(last_stream_id=ev.stream_id)
                    s.sendall(c.data_to_send())
                    return
        pump()
        s.sendall(c.data_to_send())


def tls_server(handler, alpn=('h2',)):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(os.path.join(D, 'server.pem'), os.path.join(D, 'server.key'))
    ctx.set_alpn_protocols(list(alpn))
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 0))
    srv.listen(16)

    def loop():
        while True:
            try:
                raw, _ = srv.accept()
            except OSError:
                return
            def one(raw=raw):
                try:
                    s = ctx.wrap_socket(raw, server_side=True)
                    stats['conns'] += 1
                    handler(s)
                except Exception:
                    pass
                finally:
                    raw.close()
            threading.Thread(target=one, daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()
    return srv, srv.getsockname()[1]


srv, port = tls_server(lambda s: h2_conn(s, {}))
pb = f'https://localhost:{port}'
stats.update(conns=0, streams=0)
lines = [f'GET {pb}/?{n} 0' for n in [0, 10, 70000, 5, 100000, 1, 2, 3]] + [f'POST {pb}/ 40000', f'GET {pb}/refuse?9 0', f'GET {pb}/info?4 0']
want = [f'200 {n} {h(abc(n))}' for n in [0, 10, 70000, 5, 100000, 1, 2, 3]] + ['200 40000 ' + h(b'b' * 40000), '200 9 ' + h(abc(9)), '200 4 ' + h(abc(4))]
expect('h2 package server: a 16-byte window, GOAWAY after every 3 requests (new connections), REFUSED_STREAM (sent again), 103 then 200',
       lines, want, lambda t: t.startswith('opened 5 '), CA)
srv.close()

# ---- servers that break HTTP/2 (hand-built frames): each must end in an error, never a crash or a hang


def frame(kind, flags, stream, payload=b''):
    return struct.pack('>I', len(payload))[1:] + bytes([kind, flags]) + struct.pack('>I', stream) + payload


enc = hpack.Encoder()


def hdrs(pairs):
    return hpack.Encoder().encode(pairs)


def read_request(s):
    """Reads the client's preface, settings and one request (HEADERS ... END_STREAM); returns the frames."""
    buf = b''
    frames = []
    while not buf.startswith(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n') or len(buf) < 24:
        d = s.recv(65536)
        if not d:
            return frames
        buf += d
    buf = buf[24:]
    while True:
        while len(buf) >= 9 and len(buf) >= 9 + int.from_bytes(buf[:3], 'big'):
            n = int.from_bytes(buf[:3], 'big')
            f = (buf[3], buf[4], int.from_bytes(buf[5:9], 'big') & 0x7fffffff, buf[9:9 + n])
            buf = buf[9 + n:]
            frames.append(f)
            if f[0] in (0, 1) and f[1] & 1:
                return frames
        d = s.recv(65536)
        if not d:
            return frames
        buf += d


OK200 = hdrs([(':status', '200'), ('content-length', '2')])
hostile = {
    'PUSH_PROMISE (push is off)': ([frame(1, 4, 1, OK200), frame(5, 4, 1, struct.pack('>I', 2) + hdrs([(':method', 'GET'), (':path', '/x')]))], 'broke HTTP/2 (error 1)'),
    'DATA before HEADERS': ([frame(0, 1, 1, b'hi')], 'broke HTTP/2 (error 1)'),
    'HEADERS on a stream the client never opened': ([frame(1, 5, 3, OK200)], 'broke HTTP/2 (error 1)'),
    'a header block HPACK can\'t decode': ([frame(1, 5, 1, b'\xff\xff\xff\xff\xff\xff')], 'broke HTTP/2 (error 9)'),
    'a frame of 20000 bytes': ([frame(1, 4, 1, OK200), frame(0, 1, 1, b'x' * 20000)], 'a frame larger than we allow'),
    'a body shorter than its content-length': ([frame(1, 4, 1, OK200), frame(0, 1, 1, b'x')], "the body's length isn't its content-length"),
    '33 CONTINUATION frames': ([frame(1, 0, 1, hdrs([(':status', '200')]))] + [frame(9, 0, 1, b'')] * 33, 'broke HTTP/2 (error 1)'),
    'an uppercase header name': ([frame(1, 5, 1, hdrs([(':status', '200'), ('X-Big', 'y')]))], 'broke HTTP/2 (error 1)'),
    'no :status': ([frame(1, 5, 1, hdrs([('content-type', 'x')]))], 'broke HTTP/2 (error 1)'),
    'a :status of "abc"': ([frame(1, 5, 1, hdrs([(':status', 'abc')]))], 'broke HTTP/2 (error 1)'),
    ':status after a regular header': ([frame(1, 5, 1, hdrs([('a', 'b'), (':status', '200')]))], 'broke HTTP/2 (error 1)'),
    'padding longer than the frame': ([frame(1, 4, 1, OK200), frame(0, 9, 1, b'\x09ab')], 'broke HTTP/2 (error 1)'),
    'SETTINGS with a frame size under 16384': ([frame(4, 0, 0, struct.pack('>HI', 5, 16383))], 'broke HTTP/2 (error 1)'),
    'a connection window past 2^31-1': ([frame(8, 0, 0, struct.pack('>I', 0x7fffffff))], 'broke HTTP/2 (error 3)'),
    'RST_STREAM INTERNAL_ERROR': ([frame(3, 0, 1, struct.pack('>I', 2))], 'the server reset the request (error 2)'),
    'closed in the middle of the body': ([frame(1, 4, 1, hdrs([(':status', '200'), ('content-length', '9')])), frame(0, 0, 1, b'abc'), None], 'closed'),
    'a response of 65 MB': ([frame(1, 4, 1, hdrs([(':status', '200')]))] + [frame(0, 0, 1, b'x' * 16384)] * 4161, 'the response is too large'),
    'an HPACK bomb (a 4 KB entry referenced 100 times)': ([frame(1, 5, 1, hdrs([(':status', '200')]) + b'\x40\x01a\x7f\xa1\x1e' + b'v' * 4000 + b'\xbe' * 100)], 'broke HTTP/2 (error 9)'),
    'GOAWAY before answering (sent again, then given up)': ([frame(7, 0, 0, struct.pack('>II', 0, 0)), None], 'the server is going away'),
    'silence': ([], 'timed out'),
    'a PING in the middle, trailers at the end: fine': ([frame(1, 4, 1, OK200), frame(6, 0, 0, b'12345678'), frame(0, 0, 1, b'hi'),
                                                        frame(1, 5, 1, hdrs([('x-trailer', '1')]))], '200 2 ' + h(b'hi')),
    'padded HEADERS and DATA: fine': ([frame(1, 0x0c, 1, b'\x03' + OK200 + b'\0\0\0'), frame(0, 0x09, 1, b'\x02hi\0\0')], '200 2 ' + h(b'hi')),
}
seen_ack = []


def hostile_conn(s, frames):
    req = read_request(s)
    s.sendall(frame(4, 0, 0) + frame(4, 1, 0))
    for f in frames:
        if f is None:
            s.shutdown(socket.SHUT_RDWR)
            return
        s.sendall(f)
    s.settimeout(8)
    try:
        while True:
            d = s.recv(65536)
            if not d:
                return
            if b'\x00\x00\x08\x06\x01' in d:
                seen_ack.append(1)
    except OSError:
        return


for name, (frames, want) in hostile.items():
    srv, port = tls_server(lambda s, fr=frames: hostile_conn(s, fr))
    stats['conns'] = 0
    seen_ack.clear()
    rc, got, err = run([f'GET https://localhost:{port}/ 0'], CA)
    ok = rc == 0 and len(got) == 2 and want in got[0] and 'ERROR' not in err and 'runtime error' not in err
    if name.startswith('GOAWAY'):
        ok = ok and got[1].startswith('opened 2')
    if 'PING' in name:
        ok = ok and len(seen_ack) > 0
    check(f'h2 server: {name}', ok, f'exit {rc}: {got} {err[-400:]}')
    srv.close()

print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
