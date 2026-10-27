"""The standard library's http module (std/http.vu): tests/net/http_std.vu (a server) against raw Python
sockets, and tests/net/http_client.vu (a client) against Python servers. Runs against the compiler named
by VU (default: ../vu, the compiler); extra arguments (--san) go to the build."""
import os
import socket
import ssl
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, free_port, work, counts, recv_exactly  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
server = build(os.path.join(HERE, 'net', 'http_std.vu'))
client = build(os.path.join(HERE, 'net', 'http_client.vu'))


def exchange(port, data, wait=2.0, pieces=None):
    """Sends data (all at once, or in pieces of that size) and returns every byte until the server closes
    or wait seconds pass without anything new."""
    s = socket.create_connection(('127.0.0.1', port), timeout=10)
    if pieces:
        for i in range(0, len(data), pieces):
            s.sendall(data[i:i + pieces])
            time.sleep(0.001)
    else:
        s.sendall(data)
    s.settimeout(wait)
    out = b''
    try:
        while True:
            d = s.recv(1 << 20)
            if not d:
                return out, True
            out += d
    except socket.timeout:
        return out, False
    finally:
        s.close()


def responses(raw):
    """Splits raw bytes into (status, headers dict, body) by Content-Length."""
    out = []
    while raw:
        head, _, rest = raw.partition(b'\r\n\r\n')
        lines = head.split(b'\r\n')
        status = int(lines[0].split()[1])
        hs = {}
        for l in lines[1:]:
            k, _, v = l.partition(b':')
            hs[k.strip().lower().decode()] = v.strip().decode()
        n = int(hs.get('content-length', 0))
        out.append((status, hs, rest[:n]))
        raw = rest[n:]
    return out


def get(path, extra=b''):
    return b'GET ' + path + b' HTTP/1.1\r\nHost: x\r\n' + extra + b'\r\n'


