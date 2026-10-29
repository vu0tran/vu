#!/bin/bash
# For each target (vu, node, then each again, to even out anything that changes over the run): make
# 1,000 links through its API, warm it up for 10 s, then wrk with mix.lua (90% follows, 10% creates)
# at CONNS connections for SECONDS. Prints one RESULT line per run, with the times it started and
# ended (for the memory and CPU the workflow reads from Railway), then BENCH DONE.
CONNS=${CONNS:-64}; SECONDS_RUN=${SECONDS_RUN:-60}
declare -A url=([vu]=${VU_URL:-http://vu.railway.internal:8080} [node]=${NODE_URL:-http://node.railway.internal:8080})
for t in vu node; do
  for i in $(seq 120); do curl -sf -o /dev/null "${url[$t]}/health" && break; sleep 2; done
  curl -sf -o /dev/null "${url[$t]}/health" || { echo "BENCH FAILED: $t isn't answering at ${url[$t]}"; sleep infinity; }
done
for t in vu node vu node; do
  : > /tmp/codes.txt
  for i in $(seq 1000); do
    curl -s -X POST -H 'Content-Type: application/json' -d "{\"url\": \"https://example.com/$t/$i\"}" "${url[$t]}/links" |
      python3 -c 'import sys, json; print(json.load(sys.stdin)["code"])' >> /tmp/codes.txt
  done
  CODES=/tmp/codes.txt wrk -t2 -c$CONNS -d10s -s ${MIX:-/bench/mix.lua} "${url[$t]}" > /dev/null
  start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  r=$(CODES=/tmp/codes.txt wrk -t2 -c$CONNS -d${SECONDS_RUN}s -s ${MIX:-/bench/mix.lua} "${url[$t]}" | grep RESULT)
  end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "$r target=$t start=$start end=$end conns=$CONNS"
done
echo "BENCH DONE"
[ -n "$NO_SLEEP" ] || sleep infinity   # (Railway would restart a service that ends)
