#!/bin/bash
# The HTTP benchmarks, with wrk: 50 keep-alive connections for 10 seconds.
#   TEST=hello  GET / -> "Hello, World!" (mostly measures the network path)
#   TEST=json   POST /order with order.json (5.8 KB): parse it, total it, reply with JSON
# Each server is pinned to one core and wrk to another, so every language gets the same single
# core. Before measuring, check.py confirms the server's answers (the JSON reply byte for byte).
# Each server runs 3 times; the report is the median run (by requests/second). On a 2-core machine
# wrk itself can be the limit for the fastest servers, so the report also gives the server's CPU
# use and requests per CPU-second: the work each server needs per request.
#   bench/http/run.sh [vu vustd vutree go goraw node bun noderaw bunraw]   (default: all that are installed)
# go/node/bun use each language's standard HTTP server; goraw/noderaw/bunraw do the same minimal
# HTTP handling as server.vu over plain TCP. The JSON work is each language's standard JSON.
cd "$(dirname "$0")" || exit 1
VU=${VU:-../../vu}
DUR=${DUR:-10s}
CONNS=${CONNS:-50}
TEST=${TEST:-hello}
work=$(mktemp -d); trap 'rm -rf "$work"; kill $pid 2>/dev/null' EXIT
names=("$@"); [ ${#names[@]} -eq 0 ] && names=(vu vustd vutree go goraw node bun noderaw bunraw)
case $TEST in
  hello) load=() ;;
  json)  load=(-s post.lua); [ -f order.json ] || python3 gen_order.py >/dev/null ;;
  *) echo "TEST is hello or json"; exit 1 ;;
esac
port=18080
ticks() { awk '{print $14 + $15}' /proc/$1/stat; }
ts=(node --no-warnings --experimental-strip-types)
echo "TEST=$TEST, $CONNS connections, $DUR"
for n in "${names[@]}"; do
  case $n in
    vu)      $VU build --release server.vu -o "$work/vu" || exit 1; cmd=("$work/vu" $port) ;;
    vutree)  $VU build --release server_tree.vu -o "$work/vutree" || exit 1; cmd=("$work/vutree" $port) ;;
    vustd)   $VU build --release server_std.vu -o "$work/vustd" || exit 1; cmd=("$work/vustd" $port) ;;
    go|goraw) command -v go >/dev/null || continue
             [ -x "$work/go" ] || (cd go && go build -o "$work/go" .) || exit 1
             mode=http; [ $n = goraw ] && mode=raw
             cmd=(env GOMAXPROCS=1 "$work/go" $port $mode) ;;
    node)    command -v node >/dev/null || continue; cmd=("${ts[@]}" ts/node_http.ts $port) ;;
    noderaw) command -v node >/dev/null || continue; cmd=("${ts[@]}" ts/raw.ts $port) ;;
    bun)     command -v bun >/dev/null || continue; cmd=(bun ts/bun.ts $port) ;;
    bunraw)  command -v bun >/dev/null || continue; cmd=(bun ts/raw.ts $port) ;;
    *)       echo "unknown server $n"; exit 1 ;;
  esac
  rates=()
  for run in 1 2 3; do
    taskset -c 0 "${cmd[@]}" >/dev/null 2>&1 & pid=$!
    for _ in $(seq 100); do curl -s -o /dev/null localhost:$port/ && break; sleep 0.05; done
    if [ $run = 1 ]; then
      c=$(python3 check.py $port) || { echo "$n: wrong answers: $c"; kill $pid; continue 2; }
    fi
    taskset -c 1 wrk -t1 -c$CONNS -d1s "${load[@]}" http://127.0.0.1:$port/ >/dev/null   # warm-up
    t0=$(ticks $pid); s0=$(date +%s.%N)
    out=$(taskset -c 1 wrk -t1 -c$CONNS -d$DUR --latency "${load[@]}" http://127.0.0.1:$port/)
    t1=$(ticks $pid); s1=$(date +%s.%N)
    kill $pid; wait $pid 2>/dev/null
    rate=$(echo "$out" | awk '/Requests\/sec/ {print int($2)}')
    p50=$(echo "$out" | awk '$1=="50%" {print $2}'); p99=$(echo "$out" | awk '$1=="99%" {print $2}')
    errs=$(echo "$out" | grep -E 'Socket errors|Non-2xx' | tr -s ' ' | tr '\n' ' ')
    # the server's CPU use (all its threads), as a share of the one core it has
    cpu=$(echo "$t0 $t1 $s0 $s1" | awk -v hz=$(getconf CLK_TCK) '{printf "%d", ($2-$1)/hz/($4-$3)*100}')
    eff=$(( rate * 100 / (cpu > 0 ? cpu : 1) ))
    rates+=("$rate $p50 $p99 $cpu $eff $errs")
  done
  read -r rate p50 p99 cpu eff errs <<< "$(printf '%s\n' "${rates[@]}" | sort -n | sed -n 2p)"
  all=$(printf '%s\n' "${rates[@]}" | awk '{printf "%s ", $1}')
  printf '%-8s %7s req/s  p50 %-9s p99 %-9s server CPU %3s%%  %7s req per CPU-second   runs: %s %s\n' \
    "$n" "$rate" "$p50" "$p99" "$cpu" "$eff" "$all" "$errs"
done
