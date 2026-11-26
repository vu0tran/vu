#!/bin/bash
# vlint (a new and an old build) against oxlint (1.90.0, the version this bench first used, and 1.79.0)
# on AFFiNE (9c31663) with AFFiNE's own .oxlintrc.json, cold (an empty vlint cache each run), with and
# without --type-aware, --threads = the runner's cores: three rounds alternated, then a perf profile of
# the new build's type-aware run.
#   bench/vlint_affine.sh NEW_VLINT OLD_VLINT [PERF_VLINT]     (writes everything under ./work and ./out)
set -u
NEW=$1; OLD=$2; PERFBIN=${3:-}
W=$PWD/work; OUT=$PWD/out; mkdir -p $W $OUT
P=$(nproc)
{ echo "cores $P"; lscpu | grep -E "Model name|^CPU\(s\)|Thread|Socket|MHz|L3"; free -g | head -2; uname -r; node --version; } | tee $OUT/runner.txt
cd $W
git init -q affine && git -C affine fetch -q --depth 1 https://github.com/toeverything/AFFiNE.git 9c316636e0cb8f1b7f180306c5934e8ec81c71b7 && git -C affine checkout -q FETCH_HEAD || exit 1

# AFFiNE's own dependencies (its types and its config's JS plugins), no install scripts
deps=affine
( cd affine && corepack enable >/dev/null 2>&1; export COREPACK_ENABLE_DOWNLOAD_PROMPT=0 ELECTRON_SKIP_BINARY_DOWNLOAD=1 PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 YARN_ENABLE_SCRIPTS=0;
  timeout 1200 yarn install --mode=skip-build > $OUT/yarn.txt 2>&1 ) || deps=bench
if [ $deps = bench ]; then
  echo "AFFiNE's yarn install failed (out/yarn.txt): the JS plugins from the bench's own list, no packages' types"
  tail -20 $OUT/yarn.txt
  mkdir -p bdeps && cat > bdeps/package.json <<'J'
{"name":"deps","private":true,"dependencies":{"@typescript-eslint/parser":"8.72.1","@typescript-eslint/utils":"8.72.1","eslint":"9.39.5","eslint-plugin-import-x":"4.18.0","eslint-plugin-lit":"2.3.1","eslint-plugin-react":"7.37.5","eslint-plugin-react-hooks":"7.1.1","eslint-plugin-simple-import-sort":"14.0.0","eslint-plugin-sonarjs":"4.2.2","typescript":"5.9.3"}}
J
  (cd bdeps && npm install -s --legacy-peer-deps --no-audit --no-fund) || exit 1
  rm -rf affine/node_modules; ln -s $W/bdeps/node_modules affine/node_modules
fi
echo "dependencies: $deps" | tee -a $OUT/runner.txt
du -sh affine/node_modules/ 2>/dev/null | tee -a $OUT/runner.txt

# each oxlint in its own folder with the tsgolint it asks for
for v in 1.90.0 1.79.0; do
  d=$W/ox-$v; mkdir -p $d
  tg=$(npm view oxlint@$v peerDependencies.oxlint-tsgolint 2>/dev/null)
  [ $v = 1.90.0 ] && tg=7.0.2006
  [ -n "$tg" ] || tg=latest
  echo "{\"name\":\"ox\",\"private\":true,\"dependencies\":{\"oxlint\":\"$v\",\"oxlint-tsgolint\":\"$tg\"}}" > $d/package.json
  (cd $d && npm install -s --no-audit --no-fund) || exit 1
  echo "oxlint $v: $($d/node_modules/.bin/oxlint --version), tsgolint $(node -p "require('$d/node_modules/oxlint-tsgolint/package.json').version")" | tee -a $OUT/runner.txt
done
cd affine
echo "== .oxlintrc.json options, plugins"
python3 - <<'P' | tee -a $OUT/runner.txt
import json,re
s=open('.oxlintrc.json').read()
try: c=json.loads(s)
except Exception: c=json.loads(re.sub(r'(?m)^\s*//.*$','',s))
print("options", c.get("options")); print("plugins", c.get("plugins")); print("jsPlugins", c.get("jsPlugins"))
P
find . -name node_modules -prune -o \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.mjs' -o -name '*.cjs' \) -print | wc -l | sed 's/^/source files /' | tee -a $OUT/runner.txt

# one run: /usr/bin/time -v, and the peak of the whole process tree's RSS sampled every 50 ms
cat > $W/tm.py <<'P'
import sys,os,subprocess,json,time
name,out,log=sys.argv[1],sys.argv[2],sys.argv[3]; env_extra=sys.argv[4]; cmd=sys.argv[5:]
env=dict(os.environ)
for kv in env_extra.split():
    k,v=kv.split('=',1); env[k]=v
