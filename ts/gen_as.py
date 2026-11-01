import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
T=["number","string","boolean","number | undefined","string[]","void","Promise<number>","Promise<string> | number","1 | 2"]
V={"number":"1","string":"\"s\"","boolean":"true","number | undefined":"undefined","string[]":"[\"a\"]","void":"undefined","Promise<number>":"Promise.resolve(1)","Promise<string> | number":"(Math.random() ? Promise.resolve(\"q\") : 3)","1 | 2":"(Math.random() ? 1 : 2)"}
for p in range(n):
    out=[]
    for i in range(random.randrange(1,4)):
        ann=random.choice(["", ": Promise<"+random.choice(T[:6]+["1 | 2"])+">"])
        body=[]
        for j in range(random.randrange(0,3)):
            t=random.choice(T)
            body.append(f"const v{j} = await {V[t]}")
            if random.random()<0.4: body.append(f"const w{j}: {random.choice(T[:5])} = v{j}")
        r=random.randrange(4)
        if r==0 and body: body.append(f"return v0")
        elif r==1: body.append(f"return {V[random.choice(T)]}")
        elif r==2: body.append(f"if (Math.random()) return {V[random.choice(T)]}\n  return {V[random.choice(T)]}")
        kind=random.randrange(3)
        b="\n  ".join(body)
        if kind==0: out.append(f"async function f{i}(){ann} {{\n  {b}\n}}")
        elif kind==1: out.append(f"const f{i} = async (){ann} => {{\n  {b}\n}}")
        else: out.append(f"const f{i} = async (){ann} => {V[random.choice(T)]}")
        out.append(f"const r{i}: {random.choice(T)} = f{i}()")
        if random.random()<0.5: out.append(f"const s{i}: boolean = f{i}")
    out.append("export {}")
    open(f"a{seed}_{p}.ts","w").write("\n".join(out)+"\n")
