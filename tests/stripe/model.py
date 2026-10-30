# For run_stripe.sh.
#   serve PORTFILE LOG: a fake Stripe API on a free port (written to PORTFILE), logging each request.
#   cases FILE SEED: webhook cases, with what each must give in FILE.want (from Stripe's own Python
#     library when it's installed, else from the same rules written here).
#   check FILE LOG: reads main.vu's output on stdin and checks it, and the logged requests.
import hashlib, hmac, json, random, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def sign(secret, payload, t):
    return hmac.new(secret.encode(), ("%d." % t).encode() + payload, hashlib.sha256).hexdigest()

if sys.argv[1] == "serve":
    log = open(sys.argv[3], "w")
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def answer(self, status, body):
            data = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def handle_any(self, method):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n).decode() if n else ""
            log.write(json.dumps({"method": method, "path": self.path, "body": body, "headers": {k.lower(): v for k, v in self.headers.items()}}) + "\n")
            log.flush()
            p = urllib.parse.urlsplit(self.path).path
            if self.headers.get("Authorization") != "Bearer sk_test_123":
                return self.answer(401, json.dumps({"error": {"message": "Invalid API Key provided", "type": "invalid_request_error"}}))
            if p == "/v1/checkout/sessions": return self.answer(200, json.dumps({"id": "cs_test_1", "object": "checkout.session", "url": "https://checkout.stripe.com/c/pay/cs_test_1"}))
            if p == "/v1/customers": return self.answer(200, json.dumps({"object": "list", "data": [], "has_more": False}))
            if p == "/v1/payment_intents": return self.answer(402, json.dumps({"error": {"message": "Your card was declined.", "code": "card_declined", "type": "card_error"}}))
            if p == "/v1/notjson": return self.answer(500, "<html>oops</html>")
            return self.answer(404, json.dumps({"error": {"message": "Unrecognized request URL"}}))
        def do_GET(self): self.handle_any("GET")
        def do_POST(self): self.handle_any("POST")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    open(sys.argv[2], "w").write(str(srv.server_address[1]))
    srv.serve_forever()

elif sys.argv[1] == "cases":
    rng = random.Random(int(sys.argv[3]))
    try:
        import stripe
        from stripe import WebhookSignature
    except ImportError:
        WebhookSignature = None
    out, want = [], []
    now = 1761000000
    def case(secret, payload, header, at):
        out.append("%s\t%s\t%s\t%d" % (secret, payload.hex(), header, at))
        # Stripe's library: the signature, and a timestamp no older than the tolerance (300 s)
        ok = True
        if WebhookSignature is not None:
            real = time.time
            time.time = lambda: at
            try: WebhookSignature.verify_header(payload.decode("utf-8", "replace"), header, secret, 300)
            except Exception: ok = False
            finally: time.time = real
        else:
            try:
                items = [i.split("=", 2) for i in header.split(",")]
                t = int([i[1] for i in items if i[0] == "t"][0])
                sigs = [i[1] for i in items if i[0] == "v1"]
                ok = any(hmac.compare_digest(sign(secret, payload, t), s) for s in sigs) and t >= at - 300
            except Exception: ok = False
        # and Vu's rules on top: a timestamp more than 300 s in the future is refused too, and the
        # body must be a JSON event with an id and a type
        if ok:
            t = int([i.split("=", 1)[1] for i in header.split(",") if i.startswith("t=")][0])
            if t > at + 300: ok = False
        ev = None
        if ok:
            try:
                ev = json.loads(payload)
                if not isinstance(ev, dict) or not isinstance(ev.get("id"), str) or not isinstance(ev.get("type"), str): ok = False
            except Exception: ok = False
        if ok:
            obj = ev.get("data", {}).get("object") if isinstance(ev.get("data"), dict) else None
            created = ev.get("created") if isinstance(ev.get("created"), int) else 0
            live = ev.get("livemode") if isinstance(ev.get("livemode"), bool) else False
            want.append("ok %s %s %d %s %s" % (ev["id"], ev["type"], created, "true" if live else "false",
                        "null" if obj is None else json.dumps(obj, separators=(",", ":"), ensure_ascii=False)))
        else:
            want.append("err")
    for k in range(80):
        secret = "whsec_" + "".join(rng.choice("abcdefABCDEF0123456789") for _ in range(32))
        ev = {"id": "evt_%d" % k, "object": "event", "type": rng.choice(["checkout.session.completed", "invoice.paid", "customer.subscription.deleted"]),
              "created": now - rng.randint(0, 1000), "livemode": rng.random() < 0.3,
              "data": {"object": {"id": "cs_%d" % k, "amount_total": rng.randint(0, 10**6), "metadata": {"note": rng.choice(["", "é中😀", "a\"b\\c", "<x>"])}}}}
        payload = json.dumps(ev, separators=(",", ":"), ensure_ascii=False).encode()
        t = now - rng.choice([0, 5, 299, 300, 301, 1000, -299, -301, -5000])
        sig = sign(secret, payload, t)
        kind = k % 10
        if kind == 0: header = "t=%d,v1=%s" % (t, sig)
        elif kind == 1: header = "t=%d,v1=%s,v1=%s" % (t, "0" * 64, sig)                # rotated secrets: one matches
        elif kind == 2: header = "t=%d,v1=%s" % (t, sign(secret + "x", payload, t))      # another secret
        elif kind == 3: header = "t=%d,v1=%s" % (t, sig); payload = payload[:-1] + b" }" # body changed after signing
        elif kind == 4: header = "t=%d,v1=%s" % (t + 1, sig)                             # timestamp changed
        elif kind == 5: header = "t=%d,v0=%s" % (t, sig)                                 # another scheme only
        elif kind == 6: header = "v1=%s" % sig                                           # no timestamp
        elif kind == 7: header = "t=%d,v1=%s" % (t, sig.upper())                         # hex case changed
        elif kind == 8: header = "t=%d,v1=%s,v0=abc" % (t, sig)
        else: header = "t=%d,v1=%s" % (t, sig[:-1])                                      # one hex digit short
        case(secret, payload, header, now)
    s = "whsec_fixed"
    for payload in [b"", b"not json", b"[1,2]", b'{"type":"x"}', b'{"id":"evt","type":"t","data":{}}', b'{"id":"evt","type":"t","created":"soon"}']:
        case(s, payload, "t=%d,v1=%s" % (now, sign(s, payload, now)), now)
    open(sys.argv[2], "w").write("\n".join(out) + "\n")
    open(sys.argv[2] + ".want", "w").write("\n".join(want) + "\n")
    print("webhooks: %s" % ("expected results from Stripe's library" if WebhookSignature else "Stripe's library not installed: the same rules written here"))

