#!/bin/bash
# The PostgreSQL clients under concurrency: WORKERS tasks or goroutines share a pool of CONNS
# connections and run TOTAL point selects between them, one query per checkout (as web handlers do).
# Vu's pg (concurrent.vu) and Go's pgx with pgxpool (goconc/), against a throwaway PostgreSQL on a free
# port. Prints the best of RUNS (3) runs: queries a second, and the client's CPU time (user + system)
# per 1,000 queries, which the server then doesn't have.
#   bench/pg/concurrent.sh [WORKERS 50] [CONNS 10] [TOTAL 100000]
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
RUNS=${RUNS:-3}
W=${1:-50}; C=${2:-10}; T=${3:-100000}
bin=$(ls -d /usr/lib/postgresql/*/bin | tail -1)
sudo=""; [ "$(id -u)" = 0 ] || sudo="sudo -n"
work=$(mktemp -d); chmod 755 "$work"; data="$work/data"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
asp() { $sudo su postgres -s /bin/sh -c "$*"; }
mkdir "$data" "$work/sock"; $sudo chown postgres "$data" "$work/sock"
asp "$bin/initdb -D $data -U postgres --auth-local=trust --auth-host=scram-sha-256 >/dev/null"
printf 'local all postgres trust\nhost all all 127.0.0.1/32 scram-sha-256\n' | $sudo tee "$data/pg_hba.conf" >/dev/null
asp "$bin/pg_ctl -D $data -o '-p $port -k $work/sock -c listen_addresses=127.0.0.1 -c fsync=off -c synchronous_commit=off' -l $data/log start -w >/dev/null"
trap 'asp "$bin/pg_ctl -D $data stop -m immediate >/dev/null"; $sudo rm -rf "$work"' EXIT
asp "psql -h $work/sock -p $port -U postgres -q -c \"create user bench password 'bench pw'\" -c 'create database bench owner bench' >/dev/null"
asp "psql -h $work/sock -p $port -U postgres -q -d bench -c \"create table items (id int primary key, name text, score double precision, created timestamptz); insert into items select i, 'item number ' || i, i * 0.5, now() from generate_series(1, 200000) i; create table log (id int, msg text); alter table items owner to bench; alter table log owner to bench; analyze\" >/dev/null"
$VU build concurrent.vu -o "$work/vu" >/dev/null || exit 1
command -v go >/dev/null && (cd goconc && go build -o "$work/go" .)
best() {  # name, binary
  local out=""
  for r in $(seq "$RUNS"); do
    out="$out$( { TIMEFORMAT='%U %S'; time "$2" "$port" "$W" "$C" "$T" > "$work/out"; } 2>&1 ) $(cat "$work/out")"$'\n'
  done
  echo "$out" | python3 -c '
import sys
rows = []
for l in sys.stdin:
    p = l.split()
    if len(p) > 6: rows.append((float(p[7]), float(p[0]) + float(p[1]), p[-1]))
qps, cpu, check = max(rows)
n = int(sys.argv[2])
print("%-10s %8.0f queries/s   client CPU %5.2f ms per 1,000 queries   %s" % (sys.argv[1], qps, cpu / n * 1e6, check))' "$1" "$T"
}
echo "$W workers, a pool of $C connections, $T point selects"
best "vu pg" "$work/vu"
[ -x "$work/go" ] && best "go pgx" "$work/go"
