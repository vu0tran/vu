"""The standard library's web module (std/web.vu).
1. tests/web/unit.vu against a Python model, on random routes and paths, form bodies, cookie values
   and text to escape (urllib.parse and html are the models).
2. tests/web/app.vu, a small app, against raw HTTP requests: routing, 404 and 405, middleware, forms,
   cookies (signed ones tampered with), redirects that try to leave the site, cross-site posts, static
   files with every way out of the folder we could think of, ETags, and escaping in templates.
Runs against the compiler named by VU (default: ../vu); extra arguments (--san) go to the build."""
import os
import random
import socket
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nettest import build, Server, check, counts  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, 'web')
rng = random.Random(int(os.environ.get('SEED', '7')))


def esc_bytes(b):
    return ''.join(chr(c) if 32 <= c < 127 and c != 0x5c else '\\x%02x' % c for c in b)


def show(b):
    return esc_bytes(b)


# ---- 1. the pure parts against a model

def model_route(pat, path):
    segs = pat[1:].split('/')
    if not path.startswith(b'/'):
        return None
    parts = path[1:].split(b'/')
    ps = {}
    for i, s in enumerate(segs):
        if s.startswith('*'):
            if i >= len(parts):
                return None
            ps[s[1:]] = urllib.parse.unquote_to_bytes(b'/'.join(parts[i:]))
            return ps
        if i >= len(parts):
            return None
        if s.startswith(':'):
            if parts[i] == b'':
                return None
            ps[s[1:]] = urllib.parse.unquote_to_bytes(parts[i])
        elif s.encode() != parts[i]:
            return None
    if len(parts) != len(segs):
        return None
    return ps


def model_form(body):
    out = {}
    for part in body.split(b'&'):
        if part == b'':
            continue
        k, eq, v = part.partition(b'=')
        k = urllib.parse.unquote_to_bytes(k.replace(b'+', b' '))
        v = urllib.parse.unquote_to_bytes(v.replace(b'+', b' '))
        if k not in out:
            out[k] = v
    return ';'.join(show(k) + '=' + show(v) for k, v in out.items())


def model_esc(b):
    return (b.replace(b'&', b'&amp;').replace(b'<', b'&lt;').replace(b'>', b'&gt;')
            .replace(b'"', b'&quot;').replace(b"'", b'&#39;'))


def cookie_octet(c):
    return c == 0x21 or 0x23 <= c <= 0x2B or 0x2D <= c <= 0x3A or 0x3C <= c <= 0x5B or 0x5D <= c <= 0x7E


def model_cookie(v):
    enc = ''.join(chr(c) if cookie_octet(c) and c != 0x25 else '%%%02X' % c for c in v)
    return show(b'c=' + enc.encode() + b'; Path=/; HttpOnly; Secure; SameSite=Lax') + ' | ' + show(v)


ALPHA = [b'a', b'b', b'x', b'%', b'%2F', b'%2f', b'%41', b'%zz', b'%4', b'+', b'/', b'.', b'..', b'\xc3\xa9', b'\x00',
         b'=', b'&', b';', b' ', b'"', b'<', b'>', b"'", b'\\', b'%00', b'%25', b'\r\n', b'\x7f', b'\xff']


def rand_bytes(n):
    return b''.join(rng.choice(ALPHA) for _ in range(rng.randint(0, n)))


def wire(b):
    """Bytes as unit.vu reads them: \\xHH for anything not printable ASCII, and for '\\'."""
    return esc_bytes(b)


cases, want = [], []
LIT = ['a', 'b', 'users', 'x.y', '']
for _ in range(3000):
    n = rng.randint(1, 4)
    segs, names = [], []
    for i in range(n):
        r = rng.random()
        if r < 0.45:
            segs.append(rng.choice(LIT[:-1]))
        elif r < 0.85 or i < n - 1:
            nm = rng.choice(['id', 'name', 'p2', '_x'])
            if nm in names:
                nm += str(i)
            names.append(nm)
            segs.append(':' + nm)
        else:
            segs.append('*rest')
    pat = '/' + '/'.join(segs)
    # paths: often built from the pattern, so they match
    parts = []
    for s in segs:
        if s.startswith(':') or s.startswith('*'):
            parts.append(rand_bytes(3).replace(b'/', b'') if rng.random() < 0.8 else b'')
        else:
            parts.append(s.encode())
    if rng.random() < 0.3:
        parts.append(rand_bytes(2))
    if rng.random() < 0.2 and parts:
        parts.pop()
    path = b'/' + b'/'.join(parts)
    cases.append('R ' + pat + '\t' + wire(path))
    m = model_route(pat, path)
    want.append('NOMATCH' if m is None else '&'.join(k + '=' + show(m[k]) for k in sorted(m)))
