# Vu against Node on Railway

The same backend twice: a URL shortener on PostgreSQL. `vu/main.vu` uses Vu's `web` and `pg`
modules. `node/server.js` uses Express and node-postgres, the stack an AI agent usually picks for a
Node backend. Both have a pool of 10 database connections, the same SQL and the same JSON.

`loadgen/` runs inside the Railway project, so the load goes over Railway's private network, not
the internet. For each app in turn (Vu, Node, then each again), it makes 1,000 links and warms up
for 10 s. Then it runs wrk for 60 s at 64 connections: 90% of requests follow a link (an
`UPDATE ... RETURNING`) and 10% create one (an `INSERT`). The workflow reads each app's CPU and
memory over its runs from Railway's metrics API, and works out the monthly cost at Railway's
prices ($20 per vCPU and $10 per GB of memory a month).

## Setting it up (once)

1. In Railway, make a project with a PostgreSQL database (keep its name, `Postgres`) and three
   empty services named `vu`, `node` and `loadgen`.
2. Make a project token (Project settings > Tokens) and add it to the GitHub repository as the
   secret `RAILWAY_TOKEN`.
3. Run the workflow: Actions > bench-railway > Run workflow. The table lands in the run's summary.

It runs on the Hobby plan. One run takes about 10 to 15 minutes, with three small services and a database.

## On this machine first

`local.sh` runs the two apps one after the other against a throwaway PostgreSQL, with wrk on the
same 2 cores. That checks the setup; it isn't the measurement. On 2026-10-29 it gave:

| app | requests/s | p50 | p99 | memory (peak) | CPU seconds |
|---|---|---|---|---|---|
| Vu | 7,093 | 8.1 ms | 47.3 ms | 5 MB | 5 |
| Node (Express) | 3,689 | 15.4 ms | 47.2 ms | 138 MB | 17 |
