#!/bin/bash
# vlint against oxlint on AFFiNE (9c31663) with AFFiNE's own .oxlintrc.json (six JS plugins, type-aware
# rules), on the runner's cores: three alternating runs each, then vlint with 1..4 node processes.
set -u
W=$PWD/work; mkdir -p $W; cd $W
nproc; lscpu | grep -E "Model name|^CPU\(s\)|Thread"; node --version
git init -q affine && git -C affine fetch -q --depth 1 https://github.com/toeverything/AFFiNE.git 9c316636e0cb8f1b7f180306c5934e8ec81c71b7 && git -C affine checkout -q FETCH_HEAD
mkdir -p deps && cat > deps/package.json <<'J'
{"name":"deps","private":true,"dependencies":{"@typescript-eslint/parser":"8.72.1","@typescript-eslint/utils":"8.72.1","eslint":"9.39.5","eslint-plugin-import-x":"4.18.0","eslint-plugin-lit":"2.3.1","eslint-plugin-react":"7.37.5","eslint-plugin-react-hooks":"7.1.1","eslint-plugin-simple-import-sort":"14.0.0","eslint-plugin-sonarjs":"4.2.2","oxlint":"1.90.0","oxlint-tsgolint":"7.0.2006","typescript":"5.9.3"}}
J
(cd deps && npm install -s --legacy-peer-deps --no-audit --no-fund) || exit 1
ln -s $W/deps/node_modules affine/node_modules
OX=$W/deps/node_modules/.bin/oxlint
VL=$1
cd affine
cat > $W/tm.py <<'P'
import sys,time,subprocess,resource,json
name,out=sys.argv[1],sys.argv[2]; cmd=sys.argv[3:]
r0=resource.getrusage(resource.RUSAGE_CHILDREN); t=time.time()
with open(out,'wb') as o: p=subprocess.run(cmd,stdout=o,stderr=subprocess.DEVNULL)
w=time.time()-t; r1=resource.getrusage(resource.RUSAGE_CHILDREN)
try: n=len(json.load(open(out))['diagnostics'])
except Exception: n=-1
print(f"{name:12} wall {w:6.2f} s  cpu {r1.ru_utime-r0.ru_utime+r1.ru_stime-r0.ru_stime:7.2f} s  rss {r1.ru_maxrss//1024} MB  diagnostics {n}", flush=True)
P
echo "== warm-up (plugin installs, caches)"
python3 $W/tm.py oxlint /tmp/o.json $OX -f json; python3 $W/tm.py vlint /tmp/v.json $VL -f json
echo "== three runs each, alternating"
for i in 1 2 3; do python3 $W/tm.py oxlint /tmp/o.json $OX -f json; python3 $W/tm.py vlint /tmp/v$i.json $VL -f json; done
python3 - /tmp/v1.json /tmp/v2.json /tmp/v3.json <<'P'
import json,sys
k=[sorted(json.dumps(d,sort_keys=True) for d in json.load(open(f))['diagnostics']) for f in sys.argv[1:]]
print("vlint runs identical:", all(x==k[0] for x in k))
P
echo "== vlint with N node processes"
for n in 1 2 3 4; do VLINT_JS_PROCS=$n python3 $W/tm.py "vlint procs=$n" /tmp/p.json $VL -f json; done
