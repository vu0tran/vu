#!/usr/bin/env python3
"""Reads the benchmark's RESULT lines (from the loadgen service's log) and, for each run, the
memory and CPU Railway recorded for that service over the run's minutes, then prints a table and
what the run would cost a month at Railway's prices.
  metrics.py RESULTS_FILE STATUS_JSON     (RAILWAY_TOKEN: the project token)"""
import json, os, re, sys, urllib.request

API = "https://backboard.railway.com/graphql/v2"
CPU_MONTH, GB_MONTH = 20.0, 10.0   # Railway's prices: $ per vCPU and per GB of memory, a month

def gql(query, variables):
    req = urllib.request.Request(API, json.dumps({"query": query, "variables": variables}).encode(),
                                 {"Content-Type": "application/json", "Project-Access-Token": os.environ["RAILWAY_TOKEN"]})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"): raise RuntimeError(out["errors"][0].get("message"))
    return out["data"]

Q = """query($env: String!, $svc: String!, $start: DateTime!, $end: DateTime!) {
  metrics(environmentId: $env, serviceId: $svc, startDate: $start, endDate: $end,
          sampleRateSeconds: 10, measurements: [CPU_USAGE, MEMORY_USAGE_GB]) {
    measurement values { ts value } } }"""

def main():
    results = [dict(kv.split("=", 1) for kv in l.split()[1:]) for l in open(sys.argv[1]) if l.startswith("RESULT")]
    status = json.load(open(sys.argv[2]))
    env = status["environments"]["edges"][0]["node"]["id"] if "environments" in status else status["environment"]["id"]
    services = {}
    for e in status.get("services", {}).get("edges", []): services[e["node"]["name"]] = e["node"]["id"]
    rows = []
    for r in results:
        cpu = mem = None
        try:
            d = gql(Q, {"env": env, "svc": services[r["target"]], "start": r["start"], "end": r["end"]})
            for m in d["metrics"]:
                vals = [v["value"] for v in m["values"]]
                if not vals: continue
                if m["measurement"] == "CPU_USAGE": cpu = sum(vals) / len(vals)
                if m["measurement"] == "MEMORY_USAGE_GB": mem = max(vals)
        except Exception as e:
            print("metrics for %s: %s" % (r["target"], e), file=sys.stderr)
        rows.append((r, cpu, mem))
    print("| app | requests/s | p50 | p99 | errors | CPU (vCPU, mean) | memory (MB, peak) | $ a month at this load |")
    print("|---|---|---|---|---|---|---|---|")
    for r, cpu, mem in rows:
        cost = "" if cpu is None or mem is None else "%.2f" % (cpu * CPU_MONTH + mem * GB_MONTH)
        print("| %s | %s | %s ms | %s ms | %s | %s | %s | %s |" % (r["target"], r["rps"], r["p50_ms"], r["p99_ms"],
              int(r["errors"]) + int(r["non2xx3xx"]), "" if cpu is None else "%.2f" % cpu,
              "" if mem is None else "%.0f" % (mem * 1024), cost))

main()
