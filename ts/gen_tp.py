import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
E=["string","number","boolean","1","\"a\"","string | undefined"]
V={"string":"\"s\"","number":"2","boolean":"true","1":"1","\"a\"":"\"a\"","string | undefined":"undefined"}
def tup():
    pre=[random.choice(E) for _ in range(random.randrange(0,3))]
    opt=random.random()<0.2
    r=random.random()
    s=pre[:]
    if opt and s: s[-1]=s[-1]+"?" if "|" not in s[-1] else s[-1]
    if r<0.6: s.append("..."+("("+random.choice(E)+")" if "|" in random.choice(E) else random.choice(E))+"[]")
    if r<0.2 and r>0.0: s.append(random.choice(E))
    ro=random.random()<0.2
    return ("readonly " if ro else "")+"["+", ".join(s)+"]"
for p in range(n):
    out=[]
    t1=tup(); t2=tup()
    out.append(f"type A = {t1}")
    out.append(f"type B = {t2}")
    out.append("declare const a: A")
    out.append("declare const b: B")
    out.append("const x1: B = a")
    out.append(f"const x2: A = [{', '.join(V[random.choice(E)] for _ in range(random.randrange(0,4)))}]")
    out.append(f"const x3: {random.choice(E)} = a[{random.randrange(0,4)}]")
    out.append(f"const x4: {random.choice(E)}[] = a")
    out.append(f"function f(...args: A) {{ return args }}")
    out.append(f"f({', '.join(V[random.choice(E)] for _ in range(random.randrange(0,4)))})")
    out.append(f"const x5: boolean = a.length")
    out.append(f"const x6: boolean = b")
    out.append("export {}")
    open(f"t{seed}_{p}.ts","w").write("\n".join(out)+"\n")
