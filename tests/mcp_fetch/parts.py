#!/usr/bin/env python3
"""The parts of the MCP fetch server (mcp/fetch) that answer exactly as the reference's libraries do,
each driven by a small Vu program (tests/mcp_fetch/*_driver.vu) on generated inputs and compared:
  url      whatwg.vu    against pydantic's AnyUrl (the Rust url crate), parsing and rewriting URLs
  robots   robots.vu    against Protego 0.7, allowing or refusing URLs
  guard    guard.vu     against the reference's _is_public_address
  tok      htmltok.vu   against Python's html.parser, splitting HTML into tags and text
  charset  charset.vu   against the reference's decode_page (httpx's response.text and <meta> sniffing)
  tests/mcp_fetch/parts.py PART DRIVER [--seed N] [--n N]     (run with the Python that has mcp-server-fetch)"""
import codecs, collections, ipaddress, json, random, subprocess, sys

def run(driver, lines):
    return subprocess.run([driver], input="".join(l + "\n" for l in lines), capture_output=True, text=True).stdout

# ---- url
SCHEMES = ["http", "https", "HTTP", "Https", "ftp", "ws", "wss", "file", "foo", "mailto", "data", "javascript", "a+b.c-d", "1x", ""]
HOSTS = ["a", "A.COM", "example.com", "ex-ample.org", "127.0.0.1", "0x7f.1", "0177.0.0.1", "2130706433", "127.1", "1.2.3.256",
         "999999999999", "1.2.3.4.5", "[::1]", "[::ffff:1.2.3.4]", "[1:2:3:4:5:6:7:8]", "[1::]", "[::]", "[1:0:0:2:0:0:0:3]", "[fe80::1%25eth0]",
         "[::1", "[1:2:3:4:5:6:7:8:9]", "[1:::2]", "[::1.2.3]", "ä.com", "Straße.de", "ÄÖÜ.de", "xn--nxa", "xn--a", "xn--", "a..b", "...",
         "", "localhost", "a_b", "-a-", "a%41b", "a%20b", "a%zz", "1.2.3.4.", "1.2.3.4..", ".1", "0x", "0X10", "08", "09.1", "0x1g",
         "ﬀ.com", "ＡＢＣ.com", "a。b", "日本.jp", "ελλάδα.gr", "россия.рф", "a‍b", "́a", "a­b", "1.0x", "1.", "a.1", "1.a",
         "u:p@h", "u@h", "@h", "u:p@", "a@b@c", "u:@h", "user name@h", "h:80", "h:443", "h:0", "h:65535", "h:65536", "h:x", "h:", "h:08"]
PATHS = ["", "/", "/a/b", "/a/../b", "/a/./b", "/..", "/../a", "/a/%2e%2E/b", "/a/.%2e", "/a/%2e", "/ä", "/a b", "/a\"<>`{}|^'",
         "\\a\\b", "//a", "/a//b", "/%zz", "/%41", "/a?b", "/;x", "/a/..", "/a/.", "/.a", "/..a", "/a\tb", "/a\nb", "/\x01\x7f"]
QUERIES = ["", "?", "?a=1", "?a b", "?a\"<>`{}|^'", "?ä", "?#", "?a?b", "?%zz"]
FRAGS = ["", "#", "#f", "#f g", "#a\"<>`{}|^'", "#ä", "##"]
def one(r):
    k = r.random()
    if k < 0.03: return r.choice(["x", "", " ", "/a", "//h/a", "?q", "#f", ":", "a:", "http:", "http:/", "http:a", "http:\\\\h\\x", "file:etc", "file:/etc", "file:///etc/passwd", "file://localhost/x", "file://h/x", "mailto:x@y", "data:text/plain,hi", "foo://", "foo:///x", "foo://h", "foo:/x", "foo:x y"])
    s = r.choice(SCHEMES)
    sep = r.choice(["://", "://", "://", ":/", ":", ":\\\\", ":///", "://\\"])
    h = r.choice(HOSTS)
    if r.random() < 0.1: h = "".join(r.choice("aZ09.-_~!$&'()*+,;=%:@[]") for _ in range(r.randrange(1, 6)))
    u = s + sep + h + r.choice(PATHS) + r.choice(QUERIES) + r.choice(FRAGS)
    if r.random() < 0.05: u = " \t" + u + "\n "
    return u

