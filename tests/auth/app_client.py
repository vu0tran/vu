# For run_auth.sh: drives the app `vu new app` makes as a browser would: cookies, forms with CSRF
# tokens read from the pages, redirects; and as an attacker would: forms without tokens or with
# another user's, markup in notes, another user's notes, cross-site posts.
import http.client, re, sys, urllib.parse

port = int(sys.argv[1])
fails = []
def expect(what, got, want):
    if got != want: fails.append("%s: got %r, want %r" % (what, got, want))

class Browser:
    def __init__(self): self.jar = {}
    def req(self, method, path, form=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
        h = dict(headers or {})
        if self.jar: h["Cookie"] = "; ".join("%s=%s" % kv for kv in self.jar.items())
        body = None
        if form is not None:
            body = urllib.parse.urlencode(form); h["Content-Type"] = "application/x-www-form-urlencoded"
        c.request(method, path, body=body, headers=h)
        r = c.getresponse(); data = r.read().decode(); c.close()
        for k, v in r.getheaders():
            if k.lower() == "set-cookie":
                name, _, rest = v.partition("=")
                val = rest.split(";")[0]
                if "Max-Age=0" in v: self.jar.pop(name, None)
                else: self.jar[name] = val
        return r.status, data, r.getheader("Location")
    def csrf(self, html):
        m = re.search(r'name="csrf_token" value="([0-9a-f]+)"', html)
        return m.group(1) if m else ""

ada = Browser()
expect("home signed out", ada.req("GET", "/")[0::2], (303, "/login"))
st, page, _ = ada.req("GET", "/signup")
expect("signup page", (st, "<form" in page, "pre" in ada.jar), (200, True, True))
tok = ada.csrf(page)
expect("a CSRF token in the form", len(tok), 64)
expect("signup without the token", ada.req("POST", "/signup", {"email": "ada@example.com", "password": "correct horse battery"})[0], 403)
expect("signup with another token", ada.req("POST", "/signup", {"email": "ada@example.com", "password": "correct horse battery", "csrf_token": "0" * 64})[0], 403)
st, page, loc = ada.req("POST", "/signup", {"email": "ada@example.com", "password": "short", "csrf_token": tok})
expect("short password", (st, "A password has 10 to 1000 characters." in page, 'value="ada@example.com"' in page), (400, True, True))
st, page, loc = ada.req("POST", "/signup", {"email": "Ada@Example.com", "password": "correct horse battery", "csrf_token": tok})
expect("signed up", (st, loc, "session" in ada.jar, "pre" in ada.jar), (303, "/", True, False))
st, page, _ = ada.req("GET", "/")
expect("notes page", (st, "Your notes" in page, "ada@example.com" in page), (200, True, True))
stok = ada.csrf(page)
expect("note with markup", ada.req("POST", "/notes", {"text": "<script>alert('x')</script> & more", "csrf_token": stok})[0::2], (303, "/"))
page = ada.req("GET", "/")[1]
expect("markup escaped", ("&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt; &amp; more" in page, "<script>" in page), (True, False))
expect("note without the token", ada.req("POST", "/notes", {"text": "forged"})[0], 403)
expect("note with the sign-up token", ada.req("POST", "/notes", {"text": "forged", "csrf_token": tok})[0], 403)
expect("cross-site post", ada.req("POST", "/notes", {"text": "x", "csrf_token": stok}, {"Sec-Fetch-Site": "cross-site"})[0], 403)
ids = re.findall(r'action="/notes/(\d+)/delete"', page)
expect("one note", len(ids), 1)
eve = Browser()
etok = eve.csrf(eve.req("GET", "/signup")[1])
eve.req("POST", "/signup", {"email": "eve@example.com", "password": "eve's long password", "csrf_token": etok})
epage = eve.req("GET", "/")[1]
expect("eve sees no notes", ("alert" in epage, "ada@example.com" in epage), (False, False))
eve.req("POST", "/notes/%s/delete" % ids[0], {"csrf_token": eve.csrf(epage)})
expect("eve can't delete ada's note", "alert" in ada.req("GET", "/")[1], True)
ada.req("POST", "/notes/%s/delete" % ids[0], {"csrf_token": stok})
expect("ada deletes it", "alert" in ada.req("GET", "/")[1], False)
expect("sign out", ada.req("POST", "/logout", {"csrf_token": stok})[0::2], (303, "/login"))
expect("signed out", ("session" in ada.jar, ada.req("GET", "/")[0]), (False, 303))
ltok = ada.csrf(ada.req("GET", "/login")[1])
st, page, _ = ada.req("POST", "/login", {"email": "ada@example.com", "password": "wrong password", "csrf_token": ltok})
expect("wrong password", (st, "Wrong email or password." in page), (401, True))
st, page, _ = ada.req("POST", "/login", {"email": "nobody@example.com", "password": "wrong password", "csrf_token": ltok})
expect("unknown email", (st, "Wrong email or password." in page), (401, True))
expect("signed in", ada.req("POST", "/login", {"email": "ADA@example.com", "password": "correct horse battery", "csrf_token": ltok})[0::2], (303, "/"))
expect("signed in again", "Your notes" in ada.req("GET", "/")[1], True)
expect("stylesheet", ada.req("GET", "/static/style.css")[0], 200)
expect("health", ada.req("GET", "/health")[0], 200)
for f in fails: print("FAIL  " + f)
print("app: all checks passed" if not fails else "app: %d checks failed" % len(fails))
sys.exit(1 if fails else 0)
