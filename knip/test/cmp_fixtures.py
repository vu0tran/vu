#!/usr/bin/env python3
# Runs knip and vknip on every fixture knip's own tests use (packages/knip/test/**/*.test.ts of the
# knip repo), with the options each test passes to createOptions mapped to command-line flags, and
# compares stdout, stderr, exit code (and, for --fix, the files left behind).
#   KNIPREPO=.../knip (the knip repo at the release) KNIP=.../knip.js VKNIP=.../vknip OUT=dir
#   python3 cmp_fixtures.py [--list] [--ref-only] [-j N] [PATTERN...]
# knip's results are cached in OUT/ref (delete a file to run knip again).
import os, re, sys, json, glob, shutil, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor

REPO = os.environ['KNIPREPO']; PK = REPO + '/packages/knip'
KNIP = os.environ.get('KNIP'); VKNIP = os.environ.get('VKNIP'); OUT = os.environ['OUT']
args = sys.argv[1:]
LIST = '--list' in args; HAVE = '--have-ref' in args; REF_ONLY = '--ref-only' in args; VERBOSE = '-v' in args
J = 2
if '-j' in args: J = int(args[args.index('-j') + 1]); args = [a for i, a in enumerate(args) if a != '-j' and (i == 0 or args[i - 1] != '-j')]
pats = [a for a in args if not a.startswith('-')]
SKIP_DIRS = ('util/', 'helpers/')

def flags_of(opts):
    """createOptions({...}) body -> list of flag lists (shorthand booleans give both variants)"""
    variants = [[]]
    def add(fl):
        for v in variants: v.extend(fl)
    def both(fl):
        nonlocal variants
        variants = [v + x for v in variants for x in ([], fl)]
    m = re.findall(r'\b(is[A-Za-z]+)\s*(?::\s*(true|false))?', opts)
    fmap = {'isProduction': ['--production'], 'isStrict': ['--strict'], 'isIncludeEntryExports': ['--include-entry-exports'],
            'isFix': ['--fix'], 'isUseTscFiles': ['--use-tsconfig-files'], 'isFormat': ['--format'],
            'isIsolateWorkspaces': ['--isolate-workspaces'], 'isCache': ['--cache'], 'isTreatConfigHintsAsErrors': ['--treat-config-hints-as-errors'],
            'isDisableConfigHints': ['--no-config-hints'], 'isSession': [], 'isShowProgress': [], 'isWatch': None,
            'isRemoveFiles': ['--allow-remove-files'], 'isNoGitIgnore': ['--no-gitignore'], 'isDebug': None, 'isTrace': None}
    for k, v in m:
        if k not in fmap: return None
        fl = fmap[k]
        if fl is None: return None
        if v == 'true': add(fl)
        elif v == '': both(fl)
    w = re.search(r"workspace:\s*(\[[^\]]*\]|'[^']*')", opts)
    if w:
        for x in re.findall(r"'([^']*)'", w.group(1)): add(['--workspace', x])
    t = re.search(r"tags:\s*\[([^\]]*)\]", opts)
    if t:
        add(['--tags', ','.join(re.findall(r"'([^']*)'", t.group(1)))])
    it = re.search(r"includedIssueTypes:\s*\[([^\]]*)\]", opts)
    if it:
        xs = re.findall(r"'([^']*)'", it.group(1))
        if not xs: return None
        for x in xs: add(['--include', x])
    ft = re.search(r"fixTypes:\s*\[([^\]]*)\]", opts)
    if ft:
        for x in re.findall(r"'([^']*)'", ft.group(1)): add(['--fix-type', x])
    a = re.search(r"args:\s*\{([^}]*)\}", opts)
    if a:
        if re.search(r"\bcache:\s*true", a.group(1)): add(['--cache'])
        if 'cache-location' in a.group(1): return None
    if re.search(r'\b(config|parsedConfig|tsConfigFile|cwd2|directory)\b', opts.replace('cwd,', '').replace('cwd:', '')):
        if re.search(r'\b(parsedConfig|config)\s*:', opts): return None
    return variants

