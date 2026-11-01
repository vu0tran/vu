import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
names=["a","b","m","'a'","\"b\""]
types=["number","string","1","boolean","number | undefined"]
def cmember():
    nm=random.choice(names); r=random.randrange(10); st=random.choice(["","","static "]); acc=random.choice(["","","private ","protected "])
    t=random.choice(types)
    if r<3: return f"{acc}{st}{nm}: {t} = null as any"
    if r<5: return f"{acc}{st}{nm}(x: {t}): {random.choice(types+['void'])}" + random.choice([" { return null as any }",""])
    if r==5: return f"{acc}{st}{nm}(x?: {t}) {{}}"
    if r==6: return f"{st}get {nm}() {{ return 1 }}"
    if r==7: return f"{st}set {nm}(v: number) {{}}"
    if r==8: return f"constructor(x: {t})" + random.choice([" {}",""])
    return f"{st}{nm}?: {t}"
def imember():
    nm=random.choice(names); t=random.choice(types); r=random.randrange(4)
    if r<2: return f"{nm}: {t}"
    if r==2: return f"{nm}?: {t}"
    return f"{nm}(x: {t}): void"
for p in range(n):
    out=[]
    for i in range(random.randrange(1,4)):
        r=random.randrange(4)
        if r==0: out.append(f"class C{i} {{ " + "; ".join(cmember() for _ in range(random.randrange(1,5))) + " }")
        elif r==1: out.append(f"interface I{random.randrange(2)} {{ " + "; ".join(imember() for _ in range(random.randrange(1,4))) + " }")
        elif r==2: out.append(f"type T{i} = {{ " + "; ".join(imember() for _ in range(random.randrange(1,4))) + " }")
        else:
            ps=[]
            for _ in range(random.randrange(1,4)):
                nm=random.choice(["a","b","'a'","1","\"1\""]); ps.append(f"{nm}: {random.choice(['1','\"x\"','true'])}")
            out.append(f"const o{i} = {{ " + ", ".join(ps) + " }")
    out.append("export {}")
    open(f"m{seed}_{p}.ts","w").write("\n".join(out)+"\n")
