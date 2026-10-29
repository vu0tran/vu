// The same URL shortener as ../vu/main.vu, written the way an AI agent usually writes a Node
// backend: Express, node-postgres (pg) with a pool of 10, one process.
const express = require("express");
const crypto = require("crypto");
const { Pool } = require("pg");

const ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 10 });
const app = express();
app.use(express.json());

function newCode() {
  return Array.from(crypto.randomBytes(7), (b) => ALPHABET[b % 62]).join("");
}

app.get("/health", (req, res) => res.json({ ok: true }));

app.post("/links", async (req, res) => {
  const url = req.body && req.body.url;
  if (typeof url !== "string" || !/^https?:\/\//.test(url) || Buffer.byteLength(url) > 2048) {
    return res.status(400).json({ error: "url must be http(s) and at most 2048 bytes" });
  }
  try {
    for (let tries = 0; tries < 5; tries++) {
      const code = newCode();
      const r = await pool.query("insert into links (code, url) values ($1, $2) on conflict do nothing", [code, url]);
      if (r.rowCount === 1) return res.status(201).json({ code, url });
    }
    res.status(500).json({ error: "couldn't make a code" });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get("/links/:code", async (req, res) => {
  try {
    const r = await pool.query("select url, hits from links where code = $1", [req.params.code]);
    if (r.rowCount !== 1) return res.status(404).json({ error: "no such link" });
    res.json({ code: req.params.code, url: r.rows[0].url, hits: Number(r.rows[0].hits) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get("/:code", async (req, res) => {
  try {
    const r = await pool.query("update links set hits = hits + 1 where code = $1 returning url", [req.params.code]);
    if (r.rowCount !== 1) return res.status(404).json({ error: "no such link" });
    res.redirect(302, r.rows[0].url);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

async function main() {
  await pool.query("create table if not exists links (code text primary key, url text not null, hits bigint not null default 0, created_at timestamptz not null default now())");
  const port = Number(process.env.PORT) || 8080;
  app.listen(port, () => console.log(`listening on port ${port}`));
}
main().catch((e) => { console.error(e); process.exit(1); });
