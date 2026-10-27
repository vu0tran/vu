"""Helpers for the network suites (run_net.py, run_tls.py): building servers with the compiler named
by VU, starting them on a free port, and counting checks."""
import os
import resource
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
work = tempfile.mkdtemp()
counts = {'passed': 0, 'failed': 0}


def check(name, ok, detail=''):
    if ok:
        counts['passed'] += 1
        print(f'ok    {name}')
    else:
        counts['failed'] += 1
        print(f'FAIL  {name}\n      {str(detail)[:600]}')


FLAGS = sys.argv[1:]     # e.g. --san


def build(src):
    exe = os.path.join(work, os.path.basename(src)[:-3])
    r = subprocess.run(VU + ['build', src, '-o', exe] + FLAGS, capture_output=True, text=True)
    if r.returncode:
        print(f'FAIL  build {src}\n{r.stdout}{r.stderr}')
        sys.exit(1)
    return exe


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Server:
    def __init__(self, exe, *args, nofile=None):
        self.port = free_port()
        limit = (lambda: resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, nofile))) if nofile else None
        self.p = subprocess.Popen([exe, str(self.port)] + [str(a) for a in args], preexec_fn=limit,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # stdout is a pipe, so the server's "ready" line arrives only at exit. A probe connection would
        # be seen by the server too, so watch the kernel's socket table for the listening socket instead.
        for _ in range(500):
            if self.listening():
                break
            time.sleep(0.01)

    def listening(self):
        with open('/proc/net/tcp') as f:
            return any(l.split()[1].endswith(f':{self.port:04X}') and l.split()[3] == '0A' for l in f.readlines()[1:])

    def conn(self):
        s = socket.create_connection(('127.0.0.1', self.port), timeout=10)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return s

    def finish(self, timeout=10):
        try:
            out, err = self.p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill()
            out, err = self.p.communicate()
            return None, out, err
        return self.p.returncode, out, err

    def kill(self):
        self.p.kill()
        return self.finish()


def recv_exactly(s, n):
    buf = b''
    while len(buf) < n:
        d = s.recv(min(1 << 20, n - len(buf)))
        if not d:
            break
        buf += d
    return buf


def recv_all(s):
    buf = b''
    while True:
        d = s.recv(1 << 20)
        if not d:
            return buf
        buf += d


def reset(s):
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    s.close()
