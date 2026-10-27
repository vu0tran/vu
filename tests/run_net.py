"""The network capability: real servers (tests/net/*.vu and bench/http/server.vu) driven by Python
clients over TCP. Runs against the compiler named by VU (default: ../vu, the compiler)."""
import os
import socket
import struct
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import *  # noqa: E402,F401,F403
from nettest import counts  # noqa: E402

echo = build(f'{HERE}/net/echo.vu')

# ---- many clients at once, each gets its own bytes back
srv = Server(echo)
socks = [srv.conn() for _ in range(3000)]
for i, s in enumerate(socks):
    s.sendall(f'hello {i}'.encode())
got = [recv_exactly(s, len(f'hello {i}')) for i, s in enumerate(socks)]
check('echo: 3000 connections each get their own bytes', all(g == f'hello {i}'.encode() for i, g in enumerate(got)),
      got[:3])
for s in socks:
    s.close()
time.sleep(0.3)
s = srv.conn()
s.sendall(b'STOP')
rc, out, err = srv.finish()
check('echo: closes are seen (recv returns ""), then the server stops', rc == 0 and out.count('closed') == 3000 and 'stopping' in out,
      (rc, out[-200:], err))

# ---- large transfers: recv/send in pieces
srv = Server(echo)
s = srv.conn()
blob = os.urandom(3 << 20)
t = threading.Thread(target=s.sendall, args=(blob,))
t.start()
back = recv_exactly(s, len(blob))
t.join()
check('echo: 3 MB in and out arrives intact', back == blob, len(back))
# a client that resets the connection doesn't disturb the others
r = srv.conn()
r.sendall(b'x')
recv_exactly(r, 1)
reset(r)
s.sendall(b'still here')
check('echo: a reset connection is closed, others keep working', recv_exactly(s, 10) == b'still here')
s.close()
time.sleep(0.2)
s = srv.conn()
s.sendall(b'STOP')
rc, out, err = srv.finish()
check('echo: the reset was reported as a close', rc == 0 and out.count('closed') == 2 and 'stopping' in out, (rc, out, err))

# ---- out of file descriptors: the server keeps serving, doesn't spin, and accepts again after closes
srv = Server(echo, nofile=40)
socks = [srv.conn() for _ in range(60)]
for s in socks:
    s.settimeout(3)


def served(group, msg):
    n = 0
    for s in group:
        try:
            s.sendall(msg)
            n += recv_exactly(s, len(msg)) == msg
        except OSError:
            pass
    return n


first = served(socks[:20], b'x')
stat = lambda: sum(int(x) for x in open(f'/proc/{srv.p.pid}/stat').read().rsplit(')', 1)[1].split()[11:13])
t0 = stat()
time.sleep(1)
spin = stat() - t0
for s in socks[:20]:
    s.close()
time.sleep(0.3)
late = served(socks[40:], b'y')
srv.kill()
check('fd limit: connections are served, no busy loop, accepting resumes after closes',
      first == 20 and spin < 20 and late >= 10, (first, spin, late))
for s in socks:
    s.close()

