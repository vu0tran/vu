import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
names=["a","b","c","T","U","f","g"]
types=["number","string","boolean","number | undefined","string[]","any"]
def decl(nm, depth):
    r=random.randrange(14)
    t=random.choice(types)
    if r==0: return f"var {nm}: {t}"
    if r==1: return f"var {nm} = {random.choice(['1','\"s\"','true','[1]','undefined','null'])}"
    if r==2: return f"let {nm} = 1"
    if r==3: return f"const {nm} = 2"
    if r==4: return f"function {nm}(x: {t}): {random.choice(types+['void'])}" + random.choice([" { return null as any }",""])
    if r==5: return f"function {nm}(x?: {t}, y?: number) {{}}"
    if r==6: return f"class {nm} {{}}"
    if r==7: return f"interface {nm} {{ p{random.randrange(3)}: {t} }}"
    if r==8: return f"type {nm} = {t}"
    if r==9: return f"{{ var {nm} = {random.choice(['1','\"s\"'])} }}"
    if r==10: return f"if (Math.random()) {{ {decl(nm, depth+1) if depth<2 else 'let '+nm+' = 3'} }}"
    if r==11: return f"function h{random.randrange(9)}<{nm}>({nm}: number) {{ {decl(random.choice(names), depth+1) if depth<2 else ''} }}"
    if r==12: return f"for (let {nm} = 0; {nm} < 1; {nm}++) {{ {decl(nm, depth+1) if depth<2 else ''} }}"
    return f"function k{random.randrange(9)}({nm}: {t}) {{ {decl(random.choice(names), depth+1) if depth<2 else ''} }}"
for p in range(n):
    out=[decl(random.choice(names),0) for _ in range(random.randrange(3,8))]
    out.append("export {}")
    open(f"d{seed}_{p}.ts","w").write("\n".join(out)+"\n")
