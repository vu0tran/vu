"""Start to the initialize answer (median of 15), idle RSS, and calls per second for one tool call.
  bench_start.py 'CALL_JSON' -- CMD..."""
import json, statistics, subprocess, sys, time
call = json.loads(sys.argv[1]); cmd = sys.argv[sys.argv.index("--") + 1:]
INIT = {"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"b","version":"1"}}}
def start():
    t0 = time.perf_counter(); p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    p.stdin.write((json.dumps(INIT)+"\n").encode()); p.stdin.flush(); p.stdout.readline(); return p, time.perf_counter() - t0
ts = []
for _ in range(15):
    p, t = start(); ts.append(t); p.stdin.close(); p.wait()
p, _ = start()
rss = [int(l.split()[1]) for l in open(f"/proc/{p.pid}/status") if l.startswith("VmRSS")][0] / 1024
t0 = time.perf_counter()
for i in range(1000):
    m = {"jsonrpc":"2.0","id":i+1,"method":"tools/call","params":call}; p.stdin.write((json.dumps(m)+"\n").encode()); p.stdin.flush(); p.stdout.readline()
cps = 1000 / (time.perf_counter() - t0)
p.stdin.close(); p.wait()
print("start %.1f ms | RSS %.1f MB | %d calls/s" % (statistics.median(ts) * 1000, rss, cps))
