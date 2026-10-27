#!/bin/bash
# Multi-core HTTP: the server may use both cores (not pinned), against wrk with 2 threads, also
# unpinned. On a 2-core machine wrk takes a share of the same cores, so this shows how a server
# scales when it can run on more than one core, not its peak. Median of 3 runs of 10 s.
#   bench/http/mc.sh   (TEST=hello or json)
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
TEST=${TEST:-hello}
work=$(mktemp -d); trap 'rm -rf "$work"; kill $pid 2>/dev/null' EXIT
load=(); [ $TEST = json ] && load=(-s post.lua)
[ -f order.json ] || python3 gen_order.py >/dev/null
$VU build --release server.vu -o "$work/vu" || exit 1
$VU build --release server_std.vu -o "$work/vustd" || exit 1
(cd go && go build -o "$work/go" .) || exit 1
port=18081
run() {  # label, command...
  local label=$1; shift
  local rates=()
  for r in 1 2 3; do
    "$@" >/dev/null 2>&1 & pid=$!
    for _ in $(seq 100); do curl -s -o /dev/null localhost:$port/ && break; sleep 0.05; done
    wrk -t2 -c50 -d1s "${load[@]}" http://127.0.0.1:$port/ >/dev/null
    rates+=($(wrk -t2 -c50 -d10s "${load[@]}" http://127.0.0.1:$port/ | awk '/Requests\/sec/ {print int($2)}'))
    kill $pid; wait $pid 2>/dev/null
  done
  echo "$label: $(printf '%s\n' "${rates[@]}" | sort -n | sed -n 2p) req/s (runs: ${rates[*]})"
}
echo "TEST=$TEST"
run "vu, 1 thread " env VU_THREADS=1 "$work/vu" $port
run "vu, 2 threads" env VU_THREADS=2 "$work/vu" $port
run "vustd, 1 thread " env VU_THREADS=1 "$work/vustd" $port
run "vustd, 2 threads" env VU_THREADS=2 "$work/vustd" $port
run "go raw, GOMAXPROCS=1" env GOMAXPROCS=1 "$work/go" $port raw
run "go raw, GOMAXPROCS=2" env GOMAXPROCS=2 "$work/go" $port raw
run "go net/http, GOMAXPROCS=2" env GOMAXPROCS=2 "$work/go" $port http
