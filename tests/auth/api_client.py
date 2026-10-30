# For run_auth.sh: drives the app `vu new api` makes (compiler/rt/new_api/main.vu) over HTTP, as a
# browser (cookies) and as an API client (Bearer tokens), and checks every answer.
import http.client, json, sys

port = int(sys.argv[1])
fails = []

def call(method, path, body=None, token=None, cookie=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    h = dict(headers or {})
    if body is not None: h["Content-Type"] = "application/json"
    if token: h["Authorization"] = "Bearer " + token
    if cookie: h["Cookie"] = cookie
    c.request(method, path, body=None if body is None else (body if isinstance(body, str) else json.dumps(body)), headers=h)
    r = c.getresponse()
    data = r.read().decode()
    try: parsed = json.loads(data) if data else None
    except ValueError: parsed = data
    out = (r.status, parsed, r.getheader("Set-Cookie"))
    c.close()
    return out

def expect(what, got, want):
    if got != want: fails.append("%s: got %r, want %r" % (what, got, want))

st, b, ck = call("POST", "/signup", {"email": " Ada@Example.com ", "password": "correct horse battery"})
expect("signup status", st, 201)
expect("signup email", b and b.get("email"), "ada@example.com")
tok = b["token"] if b else ""
ada = b["id"] if b else 0
expect("signup token length", len(tok), 43)
expect("signup cookie", bool(ck) and ck.startswith("session=" + tok) and "HttpOnly" in ck and "Secure" in ck and "SameSite=Lax" in ck, True)
expect("duplicate signup", call("POST", "/signup", {"email": "ada@example.com", "password": "another password"})[0], 409)
expect("short password", call("POST", "/signup", {"email": "bob@example.com", "password": "short"})[0], 400)
expect("bad email", call("POST", "/signup", {"email": "nobody", "password": "long enough pw"})[0], 400)
expect("bad json", call("POST", "/signup", "{nope")[0], 400)
expect("wrong password", call("POST", "/login", {"email": "ada@example.com", "password": "wrong password"})[:2], (401, {"error": "wrong email or password"}))
expect("unknown email", call("POST", "/login", {"email": "who@example.com", "password": "wrong password"})[:2], (401, {"error": "wrong email or password"}))
st, b, ck = call("POST", "/login", {"email": "ADA@example.com", "password": "correct horse battery"})
expect("login", st, 200)
tok2 = b["token"] if b else ""
expect("a new token each login", tok2 != tok and len(tok2) == 43, True)
expect("me by bearer", call("GET", "/me", token=tok)[:2], (200, {"id": ada, "email": "ada@example.com"}))
expect("me by cookie", call("GET", "/me", cookie="session=" + tok2)[:2], (200, {"id": ada, "email": "ada@example.com"}))
expect("me signed out", call("GET", "/me")[0], 401)
expect("me with a made-up token", call("GET", "/me", token="x" * 43)[0], 401)
expect("me with a bad header", call("GET", "/me", headers={"Authorization": "Basic abc"})[0], 401)
st, n1, _ = call("POST", "/notes", {"text": "first <note> \"quoted\" é"}, token=tok)
expect("add note", (st, n1 and n1.get("text")), (201, "first <note> \"quoted\" é"))
call("POST", "/notes", {"text": "second"}, token=tok)
st, lst, _ = call("GET", "/notes", token=tok)
expect("list notes", [x["text"] for x in lst or []], ["first <note> \"quoted\" é", "second"])
expect("empty note", call("POST", "/notes", {"text": ""}, token=tok)[0], 400)
expect("notes signed out", call("GET", "/notes")[0], 401)
st, b, _ = call("POST", "/signup", {"email": "eve@example.com", "password": "eve's password"})
eve = b["token"] if b else ""
expect("eve sees no notes", call("GET", "/notes", token=eve)[:2], (200, []))
expect("eve can't delete ada's note", call("DELETE", "/notes/%d" % n1["id"], token=eve)[0], 404)
expect("a note id that isn't a number", call("DELETE", "/notes/abc", token=tok)[0], 404)
expect("cross-site POST refused", call("POST", "/notes", {"text": "csrf"}, cookie="session=" + tok2, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
expect("delete note", call("DELETE", "/notes/%d" % n1["id"], token=tok)[0], 204)
expect("deleted", [x["text"] for x in call("GET", "/notes", token=tok)[1] or []], ["second"])
st, _, ck = call("POST", "/logout", token=tok)
expect("logout", st, 204)
expect("logout clears the cookie", bool(ck) and "Max-Age=0" in ck, True)
expect("token after logout", call("GET", "/me", token=tok)[0], 401)
expect("the other session still works", call("GET", "/me", cookie="session=" + tok2)[0], 200)
expect("health", call("GET", "/health")[:2], (200, {"ok": True}))
# 20 sign-ins and sign-ups a minute from one address: run_auth.sh made 1 and the checks above 9, so the
# 11th more is refused
codes = [call("POST", "/login", {"email": "x@example.com", "password": "guess %d" % i})[0] for i in range(12)]
expect("sign-ins limited", codes, [401] * 10 + [429, 429])
expect("other routes aren't", call("GET", "/me", cookie="session=" + tok2)[0], 200)
for f in fails: print("FAIL  " + f)
print("api: %d checks failed" % len(fails) if fails else "api: all checks passed")
sys.exit(1 if fails else 0)
