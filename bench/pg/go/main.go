// Go's pgx (v5): the same three workloads as the other clients (bench/pg/run.sh). go build, then ./pgbench PORT
package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/jackc/pgx/v5"
)

func main() {
	ctx := context.Background()
	cfg, err := pgx.ParseConfig("postgres://bench:bench%20pw@127.0.0.1:" + os.Args[1] + "/bench")
	if err != nil {
		panic(err)
	}
	// PGX_MODE=exec: no prepared-statement cache (each query parsed and planned by the server, as Vu's pg
	// does); the default caches a prepared statement per SQL text
	if os.Getenv("PGX_MODE") == "exec" {
		cfg.DefaultQueryExecMode = pgx.QueryExecModeExec
	}
	c, err := pgx.ConnectConfig(ctx, cfg)
	if err != nil {
		panic(err)
	}
	t := time.Now()
	s := 0
	for i := 0; i < 20000; i++ {
		var id int32
		var name string
		var score float64
		if err := c.QueryRow(ctx, "select id, name, score from items where id = $1", i%100000+1).Scan(&id, &name, &score); err != nil {
			panic(err)
		}
		s += len(name)
	}
	point := time.Since(t).Seconds()
	t = time.Now()
	rows, err := c.Query(ctx, "select id, name, score, created from items where id <= 200000")
	if err != nil {
		panic(err)
	}
	n, count := 0, 0
	for rows.Next() {
		var id int32
		var name string
		var score float64
		var created time.Time
		if err := rows.Scan(&id, &name, &score, &created); err != nil {
			panic(err)
		}
		n += len(name)
		count++
	}
	if rows.Err() != nil {
		panic(rows.Err())
	}
	bulk := time.Since(t).Seconds()
	if _, err := c.Exec(ctx, "truncate log"); err != nil {
		panic(err)
	}
	t = time.Now()
	for i := 0; i < 10000; i++ {
		if _, err := c.Exec(ctx, "insert into log (id, msg) values ($1, $2)", i, fmt.Sprintf("message %d", i)); err != nil {
			panic(err)
		}
	}
	ins := time.Since(t).Seconds()
	fmt.Printf("point %.3f bulk %.3f insert %.3f (%d %d %d)\n", point, bulk, ins, s, n, count)
}