srv = Server(server, 2)
p = srv.port
try:
    raw, closed = exchange(p, get(b'/'), wait=1.0)   # the server's idle timeout is 2 s
    r = responses(raw)
    check('GET / -> 200 hello, connection kept open', r == [(200, r[0][1], b'hello')] and not closed
          and r[0][1]['content-type'] == 'text/plain; charset=utf-8', raw)
    raw, closed = exchange(p, get(b'/') + get(b'/q?name=a%20b+c%2B') + get(b'/nope'))
    r = responses(raw)
    check('three pipelined requests, in order', [(x[0], x[2]) for x in r] ==
          [(200, b'hello'), (200, b'name=a b c+'), (404, b'not found')], raw)
    body = os.urandom(300000)
    req = b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: %d\r\n\r\n' % len(body) + body
    raw, _ = exchange(p, req)
    check('POST with Content-Length, 300 KB echoed', responses(raw)[0][2] == body, len(raw))
    raw, _ = exchange(p, req[:2000], pieces=1)
    raw, _ = exchange(p, b'POST /echo HTTP/1.1\r\nhOsT: x\r\ncontent-LENGTH:  5 \r\n\r\nhello' + get(b'/'), pieces=1)
    check('a request sent one byte at a time, mixed-case headers', [(x[0], x[2]) for x in responses(raw)] ==
          [(200, b'hello'), (200, b'hello')], raw)
    chunked = (b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n'
               b'5;ext=1\r\nhello\r\n1A\r\n abcdefghijklmnopqrstuvwxy\r\n0\r\nX-Trailer: t\r\n\r\n')
    raw, _ = exchange(p, chunked + get(b'/'))
    check('chunked request body (an extension, a trailer), then another request',
          [(x[0], x[2]) for x in responses(raw)] == [(200, b'hello abcdefghijklmnopqrstuvwxy'), (200, b'hello')], raw)
    raw, _ = exchange(p, chunked, pieces=3)
    check('chunked body in 3-byte pieces', responses(raw)[0][2] == b'hello abcdefghijklmnopqrstuvwxy', raw)
    # a long request, then the start of a chunked one: when the rest arrives the buffer is compacted
    # while the server is in the middle of the chunked body, so where it stopped must move too
    s2 = socket.create_connection(('127.0.0.1', p), timeout=10)
    first = get(b'/', b'X-Pad: ' + b'p' * 3000 + b'\r\n')
    s2.sendall(first + b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n3\r\nab')
    time.sleep(0.3)
    s2.sendall(b'c\r\n0\r\n\r\n')
    s2.settimeout(2)
    got = b''
    try:
        while got.count(b'HTTP/1.1') < 2 or not got.endswith(b'helloabc'):
            d = s2.recv(65536)
            if not d:
                break
            got += d
    except socket.timeout:
        pass
    s2.close()
    check('a chunked body resumed after the buffer was compacted', [(x[0], x[2]) for x in responses(got)] ==
          [(200, b'hello'), (200, b'helloabc')], got[-200:])
    # Expect: 100-continue: the client waits for the interim response before sending the body
    s3 = socket.create_connection(('127.0.0.1', p), timeout=5)
    s3.sendall(b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 4\r\nExpect: 100-continue\r\n\r\n')
    interim = s3.recv(100)
    s3.sendall(b'body')
    rest = b''
    while not rest.endswith(b'body'):
        rest += s3.recv(1000)
    s3.close()
    check('Expect: 100-continue gets "100 Continue", then the answer', interim == b'HTTP/1.1 100 Continue\r\n\r\n'
          and responses(rest)[0][2] == b'body', (interim, rest))
    raw, _ = exchange(p, b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 4\r\nExpect: 100-continue\r\n\r\nbody')
    check('no "100 Continue" when the body came along anyway', raw.startswith(b'HTTP/1.1 200 OK'), raw[:60])
    raw, closed = exchange(p, b'GET / HTTP/1.0\r\n\r\n')
    check('HTTP/1.0 without keep-alive: answered, then closed', responses(raw)[0][2] == b'hello' and closed, raw)
    raw, closed = exchange(p, get(b'/', b'Connection: close\r\n') + get(b'/'))
    check('Connection: close: one answer that says so, then closed', len(responses(raw)) == 1 and closed
          and responses(raw)[0][1].get('connection') == 'close', raw)
    raw, closed = exchange(p, b'GET / HTTP/1.0\r\nConnection: keep-alive\r\n\r\n', wait=1.0)
    check('HTTP/1.0 with keep-alive stays open and says so', not closed and responses(raw)[0][2] == b'hello'
          and responses(raw)[0][1].get('connection') == 'keep-alive', raw)
    raw, closed = exchange(p, b'HEAD / HTTP/1.1\r\nHost: x\r\n\r\n' + get(b'/'), wait=1.0)
    check('HEAD: Content-Length of the body, but no body', raw.startswith(b'HTTP/1.1 200 OK\r\n')
          and raw.count(b'Content-Length: 5') == 2 and raw.count(b'hello') == 1, raw)
    raw, closed = exchange(p, get(b'/h', b'User-Agent: test agent/1\r\n'))
    check('a request header read by name, in any case', responses(raw)[0][2] == b'test agent/1', raw)
    t0 = time.time()
    raw, closed = exchange(p, b'GET / HTTP/1.1\r\nHost: x\r\n', wait=6)
    check('an idle connection is closed after the timeout (2 s)', raw == b'' and closed and time.time() - t0 < 5,
          f'{time.time() - t0:.1f}s {raw!r}')
    raw, closed = exchange(p, get(b'/inject?v=a%0d%0aSet-Cookie:%20x=1'))
    check('a header value with a line break is refused, nothing injected', b'Set-Cookie' not in raw and closed, raw)

    bad = [
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n', 400,
         'both Transfer-Encoding and Content-Length'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\nContent-Length: 6\r\n\r\nhello!', 400,
         'two different Content-Length headers'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 5x\r\n\r\nhello', 400, "Content-Length isn't a number"),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: -1\r\n\r\n', 400, "Content-Length isn't a number"),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: ' + b'\xff' * 18 + b'\r\n\r\n', 400,
         "Content-Length isn't a number"),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 999999999999999999\r\n\r\n', 413, 'the body is too large'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: gzip\r\n\r\n', 501, 'only the chunked'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\nTransfer-Encoding: identity\r\n\r\n0\r\n\r\n',
         400, 'more than one Transfer-Encoding header'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 10485761\r\n\r\n', 413, 'the body is too large'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\nFFFFFFFFFFFFFFFFFFFF\r\n', 413,
         'the body is too large'),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabcXY', 400,
         "a chunk's data isn't followed by CRLF"),
        (b'POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\nzz\r\n', 400,
         "a chunk doesn't start with its size in hex"),
        (b'GET / HTTP/1.1\r\nHost: x\r\nX-' + b'a' * 70000 + b': 1\r\n\r\n', 431, 'the header section is too large'),
        (b'GET / HTTP/1.1\r\nHost: x\r\n' + b''.join(b'X-%d: 1\r\n' % i for i in range(101)) + b'\r\n', 431,
         'too many header lines'),
        (b'GET / HTTP/1.1\r\nHost: x\r\nX-A: 1\r\n  folded\r\n\r\n', 400, 'line folding'),
        (b'GET / HTTP/1.1\r\nHost: x\r\nBad Name: 1\r\n\r\n', 400, "a header name contains a character"),
        (b'GET / HTTP/1.1\r\nX-A: 1\r\n\r\n', 400, 'an HTTP/1.1 request needs a Host header'),
        (b'GET / HTTP/1.1\r\nHost: a\r\nHost: b\r\n\r\n', 400, 'more than one Host header'),
        (b'GET / HTTP/2.0\r\nHost: x\r\n\r\n', 505, 'only HTTP/1.0 and HTTP/1.1'),
        (b'G(T / HTTP/1.1\r\nHost: x\r\n\r\n', 400, "the method isn't a token"),
        (b'GET http://x/ HTTP/1.1\r\nHost: x\r\n\r\n', 400, "the target must start with '/'"),
        (b'GET  / HTTP/1.1\r\nHost: x\r\n\r\n', 400, 'the request line is malformed'),
        (b'GET / HTTP/1.1 extra\r\nHost: x\r\n\r\n', 400, 'the request line is malformed'),
        (b'GET /\x01 HTTP/1.1\r\nHost: x\r\n\r\n', 400, 'the target contains a control character'),
        (b'GET / HTTP/1.1\r\nHost: x\r\nX-A: a\x00b\r\n\r\n', 400, 'a header value contains a control character'),
        (b'GET / HTTP/1.1\nHost: x\n\n\r\n\r\n', 400, ''),
    ]
    for req, status, why in bad:
        raw, closed = exchange(p, req)
        r = responses(raw) if raw.startswith(b'HTTP/') else []
        ok = len(r) == 1 and r[0][0] == status and why.encode() in r[0][2] and closed and r[0][1].get('connection') == 'close'
        check(f'bad request -> {status} {why or "(LF-only lines)"}', ok, (raw[:200], closed))
    raw, _ = exchange(p, get(b'/'))
    check('still serving after all of that', responses(raw)[0][2] == b'hello', raw)

    # the Vu client against the Vu server
    r = subprocess.run([client, 'POST', f'http://127.0.0.1:{p}/echo', 'from the vu client'], capture_output=True,
                       text=True, timeout=30)
    check('Vu client -> Vu server (POST)', r.returncode == 0 and 'status 200' in r.stdout
          and 'body 18: from the vu client' in r.stdout, r.stdout + r.stderr)
    r = subprocess.run([client, 'GET', f'http://localhost:{p}/q?name=x%26y'], capture_output=True, text=True, timeout=30)
    check('Vu client -> Vu server (query, by name)', 'body 8: name=x&y' in r.stdout, r.stdout + r.stderr)
