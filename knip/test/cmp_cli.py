#!/usr/bin/env python3
"""cmp_cli.py: the `exec('knip ...', { cwd })` commands of knip's own tests (test/**/*.ts), run with
knip and with vknip; compares stdout, stderr and the exit status (NO_COLOR=1, trimmed, as the tests'
exec helper does). Commands that write files (--output-file, --fix, --cache, --watch) are skipped.

usage: KNIP=.../knip.js VKNIP=.../vknip cmp_cli.py KNIP_PACKAGE_DIR [--show N] [--list] [PATTERN...]
"""
import os, re, subprocess, sys

def find_cases(pkg):
    cases = []
    for root, _, files in os.walk(os.path.join(pkg, 'test')):
        for f in sorted(files):
            if not f.endswith('.ts'):
                continue
            path = os.path.join(root, f)
            src = open(path).read()
            if 'exec(' not in src:
                continue
            names = {}
            for m in re.finditer(r"const (\w+) = resolve\('([^']+)'\)", src):
                names[m.group(1)] = m.group(2)
            for m in re.finditer(r"exec\(\s*(['`])(knip[^'`]*)\1\s*,\s*\{\s*cwd(?:\s*:\s*(\w+|resolve\('([^']+)'\)))?\s*,?\s*\}", src):
                cmd = m.group(2)
                var = m.group(3)
                if m.group(4):
                    cwd = m.group(4)
                elif var is None:
                    cwd = names.get('cwd')
                else:
                    cwd = names.get(var)
                if cwd is None:
                    continue
                if '${' in cmd:
                    if re.search(r"\$\{(?!cwd\})", cmd):
                        continue
                    cmd = cmd.replace('${cwd}', os.path.join(pkg, cwd))
                if re.search(r'--(output-file|fix|cache|watch)\b|-f\b|-w\b', cmd):
                    continue
                rel = os.path.relpath(path, pkg)
                cases.append((rel, cwd, cmd))
    seen = set()
    out = []
    for c in cases:
        if (c[1], c[2]) in seen:
            continue
        seen.add((c[1], c[2]))
        out.append(c)
    return out

def run(tool, pkg, cwd, cmd):
    args = cmd[len('knip'):].strip().split(' ')
    args = [a for a in args if a]
    env = dict(os.environ)
    env['NO_COLOR'] = '1'
    env.pop('FORCE_COLOR', None)
    argv = ['node', tool] if tool.endswith('.js') else [tool]
    p = subprocess.run(argv + args, cwd=os.path.join(pkg, cwd), env=env, capture_output=True, timeout=300)
    return p.stdout.decode(errors='replace').strip(), p.stderr.decode(errors='replace').strip(), p.returncode

def norm(s):
    # (stack traces of crashes name the tool's own files)
    return re.sub(r'\n    at .*', '', s)

def main():
    pkg = sys.argv[1]
    rest = sys.argv[2:]
    show = None
    listing = False
    pats = []
    i = 0
    while i < len(rest):
        if rest[i] == '--show':
            show = int(rest[i + 1]); i += 2; continue
        if rest[i] == '--list':
            listing = True; i += 1; continue
        pats.append(rest[i]); i += 1
    cases = find_cases(pkg)
    knip, vknip = os.environ['KNIP'], os.environ['VKNIP']
    same = 0
    n = 0
    for k, (rel, cwd, cmd) in enumerate(cases):
        if pats and not any(p in rel or p in cwd or p in cmd for p in pats):
            continue
        if show is not None and k != show:
            continue
        if listing:
            print(k, rel, cwd, cmd)
            continue
        n += 1
        a = run(knip, pkg, cwd, cmd)
        b = run(vknip, pkg, cwd, cmd)
        ok = a[0] == b[0] and norm(a[1]) == norm(b[1]) and a[2] == b[2]
        if ok:
            same += 1
        else:
            what = [w for w, x, y in (('stdout', a[0], b[0]), ('stderr', norm(a[1]), norm(b[1]))) if x != y]
            if a[2] != b[2]:
                what.append('code %d/%d' % (a[2], b[2]))
            print('DIFF %d %s [%s] %s: %s' % (k, rel, cwd, cmd, ' '.join(what)))
            if show is not None:
                import difflib
                for name, x, y in (('stdout', a[0], b[0]), ('stderr', a[1], b[1])):
                    if x != y:
                        sys.stdout.writelines(difflib.unified_diff((x + '\n').splitlines(True), (y + '\n').splitlines(True), 'knip.' + name, 'vknip.' + name))
    if not listing:
        print('identical: %d/%d' % (same, n))

main()
