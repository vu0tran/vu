import sys,re,collections
def parse(text):
    cats=collections.OrderedDict(); cur=None
    for line in text.split('\n'):
        m=re.match(r'^([A-Z][A-Za-z ]+) \((\d+)\)$',line)
        if m: cur=m.group(1); cats[cur]=[]; continue
        if cur and line.strip(): cats[cur].append(' '.join(line.split()))
    return cats
a=parse(open(sys.argv[1]).read()); b=parse(open(sys.argv[2]).read())
n=int(sys.argv[3]) if len(sys.argv)>3 else 8
for c in set(a)|set(b):
    ra=collections.Counter(a.get(c,[])); rb=collections.Counter(b.get(c,[]))
    miss=list((rb-ra).elements()); extra=list((ra-rb).elements())
    if miss or extra:
        print(f"== {c}: missing(in ref only) {len(miss)}, extra(vknip only) {len(extra)}")
        for x in miss[:n]: print("  - "+x)
        for x in extra[:n]: print("  + "+x)
