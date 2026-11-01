"""A fake Anthropic Messages API for run_speedup.sh: answers each request with the next file given
(as a ```vu block), and keeps every request it got in REQUESTS_DIR.
    python3 fake_model.py PORT_FILE REQUESTS_DIR ANSWER1.vu ANSWER2.vu ..."""
import http.server, json, os, sys

port_file, req_dir, answers = sys.argv[1], sys.argv[2], sys.argv[3:]
count = [0]

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        i = count[0]
        count[0] += 1
        with open(os.path.join(req_dir, f"{i}.json"), "w") as fh:
            json.dump({"key": self.headers.get("x-api-key"), "body": body}, fh)
        text = "Here it is:\n```vu\n" + open(answers[min(i, len(answers) - 1)]).read() + "```\n"
        out = json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                          "usage": {"input_tokens": 1, "output_tokens": 1}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)
    def log_message(self, *a): pass

s = http.server.HTTPServer(("127.0.0.1", 0), H)
with open(port_file + ".tmp", "w") as fh: fh.write(str(s.server_address[1]))
os.replace(port_file + ".tmp", port_file)
s.serve_forever()
