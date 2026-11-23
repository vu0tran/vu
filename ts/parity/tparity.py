#!/usr/bin/env python3
# Type-aware parity of vlint against oxlint + tsgolint on one run of each (unix format).
# usage: tparity.py REF OUT ERR TRULES DIFF
#   REF: oxlint's output; OUT: vlint's; ERR: vlint's stderr with VLINT_VTSC_DEBUG=2 (the files vtsc
#   didn't type: "vlint: vtsc: NOT FILE: why"); TRULES: ts/trules.vu (its PORTED list names the
#   type-aware rules); DIFF: written, one "MISS file:line:col rule: message" or "EXTRA ..." line per
#   difference in the files vtsc typed.
import os, sys, re, collections
ref_p, out_p, err_p, trules_p, diff_p = sys.argv[1:6]
ported = set(re.search(r'const PORTED = "([^"]*)"', open(trules_p).read()).group(1).split())
JS = os.environ['VLINT_CORPUS'].rstrip('/') + '/'
LINE = re.compile(r'^(.*?):(\d+):(\d+): (.*) \[(\w+)/([\w-]+)\(([\w/-]+)\)\]$')

def load(p):
    ta, other = collections.Counter(), collections.Counter()
    for l in open(p, errors='replace'):
        l = l.rstrip('\n')
        m = LINE.match(l)
        if not m: continue
        f, ln, col, msg, sev, plug, rule = m.groups()
        if f.startswith(JS): f = f[len(JS):]
        key = (f, int(ln), int(col), rule, msg)
        if plug == 'typescript' and rule in ported: ta[key] += 1
        else: other[key] += 1
    return ta, other

rta, rother = load(ref_p)
vta, vother = load(out_p)
untyped = set()
nolint = set()   # (checked, but its rules didn't run: what they reached isn't modeled, or type errors)
for l in open(err_p, errors='replace'):
    m = re.match(r'vlint: vtsc: (?:\(inferred\) )?(NOT|NOLINT) (\S+)', l)
    if m:
        f = m.group(2).rstrip(':')
        if f.startswith(JS): f = f[len(JS):]
        untyped.add(f)
        if m.group(1) == 'NOLINT': nolint.add(f)

same = sum((rta & vta).values())
print(f"type-aware: tsgolint {sum(rta.values())}, vlint {sum(vta.values())}, same {same} ({100.0 * same / max(1, sum(rta.values())):.1f}% coverage)")
rt = collections.Counter({k: v for k, v in rta.items() if k[0] not in untyped})
vt = collections.Counter({k: v for k, v in vta.items() if k[0] not in untyped})
miss, extra = rt - vt, vt - rt
print(f"  in typed files: tsgolint {sum(rt.values())}, same {sum((rt & vt).values())}, missing {sum(miss.values())}, extra {sum(extra.values())}")
uf = {k[0] for k in rta if k[0] in untyped}
print(f"  files vtsc did not type: {len(untyped)}; tsgolint diagnostics in them: {sum(v for k, v in rta.items() if k[0] in untyped)}")
print(f"    of them checked but not linted (NOLINT): {len(nolint)}; tsgolint diagnostics in them: {sum(v for k, v in rta.items() if k[0] in nolint)}")
def by_rule(c):
    r = collections.Counter()
    for k, v in c.items(): r[k[3]] += v
    return ', '.join(f'{a} {b}' for a, b in r.most_common(8))
print('  missing by rule:', by_rule(miss))
print('  extra by rule:', by_rule(extra))
print(f"other rules: oxlint {sum(rother.values())}, vlint {sum(vother.values())}, only oxlint {sum((rother - vother).values())}, only vlint {sum((vother - rother).values())}")
with open(diff_p, 'w') as o:
    for tag, c in (('MISS', miss), ('EXTRA', extra)):
        for k in sorted(c):
            for _ in range(c[k]): o.write(f"{tag} {k[0]}:{k[1]}:{k[2]} {k[3]}: {k[4]}\n")
