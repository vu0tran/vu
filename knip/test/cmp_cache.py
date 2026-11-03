#!/usr/bin/env python3
# --cache: a project is copied (node_modules linked), then edited step by step; after each step knip
# (no cache) and vknip with --cache must give the same output, and vknip without --cache too.
#   KNIP=.../knip.js VKNIP=.../vknip python3 cmp_cache.py PROJECT_DIR OUT_DIR
import os, sys, shutil, subprocess, time
KNIP = os.environ['KNIP']; VK = os.environ['VKNIP']
src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
d = os.path.join(out, os.path.basename(src))
shutil.rmtree(d, ignore_errors=True)
def ign(dirpath, names): return [n for n in names if n in ('node_modules', '.git')]
shutil.copytree(src, d, ignore=ign, symlinks=True)
if os.path.exists(os.path.join(src, 'node_modules')):
    os.makedirs(os.path.join(d, 'node_modules'))
    for n in os.listdir(os.path.join(src, 'node_modules')):
        if n == '.cache': continue
        os.symlink(os.path.join(src, 'node_modules', n), os.path.join(d, 'node_modules', n))
subprocess.run(['git', 'init', '-q'], cwd=d)
def run(cmd, extra=[]):
    r = subprocess.run(cmd + extra, cwd=d, capture_output=True, text=True)
    return (r.stdout, r.stderr, r.returncode)
def files(ext=('.js', '.ts', '.mjs', '.tsx')):
    out = []
    for root, dirs, fs in os.walk(d):
        dirs[:] = sorted(x for x in dirs if x not in ('node_modules', '.git'))
        for f in sorted(fs):
            if f.endswith(ext) and not f.endswith('.d.ts'): out.append(os.path.join(root, f))
    return out
same = total = 0
def check(label, flags=[]):
    global same, total
    ref = run(['node', KNIP], flags)
    for vflags in (['--cache'], ['--cache'], []):
        got = run([VK], vflags + flags)
        total += 1
        if got == ref: same += 1
        else:
            what = [n for n, a, b in zip(('stdout', 'stderr', 'code'), ref, got) if a != b]
            print(f'DIFF {label} {" ".join(vflags + flags)}: {" ".join(what)}')
            if os.environ.get('V'): print(ref[0][:2000], '\n----\n', got[0][:2000], got[1][:2000])
check('initial')
fs_ = files()
# same content, newer modification time
os.utime(fs_[0], (time.time() + 5, time.time() + 5)); check('touched')
# an unused export added to every third file
for f in fs_[::3]:
    open(f, 'a').write('\nexport const __vknip_cache_probe = 1;\n')
check('exports added')
# a file emptied (its imports gone)
for f in fs_:
    if 'import' in open(f, errors='replace').read() and not f.endswith('.config.js'):
        open(f, 'w').write('export {};\n'); break
check('file emptied')
# a file deleted, a new one added
os.remove(fs_[-1]); check('file deleted')
open(os.path.join(d, 'vknip-new.ts'), 'w').write("import './vknip-new2';\nexport const x = 1;\n")
open(os.path.join(d, 'vknip-new2.ts'), 'w').write("export const y = 1;\n")
check('files added')
check('production', ['--production'])
check('production again', ['--production'])
check('tags', ['--tags=-internal'])
loc = os.path.join(out, 'cache-loc-' + os.path.basename(src))
shutil.rmtree(loc, ignore_errors=True)
check('cache location', ['--cache-location', loc])
assert os.listdir(loc), 'nothing written to --cache-location'
# a damaged cache file
for f in os.listdir(loc): open(os.path.join(loc, f), 'r+b').truncate(100)
check('damaged cache', ['--cache-location', loc])
for f in os.listdir(loc): open(os.path.join(loc, f), 'wb').write(b'\0\0garbage')
check('garbage cache', ['--cache-location', loc])
print(f'{os.path.basename(src)}: identical: {same}/{total}')
