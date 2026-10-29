#!/bin/bash
# The benchmark on this machine, before Railway: a throwaway PostgreSQL, the Vu and the Node app in
# turn, 1,000 links made through the API, then wrk with loadgen/mix.lua (90% follows, 10% creates) at 64
# connections for 20 s. Prints requests/s, latency, peak memory and CPU seconds for each.
# (Everything shares this machine's cores, so it checks the setup more than it measures.)
set -e
set -o pipefail
cd "$(dirname "$0")"
VU=${VU:-../../vu}
bin=$(ls -d /usr/lib/postgresql/*/bin | tail -1)
work=$(mktemp -d); chmod 755 "$work"; data="$work/data"
asp() { su postgres -s /bin/sh -c "$*"; }
mkdir "$data"; chown postgres "$data"
asp "$bin/initdb -D $data -U postgres --auth-host=scram-sha-256 >/dev/null"
printf 'local all all trust\nhost all all 127.0.0.1/32 scram-sha-256\n' > "$data/pg_hba.conf"
pgport=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
app=
asp "$bin/pg_ctl -D $data -o '-p $pgport -k /tmp -c listen_addresses=127.0.0.1 -c max_connections=100' -l $data/log start -w >/dev/null"
trap 'set +e; tail -5 "$work"/*.log; [ -n "$app" ] && kill $app; asp "$bin/pg_ctl -D $data stop -m immediate >/dev/null"; rm -rf "$work"' EXIT
asp "psql -h /tmp -p $pgport -U postgres -q -c \"create user app password 'bench pw'\" -c 'create database appdb owner app'"
export DATABASE_URL="postgresql://app:bench%20pw@127.0.0.1:$pgport/appdb" PORT=8099
$VU build vu/main.vu -o "$work/vu-app"
(cd node && npm install --silent >/dev/null 2>&1)
for which in vu node; do
  asp "psql -h /tmp -p $pgport -U postgres -d appdb -q -c 'drop table if exists links'"
  if [ $which = vu ]; then "$work/vu-app" > "$work/$which.log" 2>&1 & else node node/server.js > "$work/$which.log" 2>&1 & fi
  app=$!
  for i in $(seq 100); do curl -s -o /dev/null localhost:$PORT/health && break; sleep 0.1; done
  curl -s -i -X POST -H "Content-Type: application/json" -d "{\"url\": \"https://example.com/x\"}" localhost:$PORT/links | head -12
  : > "$work/codes.txt"
  for i in $(seq 1000); do curl -s -X POST -H 'Content-Type: application/json' -d "{\"url\": \"https://example.com/$i\"}" localhost:$PORT/links | python3 -c 'import sys,json; print(json.load(sys.stdin)["code"])' >> "$work/codes.txt"; done
  idle=$(awk '/VmRSS/ {print $2}' /proc/$app/status)
  t0=$(awk '{print $14 + $15}' /proc/$app/stat)
  r=$(CODES="$work/codes.txt" wrk -t2 -c64 -d20s -s loadgen/mix.lua http://localhost:$PORT | grep RESULT)
  t1=$(awk '{print $14 + $15}' /proc/$app/stat)
  peak=$(awk '/VmHWM/ {print $2}' /proc/$app/status)
  echo "$which: $r idle_rss_mb=$((idle / 1024)) peak_rss_mb=$((peak / 1024)) cpu_s=$(( (t1 - t0) / $(getconf CLK_TCK) ))"
  kill $app; wait $app 2>/dev/null || true
done
