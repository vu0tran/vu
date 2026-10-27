"""Checks that a running benchmark server gives the right answers before it is measured:
   python3 check.py PORT
GET / must say "Hello, World!", POST /order must reply with exactly expected.json, and a broken
order must get status 400. Requests go over one keep-alive connection, partly pipelined."""
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
port = int(sys.argv[1])
body = open(os.path.join(HERE, 'order.json'), 'rb').read()
want = open(os.path.join(HERE, 'expected.json'), 'rb').read()


def post(b):
    return b'POST /order HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n' % len(b) + b


def read_response(s, buf):
    while b'\r\n\r\n' not in buf:
        d = s.recv(65536)
        if not d:
            raise SystemExit('connection closed early')
        buf += d
    head, rest = buf.split(b'\r\n\r\n', 1)
    n = 0
    for line in head.split(b'\r\n')[1:]:
        k, _, v = line.partition(b':')
        if k.strip().lower() == b'content-length':
            n = int(v)
    while len(rest) < n:
        rest += s.recv(65536)
    return int(head.split()[1]), rest[:n], rest[n:]


s = socket.create_connection(('127.0.0.1', port), timeout=10)
problems = []
s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
st, b, buf = read_response(s, b'')
if (st, b) != (200, b'Hello, World!'):
    problems.append(f'GET /: {st} {b[:80]!r}')
s.sendall(post(body) + post(body) + post(b'{"id": "x", "items": [1'))   # pipelined
for i in range(2):
    st, b, buf = read_response(s, buf)
    if (st, b) != (200, want):
        problems.append(f'POST /order #{i + 1}: {st} {b[:200]!r}')
st, b, buf = read_response(s, buf)
if st != 400:
    problems.append(f'broken order: status {st}, want 400')
half = post(body)
s.sendall(half[:100])
s.sendall(half[100:])
st, b, buf = read_response(s, buf)
if (st, b) != (200, want):
    problems.append(f'POST /order sent in two pieces: {st} {b[:200]!r}')
print('\n'.join(problems) if problems else 'ok')
sys.exit(1 if problems else 0)
