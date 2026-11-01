import random, sys
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
base=["count","total","value","items","index","result","Person","Widget","helper","config","name","data","node","Event","Map","Set","Array","Math","JSON","Promise","Error","Date","console","document","window","length","parseInt","setTimeout","Record","Partial","string","number","boolean","object","bigint","symbol","it","a","ab","id","self","top","Option","Optional","x","xs","value2","Value","VALUE","valu"]
def mutate(w):
    r=random.random(); L=list(w)
    if not L: return w+"x"
    i=random.randrange(len(L))
    if r<0.2: del L[i]
    elif r<0.4: L.insert(i,random.choice("aeioxsT"))
    elif r<0.55: L[i]=L[i].swapcase()
    elif r<0.7 and len(L)>1: j=min(i+1,len(L)-1); L[i],L[j]=L[j],L[i]
    elif r<0.85: L[i]=random.choice("abcdeQ")
    else: return w+random.choice(["s","2","_",""])
    return "".join(L)
for p in range(n):
    out=[]
    decls=random.sample(base[:12],5)
    out.append(f"let {decls[0]} = 1")
    out.append(f"function {decls[1]}({decls[2]}: number) {{ let {decls[3]} = 2; return {decls[3]} }}")
    out.append(f"interface {decls[4].capitalize()}I {{ a: number }}")
    out.append(f"type {decls[0].capitalize()}T = string")
    out.append(f"class K{p} {{ {decls[2]} = 1; static {decls[3]}S = 2; m() {{ return 0 }} }}")
    for i in range(6):
        w=mutate(random.choice(decls+base))
        if not w.isidentifier() or w in ("keyof","typeof","infer","void","null","true","false","any","unknown","never","undefined","this","new","in","of","if","do","for","let","var","try","as","is"): continue
        ctx=random.randrange(6)
        if ctx==0: out.append(f"console.log({w})")
        elif ctx==1: out.append(f"let v{i}: {w} = null as any")
        elif ctx==2: out.append(f"function f{i}<TItem>(p: {w}) {{ return {mutate(random.choice(decls))} }}")
        elif ctx==3: out.append(f"class C{i} {{ q = 1; m() {{ return {w} }} }}")
        elif ctx==4: out.append(f"type A{i}<T> = T extends {w} ? 1 : 2")
        else: out.append(f"let u{i} = typeof {w}")
    out.append("export {}")
    open(f"n{seed}_{p}.ts","w").write("\n".join(out)+"\n")
