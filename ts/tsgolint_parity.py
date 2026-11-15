#!/usr/bin/env python3
# Rule parity: tsgolint's own test cases for a rule, run through tsgolint itself (the oracle) and
# vtsc --lint, each case's program in its own folder.
# usage: tsgolint_parity.py RULE [VTSC] [-v]
#   TSGOLINT: the tsgolint binary; TSGOLINT_SRC: its source at the same version (the test cases);
#   VTSC_LIB: TypeScript 7's lib folder; WORK: where the cases' folders go.
import sys, os, re, json, subprocess, shutil
TG=os.environ['TSGOLINT']
SRC=os.environ['TSGOLINT_SRC']
FIX=SRC+'/internal/rules/fixtures'
LIB=os.environ['VTSC_LIB']
WORK=os.environ.get('WORK','/tmp/tsgolint_parity')
rule=sys.argv[1]; vt=sys.argv[2] if len(sys.argv)>2 and not sys.argv[2].startswith('-') else './vtsc'
verbose='-v' in sys.argv
src=open(SRC+'/internal/rules/%s/%s_test.go'%(rule.replace('-','_'),rule.replace('-','_'))).read()

def go_string(s,i):
    # a Go string literal (raw or interpreted), possibly concatenated with +; returns (value, end)
    out=''
    while True:
        while s[i] in ' \t\n': i+=1
        if s[i]=='`':
            j=s.index('`',i+1); out+=s[i+1:j]; i=j+1
        elif s[i]=='"':
            j=i+1; buf=''
            while s[j]!='"':
                if s[j]=='\\':
                    nx=s[j+1]
                    m={'n':'\n','t':'\t','\\':'\\','"':'"','r':'\r',"'":"'"}
                    if nx in m: buf+=m[nx]; j+=2
                    elif nx=='u': buf+=chr(int(s[j+2:j+6],16)); j+=6
                    elif nx=='x': buf+=chr(int(s[j+2:j+4],16)); j+=4
                    else: buf+=nx; j+=2
                else: buf+=s[j]; j+=1
            out+=buf; i=j+1
        else: return None,i
        k=i
        while s[k] in ' \t': k+=1
        if s[k]=='+':
            i=k+1; continue
        return out,i

def block_end(s,i):
    # i at '{': the matching '}'
    d=0; j=i
    while j<len(s):
        ch=s[j]
        if ch=='`': j=s.index('`',j+1)+1; continue
        if ch=='"':
            j+=1
            while s[j]!='"':
                j+= 2 if s[j]=='\\' else 1
            j+=1; continue
        if s.startswith('//',j): j=s.index('\n',j); continue
        if ch=='{': d+=1
        elif ch=='}':
            d-=1
            if d==0: return j
        j+=1
    return j

cases=[]
for m in re.finditer(r'\n(\t+)\{\s*\n?\s*Code:', src):
    st=src.index('{',m.start())
    en=block_end(src,st)
    blk=src[st:en+1]
    ci=blk.index('Code:')+5
    code,_=go_string(blk,ci)
    if code is None: continue
    c={'code':code}
    # (only the case's own fields: not those of nested blocks)
    mo=re.search(r'Options:\s*rule_tester\.OptionsFromJSON\[[^\]]*\]\(',blk)
    if mo:
        v,_=go_string(blk,mo.end()); c['options']=v
    elif re.search(r'\n\t+Options:',blk): c['options']='?'
    mt=re.search(r'TSConfig:\s*',blk)
    if mt:
        v,_=go_string(blk,mt.end()); c['tsconfig']=v
    mf=re.search(r'FileName:\s*',blk)
    if mf:
        v,_=go_string(blk,mf.end()); c['file']=v
    if re.search(r'Tsx:\s*true',blk): c['tsx']=True
    if re.search(r'\bFiles:\s*map',blk): c['files']='?'
    cases.append(c)
# the default tsconfig of the rule's tests
mt=re.search(r'RunRuleTester\(fixtures\.GetRootDir\(\),\s*"([^"]+)"',src)
deftc=mt.group(1) if mt else 'tsconfig.json'

def run_case(i,c):
    d=WORK+'/%s/%d'%(rule,i)
    if os.path.exists(d): shutil.rmtree(d)
    shutil.copytree(FIX,d,ignore=shutil.ignore_patterns('*.go','consistent-type-exports'))
    tc=c.get('tsconfig',deftc)
    shutil.copy(d+'/'+tc,d+'/tsconfig.use.json')
    for f in os.listdir(d):
        if f.startswith('tsconfig') and f!='tsconfig.use.json': os.remove(d+'/'+f)
    os.rename(d+'/tsconfig.use.json',d+'/tsconfig.json')
    fn=c.get('file') or ('react.tsx' if c.get('tsx') else 'file.ts')
    open(d+'/'+fn,'w').write(c['code'])
    r={'name':rule}
    if 'options' in c:
        o=json.loads(c['options'])
        r['options']=o
    rules=json.dumps([r])
    pay=json.dumps({'version':2,'configs':[{'file_paths':[d+'/'+fn],'rules':[r]}],'source_overrides':None,'report_syntactic':False,'report_semantic':False})
    out=subprocess.run([TG,'headless'],input=pay.encode(),capture_output=True,cwd=d).stdout
    want=[]; k=0
    while k+5<=len(out):
        n=int.from_bytes(out[k:k+4],'little'); t=out[k+4]
        if t==1:
            j=json.loads(out[k+5:k+5+n]); j.pop('file_path',None); j.pop('fixes',None); j.pop('suggestions',None)
            want.append(j)
        k+=5+n
    p=subprocess.run([vt,'-p','tsconfig.json','--jobs','1','--lint',rules],capture_output=True,cwd=d,env=dict(os.environ,VTSC_LIB=LIB,PWD=d),text=True)
    got=[]
    for ln in p.stdout.splitlines():
        if ln.startswith('LINT '):
            j=json.loads(ln[5:])
            if os.path.basename(j['file_path'])!=fn: continue
            j.pop('file_path',None); got.append(j)
    unchecked=[l for l in p.stderr.splitlines() if (fn+':') in l and ('not checked' in l or 'rules not run' in l)]
    return want,got,unchecked

stats={'same':0,'diff':0,'unchecked':0,'skipped':0}
for i,c in enumerate(cases):
    if c.get('options')=='?' or c.get('files')=='?':
        stats['skipped']+=1; continue
    want,got,unc=run_case(i,c)
    if unc:
        stats['unchecked']+=1
        if verbose: print('UNCHECKED',i,unc[0][:200])
        continue
    if want==got: stats['same']+=1
    else:
        stats['diff']+=1
        print('DIFF case %d:\n%s\n  want %s\n  got  %s'%(i,c['code'][:400],json.dumps(want)[:700],json.dumps(got)[:700]))
print(rule, len(cases), 'cases:', stats)
