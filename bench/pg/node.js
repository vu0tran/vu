const { Client } = require(process.env.PG_MODULE);
(async () => {
  const c = new Client({ host: "127.0.0.1", port: +process.argv[2], user: "bench", password: "bench pw", database: "bench" });
  await c.connect();
  let t = Date.now(), s = 0;
  for (let i = 0; i < 20000; i++) { const r = await c.query("select id, name, score from items where id = $1", [i % 100000 + 1]); s += r.rows[0].name.length; }
  const point = (Date.now() - t) / 1000;
  t = Date.now(); const rows = (await c.query("select id, name, score, created from items where id <= 200000")).rows; let n = 0; for (const x of rows) n += x.name.length; const bulk = (Date.now() - t) / 1000;
  await c.query("truncate log"); t = Date.now();
  for (let i = 0; i < 10000; i++) await c.query("insert into log (id, msg) values ($1, $2)", [i, "message " + i]);
  const ins = (Date.now() - t) / 1000;
  console.log(`point ${point.toFixed(3)} bulk ${bulk.toFixed(3)} insert ${ins.toFixed(3)} (${s} ${n} ${rows.length})`);
  await c.end();
})();
