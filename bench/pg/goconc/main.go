// bench/pg concurrent, in Go with pgx's pool: WORKERS goroutines share a pool of CONNS connections and
// run TOTAL point selects between them, one query per acquire (as a web handler does).
//   goconc PORT [WORKERS 50] [CONNS 10] [TOTAL 100000]
package main

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func arg(i, def int) int {
	if len(os.Args) > i {
		if v, err := strconv.Atoi(os.Args[i]); err == nil {
			return v
		}
	}
	return def
}

func main() {
	ctx := context.Background()
	workers, conns, total := arg(2, 50), arg(3, 10), arg(4, 100000)
	cfg, err := pgxpool.ParseConfig("postgres://bench:bench%20pw@127.0.0.1:" + os.Args[1] + "/bench")
	if err != nil {
		panic(err)
	}
	cfg.MaxConns, cfg.MinConns = int32(conns), int32(conns)
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		panic(err)
	}
	// the connections open before the clock starts, as Vu's pg.pool does
	for pool.Stat().TotalConns() < int32(conns) {
		time.Sleep(10 * time.Millisecond)
	}
	var wg sync.WaitGroup
	sums := make([]int, workers)
	t := time.Now()
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			start, n := w*7919, total/workers
			for i := 0; i < n; i++ {
				var id int32
				var name string
				var score float64
				if err := pool.QueryRow(ctx, "select id, name, score from items where id = $1", (start+i)%100000+1).Scan(&id, &name, &score); err != nil {
					panic(err)
				}
				sums[w] += len(name)
			}
		}(w)
	}
	wg.Wait()
	secs := time.Since(t).Seconds()
	sum := 0
	for _, s := range sums {
		sum += s
	}
	fmt.Printf("queries %d secs %.3f qps %.0f (%d)\n", total, secs, float64(total)/secs, sum)
}
