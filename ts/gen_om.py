import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
T=["number","string","boolean","number | undefined","string[]","void"]
def val(t):
    return {"number":"1","string":"\"s\"","boolean":"true","number | undefined":"undefined","string[]":"[\"a\"]","void":"undefined"}[t]
for p in range(n):
    out=[]
    nm=random.randrange(1,3)
    sig=[]
    for i in range(nm):
        ps=[random.choice(T[:5]) for _ in range(random.randrange(0,3))]
        r=random.choice(T)
        sig.append((f"m{i}",ps,r))
        params=", ".join(f"p{j}: {t}" for j,t in enumerate(ps))
        kind=random.randrange(3)
        if kind==0: out.append(f"interface I{i} {{ m{i}({params}): {r}; k{i}: number }}")
        elif kind==1: out.append(f"interface I{i} {{ m{i}: ({params}) => {r}; k{i}: number }}")
        else: out.append(f"type I{i} = {{ m{i}?({params}): {r}; k{i}: number }}")
    for i,(m,ps,r) in enumerate(sig):
        q=random.randrange(len(ps)+2)
        params=", ".join(f"a{j}" + (f": {random.choice(T[:5])}" if random.random()<0.3 else "") for j in range(q))
        body=random.choice([f"return {val(random.choice(T))}", f"return a0", "", f"const z: {random.choice(T[:5])} = a0; return z" if q>0 else "return 1"])
        if q==0 and "a0" in body: body="return 2"
        lit="{ " + f"{m}({params}) {{ {body} }}, k{i}: {random.choice(['1','\"x\"'])}" + " }"
        out.append(f"const o{i}: I{i} = {lit}")
        out.append(f"const u{i} = {lit}")
        if random.random()<0.5: out.append(f"const r{i}: {random.choice(T[:5])} = u{i}.{m}({', '.join(val(random.choice(T[:5])) for _ in range(random.randrange(3)))})")
        if random.random()<0.3: out.append(f"const w{i}: number = u{i}")
    out.append("export {}")
    open(f"o{seed}_{p}.ts","w").write("\n".join(out)+"\n")
