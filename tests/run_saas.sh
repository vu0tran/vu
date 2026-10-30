#!/bin/bash
# examples/saas against a real PostgreSQL, a fake Stripe and Resend, and moto's S3: a customer's whole
# path (tests/saas/client.py). Skipped (and says so) without PostgreSQL, or moto and boto3.
# Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
PY=${SAAS_PY:-python3}
bin=$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | tail -1)
sudo=""; [ "$(id -u)" = 0 ] || sudo="sudo -n"
if [ -z "$bin" ] || ! id postgres >/dev/null 2>&1 || ! $sudo true 2>/dev/null; then echo "0 passed, 0 failed (skipped: no PostgreSQL)"; exit 0; fi
if ! $PY -c 'import moto.server, boto3' 2>/dev/null; then echo "0 passed, 0 failed (skipped: no moto[server] and boto3)"; exit 0; fi
work=$(mktemp -d); chmod 755 "$work"; data="$work/data"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
asp() { $sudo su postgres -s /bin/sh -c "$*"; }
mkdir "$data" "$work/sock"; $sudo chown postgres "$data" "$work/sock"
asp "$bin/initdb -D $data -U postgres --auth-local=trust --auth-host=scram-sha-256 >/dev/null"
printf 'local all postgres trust\nhost all all 127.0.0.1/32 scram-sha-256\n' > "$data/pg_hba.conf"
asp "$bin/pg_ctl -D $data -o '-p $port -k $work/sock -c listen_addresses=127.0.0.1' -l $data/log start -w >/dev/null"
trap 'asp "$bin/pg_ctl -D $data stop -m immediate >/dev/null"; $sudo rm -rf "$work"' EXIT
asp "psql -h $work/sock -p $port -U postgres -q -c \"create user app password 's3cret pass'\" -c 'create database appdb owner app' >/dev/null"
pass=0; fail=0
for flags in "--release" "--san"; do
  asp "psql -h $work/sock -p $port -U postgres -q -d appdb -c 'drop table if exists users, vu_sessions' >/dev/null 2>&1"
  if ! $VU build ../examples/saas/main.vu $flags -o "$work/saas" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  if timeout 300 $PY saas/client.py "$work/saas" "postgresql://app:s3cret%20pass@127.0.0.1:$port/appdb" > "$work/res" 2>&1; then pass=$((pass+1)); echo "ok    $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  $flags"; tail -20 "$work/res"; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
