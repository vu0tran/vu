#!/bin/bash
# The auth module: password hashes against Django's (Django itself when it's importable, else hashlib in
# Django's format), malformed hashes, tokens, CSRF and the session cookie; then sessions in a real
# PostgreSQL (skipped, and says so, without one). Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
PY=${AUTH_PY:-python3}
work=$(mktemp -d); chmod 755 "$work"
pass=0; fail=0
ok() { pass=$((pass+1)); echo "ok    $1"; }
no() { fail=$((fail+1)); echo "FAIL  $1"; }
$PY auth/model.py make "$work/h" "${SEED:-$RANDOM}"
for flags in "--release" "--san"; do
  if ! $VU build auth/hashes.vu $flags -o "$work/hashes" 2>"$work/err"; then no "build hashes $flags"; cat "$work/err"; continue; fi
  if "$work/hashes" "$work/h" 2>"$work/err" > "$work/out" && $PY auth/model.py check "$work/h" < "$work/out" > "$work/res"; then ok "password hashes $flags ($(tail -1 "$work/res"))"
  else no "password hashes $flags"; cat "$work/res" | head; head -5 "$work/err"; fi
  want='tokens true
header true
form true
wrong false
other session false
other secret false
missing false
Set-Cookie: session=tok; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax
Set-Cookie: session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax
cookie abc'
  if ! $VU build auth/units.vu $flags -o "$work/units" 2>"$work/err"; then no "build units $flags"; cat "$work/err"; continue; fi
  got=$("$work/units" 2>"$work/err")
  if [ "$got" = "$want" ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then ok "tokens, CSRF, cookie $flags"
  else no "tokens, CSRF, cookie $flags"; diff <(echo "$want") <(echo "$got"); head -5 "$work/err"; fi
done
bin=$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | tail -1)
# as root (the gate) or with sudo (CI runners)
sudo=""; [ "$(id -u)" = 0 ] || sudo="sudo -n"
if [ -z "$bin" ] || ! id postgres >/dev/null 2>&1 || ! $sudo true 2>/dev/null; then echo "sessions skipped: no PostgreSQL"; echo "$pass passed, $fail failed"; rm -rf "$work"; [ $fail -eq 0 ]; exit; fi
data="$work/data"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
asp() { $sudo su postgres -s /bin/sh -c "$*"; }
mkdir "$data" "$work/sock"; $sudo chown postgres "$data" "$work/sock"
asp "$bin/initdb -D $data -U postgres --auth-local=trust --auth-host=scram-sha-256 >/dev/null"
printf 'local all postgres trust\nhost all all 127.0.0.1/32 scram-sha-256\n' > "$data/pg_hba.conf"
asp "$bin/pg_ctl -D $data -o '-p $port -k $work/sock -c listen_addresses=127.0.0.1' -l $data/log start -w >/dev/null"
trap 'asp "$bin/pg_ctl -D $data stop -m immediate >/dev/null"; $sudo rm -rf "$work"' EXIT
asp "psql -h $work/sock -p $port -U postgres -q -c \"create user app password 's3cret pass'\" -c 'create database appdb owner app' >/dev/null"
want='t1 42
raw token stored 0
unknown nil short nil empty nil
expired nil
pruned 1
t2 42
after logout_all nil nil
current user-9
after logout nil
no cookie nil
left 0'
for flags in "--release" "--san"; do
  if ! $VU build auth/sessions.vu $flags -o "$work/sessions" 2>"$work/err"; then no "build sessions $flags"; cat "$work/err"; continue; fi
  got=$("$work/sessions" "$port" 2>"$work/err"); rc=$?
  if [ "$got" = "$want" ] && [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/err"; then ok "sessions in PostgreSQL $flags"
  else no "sessions in PostgreSQL $flags (exit $rc)"; diff <(echo "$want") <(echo "$got"); head -5 "$work/err"; fi
done
# the app `vu new api` makes, against the same database, driven over HTTP
app=../compiler/rt/new_api/main.vu
for flags in "--release" "--san"; do
  asp "psql -h $work/sock -p $port -U postgres -q -d appdb -c 'drop table if exists notes, users, vu_sessions' >/dev/null"
  if ! $VU build $app $flags -o "$work/api" 2>"$work/err"; then no "build the api template $flags"; cat "$work/err"; continue; fi
  aport=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  PORT=$aport DATABASE_URL="postgresql://app:s3cret%20pass@127.0.0.1:$port/appdb" "$work/api" > "$work/api.out" 2> "$work/api.err" &
  apid=$!
  for i in $(seq 100); do python3 -c "import socket; socket.create_connection(('127.0.0.1', $aport), 0.2)" 2>/dev/null && break; sleep 0.1; done
  python3 auth/api_client.py $aport > "$work/client" 2>&1; rc=$?
  # a hash with fewer iterations (from an older app, or Django's older defaults) is made again at sign-in
  old=$(python3 -c 'import base64, hashlib; print("pbkdf2_sha256$1000$oldsalt$" + base64.b64encode(hashlib.pbkdf2_hmac("sha256", b"an old password", b"oldsalt", 1000)).decode())')
  asp "psql -h $work/sock -p $port -U postgres -q -d appdb -c \"insert into users (email, password_hash) values ('old@example.com', '${old//\$/\\\$}')\" >/dev/null"
  st=$(python3 -c "import http.client, json; c = http.client.HTTPConnection('127.0.0.1', $aport); c.request('POST', '/login', json.dumps({'email': 'old@example.com', 'password': 'an old password'})); print(c.getresponse().status)")
  now=$(asp "psql -h $work/sock -p $port -U postgres -d appdb -tA -c \"select password_hash from users where email = 'old@example.com'\"")
  if [ "$st" = 200 ] && [[ "$now" == pbkdf2_sha256\$600000\$* ]] && python3 -c "
import base64, hashlib, sys; a, n, salt, h = sys.argv[1].split('\$')
sys.exit(base64.b64encode(hashlib.pbkdf2_hmac('sha256', b'an old password', salt.encode(), int(n))).decode() != h)" "$now"; then :
  else rc=1; echo "FAIL  rehash at sign-in: status $st, stored [$now]" >> "$work/client"; fi
  kill $apid; wait $apid 2>/dev/null
  if [ $rc -eq 0 ] && ! grep -q 'ERROR\|runtime error' "$work/api.err"; then ok "the api template $flags ($(tail -1 "$work/client"))"
  else no "the api template $flags"; cat "$work/client" | head -20; grep -v '^20' "$work/api.err" | head -10; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
