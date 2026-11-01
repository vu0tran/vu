import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
DT=["string | number","number | undefined","string | number | null","boolean | string","string[] | undefined","1 | 2 | 3","\"a\" | \"b\" | number"]
VAL={"string":["\"s\"","\"\""],"number":["1","0","2"],"undefined":["undefined"],"null":["null"],"boolean":["true","false"],"string[]":["[]","[\"x\"]"],"1":["1"],"2":["2"],"3":["3"],"\"a\"":["\"a\""],"\"b\"":["\"b\""]}
def vals(t): 
    out=[]
    for m in t.split(" | "): out+=VAL.get(m,["1"])
    return out
def cond(v,t):
    r=random.randrange(6)
    if r==0: return "Math.random() > 0.5"
    if r==1: return f"typeof {v} === \"string\""
    if r==2: return f"{v} === undefined"
    if r==3: return f"{v}"
    if r==4: return f"!{v}"
    return f"{v} !== null"
def stmt(v,t,depth):
    r=random.randrange(9)
    if r<3: return f"{v} = {random.choice(vals(t))}"
    if r==3: return f"if ({cond(v,t)}) {{ {stmt(v,t,depth+1) if depth<2 else 'x0 = 1'} }}"
    if r==4: return f"if ({cond(v,t)}) break"
    if r==5: return f"if ({cond(v,t)}) continue"
    if r==6: return f"const r{random.randrange(99)}: {random.choice(['string','number','boolean'])} = {v}"
    if r==7: return f"{v} ??= {random.choice(vals(t))}"
    return f"if ({cond(v,t)}) {{ {v} = {random.choice(vals(t))} }} else {{ {v} = {random.choice(vals(t))} }}"
for p in range(n):
    out=["declare const items: number[]","let x0 = 0"]
    t=random.choice(DT)
    init=random.choice(vals(t)+[""])
    out.append(f"let v: {t}" + (f" = {init}" if init else ""))
    if not init: out.append(f"v = {random.choice(vals(t))}")
    body="; ".join(stmt("v",t,0) for _ in range(random.randrange(1,4)))
    k=random.randrange(4)
    if k==0: out.append(f"while ({cond('v',t)}) {{ {body} }}")
    elif k==1: out.append(f"for (let i = 0; i < 3; i++) {{ {body} }}")
    elif k==2: out.append(f"for (const it of items) {{ {body} }}")
    else: out.append(f"do {{ {body} }} while ({cond('v',t)})")
    out.append(f"const after: {random.choice(['string','number','boolean'])} = v")
    out.append("export {}")
    open(f"l{seed}_{p}.ts","w").write("\n".join(out)+"\n")
