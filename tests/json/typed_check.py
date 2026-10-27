# Compares typed.vu output (argv[1]) with exp.json, reading numbers as values (3e10 == 30000000000).
import json,sys
def norm(v):
    if isinstance(v,float) and v==int(v): return int(v)
    if isinstance(v,list): return [norm(x) for x in v]
    if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
    return v
exp=json.load(open('exp.json')); got=open(sys.argv[1],encoding='utf-8').read().split('\n')[:-1]
lines=open('in.txt',encoding='utf-8').read().split('\n')
assert len(got)==len(exp),(len(got),len(exp))
bad=0
for i,(e,g) in enumerate(zip(exp,got)):
    ge=None if g.startswith('ERR ') else json.loads(g)
    if (e is None)!=(ge is None) or (e is not None and json.dumps(norm(e),sort_keys=True)!=json.dumps(norm(ge),sort_keys=True)):
        bad+=1
        if bad<=6: print('MISMATCH', repr(lines[i])[:300], '\n  model:', json.dumps(e)[:200], '\n  vu:', g[:200])
print(f'{len(exp)} cases, {bad} mismatches, {sum(e is None for e in exp)} rejected')
