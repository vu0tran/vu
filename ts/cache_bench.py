#!/usr/bin/env python3
# cache_bench.py DIR TARGET N: vlint without a cache (VLINT0: a build before --cache, VLINT: this one),
# with a cold cache, a warm one, a warm one after 1% of the files changed, and oxlint; min CPU and wall of N
import os, sys, subprocess, time, shutil, random
d, tgt, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
S='/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad'
V0=os.environ.get("VLINT0", S+"/cache-work/vlint0"); V=os.environ.get("VLINT", S+"/cache-work/vlint")
OX=[S+'/tsbench/node_modules/.bin/oxlint','-c','/tmp/oxempty.json','--disable-nested-config']
os.chdir(d); C=os.path.join(d,'.vlintcache')
def run(cmd, setup=None):
    bc=bw=1e9
    for _ in range(N):
        if setup: setup()
        t0=time.time(); p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        _,st,ru=os.wait4(p.pid,0); w=time.time()-t0
        bc=min(bc,ru.ru_utime+ru.ru_stime); bw=min(bw,w)
    return f"cpu {bc:6.3f}  wall {bw:6.3f}"
fs=[]
for r,_,ns in os.walk(tgt):
    for n in ns:
        if n.endswith(('.js','.ts','.mjs','.cjs','.mts','.cts','.jsx','.tsx')): fs.append(os.path.join(r,n))
fs.sort(); random.seed(1); ch=random.sample(fs,max(1,len(fs)//100))
print(f"{d}/{tgt}: {len(fs)} files, {len(ch)} changed for the 1% case; load {os.getloadavg()[0]:.1f}")
def rmc():
    if os.path.exists(C): os.remove(C)
for jobs in (['--jobs','1'],[]):
    tag='1 thread ' if jobs else 'all cores'
    print(f"vlint no cache, {tag}:        "+run([V0]+jobs+[tgt]))
    print(f"vlint (new) no cache, {tag}:  "+run([V]+jobs+[tgt]))
    print(f"vlint cold cache, {tag}:      "+run([V,'--cache']+jobs+[tgt],rmc))
    subprocess.run([V,'--cache',tgt],stdout=subprocess.DEVNULL); time.sleep(2.5)
    subprocess.run([V,'--cache',tgt],stdout=subprocess.DEVNULL)
    print(f"vlint warm cache, {tag}:      "+run([V,'--cache']+jobs+[tgt]))
    shutil.copy(C,C+'.snap')
    def chg():
        shutil.copy(C+'.snap',C)
        for f in ch: open(f,'a').write('\n')
    print(f"vlint warm, 1% changed, {tag}:"+run([V,'--cache']+jobs+[tgt],chg))
    os.remove(C+'.snap'); rmc()
    print(f"oxlint, {tag}:               "+run(OX+(['--threads','1'] if jobs else [])+[tgt]))
print(f"load {os.getloadavg()[0]:.1f}; cache file {os.path.getsize(C) if os.path.exists(C) else 0}")
