# For run_saas.sh: runs examples/saas (arg 1: the binary; arg 2: DATABASE_URL) against a fake Stripe,
# a fake Resend and moto's S3, and checks a customer's whole path: sign up, the welcome email, paying,
# webhooks (forged, replayed, real), the plan, cancelling, and an avatar uploaded with a presigned URL.
import hashlib, hmac, http.client, http.server, json, os, random, socket, subprocess, sys, threading, time, urllib.parse, urllib.request
import boto3

def free():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

def wait(port):
    for _ in range(300):
        try: socket.create_connection(("127.0.0.1", port), 0.2).close(); return
        except OSError: time.sleep(0.1)
    raise SystemExit("nothing listening on %d" % port)

stripe_reqs, mails = [], []
class Fake(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
        if self.path.startswith("/v1/checkout/sessions"):
            stripe_reqs.append((self.headers.get("Authorization"), dict(urllib.parse.parse_qsl(body))))
            data = json.dumps({"id": "cs_test_9", "url": "https://checkout.stripe.com/c/pay/cs_test_9"})
        elif self.path == "/emails":
            mails.append((self.headers.get("Authorization"), json.loads(body)))
            data = json.dumps({"id": "mail_1"})
        else:
            self.send_response(404); self.end_headers(); return
        b = data.encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
fake = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=fake.serve_forever, daemon=True).start()
fport = fake.server_address[1]

mport = free()
moto = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(mport)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
aport = free()
app = None
fails = []
def expect(what, got, want):
    if got != want: fails.append("%s: got %r, want %r" % (what, got, want))
