#!/bin/bash
# HTTPS: GET / over TLS with keep-alive, Vu (server.vu PORT CERT KEY) against Go (crypto/tls, raw HTTP
# handling), each on one core. A certificate for 127.0.0.1 is made for the run. Then resident memory
# with 1000 idle TLS connections.
#   bench/http/tls.sh
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
DUR=${DUR:-10s}
work=$(mktemp -d); trap 'rm -rf "$work"; kill $pid 2>/dev/null' EXIT
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$work/key.pem" -out "$work/cert.pem" -days 2 \
  -subj /CN=127.0.0.1 -addext subjectAltName=IP:127.0.0.1 2>/dev/null || exit 1
$VU build --release server.vu -o "$work/vu" || exit 1
(cd go && go build -o "$work/go" .) || exit 1
port=18443
for n in vu go; do
  if [ $n = vu ]; then cmd=("$work/vu" $port "$work/cert.pem" "$work/key.pem")
  else cmd=(env GOMAXPROCS=1 "$work/go" $port rawtls "$work/cert.pem" "$work/key.pem"); fi
  rates=()
  for run in 1 2 3; do
    taskset -c 0 "${cmd[@]}" >/dev/null 2>&1 & pid=$!
    sleep 0.5
    rates+=($(taskset -c 1-3 wrk -t2 -c50 -d$DUR https://127.0.0.1:$port/ 2>&1 | awk '/Requests\/sec/ {print int($2)}'))
    kill $pid; wait $pid 2>/dev/null
  done
  sorted=($(printf '%s\n' "${rates[@]}" | sort -n))
  printf '%-4s %6s req/s (runs: %s)\n' $n "${sorted[1]}" "${rates[*]}"
  "${cmd[@]}" >/dev/null 2>&1 & pid=$!
  sleep 0.5
  ulimit -n 4096
  python3 - $pid $port "$work/cert.pem" <<'PY'
import socket, ssl, sys, time
pid, port, ca = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rss = lambda: int([l for l in open(f'/proc/{pid}/status') if l.startswith('VmRSS')][0].split()[1])
ctx = ssl.create_default_context(cafile=ca)
ctx.check_hostname = False   # the certificate is for 127.0.0.1; Python checks the IP the same way
idle = rss()
conns = []
for _ in range(1000):
    s = ctx.wrap_socket(socket.create_connection(('127.0.0.1', port)))
    s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
    s.recv(200)
    conns.append(s)
time.sleep(0.3)
print(f'     idle {idle / 1024:.1f} MB, {(rss() - idle) / 1000:.1f} KB per idle TLS connection')
PY
  kill $pid; wait $pid 2>/dev/null
done