def part_url(driver, r, n):
    from pydantic import TypeAdapter, AnyUrl, ValidationError
    ta = TypeAdapter(AnyUrl)
    def ref(u):
        try: return str(ta.validate_python(u))
        except ValidationError as e: return "!! " + e.errors()[0]["msg"].replace("Input should be a valid URL, ", "")
    cases = [one(r) for _ in range(n)]
    out = run(driver, [json.dumps(c) for c in cases]).splitlines()
    return [(c, json.loads(o), ref(c)) for c, o in zip(cases, out)], len(out)

# ---- robots
UA = "ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)"
AGENTS = ["*", "ModelContextProtocol", "modelcontextprotocol", "MODELCONTEXTPROTOCOL/1.0", "autonomous", "Autonomous;", "github.com",
          "servers", "protocol", "context", "model*", "*context*", "googlebot", "", "modelcontextprotocol/1.0 (autonomous", "+https", "1.0", "ü"]
FIELDS = ["User-agent", "user-agent", "USER-AGENT", "useragent", "User agent", "Allow", "allow", "Disallow", "disallow", "dissallow", "Disalow",
          "Sitemap", "Host", "Crawl-delay", "Request-rate", "Visit-time", "Foo", "Noindex", "user  agent"]
PATS = ["/", "", "/a", "/a/", "/a/b", "/*", "/*.html", "/*.html$", "/a$", "/$", "*", "/a*b", "/a**b", "/a*b$", "/%61", "/%2F", "/%2f", "/a%20b",
        "/a b", "/ä", "/%C3%A4", "/%zz", "/%", "/index.html", "/a/index.html", "/a/index.html$", "http://h/a", "https://h/b", "/?", "/?q",
        "/a?b=1", "/a;b", "/=", "/%3D", "/$x", "/a$b$", "/*$", "/a/*/c", "/~u", "/A", "/%FF", "/%E2%82"]
URLS = ["http://h/", "http://h/a", "http://h/a/", "http://h/a/b", "http://h/ab", "http://h/x.html", "http://h/a.html?x", "http://h/a?b=1",
        "http://h/a%20b", "http://h/%C3%A4", "http://h/%61", "http://h/A", "http://h/index.html", "http://h/a/index.html", "http://h/robots.txt",
        "http://h/robots.txt?x", "http://h/a/robots.txt", "http://h/robots.txt;p", "http://h/a;b", "http://h/=", "http://h/%3D", "http://h/a$b",
        "http://h/a/x/c", "http://h/~u", "http://h/%7Eu", "http://h/a%2Fb", "http://h/a%2fb", "http://h/?", "http://h/?q", "http://h/%FF",
        "http://h//a", "http://h/a#f", "http://h/%zz", "https://h:8080/a/b?c=d"]
def robots(r):
    lines = []
    if r.random() < 0.7: lines.append("User-agent: " + r.choice(["*", "*", "ModelContextProtocol", "modelcontextprotocol/1.0", "Autonomous"]))
    for _ in range(r.randrange(0, 14)):
        k = r.random()
        if k < 0.08:
            lines.append(r.choice(["", "   ", "# comment", "  # indented", "User-agent: *  # trailing", " ", "garbage line", ":", "Disallow /a", "User agent *", "user-agent foo bar"]))
            continue
        f = r.choice(FIELDS) if r.random() < 0.5 else r.choice(["Allow", "Disallow"])
        if f.lower().replace(" ", "").replace("-", "") in ("useragent",): v = r.choice(AGENTS)
        else: v = r.choice(PATS)
        sep = r.choice([": ", ":", " : ", ":\t", " ", ":  "])
        lines.append(f + sep + v + r.choice(["", "", " ", "\t", " # c"]))
    nl = r.choice(["\n", "\r\n", "\r", "\n\n"])
    return nl.join(lines)

