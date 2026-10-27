# The model for tests/json/typed.vu: writes in.txt (one JSON document per line) and exp.json (what
# from_json should return for each, or null when it must fail) in the current directory.
#   typed_model.py SEED N        N byte-level mutations of a valid document (plus a few fixed cases)
#   typed_model.py SEED 0 N      N well-formed documents with wrong types, missing, extra and repeated fields
import json, math, random, sys
class Bad(Exception): pass
def no_const(c): raise Bad(c)
class P(dict): pass
def hook(pairs):
    d=P(pairs); d.pairs=pairs; return d
def strict(s):
    try: return json.loads(s, parse_constant=no_const, object_pairs_hook=hook)
    except (ValueError, Bad, RecursionError): raise Bad()
def isint(v): return isinstance(v,int) and not isinstance(v,bool)
def num(v):
    if isinstance(v,bool) or not isinstance(v,(int,float)): raise Bad()
    if math.isinf(float(v)): raise Bad()
    return float(v)
def I(v):
    if not isint(v) or not -2**63 <= v < 2**63: raise Bad()
    return v
def S(v):
    if not isinstance(v,str): raise Bad()
    if any(0xd800<=ord(c)<=0xdfff for c in v): raise Bad()
    return v
def B(v):
    if not isinstance(v,bool): raise Bad()
    return v
def Byte(v):
    v=I(v)
    if not 0<=v<=255: raise Bad()
    return v
def L(f): 
    def g(v):
        if not isinstance(v,list): raise Bad()
        return [f(x) for x in v]
    return g
def O(f): return lambda v: None if v is None else f(v)
def M(f):
    def g(v):
        if not isinstance(v,dict): raise Bad()
        for k,x in v.pairs: S(k); f(x)
        return {S(k):f(x) for k,x in v.items()}
    return g
def F(v): return num(v)
def struct(fields):
    def g(v):
        if not isinstance(v,dict): raise Bad()
        out={}
        for k,x in v.pairs:
            S(k)
            if k in fields: fields[k][0](x)
        for k,(f,opt) in fields.items():
            if k in v: out[k]=f(v[k])
            elif opt: out[k]=None
            else: raise Bad()
        for k in v: S(k)
        return out
    return g
item=struct({'sku':(S,0),'qty':(I,0),'price':(F,0),'b':(O(Byte),1)})
def shape(v):
    if isinstance(v,str):
        if v=='Dot': return 'Dot'
        raise Bad()
    if not isinstance(v,dict) or len(v.pairs)!=1: raise Bad()
    (k,x),=v.items()
    fs={'Circle':{'r':(F,0)},'Rect':{'w':(I,0),'h':(I,0)},'Named':{'name':(S,0),'parts':(L(shape),0)}}
    if k not in fs: raise Bad()
    return {k:struct(fs[k])(x)}
order=struct({'id':(I,0),'customer':(S,0),'items':(L(item),0),'note':(O(S),1),'tags':(M(I),0),
               'shape':(shape,0),'ok':(B,0),'nested':(L(L(O(I))),0)})
def expect(s):
    try: return order(strict(s))
    except (Bad, RecursionError): return None

base={"id":7,"customer":"Ann é \"q\"","items":[{"sku":"a","qty":2,"price":1.5,"b":200},{"sku":"b\\n","qty":-1,"price":3e10}],
      "note":None,"tags":{"x":1,"y":-9},"shape":{"Named":{"name":"n","parts":["Dot",{"Circle":{"r":0.1}},{"Rect":{"w":1,"h":2}}]}},
      "ok":True,"nested":[[1,None],[]]}
toks=['{','}','[',']',',',':','"','\\','null','true','1e999','-0','1.0','9223372036854775808','-9223372036854775808','"\\ud800"','"\\u00e9"','" "','\t','0x1','01','1e2','256','"Dot"','{"Circle":{"r":1}}','"extra":1',' ','"id":1','NaN']
def mutate(s, r):
    s=list(s)
    for _ in range(r.randint(1,3)):
        op=r.random()
        if op<0.3 and s: del s[r.randrange(len(s))]
        elif op<0.6: s.insert(r.randrange(len(s)+1), r.choice(toks))
        elif op<0.8 and s: i=r.randrange(len(s)); s[i]=r.choice(toks)
        else: s=s[:r.randrange(len(s)+1)]
    return ''.join(s)
