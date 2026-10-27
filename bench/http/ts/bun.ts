// The HTTP benchmark server on Bun's native server (Bun.serve).
import { order, errorJSON } from "./order.ts";

const port = Number(process.argv[2] ?? 8080);
Bun.serve({
  port,
  hostname: "0.0.0.0",
  async fetch(req) {
    const path = new URL(req.url).pathname;
    if (req.method === "GET" && path === "/") return new Response("Hello, World!", { headers: { "Content-Type": "text/plain" } });
    if (req.method === "POST" && path === "/order") {
      const text = await req.text();
      try {
        return new Response(order(text), { headers: { "Content-Type": "application/json" } });
      } catch (e) {
        return new Response(errorJSON(e), { status: 400, headers: { "Content-Type": "application/json" } });
      }
    }
    return new Response("not found", { status: 404 });
  },
});
