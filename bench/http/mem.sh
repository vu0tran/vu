#!/bin/bash
# Memory of each benchmark server: resident memory when idle, peak during 5 s of the JSON test
# (50 connections), and the extra memory for 5000 open idle keep-alive connections.
#   bench/http/mem.sh [vu go goraw node bun noderaw bunraw]
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
work=$(mktemp -d); trap 'rm -rf "$work"; kill $pid 2>/dev/null' EXIT
names=("$@"); [ ${#names[@]} -eq 0 ] && names=(vu go goraw node bun noderaw bunraw)
port=18090
ts=(node --no-warnings --experimental-strip-types)
$VU build --release server.vu -o "$work/vu" || exit 1
(cd go && go build -o "$work/go" .) || exit 1
kb() { awk -v k="$2:" '$1==k {print $2}' /proc/$1/status; }
printf '%-8s %10s %14s %22s\n' server "idle MB" "JSON peak MB" "per idle conn (KB)"
for n in "${names[@]}"; do
  case $n in
    vu) cmd=("$work/vu" $port) ;;
    go) cmd=(env GOMAXPROCS=1 "$work/go" $port http) ;;
    goraw) cmd=(env GOMAXPROCS=1 "$work/go" $port raw) ;;
    node) cmd=("${ts[@]}" ts/node_http.ts $port) ;;
    noderaw) cmd=("${ts[@]}" ts/raw.ts $port) ;;
    bun) cmd=(bun ts/bun.ts $port) ;;
    bunraw) cmd=(bun ts/raw.ts $port) ;;
  esac
  "${cmd[@]}" >/dev/null 2>&1 & pid=$!
  for _ in $(seq 100); do curl -s -o /dev/null localhost:$port/ && break; sleep 0.05; done
  # env execs the program, so pid is the server itself
  sleep 0.5; idle=$(kb $pid VmRSS)
  wrk -t1 -c50 -d5s -s post.lua http://127.0.0.1:$port/ >/dev/null
  peak=$(kb $pid VmHWM)
  before=$(kb $pid VmRSS)
  python3 - "$port" <<'PY' &
import socket, sys, time
socks = []
for i in range(5000):
    s = socket.create_connection(('127.0.0.1', int(sys.argv[1])))
    s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
    socks.append(s)
for s in socks:
    s.recv(4096)
open('/tmp/vu_mem_ready', 'w').close()
time.sleep(4)
PY
  py=$!
  for _ in $(seq 200); do [ -f /tmp/vu_mem_ready ] && break; sleep 0.1; done
  sleep 0.5; after=$(kb $pid VmRSS)
  wait $py; rm -f /tmp/vu_mem_ready
  kill $pid; wait $pid 2>/dev/null
  printf '%-8s %10.1f %14.1f %22.1f\n' $n $(echo "$idle/1024" | bc -l) $(echo "$peak/1024" | bc -l) $(echo "($after-$before)/5000" | bc -l)
done