else:
    got = sys.stdin.read().split("\n")
    want_hooks = open(sys.argv[2] + ".want").read().split("\n")[:-1]
    bad = []
    fixed = ["checkout cs_test_1 https://checkout.stripe.com/c/pay/cs_test_1",
             'customers {"object":"list","data":[],"has_more":false}',
             "intent error: stripe: Your card was declined. (card_declined)",
             "notjson error: stripe: HTTP 500 with a body that isn't JSON",
             "evil error: stripe: 'https://evil.example/v1/x' isn't an API path (/v1/...)",
             "dots error: stripe: '/v1/../admin' isn't an API path (/v1/...)",
             "zero error: stripe: a quantity of at least 1",
             "nokey error: stripe: no secret key (set STRIPE_SECRET_KEY)"]
    if got[:8] != fixed: bad.append("calls: got %r" % got[:8])
    hooks = got[8:8 + len(want_hooks)]
    for i, (g, w) in enumerate(zip(hooks, want_hooks)):
        if g != w: bad.append("webhook case %d: got %r, want %r" % (i, g, w))
    if len(hooks) != len(want_hooks): bad.append("%d webhook results, want %d" % (len(hooks), len(want_hooks)))
    if got[8 + len(want_hooks)] != "sign t=1700000000,v1=" + sign("whsec_x", b"{}", 1700000000): bad.append("sign_payload: %r" % got[8 + len(want_hooks)])
    reqs = [json.loads(l) for l in open(sys.argv[3])]
    if len(reqs) != 4: bad.append("%d requests reached the server, want 4 (the refused ones mustn't)" % len(reqs))
    else:
        r = reqs[0]
        fields = urllib.parse.parse_qsl(r["body"], keep_blank_values=True, strict_parsing=True)
        wantf = [("mode", "payment"), ("line_items[0][price]", "price_1"), ("line_items[0][quantity]", "2"),
                 ("success_url", "https://shop.example/thanks?id={CHECKOUT_SESSION_ID}&x=1 2"), ("cancel_url", "https://shop.example/cart"),
                 ("client_reference_id", "user 42/é"), ("customer_email", "ada+test@example.com")]
        if r["method"] != "POST" or r["path"] != "/v1/checkout/sessions" or fields != wantf: bad.append("checkout request: %r" % r)
        if r["headers"].get("content-type") != "application/x-www-form-urlencoded" or r["headers"].get("stripe-version") != "2024-06-20": bad.append("checkout headers: %r" % r["headers"])
        q = urllib.parse.urlsplit(reqs[1]["path"])
        if reqs[1]["method"] != "GET" or q.path != "/v1/customers" or urllib.parse.parse_qsl(q.query, strict_parsing=True) != [("limit", "3"), ("email", "a&b=c@example.com")] or reqs[1]["body"] != "":
            bad.append("customers request: %r" % reqs[1])
        if reqs[2]["headers"].get("idempotency-key") != "order-7" or "idempotency-key" in reqs[0]["headers"]: bad.append("idempotency keys: %r %r" % (reqs[2]["headers"], reqs[0]["headers"]))
    for b in bad: print("FAIL  " + b)
    print("%d webhook cases, %d calls checked" % (len(want_hooks), len(fixed)))
    sys.exit(1 if bad else 0)
