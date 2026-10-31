# For run_ai.sh: a fake Anthropic Messages API and OpenAI Chat Completions on one port; runs main.vu
# (arg 1) against it and checks its output and every request that arrived.
import http.server, json, subprocess, sys, threading, time

reqs = []
counts = {}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def answer(self, status, obj, headers=None):
        data = (obj if isinstance(obj, str) else json.dumps(obj)).encode()
        self.send_response(status)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        reqs.append((time.time(), self.path, {k.lower(): v for k, v in self.headers.items()}, body))
        last = body["messages"][-1]["content"]
        counts[last] = counts.get(last, 0) + 1
        if self.path == "/v1/messages":
            if last == "overloaded once" and counts[last] == 1:
                return self.answer(529, {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}, {"retry-after": "0.3"})
            if last == "overloaded always":
                return self.answer(529, {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}, {"retry-after": "0"})
            if last == "bad request":
                return self.answer(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "max_tokens: Field required"}})
            content = [{"type": "text", "text": "Hi back \"é\" 😀\n"}]
            if last == "blocks":
                content = [{"type": "text", "text": "Let me check. "}, {"type": "tool_use", "id": "toolu_1", "name": "lookup", "input": {"q": "x"}}, {"type": "text", "text": "Done."}]
            return self.answer(200, {"id": "msg_1", "type": "message", "role": "assistant", "model": body["model"], "content": content,
                                     "stop_reason": "end_turn", "stop_sequence": None, "usage": {"input_tokens": 12, "output_tokens": 7, "cache_read_input_tokens": 0}})
        if self.path == "/v1/chat/completions":
            if last == "not json": return self.answer(200, "<html>oops</html>")
            return self.answer(200, {"id": "chatcmpl-1", "object": "chat.completion", "created": 1, "model": body["model"],
                                     "choices": [{"index": 0, "message": {"role": "assistant", "content": "Sure: {json}", "refusal": None}, "logprobs": None, "finish_reason": "stop"}],
                                     "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25}})
        self.answer(404, {"error": {"message": "no such route"}})

srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
r = subprocess.run([sys.argv[1], str(srv.server_address[1])], capture_output=True, text=True, timeout=120)
srv.shutdown()
want = ['anthropic: Hi back "é" 😀\n [end_turn 12/7]'.replace("\n", "\n"),
        "blocks: Let me check. Done. [end_turn 12/7]",
        "retry: Hi back \"é\" 😀\n [end_turn 12/7]",
        "refused: error: ai: HTTP 400: max_tokens: Field required",
        "gave up: error: ai: HTTP 529: Overloaded",
        "openai: Sure: {json} [stop 20/5]",
        "garbled: error: ai: an answer that isn't a Chat Completions reply",
        "no key: error: ai: no API key",
        "empty: error: ai: no messages",
        "bad role: error: ai: a message's role is user or assistant, not 'system'",
        "reasoning: Sure: {json} [stop 20/5]"]
got = r.stdout
bad = []
if r.returncode != 0: bad.append("exit %d: %s" % (r.returncode, "\n".join(l for l in r.stderr.split("\n") if "ERROR" in l or l.lstrip().startswith("#") or "SUMMARY" in l or "READ" in l or "WRITE" in l)[:2500]))
if got != "\n".join(want) + "\n": bad.append("output:\n%s\nwant:\n%s" % (got, "\n".join(want)))
convo = [{"role": "user", "content": "Hi \"there\" é 😀\nline two"}, {"role": "assistant", "content": "Hello."}, {"role": "user", "content": "Say {json}"}]
t0, p0, h0, b0 = reqs[0]
if p0 != "/v1/messages" or h0.get("x-api-key") != "sk-ant-test" or h0.get("anthropic-version") != "2023-06-01" or "authorization" in h0:
    bad.append("anthropic headers: %s %r" % (p0, h0))
if b0 != {"model": "claude-test", "max_tokens": 100, "system": "Be brief.", "messages": convo}: bad.append("anthropic body: %r" % b0)
if "system" in reqs[1][3]: bad.append("an empty system prompt was sent")
retries = [x for x in reqs if x[3]["messages"][-1]["content"] == "overloaded once"]
if len(retries) != 2 or not (0.25 <= retries[1][0] - retries[0][0] <= 2.0): bad.append("retry after Retry-After 0.3: %d tries, %.2f s apart" % (len(retries), retries[-1][0] - retries[0][0]))
if len([x for x in reqs if x[3]["messages"][-1]["content"] == "overloaded always"]) != 3: bad.append("gave up after a number of tries other than 3")
if len([x for x in reqs if x[3]["messages"][-1]["content"] == "bad request"]) != 1: bad.append("a 400 was tried again")
oa = [x for x in reqs if x[1] == "/v1/chat/completions"][0]
if oa[2].get("authorization") != "Bearer sk-test" or "x-api-key" in oa[2]: bad.append("openai headers: %r" % oa[2])
if oa[3] != {"model": "gpt-test", "max_tokens": 100, "messages": [{"role": "system", "content": "Be brief."}] + convo}: bad.append("openai body: %r" % oa[3])
rq = reqs[-1][3]
if rq.get("max_completion_tokens") != 100 or "max_tokens" in rq: bad.append("reasoning model body: %r" % rq)
if len(reqs) != 11: bad.append("%d requests, want 11 (none for the refused calls)" % len(reqs))
for b in bad: print("FAIL  " + b)
print("ai: %s" % ("both APIs, retries, errors and refusals as expected" if not bad else "%d problems" % len(bad)))
sys.exit(1 if bad else 0)
