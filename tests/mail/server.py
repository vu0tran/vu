# For run_mail.sh: SMTP servers (aiosmtpd) with STARTTLS and sign-in, with TLS from the start, and a
# plain local relay; a fake Resend API; then runs main.vu (arg 1) and checks what each received,
# reading the messages with Python's email package.
import email, email.policy, http.server, json, os, ssl, subprocess, sys, tempfile, threading
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, LoginPassword

work = tempfile.mkdtemp()
def openssl(*a): subprocess.run(["openssl", *a], check=True, capture_output=True, cwd=work)
openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "30", "-subj", "/CN=Test CA")
openssl("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "server.key", "-out", "server.csr", "-subj", "/CN=localhost")
open(os.path.join(work, "ext"), "w").write("subjectAltName=DNS:localhost,IP:127.0.0.1\n")
openssl("x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial", "-out", "server.pem", "-days", "30", "-extfile", "ext")
ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ctx.load_cert_chain(os.path.join(work, "server.pem"), os.path.join(work, "server.key"))

got = {}
class Handler:
    def __init__(self, name): self.name = name
    async def handle_DATA(self, server, session, envelope):
        got.setdefault(self.name, []).append((envelope.mail_from, list(envelope.rcpt_tos), envelope.original_content, session.authenticated if hasattr(session, "authenticated") else None))
        return "250 OK"

def auth(server, session, envelope, mechanism, auth_data):
    if isinstance(auth_data, LoginPassword) and auth_data.login == b"app" and auth_data.password == b"s3cret pw":
        return AuthResult(success=True)
    return AuthResult(success=False, handled=False)

import socket
def free():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
starttls = Controller(Handler("starttls"), hostname="127.0.0.1", port=free(), tls_context=ctx, require_starttls=True, authenticator=auth, auth_required=True)
implicit = Controller(Handler("implicit"), hostname="127.0.0.1", port=free(), ssl_context=ctx, authenticator=auth, auth_required=True, auth_require_tls=False, server_hostname="localhost")   # (aiosmtpd hides AUTH on a connection that was TLS from the start unless told it may show it)
plain = Controller(Handler("plain"), hostname="0.0.0.0", port=free(), auth_require_tls=False)
for c in (starttls, implicit, plain): c.start()

resend = []
class R(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers["Authorization"] != "Bearer re_123":
            data, st = b'{"statusCode": 401, "message": "API key is invalid", "name": "validation_error"}', 401
        else:
            resend.append((self.path, self.headers["Content-Type"], json.loads(body)))
            data, st = b'{"id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"}', 200
        self.send_response(st); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
rs = http.server.ThreadingHTTPServer(("127.0.0.1", 0), R)
threading.Thread(target=rs.serve_forever, daemon=True).start()

# a server that sends a reply right after its 220 to STARTTLS, before the handshake: a man in the
# middle's way to get a command into the encrypted session (CVE-2011-0411 and its kin)
hs = socket.socket(); hs.bind(("127.0.0.1", 0)); hs.listen(1)
def hostile():
    c, _ = hs.accept()
    f = c.makefile("rb")
    c.sendall(b"220 hi\r\n")
    f.readline(); c.sendall(b"250-localhost\r\n250 STARTTLS\r\n")
    f.readline(); c.sendall(b"220 go ahead\r\n250 injected\r\n")
    try: c.recv(100)
    except OSError: pass
    c.close()
threading.Thread(target=hostile, daemon=True).start()

def port(c): return c.port
r = subprocess.run([sys.argv[1], str(port(starttls)), str(port(implicit)), str(port(plain)), str(rs.server_address[1]), os.path.join(work, "ca.pem"), str(hs.getsockname()[1])], capture_output=True, text=True, timeout=120)
for c in (starttls, implicit, plain): c.stop()
rs.shutdown()

bad = []
want_out = ["starttls sent", "implicit sent",
            "wrong password error: mail: the server answered 535 to AUTH: 5.7.8 Authentication credentials invalid",
            "local relay sent",
            "no starttls error: mail: 127.0.0.2 doesn't offer STARTTLS, so this won't send the message (or a password) in the clear",
            "injected subject error: mail: a subject can't contain a line break",
            "injected address error: mail: an address can't contain a line break or a zero byte",
            "bad address error: mail: 'not an address' isn't an email address",
            "resend 49a3999c-0ce1-4ea6-ab68-afcd6dc2e794",
            "resend bad key error: mail: Resend: API key is invalid",
            "hostile error: mail: the server sent data before the TLS handshake"]
out = r.stdout.split("\n")[:-1]
if r.returncode != 0: bad.append("exit %d: %s" % (r.returncode, r.stderr[-400:]))
for i, w in enumerate(want_out):
    g = out[i] if i < len(out) else None
    # (if the injected reply arrives in a packet of its own, the handshake fails on it instead)
    if w.startswith("hostile") and g and g.startswith("hostile error: mail: ") and "tls" in g.lower(): continue
    if g != w: bad.append("line %d: got %r, want %r" % (i, g, w))

def check_msg(n, raw, frm, rcpts):
    if frm != "ada@example.com": bad.append("%d: MAIL FROM %r" % (n, frm))
    if sorted(rcpts) != ["bob@example.org", "carol@example.net", "secret@example.com"]: bad.append("%d: RCPT TO %r" % (n, rcpts))
    m = email.message_from_bytes(raw, policy=email.policy.default)
    want_subject = "Grüße %d — a long subject that goes on with ünïcödé 中文 😀 so it wraps" % n
    checks = [("From", str(m["From"]), "Ädä Lövelace <ada@example.com>"), ("To", str(m["To"]), '"Bob, Jr." <bob@example.org>'),
              ("Cc", str(m["Cc"]), "carol@example.net"), ("Reply-To", str(m["Reply-To"]), "support <help@example.com>"),
              ("Subject", str(m["Subject"]), want_subject), ("Bcc", m["Bcc"], None)]
    for name, g, w in checks:
        if g != w: bad.append("%d: %s %r, want %r" % (n, name, g, w))
    if m["Message-ID"] is None or not str(m["Message-ID"]).endswith("@example.com>") or m["Date"] is None: bad.append("%d: Message-ID or Date" % n)
    text = ".starts with a dot\r\n.\r\nline after a lone dot\nnon-ASCII: é中😀\n"
    body = m.get_body(("plain",))
    if body is None or body.get_payload(decode=True).decode() != text: bad.append("%d: text body %r" % (n, body and body.get_payload(decode=True)))
    if n % 2 == 0:
        h = m.get_body(("html",))
        if h is None or h.get_payload(decode=True).decode() != "<p>Hello <b>%d</b> é</p>" % n: bad.append("%d: html body" % n)
    if any(len(line) > 998 for line in raw.split(b"\r\n")): bad.append("%d: a line over 998 bytes" % n)

for name, n in [("starttls", 1), ("implicit", 2), ("plain", 4)]:
    msgs = got.get(name, [])
    if len(msgs) != 1: bad.append("%s server got %d messages" % (name, len(msgs))); continue
    frm, rcpts, raw, _ = msgs[0]
    check_msg(n, raw, frm, rcpts)
if sum(len(v) for v in got.values()) != 3: bad.append("messages delivered: %r" % {k: len(v) for k, v in got.items()})
if len(resend) != 1: bad.append("Resend got %d requests" % len(resend))
else:
    path, ctype, body = resend[0]
    want = {"from": '"Ädä Lövelace" <ada@example.com>', "to": ['"Bob, Jr." <bob@example.org>'], "subject": "Grüße 10 — a long subject that goes on with ünïcödé 中文 😀 so it wraps",
            "text": ".starts with a dot\r\n.\r\nline after a lone dot\nnon-ASCII: é中😀\n", "html": "<p>Hello <b>10</b> é</p>", "cc": ["carol@example.net"],
            "bcc": ["secret@example.com"], "reply_to": '"support" <help@example.com>'}
    if path != "/emails" or ctype != "application/json" or body != want: bad.append("Resend request %r %r %r" % (path, ctype, body))
for b in bad: print("FAIL  " + b)
print("mail: %s" % ("STARTTLS, TLS, a local relay and Resend as expected, and every refusal" if not bad else "%d problems" % len(bad)))
sys.exit(1 if bad else 0)