# ---- a slow reader receives a large reply in full (send waits while the connection is full)
big = build(f'{HERE}/net/big.vu')
for as_bytes in (0, 1):
    srv = Server(big, 8 << 20, as_bytes)
    s = srv.conn()
    s.sendall(b'go')
    time.sleep(0.5)
    data = recv_all(s)
    want = (b'abcdefghijklmnopqrstuvwxyz' * ((8 << 20) // 26 + 1))[:8 << 20]
    rc, out, err = srv.finish()
    check(f'big: 8 MB to a slow reader ({"[Byte]" if as_bytes else "Str"})', data == want and 'sent true' in out,
          (len(data), out, err))

# ---- sending to a client that left returns false instead of killing the program
srv = Server(build(f'{HERE}/net/broken.vu'))
s = srv.conn()
s.sendall(b'x')
time.sleep(0.2)
reset(s)
rc, out, err = srv.finish(timeout=20)
check('broken: send fails once the client is gone (no SIGPIPE)',
      rc == 0 and 'send failed after the client left: the connection is closed' in out, (rc, out, err))

# ---- a port in use is an error the program sees
busy = build(f'{HERE}/net/busy.vu')
port = free_port()
r = subprocess.run([busy, str(port)], capture_output=True, text=True, timeout=10)
check('busy: listening on a taken port fails with the reason',
      r.returncode == 0 and r.stdout.strip() == f"can't listen on port {port}: Address already in use", r.stdout)

# ---- send evaluates its arguments left to right
srv = Server(build(f'{HERE}/net/order.vu'))
s = srv.conn()
s.sendall(b'x')
reply = recv_exactly(s, 2)
rc, out, err = srv.finish()
check('order: send(c, body(), timeout: secs()) runs body, then secs', out == 'ready\nb\nt\ndone\n' and reply == b'hi', (out, err))

# ---- timeouts: a silent client, and nobody else connecting
srv = Server(build(f'{HERE}/net/timeouts.vu'))
s = srv.conn()
rc, out, err = srv.finish()
check('timeouts: recv and accept give up after their timeout', rc == 0 and 'recv: timed out' in out
      and 'accept: timed out' in out, (rc, out, err))
s.close()

# ---- connecting out: a name, a closed port, a name that doesn't exist
lsock = socket.socket()
lsock.bind(('127.0.0.1', 0))
lsock.listen(1)


def pong():
    c, _ = lsock.accept()
    c.recv(10)
    c.sendall(b'pong')
    c.close()


th = threading.Thread(target=pong)
th.start()
closed_port = free_port()
r = subprocess.run([build(f'{HERE}/net/client.vu'), str(lsock.getsockname()[1]), str(closed_port)],
                   capture_output=True, text=True, timeout=60)
th.join()
lsock.close()
check('client: connect by name, round trip, a refused port, an unknown name',
      r.returncode == 0 and 'reply pong' in r.stdout and 'closed port: can\'t connect to 127.0.0.1:' in r.stdout
      and 'Connection refused' in r.stdout and 'bad name: true' in r.stdout, r.stdout + r.stderr)

# ---- the HTTP benchmark server
http = build(f'{HERE}/../bench/http/server.vu')
REQ = b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n'
RESP = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nHello, World!'
srv = Server(http)
s = srv.conn()
s.sendall(REQ)
check('http: one request, one response', recv_exactly(s, len(RESP)) == RESP)
s.sendall(REQ * 3)
check('http: three pipelined requests, three responses in order', recv_exactly(s, 3 * len(RESP)) == RESP * 3)
for b in REQ:
    s.sendall(bytes([b]))
    time.sleep(0.002)
check('http: a request sent one byte at a time', recv_exactly(s, len(RESP)) == RESP)
s.sendall(REQ + REQ[:10])
time.sleep(0.05)
s.sendall(REQ[10:] + REQ)
check('http: requests split across reads', recv_exactly(s, 3 * len(RESP)) == RESP * 3)
s.close()
s = srv.conn()
s.sendall(REQ)
s.shutdown(socket.SHUT_WR)              # half-close: the reply must still arrive, then the server closes
check('http: a client that half-closes still gets its reply', recv_all(s) == RESP)
s.close()
r = subprocess.run([sys.executable, f'{HERE}/../bench/http/check.py', str(srv.port)], capture_output=True, text=True)
check('http: POST /order answers exactly as the reference (bench/http/check.py)', r.stdout.strip() == 'ok', r.stdout + r.stderr)
ORDER = open(f'{HERE}/../bench/http/order.json', 'rb').read()
WANT = open(f'{HERE}/../bench/http/expected.json', 'rb').read()
post = b'POST /order HTTP/1.1\r\ncOnTeNt-LeNgTh:  %d \r\n\r\n' % len(ORDER) + ORDER
s = srv.conn()
for i in range(0, len(post), 997):
    s.sendall(post[i:i + 997])
    time.sleep(0.001)
head = recv_exactly(s, 200)
check('http: a POST in many pieces, header name in mixed case', head.startswith(b'HTTP/1.1 200 OK') and
      head.endswith(WANT[:200 - head.index(b'\r\n\r\n') - 4]), head)
s.close()
s = srv.conn()
s.sendall(b'POST /order HTTP/1.1\r\nContent-Length: 12x\r\n\r\n')
check('http: a malformed Content-Length gets 400 and the connection closes', recv_all(s).startswith(b'HTTP/1.1 400'))
s.close()
s = srv.conn()
s.sendall(b'POST /order HTTP/1.1\r\nContent-Length: 99999999\r\n\r\n')
check('http: a body over 1 MB is refused', recv_all(s).startswith(b'HTTP/1.1 400'))
s.close()
s = srv.conn()
s.sendall(b'POST /order HTTP/1.1\r\nContent-Length: 2\r\n\r\n[]' + REQ)
got = b''
while RESP not in got:
    d = s.recv(65536)
    if not d:
        break
    got += d
check('http: a JSON error (400) then the next pipelined request', got.startswith(b'HTTP/1.1 400') and RESP in got, got)
s.close()
results = []


def client():
    c = srv.conn()
    n = 0
    for _ in range(100):
        c.sendall(REQ)
        if recv_exactly(c, len(RESP)) == RESP:
            n += 1
    c.close()
    results.append(n)


ts = [threading.Thread(target=client) for _ in range(50)]
for t in ts:
    t.start()
for t in ts:
    t.join()
check('http: 50 keep-alive clients x 100 requests', sum(results) == 5000, sum(results))
rc, out, err = srv.kill()
check('http: no errors on stderr', err == '', err)

print(f"{counts['passed']} passed, {counts['failed']} failed")
sys.exit(1 if counts['failed'] else 0)
