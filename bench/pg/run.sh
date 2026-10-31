#!/bin/bash
# The PostgreSQL clients compared on one machine: Vu's pg, Python's asyncpg and psycopg 3, and Node's
# pg (node-postgres), against a throwaway PostgreSQL on a free port. Each prints seconds for 20,000
# point selects, one 200,000-row select, and 10,000 inserts; the best of RUNS (3) runs is kept.
#   PY=path/to/python-with-asyncpg-and-psycopg NODE_PG=path/to/node_modules/pg bench/pg/run.sh
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
PY=${PY:-python3}
RUNS=${RUNS:-3}
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
$VU build vu.vu -o "$work/vu" >/dev/null || exit 1
best() {  # name, command...
  local name=$1; shift
  local out=""
  for r in $(seq "$RUNS"); do out="$out$("$@" "$port")"$'\n'; done
  echo "$out" | python3 -c '
import sys
runs = [l.split() for l in sys.stdin if l.startswith("point")]
b = [min(float(r[i]) for r in runs) for i in (1, 3, 5)]
print("%-18s point %6.3f s   bulk %6.3f s   insert %6.3f s" % (sys.argv[1], *b))' "$name"
}
best "vu pg" "$work/vu"
$PY -c 'import asyncpg' 2>/dev/null && best "python asyncpg" "$PY" py_asyncpg.py
$PY -c 'import psycopg' 2>/dev/null && best "python psycopg 3" "$PY" py_psycopg.py
[ -n "$NODE_PG" ] && PG_MODULE="$NODE_PG" best "node pg" node node.js