try:
    wait(mport)
    s3 = boto3.client("s3", endpoint_url="http://127.0.0.1:%d" % mport, region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="y")
    s3.create_bucket(Bucket="avatars")
    secret = "whsec_test_secret"
    env = dict(os.environ, PORT=str(aport), DATABASE_URL=sys.argv[2], APP_URL="https://app.example", STRIPE_SECRET_KEY="sk_test_9",
               STRIPE_WEBHOOK_SECRET=secret, STRIPE_PRICE="price_pro", STRIPE_API_BASE="http://127.0.0.1:%d" % fport,
               RESEND_API_KEY="re_9", RESEND_API_BASE="http://127.0.0.1:%d" % fport, MAIL_FROM="App <hello@app.example>",
               S3_ENDPOINT="http://127.0.0.1:%d" % mport, S3_REGION="us-east-1", S3_BUCKET="avatars", S3_KEY_ID="x", S3_SECRET="y")
    app = subprocess.Popen([sys.argv[1]], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wait(aport)

    def call(method, path, body=None, token=None, headers=None, raw=None):
        c = http.client.HTTPConnection("127.0.0.1", aport, timeout=20)
        h = dict(headers or {})
        if token: h["Authorization"] = "Bearer " + token
        data = raw if raw is not None else (None if body is None else json.dumps(body))
        c.request(method, path, body=data, headers=h)
        r = c.getresponse(); d = r.read().decode(); c.close()
        try: d = json.loads(d) if d else None
        except ValueError: pass
        return r.status, d, dict(r.getheaders())

    def hook(event, t=None, key=secret):
        payload = json.dumps(event)
        t = int(time.time()) if t is None else t
        sig = hmac.new(key.encode(), ("%d.%s" % (t, payload)).encode(), hashlib.sha256).hexdigest()
        return call("POST", "/billing/webhook", raw=payload, headers={"Stripe-Signature": "t=%d,v1=%s" % (t, sig), "Content-Type": "application/json"})[0]

    st, b, _ = call("POST", "/signup", {"email": "ada@example.com", "password": "correct horse battery"})
    expect("signup", (st, b and b.get("plan")), (201, "free"))
    ada, uid = b["token"], b["id"]
    for _ in range(100):
        if mails: break
        time.sleep(0.05)
    expect("welcome email", [(a, m["to"], m["subject"], m["from"]) for a, m in mails], [("Bearer re_9", ["ada@example.com"], "Welcome", '"App" <hello@app.example>')])
    expect("welcome email links the app", bool(mails) and "https://app.example" in mails[0][1]["text"] and 'href="https://app.example"' in mails[0][1]["html"], True)
    expect("me", call("GET", "/me", token=ada)[:2], (200, {"id": uid, "email": "ada@example.com", "plan": "free", "avatar": False}))
    st, b, _ = call("POST", "/billing/checkout", token=ada)
    expect("checkout", (st, b), (200, {"url": "https://checkout.stripe.com/c/pay/cs_test_9"}))
    expect("what Stripe got", stripe_reqs, [("Bearer sk_test_9", {"mode": "subscription", "line_items[0][price]": "price_pro", "line_items[0][quantity]": "1",
        "success_url": "https://app.example/?paid={CHECKOUT_SESSION_ID}", "cancel_url": "https://app.example/", "client_reference_id": str(uid), "customer_email": "ada@example.com"})])
    expect("checkout signed out", call("POST", "/billing/checkout")[0], 401)
    done = {"id": "evt_1", "type": "checkout.session.completed", "created": 1, "data": {"object": {"id": "cs_test_9", "client_reference_id": str(uid), "customer": "cus_ada"}}}
    expect("forged webhook", hook(done, key="whsec_guess"), 400)
    expect("replayed webhook (an hour old)", hook(done, t=int(time.time()) - 3600), 400)
    expect("no signature", call("POST", "/billing/webhook", raw=json.dumps(done))[0], 400)
    expect("still free", call("GET", "/me", token=ada)[1]["plan"], "free")
    expect("real webhook", hook(done), 200)
    expect("now pro", call("GET", "/me", token=ada)[1]["plan"], "pro")
    expect("checkout when pro", call("POST", "/billing/checkout", token=ada)[0], 409)
    expect("an event it doesn't use", hook({"id": "evt_2", "type": "invoice.paid", "data": {"object": {}}}), 200)
    expect("pro after logging in again", call("POST", "/login", {"email": "ada@example.com", "password": "correct horse battery"})[1]["plan"], "pro")
    expect("cancelled", hook({"id": "evt_3", "type": "customer.subscription.deleted", "data": {"object": {"customer": "cus_ada"}}}), 200)
    expect("free again", call("GET", "/me", token=ada)[1]["plan"], "free")
    expect("no avatar yet", call("GET", "/avatar", token=ada)[0], 404)
    st, b, _ = call("POST", "/avatar", token=ada)
    expect("upload url", st, 200)
    up = b["upload"]
    expect("upload url is presigned for this bucket and user", up.startswith("http://127.0.0.1:%d/avatars/avatars/%s/" % (mport, uid)) and "X-Amz-Signature=" in up, True)
    png = bytes(random.randrange(256) for _ in range(2000))
    urllib.request.urlopen(urllib.request.Request(up, data=png, method="PUT", headers={"Content-Type": "image/png"})).read()
    st, _, h = call("GET", "/avatar", token=ada)
    expect("avatar redirect", st, 302)
    expect("avatar bytes", urllib.request.urlopen(h["Location"]).read() if st == 302 else None, png)
    expect("me shows an avatar", call("GET", "/me", token=ada)[1]["avatar"], True)
    eve = call("POST", "/signup", {"email": "eve@example.com", "password": "eve's long password"})[1]["token"]
    expect("eve has no avatar", call("GET", "/avatar", token=eve)[0], 404)
    expect("eve isn't pro from ada's webhook", call("GET", "/me", token=eve)[1]["plan"], "free")
    expect("cross-site checkout refused", call("POST", "/billing/checkout", token=ada, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
finally:
    if app:
        app.terminate()
        try: _, err = app.communicate(timeout=10)
        except subprocess.TimeoutExpired: app.kill(); _, err = app.communicate()
        bad = [l for l in err.decode(errors="replace").split("\n") if "ERROR" in l or "runtime error" in l or "LeakSanitizer" in l]
        if bad: fails.append("the app's stderr: %s" % bad[:5])
    moto.kill()
    fake.shutdown()
for f in fails: print("FAIL  " + f)
print("saas: %s" % ("all checks passed" if not fails else "%d checks failed" % len(fails)))
sys.exit(1 if fails else 0)
