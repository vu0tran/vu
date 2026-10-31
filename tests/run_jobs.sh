#!/bin/bash
# std/jobs against a real PostgreSQL (tests/jobs/main.vu). Skipped (and says so) without PostgreSQL.
# Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
bin=$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | tail -1)
sudo=""; [ "$(id -u)" = 0 ] || sudo="sudo -n"
if [ -z "$bin" ] || ! id postgres >/dev/null 2>&1 || ! $sudo true 2>/dev/null; then echo "0 passed, 0 failed (skipped: no PostgreSQL)"; exit 0; fi
work=$(mktemp -d); chmod 755 "$work"; data="$work/data"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
asp() { $sudo su postgres -s /bin/sh -c "$*"; }
mkdir "$data" "$work/sock"; $sudo chown postgres "$data" "$work/sock"
asp "$bin/initdb -D $data -U postgres --auth-local=trust --auth-host=scram-sha-256 >/dev/null"
printf 'local all postgres trust\nhost all all 127.0.0.1/32 scram-sha-256\n' | $sudo tee "$data/pg_hba.conf" >/dev/null
asp "$bin/pg_ctl -D $data -o '-p $port -k $work/sock -c listen_addresses=127.0.0.1' -l $data/log start -w >/dev/null"
trap 'asp "$bin/pg_ctl -D $data stop -m immediate >/dev/null"; $sudo rm -rf "$work"' EXIT
asp "psql -h $work/sock -p $port -U postgres -q -c \"create user app password 's3cret pass'\" -c 'create database appdb owner app' >/dev/null"
want='after the first pass: true, 20 waiting to be tried again
all done: true, 200 distinct, 0 twice
delayed: true
kinds: true mail attempt 1
lease: true then mail attempt 2
failed: true 0 waiting 1 failed, attempts 5, boom 5
retry_failed: 1, then attempt 1
transaction: 3,7, then not enough: -4'
pass=0; fail=0
for flags in "--release" "--san"; do
  if ! $VU build jobs/main.vu $flags -o "$work/jobs" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  got=$(timeout 300 "$work/jobs" "$port" 2>"$work/err"); rc=$?
  if [ "$got" = "$want" ] && [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then pass=$((pass+1)); echo "ok    jobs $flags"
  else fail=$((fail+1)); echo "FAIL  jobs $flags (exit $rc)"; diff <(echo "$want") <(echo "$got"); head -5 "$work/err"; fi
done
# std/migrate, in stages
m="$work/mig"
for flags in "--release" "--san"; do
  if ! $VU build jobs/migrations_test.vu $flags -o "$work/mig_bin" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build migrate $flags"; cat "$work/err"; continue; fi
  asp "psql -h $work/sock -p $port -U postgres -q -d appdb -c 'drop table if exists vu_migrations, mig_a, mig_b, mig_c, mig_d' >/dev/null 2>&1"
  rm -rf "$m"; mkdir "$m"
  echo 'create table mig_a (id int);' > "$m/001_a.sql"
  printf 'create table mig_b (id int);\ninsert into mig_b values (1), (2);\n' > "$m/002_b.sql"
  echo 'not sql' > "$m/README"
  got="$("$work/mig_bin" $port "$m" 2>&1)"
  got="$got;$("$work/mig_bin" $port "$m" 2>&1)"
  printf 'create table mig_c (id int);\nselect nonsense;\n' > "$m/003_c.sql"
  got="$got;$("$work/mig_bin" $port "$m" 2>&1)"
  echo 'create table mig_c (id int);' > "$m/003_c.sql"
  got="$got;$("$work/mig_bin" $port "$m" 2>&1)"
  echo 'create table mig_a (id bigint);' > "$m/001_a.sql"
  got="$got;$("$work/mig_bin" $port "$m" 2>&1)"
  echo 'create table mig_a (id int);' > "$m/001_a.sql"
  # two instances at once: one applies it, the other waits for the lock and finds it done
  printf 'select pg_sleep(1);\ncreate table mig_d (id int);\n' > "$m/004_d.sql"
  "$work/mig_bin" $port "$m" > "$work/m1" 2>&1 & p1=$!
  "$work/mig_bin" $port "$m" > "$work/m2" 2>&1 & p2=$!
  wait $p1 $p2
  both="$(sort "$work/m1" "$work/m2" | tr '\n' ' ')"
  want='applied [001_a.sql, 002_b.sql]
tables 2;applied []
tables 2;error: migrate: 003_c.sql: server: column "nonsense" does not exist (SQLSTATE 42703)
tables 2;applied [003_c.sql]
tables 3;error: migrate: 001_a.sql was applied and has changed since; add a new migration instead
tables 3'
  wantboth='applied [004_d.sql] applied [] tables 4 tables 4 '
  if [ "$got" = "$want" ] && [ "$both" = "$wantboth" ]; then pass=$((pass+1)); echo "ok    migrate $flags"
  else fail=$((fail+1)); echo "FAIL  migrate $flags"; diff <(echo "$want") <(echo "$got"); echo "both: [$both]"; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