def part_robots(driver, r, n):
    from protego import Protego
    cases = []
    for _ in range(n):
        t = "\n".join(l for l in robots(r).splitlines() if not l.strip().startswith("#"))
        cases.append([t, r.choice(URLS), UA if r.random() < 0.8 else r.choice(["Googlebot/2.1", "modelcontextprotocol", " x ", "MyBot-Servers"])])
    out = run(driver, [json.dumps(c) for c in cases]).split()
    return [(c, o, "1" if Protego.parse(c[0]).can_fetch(c[1], c[2]) else "0") for c, o in zip(cases, out)], len(out)

# ---- guard
NETS = ["0.0.0.0/8","10.0.0.0/8","100.64.0.0/10","127.0.0.0/8","169.254.0.0/16","172.16.0.0/12","192.0.0.0/24","192.0.2.0/24","192.88.99.0/24","192.168.0.0/16","198.18.0.0/15","198.51.100.0/24","203.0.113.0/24","240.0.0.0/4","224.0.0.0/4","192.0.0.170/31","255.255.255.255/32","192.0.0.9/32","192.0.0.10/32",
        "::/96","64:ff9b:1::/48","100::/64","2001::/23","2001:db8::/32","2002::/16","fc00::/7","fe80::/10","::1/128","::ffff:0:0/96","3fff::/20","2001:1::1/128","2001:1::2/128","2001:3::/32","2001:4:112::/48","2001:20::/28","2001:30::/28","ff00::/8","64:ff9b::/96","fec0::/10","2000::/3"]
def part_guard(driver, r, n):
    from mcp_server_fetch.server import _is_public_address
    cases = []
    for _ in range(n):
        k = r.random()
        if k < 0.5:
            net = ipaddress.ip_network(r.choice(NETS))
            span = net.num_addresses
            off = r.choice([0, span - 1, -1, span, r.randrange(span)]) if span > 1 else r.choice([0, -1, 1])
            v = (int(net.network_address) + off) % (2**32 if net.version == 4 else 2**128)
            a = ipaddress.IPv4Address(v) if net.version == 4 else ipaddress.IPv6Address(v)
        elif k < 0.75: a = ipaddress.IPv4Address(r.getrandbits(32))
        else:
            a = ipaddress.IPv6Address(r.getrandbits(128))
            if r.random() < 0.3: a = ipaddress.IPv6Address((0xFFFF << 32) | r.getrandbits(32))
            elif r.random() < 0.3: a = ipaddress.IPv6Address((0x64ff9b << 96) | r.getrandbits(32))
        cases.append(str(a))
    out = run(driver, cases).split()
    return [(c, o, "1" if _is_public_address(c) else "0") for c, o in zip(cases, out)], len(out)