def variants(r):
    yield json.dumps(base)
    yield json.dumps(base, ensure_ascii=False)
    d=dict(base); d.pop('note'); yield json.dumps(d)
    yield '{"id":1,"id":2,'+json.dumps(base)[1:]   # duplicate key: last wins
    yield json.dumps(base)+'  '
    yield json.dumps(base)+' x'
    yield '{"Named":'*2000
    for _ in range(int(sys.argv[2])):
        yield mutate(json.dumps(base, ensure_ascii=r.random()<0.5), r)
r=random.Random(int(sys.argv[1]))
lines=[v.replace('\n','\\n') for v in variants(r)]
open('in.txt','w',encoding='utf-8',errors='surrogatepass').write('\n'.join(lines))
json.dump([expect(l) for l in lines], open('exp.json','w'))

def rv(r, kind, d=0):
    # a value of the right kind most of the time, sometimes something else
    if r.random() < 0.04:
        return r.choice([None, 1, -3, 2.5, "s", True, [], {}, [1], {"a": 1}, 300, 2**63, "Dot"])
    if kind == 'I': return r.choice([0, 1, -5, 2**62, -2**63, 2**63-1])
    if kind == 'F': return r.choice([0.1, 1, -2.5e-300, 1e308, 7])
    if kind == 'S': return r.choice(["", "x", "é", " ", "a\"b", "\\", "\U0001F600", "nul\u0000"])
    if kind == 'B': return r.random() < 0.5
    if kind == 'Byte': return r.choice([0, 255, 17])
    if kind == 'item':
        o = {"sku": rv(r,'S'), "qty": rv(r,'I'), "price": rv(r,'F')}
        if r.random() < 0.5: o["b"] = None if r.random() < 0.3 else rv(r,'Byte')
        return fiddle(r, o)
    if kind == 'shape':
        c = r.randrange(4) if d < 4 else r.randrange(3)
        if c == 0: return "Dot"
        if c == 1: return {"Circle": fiddle(r, {"r": rv(r,'F')})}
        if c == 2: return {"Rect": fiddle(r, {"w": rv(r,'I'), "h": rv(r,'I')})}
        return {"Named": fiddle(r, {"name": rv(r,'S'), "parts": [rv(r,'shape',d+1) for _ in range(r.randrange(4))]})}
    if kind == 'order':
        return fiddle(r, {"id": rv(r,'I'), "customer": rv(r,'S'), "items": [rv(r,'item') for _ in range(r.randrange(4))],
                          "note": None if r.random() < 0.5 else rv(r,'S'), "tags": {r.choice(["", "k", "é", "k2", "\\"]): rv(r,"I") for _ in range(r.randrange(3))},
                          "shape": rv(r,'shape'), "ok": rv(r,'B'),
                          "nested": [[None if r.random()<0.3 else rv(r,'I') for _ in range(r.randrange(3))] for _ in range(r.randrange(3))]})
def fiddle(r, o):
    if r.random() < 0.03 and o: o.pop(r.choice(list(o)))
    if r.random() < 0.05: o["zz" + str(r.randrange(9))] = r.choice([{"deep": [1, {"x": None}]}, "s", [], 1.5])
    return o
def dump(r, v):
    s = json.dumps(v, ensure_ascii=r.random() < 0.5)
    if r.random() < 0.05 and s.startswith('{"id"'):
        s = '{"id": "dup", ' + s[1:]   # an earlier duplicate key with a wrong type: last one wins
    return s
if len(sys.argv) > 3:
    r = random.Random(int(sys.argv[1]) * 7919)
    lines = [dump(r, rv(r, 'order')).replace('\n', '\\n') for _ in range(int(sys.argv[3]))]
    open('in.txt','w',encoding='utf-8',errors='surrogatepass').write('\n'.join(lines))
    json.dump([expect(l) for l in lines], open('exp.json','w'))
