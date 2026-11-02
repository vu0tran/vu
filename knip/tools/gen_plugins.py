# Writes plugins.vu's table from tools/plugins.json (node tools/dump_plugins.mjs > tools/plugins.json:
# the static fields of knip's plugins).
import json, os
d = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(d, 'plugins.json')))
def vs(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('{', '{{').replace('}', '}}') + '"'
def lst(xs):
    out = []
    for x in xs or []:
        if isinstance(x, dict) and 're' in x: out.append(vs('/' + x['re']))
        elif isinstance(x, str): out.append(vs(x))
    return '[' + ', '.join(out) + ']'
rows = []
for p in P:
    en = p['enablers'] if isinstance(p['enablers'], list) else ([p['enablers']] if isinstance(p['enablers'], str) and p['enablers'] != 'fn' and not p['isEnabled'] else [])
    if isinstance(p['enablers'], str) and p['isEnabled'] and 'hasDependency' in (p['isEnabled'] or '') and p['enablers'] != 'fn':
        en = []
    if p['name'] == 'tsx': en = ['tsx']
    cfg = p['config'] if isinstance(p['config'], list) else []
    pj = p['packageJsonPath'] if isinstance(p['packageJsonPath'], str) else ''
    rows.append(f"  t.push(Plugin({vs(p['name'])}, {vs(p['title'])}, {lst(en)}, {str(p['isRootOnly']).lower()}, {lst(cfg)}, {lst(p['entry'])}, {lst(p['production'])}, {lst(p['project'])}, {vs(pj)}, {str(p['resolveConfig']).lower()}, {str(p['resolveFromAST']).lower()}, {str(p['resolve']).lower()}))")
src = open(os.path.join(d, '..', 'plugins.vu')).read()
a = src.index('# BEGIN TABLE\n') + len('# BEGIN TABLE\n'); b = src.index('  # END TABLE\n')
src = src[:a] + '\n'.join(rows) + '\n' + src[b:]
open(os.path.join(d, '..', 'plugins.vu'), 'w').write(src)