# ---- tok
PIECES = ["<p>", "</p>", "<div class=\"a b\">", "<a href='x?a=1&amp;b=2'>", "<a href=x&ampy=1>", "<a href=\"&#x41;&#65;&#0;&#xD800;&#999999999;\">",
          "<img src=a.png alt=\"x\"/>", "<br/>", "<br />", "<br/ >", "<input disabled>", "<input value=>", "<x a=b=c>", "<x a = 'b' c>",
          "<x 'a'=b>", "<x a='b>", "<x a=\"b>", "<x\ta\n=\r'b'>", "<x/a/b>", "<x a=b/>", "<X Y=Z>", "<x a b c=d>", "<x =a>", "<x a==b>",
          "<script>", "</script>", "</SCRIPT >", "</script/>", "<script>a<b</p>x</script>", "<style>p{}</style>", "<title>a&amp;b</title>",
          "<textarea>&lt;x&gt;</textarea>", "<xmp><b></xmp>", "<!-- c -->", "<!---->", "<!-->", "<!--->", "<!-- a --!>", "<!-- unterminated",
          "<!doctype html>", "<!DOCTYPE x", "<![CDATA[x]]>", "<![CDATA[x", "<?xml v?>", "<?pi", "<!x>", "<!", "</>", "</ x>", "</1>", "</",
          "<", "< p>", "<1>", "a < b", "x &amp; y", "&lt;&gt;&quot;&apos;&nbsp;", "&notit;", "&notin;", "&amp", "&ampx", "&#65", "&#x41;", "&#x;",
          "&#;", "&;", "&", "&copy2", "&CounterClockwiseContourIntegral;", "text", " ", "\n", "é", "日本", "&#128;&#150;", "&#x80", "&#1;&#11;",
          "<meta charset=utf-8>", "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=iso-8859-1\">", "<p", "<a href=\"x", "</p",
          "<x y='&quot;'>", "<x y=\"&notit;&notin;&amp=\">", "<x y=&lt>", "<x y=a&#62;b>", "<noscript><b></noscript>", "<plaintext>",
          "<iframe><p></iframe>", "<noembed>a</noembed>", "<x\x00y>", "<x y=\x00>", "\x00", "\r\n", "<a b>", "<p  >"]
def frag(r, n=None):
    return "".join(r.choice(PIECES) for _ in range(n if n is not None else r.randrange(0, 12)))

def part_tok(driver, r, n):
    from html.parser import HTMLParser
    class P(HTMLParser):
        def __init__(self):
            super().__init__(); self.ev = []
        def add(self, e):
            if e[0] == "t" and self.ev and self.ev[-1][0] == "t": self.ev[-1][2] += e[2]
            else: self.ev.append(e)
        def handle_starttag(self, t, a): self.add(["s", t, [[k, v] for k, v in a]])
        def handle_endtag(self, t): self.add(["e", t, []])
        def handle_data(self, d): self.add(["t", "", d])
        def handle_comment(self, d): self.add(["c", "", d])
        def handle_decl(self, d): self.add(["x", "", d])
        def handle_pi(self, d): self.add(["x", "", d])
        def unknown_decl(self, d): self.add(["x", "", d])
    def ref(html, end):
        p = P(); p.feed(html)
        if end: p.close()
        return p.ev
    cases = [{"html": frag(r), "end": r.random() < 0.5} for _ in range(n)]
    groups, cur = [], []
    for l in run(driver, [json.dumps(c) for c in cases]).split("\n"):
        if l == ".": groups.append(cur); cur = []
        elif l: cur.append(json.loads(l))
    res = []
    for c, g in zip(cases, groups):
        merged = []
        for e in g:
            if e[0] == "t" and merged and merged[-1][0] == "t": merged[-1][2] += e[2]
            else: merged.append(e)
        res.append((c, merged, ref(c["html"], c["end"])))
    return res, len(groups)

# ---- charset
NAMES = ["utf-8", "UTF-8", "utf8", "UTF 8", "\"utf-8\"", "'utf-8'", "latin1", "iso-8859-1", "ISO_8859-1:1987", "windows-1252", "cp1252",
         "iso-8859-2", "iso-8859-15", "koi8-r", "KOI8-U", "cp1251", "windows-1251", "mac-roman", "macintosh", "cp437", "ascii", "us-ascii",
         "utf-16", "utf-16le", "UTF-16BE", "utf-32", "utf-8-sig", "cp037", "cp500", "utf-7", "base64", "rot13", "idna", "unicode-escape",
         "x-unknown", "", "utf-8;", "tis-620", "cp874", "iso8859_11", "hz", "\u00fctf8", "utf.8", "latin-1 ", " cp1252", "l1", "8859", "u8",
         "csISOLatin1", "iso-ir-100", "greek", "hebrew", "arabic", "cyrillic", "cp65001", "utf_8", "UTF-\uff18"]
