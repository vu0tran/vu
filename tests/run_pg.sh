#!/bin/bash
# The pg module against a real PostgreSQL server: a throwaway cluster (initdb) on a free port, with a
# SCRAM-SHA-256 user and one with a plain password. Skipped (and says so) if PostgreSQL isn't installed.
# Runs the client plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
bin=$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | tail -1)
# as root (the gate) or with sudo (CI runners)
sudo=""; [ "$(id -u)" = 0 ] || sudo="sudo -n"
if [ -z "$bin" ] || ! id postgres >/dev/null 2>&1 || ! $sudo true 2>/dev/null; then echo "0 passed, 0 failed (skipped: no PostgreSQL)"; exit 0; fi
work=$(mktemp -d); chmod 755 "$work"; data="$work/data"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
asp() { $sudo su postgres -s /bin/sh -c "$*"; }
mkdir "$data" "$work/sock"; $sudo chown postgres "$data" "$work/sock"
echo "s3cret pass" > "$work/pw"; chmod 644 "$work/pw"
asp "$bin/initdb -D $data -U postgres --auth-local=trust --auth-host=scram-sha-256 >/dev/null"
printf 'local all postgres trust\nhost all plain 127.0.0.1/32 password\nhost all all 127.0.0.1/32 scram-sha-256\n' | $sudo tee "$data/pg_hba.conf" >/dev/null
asp "$bin/pg_ctl -D $data -o '-p $port -k $work/sock -c listen_addresses=127.0.0.1' -l $data/log start -w >/dev/null"
trap 'asp "$bin/pg_ctl -D $data stop -m immediate >/dev/null"; [ -n "$KEEP" ] || $sudo rm -rf "$work"' EXIT
asp "psql -h $work/sock -p $port -U postgres -q -c \"create user app password 's3cret pass'\" -c \"create user plain password 'plainpw'\" -c 'create database appdb owner app' >/dev/null"
want='connected
n, t, z = 42,héllo wörld 中,NULL
inserted 2
1,ann;2,bob;3,x'"'"'); drop table users; -- / 3 rows
error 23505: duplicate key value violates unique constraint "users_pkey"
server: column "nope" does not exist (SQLSTATE 42703)
t,x x
1 ann a,b
5000 rows, sum 12502500
3000000 bytes
refused: server: password authentication failed for user "app" (SQLSTATE 28P01)
refused: sign-in: the server asks for the password in clear text; pg sends it only with allow_plain set in the config (use SCRAM-SHA-256 on the server instead)
plain'
pass=0; fail=0
for flags in "" "--san"; do
  asp "psql -h $work/sock -p $port -U postgres -q -d appdb -c 'drop table if exists users' >/dev/null 2>&1"
  if ! $VU build pg/basic.vu $flags -o "$work/basic" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  got=$("$work/basic" "$port" 2>"$work/err"); rc=$?
  if [ "$got" = "$want" ] && [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then pass=$((pass+1)); echo "ok    pg/basic.vu ${flags:-optimized}"
  else fail=$((fail+1)); echo "FAIL  pg/basic.vu ${flags:-optimized} (exit $rc)"; diff <(echo "$want") <(echo "$got") | head -20; head -5 "$work/err"; fi
done
# typed rows (pg/typed.vu prints what it found; the comparisons are inside it)
TYPED_WANT='rows 300, 0 different
short 3 2 true
none 0
one  5
missing true
returning 2 new b
update 2 new a!
wrong type: [0].id: expected a string at byte 7
missing column: missing field '"'"'name'"'"' at byte 8
bad sql: server: column "nope" does not exist (SQLSTATE 42703)'

for flags in "" "--san"; do
  if ! $VU build pg/typed.vu $flags -o "$work/typed" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build typed $flags"; cat "$work/err"; continue; fi
  got=$("$work/typed" "$port" 2>"$work/err"); rc=$?
  echo "$got" > "$work/typed.out"
  if [ "$got" = "$TYPED_WANT" ] && [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then pass=$((pass+1)); echo "ok    pg/typed.vu ${flags:-optimized}"
  else fail=$((fail+1)); echo "FAIL  pg/typed.vu ${flags:-optimized} (exit $rc)"; diff <(echo "$TYPED_WANT") <(echo "$got") | head -20; head -5 "$work/err"; fi
done
NOTIFY_WANT='none | events:hello é 😀 | 42 | events:one | Other_2:two | none | none | events:committed | none | 1000 in order | protocol: a channel'"'"'s name is letters, digits and _, not '"'"'bad name; drop table x'"'"''
COPY_WANT='loaded 100000, read 100000, 0 different | protocol: a value contains a zero byte, which PostgreSQL text can'"'"'t hold | count 100000 | server: duplicate key value violates unique constraint "copied_pkey" (Key (id)=(5) already exists., SQLSTATE 23505) | count 100000 | protocol: the statement isn'"'"'t COPY ... FROM STDIN | id,name/1,tab	here 1/2,"new/line 2"/10,/'
for flags in "" "--san"; do
  if ! $VU build pg/copy.vu $flags -o "$work/copy" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build copy $flags"; cat "$work/err"; continue; fi
  got=$("$work/copy" "$port" 2>"$work/err"); rc=$?
  if [ "$got" = "$COPY_WANT" ] && [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then pass=$((pass+1)); echo "ok    pg/copy.vu ${flags:-optimized} ($(grep 'copy of' "$work/err"))"
  else fail=$((fail+1)); echo "FAIL  pg/copy.vu ${flags:-optimized} (exit $rc)"; diff <(echo "$COPY_WANT") <(echo "$got") | head -20; head -5 "$work/err"; fi
done
for flags in "" "--san"; do
  if ! $VU build pg/notify.vu $flags -o "$work/notify" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build notify $flags"; cat "$work/err"; continue; fi
  got=$("$work/notify" "$port" 2>"$work/err"); rc=$?
  if [ "$got" = "$NOTIFY_WANT" ] && [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then pass=$((pass+1)); echo "ok    pg/notify.vu ${flags:-optimized}"
  else fail=$((fail+1)); echo "FAIL  pg/notify.vu ${flags:-optimized} (exit $rc)"; diff <(echo "$NOTIFY_WANT") <(echo "$got") | head -20; head -5 "$work/err"; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
