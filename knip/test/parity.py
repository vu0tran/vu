import sys,os,re,subprocess,collections
W=os.path.dirname(os.path.abspath(__file__))
# VKNIP: the vknip binary; REF: the folder of knip's outputs (NAME.txt for each project)
VK=os.environ.get('VKNIP', os.path.join(W,'vknip'))
REF=os.environ.get('REF', os.path.join(W,'ref'))
def parse(text):
    cats=collections.OrderedDict(); cur=None
    for line in text.split('\n'):
        m=re.match(r'^([A-Z][A-Za-z ]+) \((\d+)\)$',line)
        if m: cur=m.group(1); cats[cur]=[]; continue
        if cur and line.strip(): cats[cur].append(' '.join(line.split()))
    return cats
def main():
    corpus=sys.argv[1]; names=sys.argv[2:]
    vk=VK
    tot=collections.Counter(); ident_files=0
    rows=[]
    for n in names:
        ref=open(os.path.join(REF,n+'.txt')).read()
        out=subprocess.run([vk],cwd=os.path.join(corpus,n),capture_output=True,text=True)
        got=out.stdout
        same = got==ref
        ident_files+=same
        a=parse(ref); b=parse(got)
        cs=set(a)|set(b)
        detail=[]
        for c in sorted(cs):
            ra=collections.Counter(a.get(c,[])); rb=collections.Counter(b.get(c,[]))
            common=sum((ra&rb).values()); miss=sum((ra-rb).values()); extra=sum((rb-ra).values())
            tot[(c,'ref')]+=sum(ra.values()); tot[(c,'same')]+=common; tot[(c,'missing')]+=miss; tot[(c,'extra')]+=extra
            if miss or extra: detail.append(f"{c}: -{miss} +{extra}")
        print(f"{n:16} {'IDENTICAL' if same else 'DIFF'} {'; '.join(detail)} {('stderr: '+out.stderr.strip()[:200]) if out.stderr.strip() else ''}")
    print(f"identical outputs: {ident_files}/{len(names)}")
    cats=sorted(set(c for c,_ in tot))
    for c in cats:
        print(f"  {c:32} ref={tot[(c,'ref')]:4} same={tot[(c,'same')]:4} missing={tot[(c,'missing')]:3} extra={tot[(c,'extra')]:3}")
main()