TEXTS = ["hello", "caf\u00e9", "\u20ac 5", "\u043f\u0440\u0438\u0432\u0435\u0442", "\u00c5ngstr\u00f6m", "\u05e9\u05dc\u05d5\u05dd", "plain ascii text"]
def part_charset(driver, r, n):
    import httpx
    from mcp_server_fetch.server import decode_page
    def enc(t, name):
        for nm in [name, "utf-8"]:
            try: return t.encode(codecs.lookup(nm.strip("\"' ;")).name, errors="replace")
            except Exception: pass
        return t.encode("utf-8")
    def case():
        name = r.choice(NAMES)
        text = r.choice(TEXTS) * r.randrange(1, 4)
        k = r.random()
        if k < 0.3: head = "<meta charset=%s>" % name
        elif k < 0.45: head = "<meta charset=\"%s\">" % name
        elif k < 0.6: head = "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=%s\">" % name
        elif k < 0.65: head = "<META HTTP-EQUIV=content-type CONTENT='text/html;charset = \"%s\"'>" % name
        elif k < 0.7: head = "<!-- <meta charset=%s> --><meta charset=utf-8>" % name
        elif k < 0.75: head = "<meta data-charset=%s><meta name=x>" % name
        elif k < 0.8: head = "<script>var s='<meta charset=%s>'</script>" % name
        else: head = ""
        pre = r.choice(["", "<!doctype html>", "<html><head>", "\ufeff", " " * r.choice([0, 1000, 1010, 1030])])
        body = enc(pre + head + "<p>" + text + "</p>", r.choice([name, name, "utf-8", "latin-1", "utf-16"]))
        if r.random() < 0.05: body = bytes(r.randrange(256) for _ in range(r.randrange(0, 40)))
        # (header charsets: not the codecs that aren't text or rewrite escapes, which no server sends)
        hn = [x for x in NAMES if x not in ("base64", "rot13", "unicode-escape", "idna", "utf-7", "hz")]
        ct = r.choice([None, None, "text/html", "text/html; charset=%s" % r.choice(hn), "TEXT/HTML ; Charset=\"%s\"" % r.choice(hn),
                       "application/xhtml+xml", "text/plain", "application/json", "", "text/html;charset", "text/html; charset=", "charset=latin1",
                       "text/html; foo=\"a;b\"; charset=cp1252", "text/html; charset*=utf-8''latin1"])
        return body, ct
    cases = [c for c in (case() for _ in range(n)) if c[1] is None or c[1].isascii()]
    out = run(driver, [json.dumps({"body": b.hex(), "ct": ct}) for b, ct in cases]).split("\n")
    res = []
    for (b, ct), o in zip(cases, out):
        try: want = decode_page(httpx.Response(200, headers={} if ct is None else {"content-type": ct}, content=b))
        except Exception as e: want = "!! " + str(e)
        res.append(([b.hex()[:200], ct], json.loads(o), want))
    return res, len([x for x in out if x])

def main():
    a = sys.argv[1:]
    part, driver = a[0], a[1]
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    n = int(a[a.index("--n") + 1]) if "--n" in a else 3000
    r = random.Random(seed)
    res, answered = globals()["part_" + part](driver, r, n)
    bad = [x for x in res if x[1] != x[2]]
    for c, got, want in bad[:8]: print("  %s\n    vu:  %s\n    ref: %s" % (json.dumps(c, ensure_ascii=False)[:400], json.dumps(got, ensure_ascii=False)[:400], json.dumps(want, ensure_ascii=False)[:400]))
    if bad or answered != len(res): sys.exit("FAIL %s: %d of %d differ (%d answered)" % (part, len(bad), len(res), answered))
    print("%s: %d the same (seed %d)" % (part, len(res), seed))

main()
