# For run_sse.sh: starts server.vu's binary (arg 1) and reads its event streams as a browser's
# EventSource would (the parsing rules of the HTML standard), checks refusals, many clients at once,
# clients that leave in the middle, and HTTP/2.
import socket, subprocess, sys, threading, time

def free():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
port = free()
srv = subprocess.Popen([sys.argv[1], str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
fails = []
def expect(what, got, want):
    if got != want: fails.append("%s: got %r, want %r" % (what, got, want))

def raw(path, token="ok", read=True):
    s = socket.create_connection(("127.0.0.1", port), 10)
    s.sendall(("GET %s HTTP/1.1\r\nHost: x\r\nAccept: text/event-stream\r\nx-token: %s\r\nConnection: close\r\n\r\n" % (path, token)).encode())
    if not read: return s
    data = b""
    while True:
        d = s.recv(65536)
        if not d: break
        data += d
    s.close()
    return data

def parse(body):
    # the HTML standard's event stream interpretation, for complete events
    events, name, data = [], "", []
    for line in body.decode().replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line == "":
            if data: events.append((name or "message", "\n".join(data)))
            name, data = "", []
        elif line.startswith(":"): continue
        else:
            field, _, value = line.partition(":")
            if value.startswith(" "): value = value[1:]
            if field == "event": name = value
            elif field == "data": data.append(value)
    return events

try:
    for _ in range(200):
        try: socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError: time.sleep(0.05)
    r = raw("/events/6")
    head, _, body = r.partition(b"\r\n\r\n")
    hl = head.decode().split("\r\n")
    expect("status", hl[0], "HTTP/1.1 200 OK")
    expect("content type", "Content-Type: text/event-stream; charset=utf-8" in hl, True)
    expect("no caching", "Cache-Control: no-cache" in hl, True)
    want = [("message", "plain 0 for tester"), ("multi", "line one 1\nline two é 😀\nline three"), ("tick", ""),
            ("message", "plain 3 for tester"), ("multi", "line one 4\nline two é 😀\nline three"), ("tick", "")]
    expect("events", parse(body), want)
    expect("refused by middleware", raw("/events/3", token="no").split(b"\r\n")[0], b"HTTP/1.1 401 Unauthorized")
    expect("other routes", raw("/").split(b"\r\n\r\n")[1], b"home")
    # 30 clients at once
    results = [None] * 30
    def one(i): results[i] = parse(raw("/events/%d" % (i % 7 + 1)).partition(b"\r\n\r\n")[2])
    ts = [threading.Thread(target=one, args=(i,)) for i in range(30)]
    for t in ts: t.start()
    for t in ts: t.join()
    expect("30 clients at once", [len(x or []) for x in results], [i % 7 + 1 for i in range(30)])
    # clients that leave in the middle of an endless stream: the server notices, and goes on
    for i in range(5):
        s = raw("/forever", read=False)
        s.recv(200)
        s.close()
    time.sleep(1.0)
    expect("streams that ended when their client left", raw("/ended").split(b"\r\n\r\n")[1], b"5")
    # HTTP/2 with prior knowledge: 505
    s = socket.create_connection(("127.0.0.1", port), 10)
    import h2.connection, h2.events
    c = h2.connection.H2Connection(); c.initiate_connection(); s.sendall(c.data_to_send())
    c.send_headers(1, [(":method", "GET"), (":path", "/events/2"), (":scheme", "http"), (":authority", "x"), ("x-token", "ok")], end_stream=True)
    s.sendall(c.data_to_send())
    status = None
    while status is None:
        for ev in c.receive_data(s.recv(65536)):
            if isinstance(ev, h2.events.ResponseReceived): status = dict(ev.headers).get(b":status")
        s.sendall(c.data_to_send())
    s.close()
    expect("HTTP/2", status, b"505")
finally:
    srv.terminate()
    try: _, err = srv.communicate(timeout=10)
    except subprocess.TimeoutExpired: srv.kill(); _, err = srv.communicate()
    bad = [l for l in err.decode(errors="replace").split("\n") if "ERROR" in l or "runtime error" in l or "panic" in l]
    if bad: fails.append("server stderr: %r" % bad[:5])
for f in fails: print("FAIL  " + f)
print("sse: all checks passed" if not fails else "sse: %d checks failed" % len(fails))
sys.exit(1 if fails else 0)