def cases():
    out = []; seen = set()
    for tf in sorted(glob.glob(PK + '/test/**/*.test.ts', recursive=True)):
        rel = os.path.relpath(tf, PK + '/test')
        if rel.startswith(SKIP_DIRS): continue
        src = open(tf).read()
        for m in re.finditer(r'createOptions\(\{(.*?)\}\s*\)', src, re.S):
            body = m.group(1)
            before = src[:m.start()]
            cm = re.search(r"cwd\s*:\s*resolve\('([^']+)'\)", body)
            copy = False
            if cm: fx = cm.group(1)
            else:
                if not re.search(r'\bcwd\b', body): continue
                decl = list(re.finditer(r"const cwd\s*=\s*(resolve|await copyFixture)\('([^']+)'\)", before))
                if not decl: continue
                fx = decl[-1].group(2); copy = decl[-1].group(1) != 'resolve'
            fx = fx.rstrip('/')
            if not os.path.isdir(PK + '/' + fx): continue
            vs = flags_of(body)
            if vs is None: continue
            for fl in vs:
                if '--fix' in fl or '--cache' in fl: copy = True
                key = (fx, tuple(fl))
                if key in seen: continue
                seen.add(key)
                out.append({'test': rel, 'fixture': fx, 'flags': fl, 'copy': copy})
    return out

def cid(c):
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', c['fixture'].replace('fixtures/', '')) + ('__' + hashlib.md5(' '.join(c['flags']).encode()).hexdigest()[:6] if c['flags'] else '')

def snapshot(d):
    files = {}
    for root, dirs, fs in os.walk(d):
        dirs[:] = [x for x in dirs if x not in ('node_modules', '.git')]
        for f in fs:
            p = os.path.join(root, f)
            try: files[os.path.relpath(p, d)] = hashlib.md5(open(p, 'rb').read()).hexdigest()
            except OSError: pass
    return files

def run(cmd, c, tag):
    src = PK + '/' + c['fixture']
    if c['copy']:
        wd = OUT + '/tmp/' + cid(c)
        shutil.rmtree(wd, ignore_errors=True); shutil.copytree(src, wd, symlinks=True)
    else: wd = src
    try:
        p = subprocess.run(cmd + c['flags'], cwd=wd, capture_output=True, timeout=120, env=dict(os.environ, NO_COLOR='1', FORCE_COLOR='0'))
        r = {'out': p.stdout.decode('utf-8', 'replace'), 'err': p.stderr.decode('utf-8', 'replace'), 'code': p.returncode}
    except subprocess.TimeoutExpired:
        r = {'out': '', 'err': 'TIMEOUT', 'code': -1}
    if c['copy']:
        r['files'] = snapshot(wd)
        shutil.rmtree(wd, ignore_errors=True)
    return r

def norm(r):
    # knip prints its own timing in some messages; strip node's deprecation warnings
    err = '\n'.join(l for l in r['err'].split('\n') if 'ExperimentalWarning' not in l and 'node --trace-' not in l and 'DeprecationWarning' not in l)
    return r['out'], err.strip(), r['code'], r.get('files')

def main():
    cs = cases()
    if '--show' in args:
        c = [c for c in cs if cid(c) == pats[0]][0]
        k = json.load(open(OUT + '/ref/' + cid(c) + '.json')); v = run([VKNIP], c, 'v')
        import difflib
        print('#', c['test'], c['fixture'], ' '.join(c['flags']), 'code', k['code'], v['code'])
        for nm in ('out', 'err'):
            for l in difflib.unified_diff(k[nm].split('\n'), v[nm].split('\n'), 'knip.' + nm, 'vknip.' + nm, lineterm='', n=2): print(l)
        return
    if pats: cs = [c for c in cs if any(p in c['fixture'] or p in c['test'] for p in pats)]
    if HAVE: cs = [c for c in cs if os.path.exists(OUT + '/ref/' + cid(c) + '.json')]
    if LIST:
        for c in cs: print(cid(c), c['test'], ' '.join(c['flags']), '(copy)' if c['copy'] else '')
        print(len(cs), 'cases'); return
    os.makedirs(OUT + '/ref', exist_ok=True); os.makedirs(OUT + '/tmp', exist_ok=True)
    def ref(c):
        f = OUT + '/ref/' + cid(c) + '.json'
        if os.path.exists(f): return json.load(open(f))
        r = run(['node', KNIP], c, 'k'); json.dump(r, open(f, 'w')); return r
    def one(c):
        k = ref(c)
        if REF_ONLY: return c, True, ''
        v = run([VKNIP], c, 'v')
        a, b = norm(k), norm(v)
        why = []
        if a[0] != b[0]: why.append('stdout')
        if a[1] != b[1]: why.append('stderr')
        if a[2] != b[2]: why.append('code %s/%s' % (a[2], b[2]))
        if a[3] != b[3]: why.append('files')
        return c, not why, ' '.join(why)
    ok = 0; bad = []
    with ThreadPoolExecutor(J) as ex:
        for c, same, why in ex.map(one, cs):
            if same: ok += 1
            else: bad.append((c, why))
            if VERBOSE or not same: print(('SAME ' if same else 'DIFF ') + cid(c), why, flush=True)
    print('identical: %d/%d' % (ok, len(cs)))

main()
