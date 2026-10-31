import sys, time, psycopg
c = psycopg.connect(host="127.0.0.1", port=int(sys.argv[1]), user="bench", password="bench pw", dbname="bench", autocommit=True)
t = time.time(); s = 0
for i in range(20000):
    r = c.execute("select id, name, score from items where id = %s", (i % 100000 + 1,)).fetchone(); s += len(r[1])
point = time.time() - t
t = time.time(); rows = c.execute("select id, name, score, created from items where id <= 200000").fetchall(); n = sum(len(x[1]) for x in rows); bulk = time.time() - t
c.execute("truncate log"); t = time.time()
for i in range(10000): c.execute("insert into log (id, msg) values (%s, %s)", (i, "message %d" % i))
ins = time.time() - t
print("point %.3f bulk %.3f insert %.3f (%d %d %d)" % (point, bulk, ins, s, n, len(rows)))
