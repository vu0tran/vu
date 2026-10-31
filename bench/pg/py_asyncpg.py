import asyncio, sys, time, asyncpg
async def main():
    c = await asyncpg.connect(host="127.0.0.1", port=int(sys.argv[1]), user="bench", password="bench pw", database="bench")
    t = time.time(); s = 0
    for i in range(20000):
        r = await c.fetchrow("select id, name, score from items where id = $1", i % 100000 + 1); s += len(r["name"])
    point = time.time() - t
    t = time.time(); rows = await c.fetch("select id, name, score, created from items where id <= 200000"); n = sum(len(x["name"]) for x in rows); bulk = time.time() - t
    await c.execute("truncate log"); t = time.time()
    for i in range(10000): await c.execute("insert into log (id, msg) values ($1, $2)", i, "message %d" % i)
    ins = time.time() - t
    print("point %.3f bulk %.3f insert %.3f (%d %d %d)" % (point, bulk, ins, s, n, len(rows)))
asyncio.run(main())
