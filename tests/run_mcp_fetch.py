#!/usr/bin/env python3
"""The MCP fetch server (mcp/fetch) against the reference (mcp-server-fetch, Python), over stdio, on
pages served by a local HTTP server: random pages (text, JSON, HTML, in many charsets, gzip, chunked),
redirects (relative, absolute, chains past the limit, loops), robots.txt files (random rules, 401,
403, 404, 5xx, redirects), status codes, servers that hang up or stall, random arguments (valid and
not), the fetch prompt, and the private-address guard (without --allow-private-ips). Every answer is
compared as JSON, except the Markdown of an HTML page, which is this server's own: for those the
text around it must match and the words must mostly agree (reported).
  tests/run_mcp_fetch.py VU_SERVER PYTHON_WITH_MCP_SERVER_FETCH [--seed N] [--rounds N]"""
import collections, gzip, http.server, json, os, random, re, socket, socketserver, subprocess, sys, threading, time, zlib

INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}

class S:
    def __init__(self, cmd, env):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
        self.n = 0
        self.init = self.ask(INIT)
        self.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    def ask(self, m):
        self.p.stdin.write((json.dumps(m) + "\n").encode()); self.p.stdin.flush()
        l = self.p.stdout.readline()
        if not l: sys.exit("FAIL: a server closed its output")
        return json.loads(l)
    def call(self, name, args):
        self.n += 1
        return self.ask({"jsonrpc": "2.0", "id": self.n, "method": "tools/call", "params": {"name": name, "arguments": args}})
    def prompt(self, args):
        self.n += 1
        return self.ask({"jsonrpc": "2.0", "id": self.n, "method": "prompts/get", "params": {"name": "fetch", "arguments": args}})

# ---- the web: what each path answers, set by the test before each request
ROUTES = {}       # (port, path) -> spec
ROBOTS = {}       # port -> spec for /robots.txt
HITS = collections.Counter()

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_GET(self):
        port = self.server.server_address[1]
        path = self.path
        HITS[(port, path)] += 1
        spec = ROBOTS.get(port) if path == "/robots.txt" else ROUTES.get((port, path))
        if spec is None: spec = {"status": 404, "headers": [("Content-Type", "text/plain")], "body": b"not found"}
        if spec.get("hang"):
            time.sleep(spec["hang"]); return
        if spec.get("close"):
            self.close_connection = True; return
        if spec.get("short"):
            # a body cut off: fewer bytes than the Content-Length promised
            self.send_response(200); self.send_header("Content-Type", "text/plain"); self.send_header("Content-Length", "100"); self.end_headers()
            self.wfile.write(b"only ten b"); self.wfile.flush(); self.close_connection = True; return
        body = spec.get("body", b"")
        if callable(body): body = body(self)
        enc = spec.get("encoding")
        if enc == "gzip": body = gzip.compress(body)
        elif enc == "deflate": body = zlib.compress(body)
        self.send_response(spec.get("status", 200))
        for k, v in spec.get("headers", []): self.send_header(k, v)
        if enc: self.send_header("Content-Encoding", enc)
        if spec.get("chunked"):
            self.send_header("Transfer-Encoding", "chunked"); self.end_headers()
            for i in range(0, len(body), 7): self.wfile.write(b"%x\r\n%s\r\n" % (len(body[i:i + 7]), body[i:i + 7]))
            self.wfile.write(b"0\r\n\r\n")
        else:
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)