def tree_rss(root):
    kids={}
    for p in os.listdir('/proc'):
        if not p.isdigit(): continue
        try:
            st=open(f'/proc/{p}/stat').read(); pp=int(st[st.rindex(')')+2:].split()[1]); kids.setdefault(pp,[]).append(int(p))
        except Exception: pass
    tot=0; todo=[root]
    while todo:
        q=todo.pop(); todo+=kids.get(q,[])
        try:
            for l in open(f'/proc/{q}/status'):
                if l.startswith('VmRSS:'): tot+=int(l.split()[1])
        except Exception: pass
    return tot
tf=out+'.time'
with open(out,'wb') as o, open(out+'.err','wb') as e:
    p=subprocess.Popen(['/usr/bin/time','-v','-o',tf]+cmd,stdout=o,stderr=e,env=env)
    peak=0
    while p.poll() is None:
        peak=max(peak,tree_rss(p.pid)); time.sleep(0.05)
t={}
for l in open(tf):
    if ': ' in l: k,v=l.strip().rsplit(': ',1); t[k]=v
w=t.get('Elapsed (wall clock) time (h:mm:ss or m:ss)','0'); wall=0
for x in w.split(':'): wall=wall*60+float(x)
cpu=float(t.get('User time (seconds)',0))+float(t.get('System time (seconds)',0))
rss=int(t.get('Maximum resident set size (kbytes)',0))//1024
try: n=len(json.load(open(out))['diagnostics'])
except Exception: n=-1
r=dict(name=name,wall=wall,user=float(t.get('User time (seconds)',0)),sys=float(t.get('System time (seconds)',0)),cpu=cpu,maxrss_mb=rss,tree_peak_mb=peak//1024,diagnostics=n,exit=p.returncode)
print(f"{name:22} wall {wall:7.2f} s  cpu {cpu:8.2f} s  maxrss {rss:6} MB  tree peak {peak//1024:6} MB  diagnostics {n:6}  exit {p.returncode}", flush=True)
open(log,'a').write(json.dumps(r)+'\n')
P
# AFFiNE's config sets options.typeAware: the plain mode runs with a copy without it (swapped in
# before each run), the type-aware mode with the config as it is and --type-aware
cp .oxlintrc.json $W/rc-ta.json
python3 -c '
import json,sys
c=json.load(open(sys.argv[1])); o=c.get("options") or {}; o.pop("typeAware",None); o.pop("typeCheck",None)
if o: c["options"]=o
else: c.pop("options",None)
json.dump(c,open(sys.argv[2],"w"),indent=2)' $W/rc-ta.json $W/rc-plain.json
CL=$W/cache   # vlint's cache, emptied before each run (cold)
run() { # NAME MODE(plain|ta) OUTFILE
  local name=$1 mode=$2 o=$3 ta="" env="XDG_CACHE_HOME=$CL"
  [ $mode = ta ] && ta=--type-aware
  cp $W/rc-$mode.json .oxlintrc.json
  rm -rf $CL; mkdir -p $CL
  case $name in
    vlint-new) python3 $W/tm.py "$name $mode" $o $OUT/runs.jsonl "$env" $NEW --threads=$P $ta -f json ;;
    vlint-old) python3 $W/tm.py "$name $mode" $o $OUT/runs.jsonl "$env" $OLD --threads=$P $ta -f json ;;
    oxlint-*) local v=${name#oxlint-}; python3 $W/tm.py "$name $mode" $o $OUT/runs.jsonl "$env OXLINT_TSGOLINT_PATH=$W/ox-$v/node_modules/.bin/tsgolint" $W/ox-$v/node_modules/.bin/oxlint --threads=$P $ta -f json ;;
  esac
}
TOOLS="oxlint-1.90.0 vlint-new vlint-old oxlint-1.79.0"
echo "== warm-up (each tool once, type-aware: the page cache, node's first start; not counted)"
: > $OUT/runs.jsonl
for m in ta; do for t in $TOOLS; do run $t $m $W/warm.json; tail -c 600 $W/warm.json.err | tail -3; done; done
mv $OUT/runs.jsonl $OUT/warmup.jsonl
echo "== three rounds, alternated"
for i in 1 2 3; do for m in plain ta; do for t in $TOOLS; do run $t $m $OUT/$t-$m-$i.json; done; done; done
python3 - $OUT/runs.jsonl <<'P' | tee $OUT/table.md
import json,sys,statistics as st
rs=[json.loads(l) for l in open(sys.argv[1])]
g={}
for r in rs: g.setdefault(r['name'],[]).append(r)
print("| tool | mode | wall s (median; runs) | cpu s (user+sys, median) | max RSS MB (one process) | tree peak RSS MB | diagnostics |")
print("|---|---|---|---|---|---|---|")
for k,v in g.items():
    t,m=k.split()
    ws=', '.join('%.2f' % x['wall'] for x in v)
    print(f"| {t} | {m} | {st.median(x['wall'] for x in v):.2f} ({ws}) | {st.median(x['cpu'] for x in v):.1f} | {max(x['maxrss_mb'] for x in v)} | {max(x['tree_peak_mb'] for x in v)} | {sorted(set(x['diagnostics'] for x in v))} |")