for _ in range(2000):
    body = b'&'.join(rand_bytes(3) + (b'=' + rand_bytes(4) if rng.random() < 0.8 else b'') for _ in range(rng.randint(0, 4)))
    cases.append('F ' + wire(body))
    want.append(model_form(body))
for _ in range(1000):
    t = rand_bytes(8)
    cases.append('E ' + wire(t))
    want.append(show(model_esc(t)))
for _ in range(1000):
    v = rand_bytes(8)
    cases.append('C ' + wire(v))
    want.append(model_cookie(v))
for _ in range(500):
    v = rand_bytes(8)
    cases.append('T x\t' + wire(v))
    e = model_esc(v)
    want.append(show(b'<p title="' + e + b'">' + e + b'</p>'))

unit = build(os.path.join(WEB, 'unit.vu'))
r = subprocess.run([unit], input='\n'.join(cases) + '\n', capture_output=True, text=True, errors='replace')
got = r.stdout.split('\n')[:-1]
bad = [(c, w, g) for c, w, g in zip(cases, want, got) if w != g]
check(f'unit: {len(cases)} random cases (routes, forms, escaping, cookies, templates) match the model',
      r.returncode == 0 and len(got) == len(cases) and not bad, (r.returncode, r.stderr[-300:], len(got), bad[:3]))

# ---- 2. the app over HTTP

app = build(os.path.join(WEB, 'app.vu'))
os.chdir(WEB)


def exchange(port, data, head=False):
    s = socket.create_connection(('127.0.0.1', port), timeout=10)
    s.sendall(data)
    out = b''
    s.settimeout(3)
    try:
        while True:
            d = s.recv(1 << 20)
            if not d:
                break
            out += d
            if parse(out, head) is not None:
                break
    except socket.timeout:
        pass
    s.close()
    return out


def parse(raw, is_head=False):
    head, sep, rest = raw.partition(b'\r\n\r\n')
    if not sep:
        return None
    lines = head.split(b'\r\n')
    status = int(lines[0].split()[1])
    hs = []
    for l in lines[1:]:
        k, _, v = l.partition(b':')
        hs.append((k.strip().lower().decode(), v.strip().decode('latin-1')))
    n = 0 if is_head else int(dict(hs).get('content-length', '0'))
    if len(rest) < n:
        return None
    return status, hs, rest[:n]


def req(method, path, headers=(), body=b''):
    h = b''.join(k.encode() + b': ' + v.encode('latin-1') + b'\r\n' for k, v in headers)
    if body or method in ('POST', 'PUT'):
        h += b'Content-Length: %d\r\n' % len(body)
    raw = exchange(srv.port, method.encode() + b' ' + path + b' HTTP/1.1\r\nHost: app.test\r\nConnection: close\r\n' + h + b'\r\n' + body, method == 'HEAD')
    r = parse(raw, method == 'HEAD')
    if r is None:
        return 0, {}, raw
    status, hs, b = r
    d = {}
    for k, v in hs:
        d.setdefault(k, []).append(v)
    return status, d, b


def hdr(d, k):
    return d.get(k, [''])[0]


