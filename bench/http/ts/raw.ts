// The HTTP benchmark server over plain TCP (node:net) with the same minimal HTTP handling as
// server.vu. Runs on Node and Bun.
import { createServer } from "node:net";
import { order, errorJSON } from "./order.ts";

const port = Number(process.argv[2] ?? 8080);
const CL = Buffer.from("\r\ncontent-length:");

function respond(out: Buffer[], status: string, kind: string, body: string) {
  const b = Buffer.from(body);
  out.push(Buffer.from(`HTTP/1.1 ${status}\r\nContent-Type: ${kind}\r\nContent-Length: ${b.length}\r\n\r\n`), b);
}

// Content-Length of the head: 0 if none, -1 if malformed.
function contentLength(head: Buffer): number {
  const lower = Buffer.from(head.toString("latin1").toLowerCase(), "latin1");
  const i = lower.indexOf(CL);
  if (i < 0) return 0;
  const v = head.subarray(i + CL.length, head.indexOf("\r", i + CL.length)).toString("latin1").trim();
  return /^[0-9]+$/.test(v) ? Number(v) : -1;
}

function handle(head: Buffer, body: Buffer, out: Buffer[]) {
  const line = head.toString("latin1", 0, 12);
  if (line.startsWith("GET / ")) respond(out, "200 OK", "text/plain", "Hello, World!");
  else if (line.startsWith("POST /order ")) {
    try { respond(out, "200 OK", "application/json", order(body.toString("utf8"))); }
    catch (e) { respond(out, "400 Bad Request", "application/json", errorJSON(e)); }
  } else respond(out, "404 Not Found", "text/plain", "not found");
}

createServer((sock) => {
  sock.setNoDelay(true);
  let buf = Buffer.alloc(0);
  sock.on("data", (data: Buffer) => {
    buf = buf.length ? Buffer.concat([buf, data]) : data;
    const out: Buffer[] = [];
    let at = 0, broken = false;
    for (;;) {
      const i = buf.indexOf("\r\n\r\n", at);
      if (i < 0) break;
      const end = i + 4;
      const n = contentLength(buf.subarray(at, end));
      if (n < 0 || n > 1 << 20) { respond(out, "400 Bad Request", "text/plain", "bad Content-Length"); broken = true; break; }
      if (end + n > buf.length) break;
      handle(buf.subarray(at, end), buf.subarray(end, end + n), out);
      at = end + n;
    }
    buf = buf.subarray(at);
    if (out.length) sock.write(out.length === 1 ? out[0] : Buffer.concat(out));
    if (broken) sock.end();
  });
  sock.on("error", () => {});
}).listen(port, "0.0.0.0");
