"""Times the MCP filesystem server against the reference one: start-up, memory, and a few tools.
  python3 mcp/filesystem/bench.py VU_SERVER REF_SERVER_JS"""
import json, os, subprocess, sys, tempfile, time, statistics
vu, ref = sys.argv[1], sys.argv[2]
root = tempfile.mkdtemp(prefix="vu-mcp-bench-")
for i in range(40):
    d = os.path.join(root, "d%02d" % i); os.makedirs(d)
    for j in range(50):
        with open(os.path.join(d, "f%02d.txt" % j), "w") as f: f.write("line\n" * 20)
with open(os.path.join(root, "a.txt"), "w") as f: f.write("hello\n" * 100)
INIT = {"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}
def rss(pid):
    for l in open("/proc/%d/status" % pid):
        if l.startswith("VmRSS"): return int(l.split()[1]) / 1024
def run(cmd):
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd + [root], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    p.stdin.write((json.dumps(INIT) + "\n").encode()); p.stdin.flush(); p.stdout.readline()
    return p, time.perf_counter() - t0
def call(p, i, name, args):
    p.stdin.write((json.dumps({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":name,"arguments":args}}) + "\n").encode()); p.stdin.flush()
    return p.stdout.readline()
for label, cmd in [("vu", [vu]), ("node", ["node", ref])]:
    starts = []
    for _ in range(15):
        p, t = run(cmd); starts.append(t); p.stdin.close(); p.wait()
    p, _ = run(cmd)
    r0 = rss(p.pid)
    t0 = time.perf_counter()
    for i in range(2000): call(p, i + 1, "read_text_file", {"path": "a.txt"})
    reads = 2000 / (time.perf_counter() - t0)
    t0 = time.perf_counter()
    for i in range(20): call(p, 9000 + i, "search_files", {"path": ".", "pattern": "**/f1*.txt"})
    search = (time.perf_counter() - t0) / 20 * 1000
    t0 = time.perf_counter()
    for i in range(20): call(p, 9100 + i, "directory_tree", {"path": "."})
    tree = (time.perf_counter() - t0) / 20 * 1000
    r1 = rss(p.pid)
    p.stdin.close(); p.wait()
    print("%-5s start to initialize answer: median %.1f ms | RSS idle %.1f MB, after work %.1f MB | read_text_file %.0f calls/s | search_files 2,000 files %.1f ms | directory_tree %.1f ms" % (label, statistics.median(starts) * 1000, r0, r1, reads, search, tree))
