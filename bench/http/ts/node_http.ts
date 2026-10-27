// The HTTP benchmark server on node:http (Node 22.6+ with --experimental-strip-types).
import { createServer } from "node:http";
import { order, errorJSON } from "./order.ts";

const port = Number(process.argv[2] ?? 8080);
createServer((req, res) => {
  if (req.method === "GET" && req.url === "/") {
    res.writeHead(200, { "Content-Type": "text/plain", "Content-Length": "13" });
    res.end("Hello, World!");
  } else if (req.method === "POST" && req.url === "/order") {
    const chunks: Buffer[] = [];
    req.on("data", (c: Buffer) => chunks.push(c));
    req.on("end", () => {
      let status = 200, body: string;
      try { body = order(Buffer.concat(chunks).toString("utf8")); } catch (e) { status = 400; body = errorJSON(e); }
      res.writeHead(status, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) });
      res.end(body);
    });
  } else {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("not found");
  }
}).listen(port, "0.0.0.0");