class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def serve():
    s = TS(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s.server_address[1]

def words(s): return collections.Counter(w.lower() for w in re.findall(r"\w+", s))
def f1(a, b):
    ca, cb = words(a), words(b)
    inter = sum((ca & cb).values())
    if not ca and not cb: return 1.0
    p = inter / max(1, sum(ca.values())); r = inter / max(1, sum(cb.values()))
    return 2 * p * r / (p + r) if p + r else 0.0

TEXTS = ["hello world", "caf\u00e9 cr\u00e8me", "\u20ac 5 and \u00a3 3", "\u043f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440", "\u65e5\u672c\u8a9e\u306e\u30c6\u30ad\u30b9\u30c8", "emoji \U0001F600 here", "tabs\tand\nnew\r\nlines"]
CHARSETS = [None, "utf-8", "UTF-8", "latin-1", "iso-8859-1", "windows-1252", "cp1251", "koi8-r", "ascii", "utf-16", "x-unknown", "iso-8859-15"]

def encode(text, cs):
    try: return text.encode(cs or "utf-8", errors="replace")
    except LookupError: return text.encode("utf-8")

def html_page(r):
    title = r.choice(["News", "A post", "Docs"])
    paras = "".join("<p>%s %s</p>" % (r.choice(TEXTS), " ".join(r.choice(["alpha", "beta", "<b>gamma</b>", "<a href='/x'>delta</a>", "epsilon"]) for _ in range(r.randrange(1, 30)))) for _ in range(r.randrange(1, 12)))
    nav = "<nav><a href=/>Home</a><a href=/about>About</a></nav>" if r.random() < 0.5 else ""
    return "<!doctype html><html><head><title>%s</title></head><body>%s<article><h1>%s</h1>%s</article><footer>c</footer></body></html>" % (title, nav, title, paras)

def body_spec(r):
    k = r.random()
    if k < 0.35:
        text = " ".join(r.choice(TEXTS) for _ in range(r.randrange(0, 400)))
        cs = r.choice(CHARSETS)
        ct = r.choice(["text/plain", "application/json", "text/csv", "", None, "application/octet-stream"])
        hd = []
        if ct is not None: hd.append(("Content-Type", ct + ("; charset=%s" % cs if cs and ct else "")))
        return {"status": 200, "headers": hd, "body": encode(text, cs if cs != "utf-16" else "utf-16")}, False
    if k < 0.75:
        page = html_page(r)
        cs = r.choice([None, "utf-8", "latin-1", "windows-1252"])
        meta = r.choice(["", "<meta charset=%s>" % (cs or "utf-8")])
        page = page.replace("<head>", "<head>" + meta)
        ct = r.choice(["text/html", "text/html; charset=%s" % (cs or "utf-8"), "", "application/xhtml+xml", None])
        hd = [] if ct is None else [("Content-Type", ct)]
        return {"status": 200, "headers": hd, "body": encode(page, cs)}, True
    if k < 0.85:
        st = r.choice([200, 201, 204, 300, 304, 400, 401, 403, 404, 410, 418, 429, 500, 502, 503])
        return {"status": st, "headers": [("Content-Type", "text/plain")], "body": b"status page" if st not in (204, 304) else b""}, False
    if k < 0.9:
        return {"status": 200, "headers": [("Content-Type", "text/plain")], "body": b"x" * r.randrange(0, 20000), "encoding": r.choice(["gzip", "deflate"])}, False
    if k < 0.95:
        return {"status": 200, "headers": [("Content-Type", "text/plain; charset=utf-8")], "body": ("chunked " * r.randrange(1, 300)).encode(), "chunked": True}, False
    if k < 0.97:
        return {"status": 200, "headers": [("Content-Type", "text/plain"), ("Content-Type", "text/html")], "body": b"<p>two types</p>"}, True
    return r.choice([{"close": True}, {"short": True}]), False

ROBOTS_FILES = ["User-agent: *\nDisallow: /", "User-agent: *\nDisallow: /p/\nAllow: /p/ok", "User-agent: ModelContextProtocol\nDisallow: /", "User-agent: googlebot\nDisallow: /",
                "# comment\nUser-agent: *\nDisallow: /*.json$", "User-agent: *\nAllow: /", "", "User-agent: *\nDisallow:", "garbage\x00here"]

def robots_spec(r):
    k = r.random()
    if k < 0.45: return None
    if k < 0.85: return {"status": 200, "headers": [("Content-Type", "text/plain")], "body": r.choice(ROBOTS_FILES).encode()}
    return {"status": r.choice([401, 403, 404, 410, 500, 503]), "headers": [], "body": b"no"}

def main():
    a = sys.argv[1:]
    vu, py = a[0], a[1]
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    rounds = int(a[a.index("--rounds") + 1]) if "--rounds" in a else 300
    r = random.Random(seed)
    ports = [serve() for _ in range(3)]
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    ref_cmd = [py, "-m", "mcp_server_fetch", "--allow-private-ips"]
    if "--no-readability" in a: ref_cmd.append("--no-readability-js")
    sv = S([vu, "--allow-private-ips"], env)
    sr = S(ref_cmd, env)
    n = 0
    html_scores = []
    seen = collections.Counter()
    def kind_of(y):
        if "error" in y: return "JSON-RPC error"
        res = y["result"]
        if "content" in res: t = res["content"][0]["text"]
        elif "messages" in res: t = res["messages"][0]["content"]["text"]
        else: return "list"
        t = re.sub(r"Error executing tool fetch: ", "", t)
        for key in ["validation error", "robots.txt (", "received status", "Failed to fetch robots.txt", "status code", "Refused to fetch", "Failed to fetch", "Content truncated", "No more content", "cannot be simplified", "failed to be simplified"]:
            if key in t: return key
        return "page"
    def compare(kind, args, x, y, html):
        nonlocal n
        n += 1
        x["id"] = y["id"] = 0
        seen[kind_of(y)] += 1
        if x == y: return
        if html and "result" in x and "result" in y and kind == "tool":
            tx, ty = x["result"]["content"][0]["text"], y["result"]["content"][0]["text"]
            hx, hy = tx.split("\n", 1)[0], ty.split("\n", 1)[0]
            if hx == hy and x["result"].get("isError") == y["result"].get("isError"):
                html_scores.append(f1(tx, ty)); return
        if html and kind == "prompt" and "result" in x and "result" in y:
            html_scores.append(f1(json.dumps(x), json.dumps(y))); return
        sys.exit("FAIL %s %s:\n  vu:  %s\n  ref: %s" % (kind, json.dumps(args), json.dumps(x)[:2500], json.dumps(y)[:2500]))
    for m in [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, {"jsonrpc": "2.0", "id": 1, "method": "prompts/list"},
              {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nope", "arguments": {}}},
              {"jsonrpc": "2.0", "id": 1, "method": "prompts/get", "params": {"name": "nope", "arguments": {}}},
              {"jsonrpc": "2.0", "id": 1, "method": "prompts/get", "params": {"name": "fetch", "arguments": {}}}]:
        compare("protocol", m, sv.ask(m), sr.ask(m), False)
    if sv.init != sr.init: sys.exit("FAIL initialize: %s vs %s" % (sv.init, sr.init))
    for i in range(rounds):
        ROUTES.clear(); ROBOTS.clear()
        for p in ports: ROBOTS[p] = robots_spec(r)
        port = r.choice(ports)
        path = "/p/%d%s" % (i, r.choice(["", ".json", "/ok", "?q=1"]))
        spec, html = body_spec(r)
        k = r.random()
        if k < 0.15:
            # a redirect chain, maybe to another origin, maybe past the limit, maybe a loop
            hops = r.choice([1, 2, 3, 19, 20, 21, 25])
            prev = (port, path)
            for h in range(hops):
                np = r.choice(ports) if r.random() < 0.3 else prev[0]
                npath = "/r/%d/%d" % (i, h)
                loc = r.choice(["http://127.0.0.1:%d%s" % (np, npath), npath if np == prev[0] else "http://127.0.0.1:%d%s" % (np, npath),
                                "//127.0.0.1:%d%s" % (np, npath)])
                if h == hops - 1 and r.random() < 0.15:
                    loc = r.choice(["ftp://127.0.0.1/x", "?q=2", "#frag", "", "mailto:a@b", "relative/path", "http:/same/host"])
                ROUTES[prev] = {"status": r.choice([301, 302, 303, 307, 308]), "headers": [("Location", loc)], "body": b""}
                prev = (np, npath)
            ROUTES[prev] = spec
        else:
            ROUTES[(port, path)] = spec
        url = "http://127.0.0.1:%d%s" % (port, path)
        args = {"url": url}
        for key, vals in (("max_length", [1, 10, 100, 5000, 999999, 0, -1, "5", 1.5, True]), ("start_index", [0, 1, 50, 100000, -1, None]), ("raw", [True, False, "yes", 1])):
            if r.random() < 0.3: args[key] = r.choice(vals)
        if r.random() < 0.05: args["url"] = r.choice(["", "x", "ftp://127.0.0.1/", "http://", "http://127.0.0.1:1/", 5, "file:///etc/passwd", "http://127.0.0.1:%d/robots.txt" % port])
        if r.random() < 0.03: del args["url"]
        if r.random() < 0.85:
            compare("tool", args, sv.call("fetch", args), sr.call("fetch", args), html)
        else:
            pa = {"url": url}
            compare("prompt", pa, sv.prompt(pa), sr.prompt(pa), html)
    # a robots.txt that never comes (the reference waits 5 s for it)
    ROUTES.clear(); ROBOTS.clear()
    ROBOTS[ports[0]] = {"hang": 6}
    args = {"url": "http://127.0.0.1:%d/slow" % ports[0]}
    compare("tool", args, sv.call("fetch", args), sr.call("fetch", args), False)
    sv.p.stdin.close(); sr.p.stdin.close()
    # the guard: without --allow-private-ips every local address is refused, on every hop
    gv, gr = S([vu], env), S([py, "-m", "mcp_server_fetch"], env)
    ROUTES.clear(); ROBOTS.clear()
    p0 = ports[0]
    for u in ["http://127.0.0.1:%d/x" % p0, "http://localhost:%d/x" % p0, "http://[::1]:%d/x" % p0, "http://0x7f.1:%d/x" % p0, "http://2130706433/",
              "http://10.0.0.1/", "http://169.254.169.254/latest/meta-data/", "http://[::ffff:127.0.0.1]/", "http://[fd00::1]/", "http://no-such-host.invalid/"]:
        for args in ({"url": u}, {"url": u, "raw": True}):
            compare("guard", args, gv.call("fetch", args), gr.call("fetch", args), False)
        compare("guard-prompt", {"url": u}, gv.prompt({"url": u}), gr.prompt({"url": u}), False)
    gv.p.stdin.close(); gr.p.stdin.close()
    hs = sorted(html_scores)
    med = hs[len(hs) // 2] if hs else 1.0
    if hs and med < 0.8: sys.exit("FAIL: the Markdown of HTML pages agrees too little with the reference's (median word F1 %.2f)" % med)
    print("  answers by kind: " + ", ".join("%s %d" % kv for kv in sorted(seen.items(), key=lambda kv: -kv[1])))
    print("run_mcp_fetch: %d answers the same as the reference server (seed %d); %d HTML pages as Markdown, median word F1 %.2f, lowest %.2f"
          % (n - len(hs), seed, len(hs), med, hs[0] if hs else 1.0))

main()
