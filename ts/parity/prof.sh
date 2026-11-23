#!/bin/zsh
# prof.sh VLINT PKG [SECS] [DELAY]: sample vlint on packages/PKG (one worker a program) with macOS
# sample; prints the busy thread's top functions by inclusive samples, then by self samples.
V=$1; P=$2; N=${3:-12}; W=${4:-5}
D=$HOME/.cache/vlint-parity/prof; mkdir -p $D
X=$D/xdg; rm -rf $X; mkdir -p $X/vlint; cp -R $HOME/.cache/vlint-parity/tslib $X/vlint/tslib-b82676463eea69ca
export PATH=/opt/homebrew/bin:$PATH
cd "${VLINT_CORPUS:?set VLINT_CORPUS to the folder linted (the root of a JS monorepo)}"
VTSC_SHARD_STATIC=1 VLINT_VTSC_BIGJ=1 VLINT_VTSC_CACHE=0 XDG_CACHE_HOME=$X $V --disable-nested-config -A typescript/no-misused-promises -f unix packages/$P > /dev/null 2>&1 &
pid=$!; sleep $W; /usr/bin/sample $pid $N -mayDie -file $D/$P.txt >/dev/null 2>&1; wait $pid
python3 -I - $D/$P.txt <<'PY'
import re,sys,collections
lines=open(sys.argv[1]).read().split('\n'); inc=collections.Counter(); stack=[]; busy=0
for l in lines:
    if l.startswith('Sort by'): break
    m=re.match(r'^[\s+!:|]*(\d+)\s+(\S+)',l)
    if not m: continue
    ind=len(l)-len(l.lstrip(' +!:|')); n=int(m.group(1)); fn=m.group(2)
    while stack and stack[-1][0]>=ind: stack.pop()
    names=[s[1] for s in stack]
    if fn=='fn_tsprog__run' and fn not in names: busy+=n
    if fn not in names: inc[fn]+=n
    stack.append((ind,fn))
print('busy (tsprog.run) samples', busy)
for f,n in inc.most_common(60):
    if f.startswith('fn_'): print(f'{n:7d} {100.0*n/max(1,busy):5.1f}% {f}')
PY
L=$(grep -n 'Sort by top of stack' $D/$P.txt | cut -d: -f1)
echo '--- self'
sed -n "$((L+1)),$((L+40))p" $D/$P.txt | grep -v 'kevent\|  read \|ulock\|psynch\|semaphore'
