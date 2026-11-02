#!/bin/bash
# Compares the Vu parser's nodes with go/parser's on every .go file under the given folders.
S=/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad
find "$@" -name '*.go' -not -path '*/testdata/*' | sort > $S/golint/astfiles.txt
xargs -a $S/golint/astfiles.txt $S/astdump > $S/golint/ast_go.txt
xargs -a $S/golint/astfiles.txt $S/gpt --dump > $S/golint/ast_vu.txt
python3 - <<'PY'
S="/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/"
def load(p):
    d={}; cur=None
    for l in open(p):
        l=l.rstrip("\n")
        if l.startswith("FILE "): cur=l[5:]; d[cur]=[]
        elif l.startswith("ERR "): pass
        else: d[cur].append(l)
    return d
g=load(S+"ast_go.txt"); v=load(S+"ast_vu.txt")
import collections
bad=0
for f in g:
    a=collections.Counter(g[f]); b=collections.Counter(v.get(f,[]))
    if a!=b:
        bad+=1
        if bad<=6:
            print("==",f)
            print("  go only:", sorted((a-b).elements())[:8])
            print("  vu only:", sorted((b-a).elements())[:8])
print(len(g),"files,",bad,"differ")
PY
