#!/bin/zsh
# profall.sh VLINT [SECS] [DELAY] [ENV=...]: macOS sample of a cold run on all of the corpus ($VLINT_CORPUS), the
# type-aware programs kept in vlint's process (no worker processes: VLINT_VTSC_SUB=0 VTSC_FORK=0) so
# the sample sees every program. Writes the call tree to ~/.cache/vlint-parity/prof/all.txt and
# prints the inclusive share of the type-aware part's phases and of each type-aware rule.
V=$1; N=${2:-60}; W=${3:-4}; shift; [ $# -gt 0 ] && shift; [ $# -gt 0 ] && shift
D=$HOME/.cache/vlint-parity/prof; mkdir -p $D
X=$D/xdg_all; rm -rf $X; mkdir -p $X/vlint; cp -R $HOME/.cache/vlint-parity/tslib $X/vlint/tslib-b82676463eea69ca
export PATH=/opt/homebrew/bin:$PATH
cd "${VLINT_CORPUS:?set VLINT_CORPUS to the folder linted (the root of a JS monorepo)}"
env "$@" VLINT_VTSC_SUB=0 VTSC_FORK=0 VTSC_SHARD_STATIC=1 VLINT_VTSC_CACHE=0 XDG_CACHE_HOME=$X $V --disable-nested-config -A typescript/no-misused-promises -f unix > /dev/null 2>&1 &
pid=$!; sleep $W; /usr/bin/sample $pid $N -mayDie -file $D/all.txt >/dev/null 2>&1; wait $pid
python3 -I - $D/all.txt <<'PY'
import re,sys,collections
lines=open(sys.argv[1]).read().split('\n'); inc=collections.Counter(); stack=[]
for l in lines:
    if l.startswith('Sort by'): break
    m=re.match(r'^[\s+!:|]*(\d+)\s+(\S+)',l)
    if not m: continue
    ind=len(l)-len(l.lstrip(' +!:|')); n=int(m.group(1)); fn=m.group(2)
    while stack and stack[-1][0]>=ind: stack.pop()
    names=[s[1] for s in stack]
    if fn not in names: inc[fn]+=n
    stack.append((ind,fn))
tot=max(1,inc['fn_tsprog__run_libs'])
print('type-aware samples (tsprog.run_libs)', tot)
for key in ['fn_parse__parse_file_x','fn_chk__check_file','fn_trules__run','fn_chk__declare_only','fn_chk__check_declarations','fn_tsprog__file_keys','fn_chk__global_conflicts']:
    print(f'{inc[key]:8d} {100*inc[key]/tot:5.1f}% {key}')
print('--- type-aware rules, inclusive (>0.4%)')
for f,n in inc.most_common(4000):
    if (f.startswith('fn_trules2__') or f.startswith('fn_trules__')) and n>tot*0.004: print(f'{n:8d} {100*n/tot:5.1f}% {f}')
print('--- checker, inclusive (>3%)')
for f,n in inc.most_common(200):
    if (f.startswith('fn_chk__') or f.startswith('fn_rel__') or f.startswith('fn_bind__') or f.startswith('fn_tyops__')) and n>tot*0.03: print(f'{n:8d} {100*n/tot:5.1f}% {f}')
PY
