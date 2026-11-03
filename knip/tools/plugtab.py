import json, re, os, glob, sys
# The plugin coverage table of README.md: python3 tools/plugtab.py > table.md (WORK=dir with corpus/)
K=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W=os.environ.get('WORK', os.getcwd())
d=json.load(open(K+'/tools/plugins.json'))
src=open(K+'/vknip.vu').read()
hr=set(re.search(r'fn has_resolver.*?return " (.*?) "\.find',src,re.S).group(1).split())
ast=set(re.findall(r'key == "([a-z0-9-]+)"', re.search(r'fn ast_ported.*?\n\n',src,re.S).group(0)))
rs_block=re.search(r'fn plugin_resolve\(.*?\n\n# /',src,re.S).group(0)
res=set(re.findall(r'key == "([a-z0-9-]+)"', rs_block))
hand=set("node typescript tsx husky mcp github-actions borp typedoc tsrs lefthook".split())
vis_done=set("jest vitest rstest execa zx nano-spawn vite webpack rspack node pino knex lit catalyst fast stencil angular".split())
cases=''.join(open(f).read() for f in glob.glob(K+'/test/cases*.py'))
corp={}
for proj in sorted(glob.glob(W+'/corpus/*')):
    deps=set()
    for m in glob.glob(proj+'/package.json')+glob.glob(proj+'/*/package.json')+glob.glob(proj+'/*/*/package.json'):
        if '/node_modules/' in m: continue
        try: j=json.load(open(m))
        except: continue
        for k in ('dependencies','devDependencies','peerDependencies','optionalDependencies'):
            deps.update((j.get(k) or {}).keys())
    corp[os.path.basename(proj)]=deps
def enabled(pl,deps):
    for e in pl['enablers'] or []:
        if isinstance(e,dict):
            if any(re.search(e['re'],x) for x in deps): return True
        elif e in deps: return True
    return False
rows=[]; missing=[]
for pl in d:
    n=pl['name']; rc=bool(pl['resolveConfig']); ra=bool(pl['resolveFromAST']); rs=bool(pl['resolve']); vi=bool(pl.get('registerVisitors'))
    parts=[]; ok=True
    if n in hand: parts.append('ported (hand-written)')
    else:
        if rc: parts.append('resolveConfig ported' if n in hr else 'resolveConfig NOT ported'); ok = ok and n in hr
        if ra: parts.append('resolveFromAST ported' if n in ast else 'resolveFromAST NOT ported'); ok = ok and n in ast
        if rs: parts.append('resolve ported' if n in res else 'resolve NOT ported'); ok = ok and n in res
    if vi: parts.append('visitors ported' if n in vis_done else 'visitors NOT ported'); ok = ok and (n in vis_done)
    if not parts: parts.append('complete (static plugin)')
    if not ok: missing.append(n)
    t=[]
    if re.search(r'(p7|pl|v8)_%s\b'%re.escape(n.replace('-','_')),cases) or ('"%s"'%n in cases): t.append('generated')
    cp=[p for p,deps in corp.items() if enabled(pl,deps)]
    if cp: t.append(', '.join(cp[:4])+(' +%d'%(len(cp)-4) if len(cp)>4 else ''))
    rows.append((n,pl['title'],'; '.join(parts),'; '.join(t)))
print(len(rows),'plugins;',len(rows)-len(missing),'complete;',len(missing),'with parts not ported:',' '.join(missing), file=sys.stderr)
print('| plugin | status | tested on |'); print('|---|---|---|')
for n,t,st,te in rows: print(f'| {t} (`{n}`) | {st} | {te} |')
