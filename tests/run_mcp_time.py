#!/usr/bin/env python3
"""The MCP time server (mcp/time) against the reference (mcp-server-time, Python): every zone the
reference knows, through get_current_time, and random convert_time requests (zones, times, malformed
times, missing arguments), every answer compared as JSON. The current time can tick between the two
servers' answers, so get_current_time's seconds aren't compared.
  tests/run_mcp_time.py VU_SERVER PYTHON_WITH_MCP_SERVER_TIME [--seed N] [--rounds N]"""
import json, os, random, re, subprocess, sys

INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}

class S:
    def __init__(self, cmd):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.n = 0
        self.ask(INIT)
        self.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    def ask(self, m):
        self.p.stdin.write((json.dumps(m) + "\n").encode()); self.p.stdin.flush()
        l = self.p.stdout.readline()
        if not l: sys.exit("FAIL: a server closed its output after " + json.dumps(m)[:500] + ": " + self.p.stderr.read().decode()[-2000:])
        return json.loads(l)
    def call(self, name, args):
        self.n += 1
        return self.ask({"jsonrpc": "2.0", "id": self.n, "method": "tools/call", "params": {"name": name, "arguments": args}})

def norm(r, drop_seconds):
    s = json.dumps(r, sort_keys=True)
    if drop_seconds: s = re.sub(r"(T\d\d:\d\d):\d\d", r"\1:SS", s)
    return json.loads(s)

def main():
    a = sys.argv[1:]
    vu, py = a[0], a[1]
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    rounds = int(a[a.index("--rounds") + 1]) if "--rounds" in a else 2000
    rnd = random.Random(seed)
    # the zones in the system's tz database (the reference also falls back to Python's bundled tzdata
    # for names the system lacks; this server reads only the system's: documented)
    zones = []
    root = "/usr/share/zoneinfo"
    for d, dirs, files in os.walk(root):
        if d == root: dirs[:] = [x for x in dirs if x not in ("posix", "right")]
        for f in files:
            k = os.path.relpath(os.path.join(d, f), root)
            try:
                if open(os.path.join(d, f), "rb").read(4) == b"TZif" and k != "posixrules" and not os.path.islink(os.path.join(d, f)): zones.append(k)
            except OSError: pass
    zones.sort()
    sv = S([vu, "--local-timezone", "America/Los_Angeles"])
    sr = S([py, "-m", "mcp_server_time", "--local-timezone", "America/Los_Angeles"])
    n = 0
    def same(name, args, drop):
        nonlocal n
        n += 1
        x, y = sv.call(name, args), sr.call(name, args)
        x["id"] = y["id"] = 0
        if norm(x, drop) != norm(y, drop):
            # the minute may have turned between the two answers: ask once more
            x, y = sv.call(name, args), sr.call(name, args)
            x["id"] = y["id"] = 0
            if norm(x, drop) != norm(y, drop):
                sys.exit("FAIL %s %s:\n  vu:  %s\n  ref: %s" % (name, json.dumps(args), json.dumps(x)[:1500], json.dumps(y)[:1500]))
    l1 = sv.ask({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}); l2 = sr.ask({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    if l1 != l2: sys.exit("FAIL tools/list differs")
    for z in zones: same("get_current_time", {"timezone": z}, True)
    odd = ["", "mars/base", "europe/warsaw", "UTC/", "/etc/passwd", "../x", "posix/UTC", "right/UTC", "Etc", "America", "zone.tab", "iso3166.tab"]
    # with Python's tzdata package installed, the reference also looks a name up there, and a folder or
    # a file that isn't a zone fails with that package's path in the message: those aren't compared
    if subprocess.run([py, "-c", "import tzdata"], capture_output=True).returncode == 0:
        odd = [z for z in odd if z not in ("Etc", "America", "zone.tab", "iso3166.tab")]
    for z in odd:
        same("get_current_time", {"timezone": z}, True)
    times = ["00:00", "23:59", "12:30", "1:5", "01:05", "24:00", "12:60", "12-30", "", "1230", " 1:05", "+1:05", "-1:05", "12:3a", "007:00", "9:7",
             "  1:05", "1:05 ", "\t1:05", " 01:05", "1: 5", "01:5", "0:0", "1:005", "20:00", "19:59", "2:60", " 9:59", "12:30\n"]
    for _ in range(rounds):
        t = rnd.choice(times) if rnd.random() < 0.2 else "%02d:%02d" % (rnd.randrange(24), rnd.randrange(60))
        same("convert_time", {"source_timezone": rnd.choice(zones), "time": t, "target_timezone": rnd.choice(zones)}, False)
    same("convert_time", {"source_timezone": "", "time": "10:00", "target_timezone": "UTC"}, False)
    print("run_mcp_time: %d answers the same as the reference server (%d zones, seed %d)" % (n, len(zones), seed))

main()
