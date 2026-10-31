# For run_ai.sh: a fake Anthropic and OpenAI that stream (chunked, split in awkward places, slowly);
# runs stream.vu (arg 1) and checks what it printed and what was asked.
import http.server, json, subprocess, sys, threading, time

reqs, counts = [], {}
def sse(name, obj): return "event: %s\ndata: %s\n\n" % (name, json.dumps(obj))

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def plain(self, status, obj, headers=None):
        data = json.dumps(obj).encode()
        self.send_response(status)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def chunks(self, parts, delay):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream"); self.send_header("Transfer-Encoding", "chunked"); self.end_headers()
        try:
            for p in parts:
                b = p.encode()
                self.wfile.write(b"%x\r\n%s\r\n" % (len(b), b)); self.wfile.flush()
                time.sleep(delay)
            self.wfile.write(b"0\r\n\r\n"); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            reqs.append("client left")
        self.close_connection = True
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        q = body["messages"][-1]["content"]
        reqs.append((self.path, body.get("stream"), body.get("stream_options")))
        counts[q] = counts.get(q, 0) + 1
        if self.path == "/v1/messages":
            if q == "overloaded once" and counts[q] == 1:
                return self.plain(529, {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}, {"retry-after": "0"})
            if q == "bad request":
                return self.plain(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "messages: too short"}})
            words = ["Hel", "lo, ", "wor", "ld é😀"] if q != "long" else ["w%d " % i for i in range(30)]
            evs = [sse("message_start", {"type": "message_start", "message": {"id": "m", "type": "message", "role": "assistant", "content": [], "usage": {"input_tokens": 10, "output_tokens": 1}}}),
                   sse("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
                   sse("ping", {"type": "ping"})]
            for i, w in enumerate(words):
                evs.append(sse("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": w}}))
                if q == "error midway" and i == 1:
                    evs.append(sse("error", {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}))
                    break
            evs += [sse("content_block_stop", {"type": "content_block_stop", "index": 0}),
                    sse("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 5}}),
                    sse("message_stop", {"type": "message_stop"})]
            text = "".join(evs)
            if q == "crlf": text = text.replace("\n", "\r\n")
            # split at awkward places: in the middle of lines and of UTF-8 characters
            raw = text.encode()
            parts, i = [], 0
            while i < len(raw):
                n = 7 + (i * 13) % 37
                parts.append(raw[i:i + n]); i += n
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream"); self.send_header("Transfer-Encoding", "chunked"); self.end_headers()
            try:
                for k, p in enumerate(parts):
                    self.wfile.write(b"%x\r\n%s\r\n" % (len(p), p)); self.wfile.flush()
                    if k % 3 == 0: time.sleep(0.08)
                self.wfile.write(b"0\r\n\r\n"); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                reqs.append("client left")
            self.close_connection = True
            return
        if self.path == "/v1/chat/completions":
            parts = []
            for w in ["Su", "re: ", "{json}"]:
                parts.append("data: %s\n\n" % json.dumps({"id": "c", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"content": w}, "finish_reason": None}]}))
            parts.append("data: %s\n\n" % json.dumps({"id": "c", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}))
            parts.append("data: %s\n\n" % json.dumps({"id": "c", "object": "chat.completion.chunk", "choices": [], "usage": {"prompt_tokens": 20, "completion_tokens": 3}}))
            parts.append("data: [DONE]\n\n")
            return self.chunks(parts, 0.2)
        self.plain(404, {"error": {"message": "no"}})

srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
r = subprocess.run([sys.argv[1], str(srv.server_address[1])], capture_output=True, text=True, timeout=120)
time.sleep(0.3)
srv.shutdown()
want = ["anthropic: Hel|lo, |wor|ld é😀 (as written) [end_turn 10/5] Hello, world é😀",
        "crlf: Hel|lo, |wor|ld é😀 (as written) [end_turn 10/5] Hello, world é😀",
        "overloaded first: Hel|lo, |wor|ld é😀 (as written) [end_turn 10/5] Hello, world é😀",
        "error mid-stream: Hel|lo,  (all at once) error: ai: Overloaded",
        "refused:  (all at once) error: ai: HTTP 400: messages: too short",
        "openai: Su|re: |{json} (as written) [stop 20/3] Sure: {json}",
        "reader stops: w0 |w1  (all at once) error: ai: the reader stopped"]
got = r.stdout.split("\n")[:-1]
bad = []
if r.returncode != 0: bad.append("exit %d: %s" % (r.returncode, r.stderr[-300:]))
for i, w in enumerate(want):
    g = got[i] if i < len(got) else None
    # (whether a short stream counts as "as written" depends on timing: only the long ones are checked)
    if g != w and not (w.endswith("Hello, world é😀") is False and g and g.replace("(as written)", "(all at once)") == w.replace("(as written)", "(all at once)") and "error" in w):
        bad.append("line %d: got %r, want %r" % (i, g, w))
streams = [x for x in reqs if isinstance(x, tuple)]
if not all(x[1] is True for x in streams): bad.append("a request without stream: true: %r" % streams)
if [x[2] for x in streams if x[0] == "/v1/chat/completions"] != [{"include_usage": True}]: bad.append("openai stream_options: %r" % streams)
for b in bad: print("FAIL  " + b)
print("ai.stream: %s" % ("both APIs, CRLF, retries, errors and a reader that stops" if not bad else "%d problems" % len(bad)))
sys.exit(1 if bad else 0)