P
python3 - $OUT <<'P'
import json,sys,glob
for t in ['vlint-new','vlint-old','oxlint-1.90.0','oxlint-1.79.0']:
    for m in ['plain','ta']:
        k=[]
        for f in sorted(glob.glob(f"{sys.argv[1]}/{t}-{m}-*.json")):
            try: k.append(sorted(json.dumps(d,sort_keys=True) for d in json.load(open(f))['diagnostics']))
            except Exception: k.append(None)
        print(t,m,"runs identical:", all(x==k[0] for x in k))
P

echo "== why vtsc doesn't fully type files (the new build, VLINT_VTSC_DEBUG=2)"
cp $W/rc-ta.json .oxlintrc.json; rm -rf $CL; mkdir -p $CL
XDG_CACHE_HOME=$CL VLINT_VTSC_DEBUG=2 timeout 900 $NEW --threads=$P --type-aware -f json > /dev/null 2> $W/vtsc-debug.txt
gzip -c $W/vtsc-debug.txt > $OUT/vtsc-debug.txt.gz
grep -oE 'vtsc: (NOLINT|RULEWHY)' $W/vtsc-debug.txt | sort | uniq -c
grep -c 'NOLINT .*(type errors)' $W/vtsc-debug.txt | sed 's/^/NOLINT for type errors: /'
grep 'NOLINT' $W/vtsc-debug.txt | head -5

if [ -n "$PERFBIN" ] && command -v perf >/dev/null && perf --version >/dev/null 2>&1; then
  echo "== perf: the new build (frame pointers, -g) type-aware, cold"
  cp $W/rc-ta.json .oxlintrc.json; rm -rf $CL; mkdir -p $CL
  XDG_CACHE_HOME=$CL perf record -F 499 -g -o $W/perf.data -- $PERFBIN --threads=$P --type-aware -f json > $W/perf-out.json 2> $OUT/perf-record.txt
  echo "exit $? (vlint exits 1 with errors)"
  if ! grep -q "Captured and wrote" $OUT/perf-record.txt; then
    rm -rf $CL; mkdir -p $CL
    XDG_CACHE_HOME=$CL perf record -e cpu-clock -F 499 -g -o $W/perf.data -- $PERFBIN --threads=$P --type-aware -f json > $W/perf-out.json 2>> $OUT/perf-record.txt
  fi
  grep -E "perf record|event" $OUT/perf-record.txt
  R="timeout 900 perf report -i $W/perf.data --stdio"
  $R --no-children -g none --sort sym --percent-limit 0.05 2>/dev/null | grep -v '^#' | grep -v '^$' | head -40 > $OUT/perf-top40-self.txt
  $R --no-children -g none --comm vlint-perf --sort sym --percent-limit 0.01 2>/dev/null | grep -v '^#' | grep -v '^$' | head -40 > $OUT/perf-top40-self-vlint.txt
  $R --no-children -g none --sort comm,dso 2>/dev/null | grep -v '^#' | grep -v '^$' | head -30 > $OUT/perf-by-dso.txt
  $R --children --comm vlint-perf -g none --sort sym --percent-limit 0.5 2>/dev/null | grep -v '^#' | grep -v '^$' | head -60 > $OUT/perf-top-inclusive-vlint.txt
  timeout 1500 perf script -i $W/perf.data 2>/dev/null | python3 -c '
import sys,collections
c=collections.Counter(); comm=None; fr=[]
def flush():
    if comm is not None: c[";".join([comm]+fr[::-1])]+=1
for l in sys.stdin:
    if not l.strip():
        flush(); comm=None; fr=[]; continue
    if not l[0].isspace():
        comm=l.split()[0]; fr=[]; continue
    p=l.strip().split(None,1)
    s=p[1] if len(p)>1 else "?"
    s=s.rsplit(" (",1)[0]
    if "+0x" in s: s=s[:s.rindex("+0x")]
    fr.append(s.replace(";",":") or "?")
flush()
for k,v in c.most_common(): print(k,v)
' | gzip > $OUT/perf-folded.txt.gz
  ls -l $OUT/perf-*
  echo "self time, top 40:"; cat $OUT/perf-top40-self.txt; echo "vlint's own process, self, top 40:"; cat $OUT/perf-top40-self-vlint.txt; echo "by command and object:"; cat $OUT/perf-by-dso.txt
else
  echo "== perf: not available, skipped" | tee $OUT/perf-skipped.txt
fi