finally:
    exchange(p, get(b'/quit'), wait=0.5)
    code, out, err = srv.finish()
check('server quits cleanly', code == 0 and out.strip() == 'quit', (code, out, err[-300:]))
check('bad requests logged', 'bad: 431 too many header lines' in err and 'info listening on' in err, err[-500:])
check('the injected header was refused on the server', 'reply: the value of header \'X-V\' contains a line break' in err,
      err[-500:])
check('no sanitizer report', 'ERROR' not in err and 'runtime error' not in err, err[-600:])
import json as _json
logged = [_json.loads(l) for l in err.splitlines() if l.startswith('{')]
check('log.json: one JSON object per line, with the fields',
      any(e.get('level') == 'warn' and e.get('msg') == 'bad request' and e.get('status') == '431'
          and e.get('why') == 'too many header lines' and e.get('time', '').endswith('Z') for e in logged), logged[:2])


# ---- the client against Python servers, each answering one connection with fixed bytes
def py_server(reply, tls=False, pieces=None):
    ls = socket.socket()
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(('127.0.0.1', 0))
    ls.listen(1)
    port = ls.getsockname()[1]
    got = []

    def run():
        try:
            c, _ = ls.accept()
            c.settimeout(10)
            if tls:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ctx.load_cert_chain(os.path.join(D, 'server.pem'), os.path.join(D, 'server.key'))
                c = ctx.wrap_socket(c, server_side=True)
            req = b''
            while b'\r\n\r\n' not in req:
                d = c.recv(65536)
                if not d:
                    break
                req += d
            got.append(req)
            if pieces:
                for i in range(0, len(reply), pieces):
                    c.sendall(reply[i:i + pieces])
                    time.sleep(0.001)
            else:
                c.sendall(reply)
            c.close()
        except (OSError, ssl.SSLError):
            pass
        ls.close()
    threading.Thread(target=run, daemon=True).start()
    return port, got