srv = Server(app)
try:
    s, h, b = req('GET', b'/')
    check('GET / with no cookie', (s, b) == (200, b'<h1>Hello, stranger</h1>')
          and hdr(h, 'content-type') == 'text/html; charset=utf-8' and hdr(h, 'x-content-type-options') == 'nosniff'
          and hdr(h, 'x-frame-options') == 'DENY', (s, h, b))
    s, h, b = req('GET', b'/', [('Cookie', 'name=%3Cscript%3Ealert(1)%3C%2Fscript%3E')])
    check('a cookie value is escaped in the page', b == b'<h1>Hello, &lt;script&gt;alert(1)&lt;/script&gt;</h1>', b)
    s, h, b = req('GET', b'/users/%22%3E%3Cimg%20src=x%20onerror=alert(1)%3E')
    check('a route parameter is escaped, in an attribute and in text; markup from render and join is not',
          b == b'<p data-id="&quot;&gt;&lt;img src=x onerror=alert(1)&gt;">&quot;&gt;&lt;img src=x onerror=alert(1)&gt; by -</p>'
               b'<ul><li>&lt;b&gt;</li><li>a&amp;b</li></ul><style>p { color: red }</style>', b)
    s, h, b = req('GET', b'/users/')
    check('/users/ (an empty :id) is 404', s == 404, (s, b))
    s, h, b = req('GET', b'/users/1/2')
    check('/users/1/2 (one part too many) is 404', s == 404, (s, b))
    s, h, b = req('GET', b'/files/a/b%2Fc/%2e%2e')
    check('*rest takes the rest of the path, decoded', (s, b) == (200, b'a/b/c/..'), (s, b))
    s, h, b = req('DELETE', b'/users/7')
    check('DELETE on a GET/PUT route is 405 with Allow', s == 405 and hdr(h, 'allow') == 'GET, HEAD, PUT', (s, h))
    s, h, b = req('PUT', b'/users/7', [('Sec-Fetch-Site', 'same-origin')])
    check('PUT /users/7 from the same origin', (s, b) == (200, b'put 7'), (s, b))
    s, h, b = req('HEAD', b'/users/7')
    check('HEAD runs the GET route, without the body', s == 200 and b == b'' and int(hdr(h, 'content-length')) > 0, (s, h, b))
    s, h, b = req('GET', b'/nope')
    check('an unknown path is 404', s == 404, s)
    s, h, b = req('GET', b'*')
    check('a target that isn\'t a path is 404 (or refused)', s in (400, 404), (s, b))

    # forms, cookies and redirects
    form = urllib.parse.urlencode({'name': 'ada lovelace;=%', 'next': '/me'}).encode()
    s, h, b = req('POST', b'/login', [('Content-Type', 'application/x-www-form-urlencoded'), ('Sec-Fetch-Site', 'same-origin')], form)
    cookies = h.get('set-cookie', [])
    check('POST /login: 303 to /me, two cookies with safe defaults', s == 303 and hdr(h, 'location') == '/me'
          and len(cookies) == 2 and all('HttpOnly' in c and 'Secure' in c and 'SameSite=Lax' in c and 'Path=/' in c for c in cookies)
          and cookies[0].startswith('name=ada%20lovelace%3B=%25;'), (s, h))
    sid = cookies[1].split(';')[0] if len(cookies) == 2 else 'sid=x'
    s, h, b = req('GET', b'/me', [('Cookie', sid)])
    check('the signed cookie signs you in', (s, b) == (200, b'you are ada lovelace;=%'), (s, b, sid))
    name, _, val = sid.partition('=')
    tampered = urllib.parse.unquote(val).replace('ada', 'eve', 1)
    s, h, b = req('GET', b'/me', [('Cookie', 'sid=' + urllib.parse.quote(tampered, safe=''))])
    check('a signed cookie with its value changed is ignored', s == 401, (s, b))
    for bad in ['', '.', 'ada', 'ada.', '.' + urllib.parse.unquote(val).rpartition('.')[2], urllib.parse.unquote(val)[:-1],
                urllib.parse.unquote(val) + 'A']:
        s, h, b = req('GET', b'/me', [('Cookie', 'sid=' + urllib.parse.quote(bad, safe=''))])
        if s != 401:
            break
    check('signatures that are missing, empty, truncated or extended are refused', s == 401, (bad, s, b))
    for nxt, where in [('//evil.example', '/'), ('https://evil.example', '/'), ('/\\evil.example', '/'),
                       ('/ok\r\nSet-Cookie: x=1', '/'), ('/fine?a=1', '/fine?a=1'), ('', '/'), ('evil', '/')]:
        f = urllib.parse.urlencode({'name': 'x', 'next': nxt}).encode()
        s, h, b = req('POST', b'/login', [('Content-Type', 'application/x-www-form-urlencoded')], f)
        if not (s == 303 and hdr(h, 'location') == where and len(h.get('set-cookie', [])) == 2):
            break
    check('redirects stay on the site (//host, scheme, backslash, a line break)', s == 303 and hdr(h, 'location') == where,
          (nxt, s, h))

    # cross-site requests
    f = urllib.parse.urlencode({'name': 'x'}).encode()
    ct = ('Content-Type', 'application/x-www-form-urlencoded')
    s, h, b = req('POST', b'/login', [ct, ('Sec-Fetch-Site', 'cross-site')], f)
    check('a cross-site POST (Sec-Fetch-Site) is refused with 403', s == 403 and 'set-cookie' not in h, (s, h))
    s, h, b = req('POST', b'/login', [ct, ('Sec-Fetch-Site', 'same-site')], f)
    check('a same-site but cross-origin POST is refused too', s == 403, s)
    s, h, b = req('POST', b'/login', [ct, ('Origin', 'https://evil.example')], f)
    check('a POST with another Origin (no Sec-Fetch-Site) is refused', s == 403, s)
    s, h, b = req('POST', b'/login', [ct, ('Origin', 'https://app.test')], f)
    check('a POST whose Origin is the host is let through', s == 303, s)
    s, h, b = req('GET', b'/', [('Sec-Fetch-Site', 'cross-site')])
    check('a cross-site GET is let through (links must work)', s == 200, s)

    # static files
    s, h, b = req('GET', b'/static/app.css')
    etag = hdr(h, 'etag')
    check('a static file, with its type, an ETag and nosniff', (s, b) == (200, b'body{color:red}\n')
          and hdr(h, 'content-type') == 'text/css; charset=utf-8' and len(etag) == 34 and hdr(h, 'x-content-type-options') == 'nosniff', (s, h))
    s, h, b = req('GET', b'/static/app.css', [('If-None-Match', etag)])
    check('If-None-Match with the ETag: 304, no body', s == 304 and b == b'', (s, h, b))
    s, h, b = req('GET', b'/static/a.png')
    check('a PNG is image/png', s == 200 and hdr(h, 'content-type') == 'image/png' and b == b'\x89PNG', (s, h))
    s, h, b = req('GET', b'/static/')
    check('a folder gives its index.html', (s, b) == (200, b'<h1>index</h1>\n'), (s, b))
    s, h, b = req('GET', b'/static/sub/')
    check('a subfolder gives its index.html', (s, b) == (200, b'<h1>sub</h1>\n'), (s, b))
    escapes = [b'/static/.env', b'/static/%2eenv', b'/static/../secret.txt', b'/static/%2e%2e/secret.txt',
               b'/static/%2E%2E%2Fsecret.txt', b'/static/sub/..%2F..%2Fsecret.txt', b'/static/..%5csecret.txt',
               b'/static/sub/%2e%2e/%2e%2e/secret.txt', b'/static//etc/passwd', b'/static/%2Fetc%2Fpasswd',
               b'/static/app.css%00.png', b'/static/sub', b'/static/nope.css', b'/static/./app.css',
               b'/static/sub/../app.css', b'/static/' + b'a/' * 300 + b'x']
    leaked = []
    for p in escapes:
        s, h, b = req('GET', p)
        if s != 404 or b'SECRET' in b or b'root:' in b:
            leaked.append((p, s, b[:60]))
    check(f'{len(escapes)} attempts to leave the folder, read a hidden file or a folder are all 404', not leaked, leaked)
    # random paths made of the pieces that escape folders, against a model of what may be served
    PIECES = [b'..', b'.', b'%2e%2e', b'%2E%2e', b'%2e', b'sub', b'app.css', b'index.html', b'.env', b'%2eenv', b'',
              b'%2f', b'%2F', b'%5c', b'\\', b'%00', b'secret.txt', b'a.png', b'%61pp.css', b'sub%2findex.html']
    files = {}
    for root, dirs, fs_ in os.walk('public'):
        for f in fs_:
            full = os.path.join(root, f)
            files[os.path.relpath(full, 'public')] = open(full, 'rb').read()
    def model_static(p):
        name = urllib.parse.unquote_to_bytes(p)
        if name == b'' or name.endswith(b'/'):
            name += b'index.html'
        parts = name.split(b'/')
        if any(x == b'' or x.startswith(b'.') for x in parts) or b'\0' in name or b'\\' in name:
            return None
        return files.get(name.decode('latin-1'))
    wrong = []
    for _ in range(400):
        p = b'/'.join(rng.choice(PIECES) for _ in range(rng.randint(1, 4)))
        s, h, b = req('GET', b'/static/' + p)
        want = model_static(p)
        if (want is None and s != 404) or (want is not None and (s, b) != (200, want)):
            wrong.append((p, s, b[:40], want))
    check('400 random paths under /static: served exactly when the model says the file is inside and not hidden', not wrong, wrong[:5])
    # many clients at once, each checking it got its own answer (the app is shared by every thread)
    import threading
    bad = []
    def client(k):
        for i in range(40):
            ident = '%d-%d' % (k, i)
            s, h, b = req('GET', b'/users/' + ident.encode(), [('Cookie', sid)])
            if s != 200 or (b'>' + ident.encode() + b' by ada lovelace;=%</p>') not in b:
                bad.append((ident, s, b[:80]))
    ts = [threading.Thread(target=client, args=(k,)) for k in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    check('8 clients at once, 320 requests: each gets its own parameter and user', not bad, bad[:3])
finally:
    srv.p.terminate()   # SIGTERM: web.serve stops and returns
code, out, err = srv.finish(timeout=15)
check('SIGTERM stops the app (exit 0)', code == 0, (code, err[-300:]))
check('the logger wrote a line per request', 'GET /static/app.css 200' in err and 'POST /login 403' in err, err[-500:])

# ---- 3. the starter that `vu new web` writes, built and run as its README says
from nettest import VU, work, free_port  # noqa: E402
import time
r = subprocess.run(VU + ['new', 'web', 'starter'], cwd=work, capture_output=True, text=True)
sdir = os.path.join(work, 'starter')
b = subprocess.run(VU + ['build', 'main.vu', '-o', 'app'] + sys.argv[1:], cwd=sdir, capture_output=True, text=True)
check('vu new web: the starter builds', r.returncode == 0 and b.returncode == 0, r.stderr + b.stderr)
if b.returncode == 0:
    port = free_port()
    sp = subprocess.Popen(['./app'], cwd=sdir, env={**os.environ, 'PORT': str(port)}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    class P:
        pass
    srv = P(); srv.port = port
    for _ in range(500):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.01)
    s1, h1, b1 = req('GET', b'/')
    s2, h2, b2 = req('POST', b'/hello', [('Content-Type', 'application/x-www-form-urlencoded'), ('Sec-Fetch-Site', 'same-origin')], b'name=Ada+%3Cb%3E')
    s3, h3, b3 = req('GET', hdr(h2, 'location').encode() or b'/x', [('Cookie', (h2.get('set-cookie', ['x=y'])[0]).split(';')[0])])
    s4, h4, b4 = req('GET', b'/', [('Cookie', (h2.get('set-cookie', ['x=y'])[0]).split(';')[0])])
    s5, h5, b5 = req('GET', b'/health')
    s6, h6, b6 = req('GET', b'/static/style.css')
    s7, h7, b7 = req('POST', b'/hello', [('Content-Type', 'application/x-www-form-urlencoded'), ('Origin', 'https://evil.example')], b'name=x')
    sp.terminate()
    out, err = sp.communicate(timeout=15)
    check('starter: home, a form post (303 and a cookie), the page it leads to (escaped), the cookie remembered, '
          'health, CSS, and a cross-site post refused; SIGTERM stops it',
          s1 == 200 and b'<h1>Hello.</h1>' in b1 and s2 == 303 and hdr(h2, 'location') == '/hello/Ada%20%3Cb%3E'
          and s3 == 200 and b'Hello, Ada &lt;b&gt;!' in b3 and b'Welcome back, Ada &lt;b&gt;.' in b4
          and (s5, b5) == (200, b'{"ok": true}') and s6 == 200 and hdr(h6, 'content-type').startswith('text/css')
          and s7 == 403 and sp.returncode == 0,
          (s1, s2, h2, s3, b3[-120:], b4[-200:], s5, b5, s6, s7, sp.returncode, err[-300:]))

print(f"{counts['passed']} passed, {counts['failed']} failed")
sys.exit(1 if counts['failed'] else 0)
