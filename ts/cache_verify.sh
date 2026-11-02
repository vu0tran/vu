#!/bin/bash
# cache_verify.sh BIN PARENT NAME: vlint without a cache vs --cache cold and warm on PARENT/NAME, then in a
# /dev/shm copy after appending to, truncating, deleting, adding and same-size-same-mtime editing 1% each
B=$1; P=$2; N=$3; C=/dev/shm/vlc-$N; D=/dev/shm/vlcopy
cd $P; rm -f $C
$B $N > /dev/shm/o-ref; $B --cache --cache-location $C $N > /dev/shm/o-cold; $B --cache --cache-location $C $N > /dev/shm/o-warm
r1=same; cmp -s /dev/shm/o-ref /dev/shm/o-cold || r1=DIFF; r2=same; cmp -s /dev/shm/o-ref /dev/shm/o-warm || r2=DIFF
echo "$N: $(wc -l < /dev/shm/o-ref) lines; cold $r1, warm $r2"
rm -rf $D; mkdir -p $D; cp -r $N $D/; cd $D
$B --cache --cache-location $C $N > /dev/shm/o-warm2; cmp -s /dev/shm/o-ref /dev/shm/o-warm2 && echo "  copy (new inodes/ctimes): same" || echo "  copy: DIFF"
# edits: append a debugger statement to some, truncate some, delete some, add some
python3 -I - $N <<'PY'
import os, sys, random
random.seed(7)
fs=[]
for d,_,ns in os.walk(sys.argv[1]):
  for n in ns:
    if n.endswith(('.js','.ts','.mjs','.cjs','.mts','.cts','.jsx','.tsx')): fs.append(os.path.join(d,n))
fs.sort(); random.shuffle(fs); k=max(3,len(fs)//100)
for f in fs[:k]: open(f,'a').write('\ndebugger;\nif (x == -0) {}\n')
for f in fs[k:2*k]:
  s=open(f,'rb').read(); open(f,'wb').write(s[:len(s)//2])
for f in fs[2*k:3*k]: os.remove(f)
for i,f in enumerate(fs[3*k:4*k]):
  open(f+'.new%d.ts'%i,'w').write(open(f,'rb').read().decode('utf8','replace')+'\nvar a = a;\n')
# same size, same mtime: overwrite content keeping size and restore mtime
for f in fs[4*k:5*k]:
  st=os.stat(f); s=bytearray(open(f,'rb').read())
  if len(s)>10:
    s[len(s)//2:len(s)//2+1]=b'\x01'
    open(f,'wb').write(bytes(s)); os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns))
print("  edited", 5*k, "files of", len(fs))
PY
$B $N > /dev/shm/o-ref3; $B --cache --cache-location $C $N > /dev/shm/o-w3; $B --cache --cache-location $C $N > /dev/shm/o-w4
r3=same; cmp -s /dev/shm/o-ref3 /dev/shm/o-w3 || r3=DIFF; r4=same; cmp -s /dev/shm/o-ref3 /dev/shm/o-w4 || r4=DIFF
echo "  after edits ($(wc -l < /dev/shm/o-ref3) lines): first cached run $r3, next $r4; cache $(stat -c %s $C) bytes, $(head -1 $C | cut -d' ' -f3) records"
cd /; rm -rf $D $C /dev/shm/o-*