def run_client(port, method='GET', path='/', body='', scheme='http', ca=''):
    r = subprocess.run([client, method, f'{scheme}://localhost:{port}{path}', body] + ([ca] if ca else []),
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout + r.stderr


D = os.path.join(work, 'certs')
os.makedirs(D)
for args in [('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '30',
              '-subj', '/CN=Vu Test CA', '-addext', 'basicConstraints=critical,CA:TRUE',
              '-addext', 'keyUsage=critical,keyCertSign,cRLSign'),
             ('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.csr', '-subj', '/CN=localhost')]:
    subprocess.run(['openssl', *args], cwd=D, check=True, capture_output=True)
open(os.path.join(D, 'san.ext'), 'w').write('subjectAltName=DNS:localhost\nkeyUsage=critical,digitalSignature,keyEncipherment\n'
                                           'extendedKeyUsage=serverAuth\nauthorityKeyIdentifier=keyid\n')
subprocess.run(['openssl', 'x509', '-req', '-in', 'server.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial',
                '-out', 'server.pem', '-days', '30', '-extfile', 'san.ext'], cwd=D, check=True, capture_output=True)

port, got = py_server(b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 5\r\n\r\nhello')
code, out = run_client(port, 'POST', '/x?y=1', 'abc')
req = got[0] if got else b''
check('client: Content-Length response', code == 0 and 'status 200' in out and 'body 5: hello' in out
      and 'content-type=text/plain' in out, out)
check('client: the request it sent', req.startswith(b'POST /x?y=1 HTTP/1.1\r\nHost: localhost:%d\r\n' % port)
      and b'Content-Length: 3\r\n' in req and b'Connection: close\r\n' in req and b'User-Agent: vu-http' in req, req)
port, _ = py_server(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n4;x=y\r\nwiki\r\n5\r\npedia\r\n0\r\nT: 1\r\n\r\n', pieces=2)
code, out = run_client(port)
check('client: chunked response in 2-byte pieces', code == 0 and 'body 9: wikipedia' in out, out)
port, _ = py_server(b'HTTP/1.0 200 OK\r\n\r\nuntil the connection closes')
code, out = run_client(port)
check('client: a body without a length, read to the close', code == 0 and 'body 27: until the connection closes' in out, out)
port, _ = py_server(b'HTTP/1.1 100 Continue\r\n\r\nHTTP/1.1 204 No Content\r\nX-A: 1\r\n\r\n')
code, out = run_client(port)
check('client: 100 Continue skipped, 204 has no body', code == 0 and 'status 204' in out and 'body 0:' in out, out)
port, _ = py_server(b'HTTP/1.1 200 OK\r\nContent-Length: 1000\r\n\r\nshort')
code, out = run_client(port)
check('client: a body cut short is an error', code == 1 and 'the connection closed before the whole body arrived' in out, out)
port, _ = py_server(b'SSH-2.0-OpenSSH\r\n\r\n')
code, out = run_client(port)
check('client: not an HTTP response', code == 1 and 'bad response: no HTTP status line' in out, out)
port, _ = py_server(b'HTTP/1.1 301 Moved\r\nLocation: /new\r\nContent-Length: 0\r\n\r\n')
code, out = run_client(port)
check('client: a redirect is returned, not followed', code == 0 and 'status 301' in out and 'location=/new' in out, out)
port, _ = py_server(b'HTTP/1.1 200 OK\r\nContent-Length: 7\r\n\r\nsecured', tls=True)
code, out = run_client(port, scheme='https', ca=os.path.join(D, 'ca.pem'))
check('client: https with a CA', code == 0 and 'body 7: secured' in out, out)
port, _ = py_server(b'HTTP/1.1 200 OK\r\nContent-Length: 7\r\n\r\nsecured', tls=True)
code, out = run_client(port, scheme='https')
check('client: https with the system CAs refuses a private CA', code == 1 and "can't verify" in out, out)
for url, want in [('ftp://x/', 'must start with http:// or https://'), ('http:///x', 'the URL has no host'),
                  ('http://x:0/', "the port '0' is not 1..65535"), ('http://u:p@x/', "user names and passwords"),
                  ('http://x/a b', 'the URL contains a space')]:
    r = subprocess.run([client, 'GET', url], capture_output=True, text=True, timeout=30)
    check(f'client: bad URL {url}', r.returncode == 1 and want in r.stderr, r.stderr)


# ---- http.serve: a handler on every core, and a graceful stop on SIGTERM / SIGINT
import signal
serve = build(os.path.join(HERE, 'net', 'http_serve.vu'))
for sig, name in [(signal.SIGTERM, 'SIGTERM'), (signal.SIGINT, 'SIGINT')]:
    srv = Server(serve, 5)
    p = srv.port
    raw, closed = exchange(p, get(b'/') * 3, wait=0.5)
    check(f'serve: three pipelined requests answered by the handler ({name} run)',
          [x[2] for x in responses(raw)] == [b'hello from serve'] * 3 and not closed, raw)
    idle = srv.conn()
    idle.sendall(get(b'/'))
    first = idle.recv(1000)
    slow = srv.conn()
    slow.sendall(get(b'/slow'))
    time.sleep(0.3)
    t0 = time.time()
    srv.p.send_signal(sig)
    slow.settimeout(10)
    got = recv_exactly(slow, len(b'HTTP/1.1 200 OK'))
    rest = slow.recv(1000)
    check(f'serve: a request in progress when {name} came still gets its answer',
          got == b'HTTP/1.1 200 OK' and rest.endswith(b'slow done'), got + rest)
    idle.settimeout(5)
    check(f'serve: an idle keep-alive connection is closed after {name}', first.startswith(b'HTTP/1.1 200')
          and idle.recv(1000) == b"" and time.time() - t0 < 8, time.time() - t0)
    code, out, err = srv.finish(timeout=10)
    check(f'serve: returns once its connections are done, after {name} (exit 0, "stopped")',
          code == 0 and out.strip() == "stopped" and time.time() - t0 < 8, (code, out, err, time.time() - t0))
    refused = False
    try:
        socket.create_connection(('127.0.0.1', p), timeout=1).close()
    except OSError:
        refused = True
    check(f'serve: no longer accepting after {name}', refused)
# a request that never finishes doesn't hold the stop up past the grace period
srv = Server(serve, 1)
stuck = srv.conn()
stuck.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n')   # no blank line: the request never ends
time.sleep(0.3)
t0 = time.time()
srv.p.send_signal(signal.SIGTERM)
code, out, err = srv.finish(timeout=10)
check('serve: a request that never finishes is given up after the grace period (1 s)',
      code == 0 and out.strip() == "stopped" and 0.8 < time.time() - t0 < 8, (code, out, err, time.time() - t0))

print(f"{counts['passed']} passed, {counts['failed']} failed")
sys.exit(1 if counts['failed'] else 0)
