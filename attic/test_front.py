#!/usr/bin/env python3
"""Dumps vu.py's syntax tree in the uniform layout vuc uses, to check vuc's lexer and parser.
usage: test_front.py FILE.vu   (prints the dump, or the error report exactly as vu.py would)"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import vu  # noqa: E402


def ty(t):
    """vu.py's parsed type tuple -> vuc's canonical type string."""
    if t is None:
        return ''
    k = t[0]
    if k in ('int', 'float', 'bool', 'byte', 'str'):
        return k.capitalize()
    if k == 'cap':
        return t[1]
    if k == 'named':
        return t[1]
    if k == 'void':
        return '~void'
    if k == 'list':
        return '[' + ty(t[1]) + ']'
    if k == 'map':
        return '{' + ty(t[1]) + ': ' + ty(t[2]) + '}'
    if k == 'opt':
        return ty(t[1]) + '?'
    raise ValueError(t)


def N(k, line, name='', name2='', op='', v='', tyv='', ret='', ival=0, prec=-1, big=False, flag=False,
      flag2=False, elif_=False, par=False, kids=(), names=()):
    return dict(k=k, line=line, name=name, name2=name2, op=op, v=v, ty=tyv, ret=ret, ival=ival, prec=prec,
                big=big, flag=flag, flag2=flag2, elif_=elif_, par=par, kids=list(kids), names=list(names))


def block(stmts, line=0):
    return N('block', line, kids=[conv(s) for s in stmts])


def conv(n):
    k = n.k
    if k == 'const':
        return N('const', n.line, name=n.name, kids=[conv(n.expr)])
    if k == 'fn':
        params = N('params', n.line, kids=[N('param', pl, name=pn, tyv=ty(pt), flag=pv) for pn, pt, pv, pl in n.params])
        return N('fn', n.line, name=n.name, ret=ty(n.ret), flag=n.throws, kids=[params, block(n.body)])
    if k == 'type':
        return N('type', n.line, name=n.name, kids=[N('field', fl, name=fn, tyv=ty(ft)) for fn, ft, _, fl in n.fields])
    if k == 'enum':
        vs = [N('variant', vl, name=vn, kids=[N('field', fl, name=fn, tyv=ty(ft)) for fn, ft, _, fl in vf])
              for vn, vf, vl in n.variants]
        return N('enum', n.line, name=n.name, kids=vs)
    if k == 'if':
        kids = [conv(n.cond), block(n.body)]
        if n.els is not None:
            if len(n.els) == 1 and n.els[0].is_elif:
                kids.append(N('block', 0, kids=[conv(n.els[0])]))
            else:
                kids.append(block(n.els))
        return N('if', n.line, name=n.bind or '', flag=n.mut, flag2=n.bind is not None, elif_=n.is_elif, kids=kids)
    if k == 'while':
        return N('while', n.line, kids=[conv(n.cond), block(n.body)])
    if k == 'range':
        kids = [conv(n.start), conv(n.end)] + ([conv(n.step)] if n.step is not None else []) + [block(n.body)]
        return N('range', n.line, name=n.name, flag=n.incl, flag2=n.step is not None, par=n.par, kids=kids)
    if k == 'each':
        return N('each', n.line, name=n.name, name2=n.name2 or '', flag=n.mut, kids=[conv(n.seq), block(n.body)])
    if k == 'match':
        arms = [N('arm', line, name=pn, flag=binds is not None, names=binds or [], kids=[block(body)])
                for pn, binds, body, line in n.arms]
        return N('match', n.line, flag=n.mut, kids=[conv(n.subj)] + arms)
    if k == 'let':
        return N('let', n.line, name=n.name, flag=n.mut, tyv=ty(n.ty), kids=[conv(n.expr)])
    if k == 'return':
        return N('return', n.line, kids=[conv(n.expr)] if n.expr is not None else [])
    if k == 'fail':
        return N('fail', n.line, kids=[conv(n.expr)])
    if k in ('break', 'continue'):
        return N(k, n.line)
    if k == 'assign':
        return N('assign', n.line, op=n.op, kids=[conv(n.target), conv(n.expr)])
    if k == 'exprstmt':
        return N('exprstmt', n.line, kids=[conv(n.expr)])
    if k == 'orelse':
        return N('orelse', n.line, kids=[conv(n.e), conv(n.d)])
    if k == 'bin':
        return N('bin', n.line, op=n.op, kids=[conv(n.l), conv(n.r)])
    if k == 'un':
        return N('un', n.line, op=n.op, kids=[conv(n.e)])
    if k == 'ref':
        return N('ref', n.line, op='&', kids=[conv(n.e)])
    if k == 'call':
        args = [N('arg', a.line, name=nm or '', flag=nm is not None, kids=[conv(a)]) for nm, a in n.args]
        return N('call', n.line, kids=[conv(n.fn)] + args)
    if k == 'field':
        return N('field', n.line, name=n.name, kids=[conv(n.e)])
    if k == 'slice':
        return N('slice', n.line, kids=[conv(n.e), conv(n.lo), conv(n.hi)])
    if k == 'index':
        return N('index', n.line, kids=[conv(n.e), conv(n.i)])
    if k == 'try':
        return N('try', n.line, kids=[conv(n.e)])
    if k == 'int':
        big = n.v > 2 ** 63 - 1
        return N('int', n.line, ival=0 if big else n.v, big=big)
    if k == 'float':
        return N('float', n.line, v=n.v)
    if k == 'str':
        kids = []
        for p in n.parts:
            if isinstance(p, str):
                kids.append(N('text', n.line, v=p))
            else:
                e, (zero, width, prec, hexa) = p
                kids.append(N('part', n.line, name=zero, name2=width, prec=-1 if prec is None else prec, op=hexa,
                              kids=[conv(e)]))
        return N('str', n.line, kids=kids)
    if k == 'char':
        return N('char', n.line, ival=n.v)
    if k == 'name':
        return N('name', n.line, name=n.name)
    if k == 'bool':
        return N('bool', n.line, flag=n.v)
    if k == 'nil':
        return N('nil', n.line)
    if k == 'list':
        return N('list', n.line, kids=[conv(x) for x in n.items])
    if k == 'map':
        return N('map', n.line, kids=[N('pair', a.line, kids=[conv(a), conv(b)]) for a, b in n.pairs])
    raise ValueError(k)


def esc(s):
    return ''.join(ch if ' ' <= ch <= '~' and ch not in '\\|' else '\\%02x' % b for ch in s
                   for b in ([ord(ch)] if ' ' <= ch <= '~' and ch not in '\\|' else ch.encode('utf-8')))


def dump(d, depth, out):
    # Block lines aren't compared (vu.py has no block nodes).
    line = 0 if d['k'] == 'block' else d['line']
    fields = [d['k'], str(line), esc(d['name']), esc(d['name2']), d['op'], esc(d['v']), esc(d['ty']), esc(d['ret']),
              str(d['ival']), str(d['prec']), *('1' if d[f] else '0' for f in ('big', 'flag', 'flag2', 'elif_', 'par')),
              ','.join(esc(x) for x in d['names'])]
    out.append('  ' * depth + '|'.join(fields))
    for kid in d['kids']:
        dump(kid, depth + 1, out)


def main():
    path = sys.argv[1]
    src = open(path, encoding='utf-8').read()
    try:
        items = vu.Parser(vu.lex(src)).program()
    except vu.VuError as e:
        vu.report(path, src, e)
        sys.exit(1)
    except RecursionError:
        print(f'{path}: error: the program is nested too deeply to compile (simplify the deepest expression '
              f'or block)', file=sys.stderr)
        sys.exit(1)
    out = []
    for it in items:
        dump(conv(it), 0, out)
    print('\n'.join(out))


if __name__ == '__main__':
    sys.setrecursionlimit(60000)
    main()
