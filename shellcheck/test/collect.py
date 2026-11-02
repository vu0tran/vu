# collect.py SRC DST [MAXBYTES]: copy the shell scripts under SRC (by extension or shebang, zsh
# excluded, files up to MAXBYTES, default 400000) to DST
import os, sys, shutil, re
src, dst = sys.argv[1], sys.argv[2]
maxb = int(sys.argv[3]) if len(sys.argv) > 3 else 400000
n = 0
for root, dirs, files in os.walk(src):
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'vendor', 'third_party', '_output')]
    for f in files:
        p = os.path.join(root, f)
        if os.path.islink(p): continue
        try:
            if os.path.getsize(p) > maxb: continue
        except OSError: continue
        ok = False
        if f.endswith(('.zsh', '.zsh-theme')): continue
        if f.endswith(('.sh', '.bash', '.ksh', '.bats', '.dash')): ok = True
        else:
            try:
                with open(p, 'rb') as fh: h = fh.readline(120)
            except OSError: continue
            if h.startswith(b'#!'):
                hs = h.decode('latin1')
                if 'zsh' in hs: continue
                if any(k in hs for k in ('bash', '/sh', 'env sh', 'ksh', 'dash', 'bats')): ok = True
        if not ok: continue
        try:
            data = open(p, 'rb').read()
        except OSError: continue
        if b'\0' in data: continue
        rel = os.path.relpath(p, src)
        rel = '/'.join(re.sub(r"[^A-Za-z0-9._/+=-]", '_', c).lstrip('-') or '_' for c in rel.split('/'))
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(p, out); n += 1
print(n)
