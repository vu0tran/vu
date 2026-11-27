# gen_worker.py (run in ts/): types.vu's worker_checker and its copy functions, between the
# markers, from type C's fields: run it after changing C's fields (VTSC_THREADS, tsprog.run_libs)
import os,re,sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
p='types.vu'; s=open(p).read()
B='# ---- a worker\'s checker (made by ts/gen_worker.py: edit the generator, not this)'
E='# ---- (the end of what ts/gen_worker.py makes)'
tail=''
if B in s:
    head=s[:s.index('\n'+B)]
    if E in s: tail=s[s.index(E)+len(E):]
    s=head
L=s.split('\n'); st=L.index('type C:')
fields=[]
for i in range(st+1,len(L)):
    l=L[i]
    if l and not l.startswith(' '): break
    if not l.strip() or l.strip().startswith('#'): continue
    m=re.match(r'^  (\w+): (.+?)(?:\s+=\s+(.+?))?\s*(?:#.*)?$', l)
    fields.append((m.group(1),m.group(2).strip(),(m.group(3) or '').strip()))
EMPTY={'diags','kept','spec_keep','touch_moved','checked_log'}   # lists a merge appends: each worker's own
# The type-aware rules' memos start empty in a worker: the rules run after the check, so the main
# checker's are empty when the workers start, and a memo may start empty anyway (dep_memo holds
# indexes into dep_reasons: the two go together)
EMPTY|={'dep_memo','dep_reasons','mp_then_memo','mp_void_memo'}
FRESH_TAB={'ho_mine'}
VIEW={'Tab':'ct','Lst':'cl','Grp':'cg','Ns':'ns','Ik':'ik','Ph':'ph'}
cps={}
def cpname(t):
    return 'wcp_'+t.replace('{','M').replace('[','L').replace(': ','').replace('}','').replace(']','').replace('.','')
def scalar(t): return t in ('Int','Bool','Float','Byte')
def gen_cp(t):
    if t in cps: return cpname(t)
    n=cpname(t); body=[]
    if t.startswith('{'):
        m=re.match(r'^\{(\w+): (.+)\}$',t); K,V=m.group(1),m.group(2)
        body.append(f'fn {n}(m: {t}) -> {t}:'); body.append(f'  var out: {t} = {{}}')
        if scalar(V): body.append('  for k, v in m: out[k] = v')
        elif V=='Str': body.append('  for k, v in m: out[k] = v + ""')
        else:
            sub=gen_cp(V); body.append(f'  for k, v in m: out[k] = {sub}(v)')
        body.append('  return out')
    elif t.startswith('['):
        V=t[1:-1]
        body.append(f'fn {n}(xs: {t}) -> {t}:'); body.append(f'  var out: {t} = []')
        if scalar(V): body.append('  for x in xs: out.push(x)')
        elif V=='Str': body.append('  for x in xs: out.push(x + "")')
        elif V=='parse.Diag': body.append('  for d in xs: out.push(parse.Diag(d.file, d.pos, d.end, d.code, d.msg + ""))')
        elif V=='LoopRec': body.append('  if xs.len > 0: panic("worker_checker: a loop being checked")')
        else:
            sub=gen_cp(V); body.append(f'  for x in xs: out.push({sub}(x))')
        body.append('  return out')
    else: raise Exception(t)
    cps[t]='\n'.join(body)
    return n
def val(n,t):
    if n=='t' or n=='bd': return f'm.{n}.share()'
    if t=='Ffi': return 'ffi'
    if t in VIEW:
        if n in FRESH_TAB: return f'ct_new(ffi, st)'
        v=VIEW[t]; return f'{v}_view(ffi, {v}_addr(ffi, m.{n}))'
    if t.startswith('SharedMap['): return f'm.{n}.share()'
    if t=='NodeMap': return f'nm_copy(m.{n})'   # (NodeMap, nm_copy: above the markers)
    if scalar(t): return f'm.{n}'
    if t=='Str': return f'm.{n} + ""'
    if t.startswith('{') or t.startswith('['):
        if n in EMPTY: return '[]' if t.startswith('[') else '{}'
        return f'{gen_cp(t)}(m.{n})'
    raise Exception((n,t))
pos=[val(n,t) for n,t,d in fields if d=='']
rest=[(n,val(n,t)) for n,t,d in fields if d!='']
out=[B,
"# A worker's checker (VTSC_THREADS): the main one's tables as views (ho_mine its own, in st), its",
"# SharedMaps, tree and binding as more handles, its settings, and a copy of every other map and",
"# list as the main checker has them when the workers start (each worker's own from then on); the",
"# diagnostics' lists empty (merged back by tsprog.merge_worker).",
"fn worker_checker(m: C, ffi: Ffi, st: Store) -> C:",
"  var w = C(" + ', '.join(pos) + ")"]
for n,v in rest: out.append(f'  w.{n} = {v}')
out.append('  return w')
out.append('')
out.append("# (debugging, VTSC_THREADS_SEQ: the maps and lists named in want taken from another worker's checker)")
out.append('fn worker_carry(var w: C, f: C, want: {Str: Bool}):')
for n,t,d in fields:
    if (t.startswith('{') or t.startswith('[')) and n not in EMPTY and n not in ('t','bd'):
        out.append(f'  if "{n}" in want: w.{n} = {gen_cp(t)}(f.{n})')
    elif t=='NodeMap':
        out.append(f'  if "{n}" in want: w.{n} = nm_copy(f.{n})')
out.append('')
for t in sorted(cps): out.append(cps[t]); out.append('')
s=s+'\n'+'\n'.join(out)+E+tail
if not s.endswith('\n'): s+='\n'
open(p,'w').write(s)
print(len(pos),len(rest),len(cps))
