# Translate the const descriptor tables of oxc_react_compiler globals.rs into Vu (rc_shapes_gen.vu).
import re, sys
src = open(sys.argv[1]).read()
src = re.sub(r'//[^\n]*', '', src)

def tokens(s):
    i = 0; out = []
    while i < len(s):
        c = s[i]
        if c.isspace(): i += 1; continue
        if c == '"':
            j = i + 1
            while s[j] != '"':
                j += 2 if s[j] == '\\' else 1
            out.append(('str', s[i+1:j])); i = j + 1; continue
        if s.startswith('..', i): out.append(('p', '..')); i += 2; continue
        if c.isalnum() or c == '_':
            m = re.match(r"[A-Za-z0-9_]+(::[A-Za-z0-9_]+)*", s[i:])
            out.append(('id', m.group(0))); i += len(m.group(0)); continue
        out.append(('p', c)); i += 1
    return out

class P:
    def __init__(s, t): s.t = t; s.i = 0
    def peek(s): return s.t[s.i] if s.i < len(s.t) else ('eof', '')
    def take(s, v=None):
        x = s.t[s.i]; s.i += 1
        if v is not None and x[1] != v: raise Exception("expected %s got %s at %d" % (v, x, s.i))
        return x
    def expr(s):
        k, v = s.peek()
        if v == '&': s.take(); return s.expr()
        if v == '[':
            s.take(); items = []
            while s.peek()[1] != ']':
                items.append(s.expr())
                if s.peek()[1] == ',': s.take()
            s.take(']'); return ('list', items)
        if k == 'str': s.take(); return ('str', v)
        if k == 'id':
            s.take()
            if s.peek()[1] == '{':
                s.take(); fields = []
                while s.peek()[1] != '}':
                    if s.peek()[1] == '..': s.take(); s.expr()
                    else:
                        n = s.take()[1]; s.take(':'); fields.append((n, s.expr()))
                    if s.peek()[1] == ',': s.take()
                s.take('}'); return ('struct', v, fields)
            if s.peek()[1] == '(':
                s.take(); args = []
                while s.peek()[1] != ')':
                    args.append(s.expr())
                    if s.peek()[1] == ',': s.take()
                s.take(')'); return ('call', v, args)
            return ('path', v)
        raise Exception("bad token %s" % (s.peek(),))

def snake(n): return re.sub(r'(?<!^)(?=[A-Z])', '_', n).upper()
EF = {'Read': 'EF_READ', 'Freeze': 'EF_FREEZE', 'Capture': 'EF_CAPTURE', 'ConditionallyMutateIterator': 'EF_COND_MUTATE_ITER',
      'ConditionallyMutate': 'EF_COND_MUTATE', 'Mutate': 'EF_MUTATE', 'Store': 'EF_STORE', 'Unknown': 'EF_UNKNOWN'}
def path(v):
    if v.startswith('Effect::'): return 'rc_hir.' + EF[v[8:]]
    if v.startswith('ValueKind::'): return 'rc_hir.VK_' + snake(v[11:])
    if v.startswith('ValueReason::'): return 'rc_hir.VR_' + snake(v[13:])
    if v.startswith('HookKind::'): return 'HK_' + snake(v[10:])
    if v == 'TypeDef::Primitive': return 'rc_hir.TPrimitive'
    if v == 'TypeDef::Poly': return 'rc_hir.TPoly'
    if v in ('true', 'false'): return v
    if v.startswith('BUILT_IN_') or v.startswith('REANIMATED_'): return v
    if v in ('PURE_PRIMITIVE_FN', 'SYMBOL_FN', 'FREEZE_ARGS_FN'): return v.lower() + '()'
    raise Exception('path ' + v)

NONE = {'rest_param': '-1', 'return_value_reason': '-1', 'shape_id': '""', 'canonical_name': '""', 'rest': '""',
        'setter_rest_param': '-1', 'aliasing': '[]'}
def vs(s): return '"' + s.replace('{', '{{').replace('}', '}}') + '"'
def field(n, e):
    if e == ('path', 'None'): return NONE[n]
    if e[0] == 'call' and e[1] == 'Some':
        x = emit(e[2][0])
        return '[' + x + ']' if n == 'aliasing' else x
    return emit(e)
AEC_FIELDS = {'value': 'a', 'place': 'a', 'from': 'a', 'receiver': 'a', 'into': 'b'}
def emit(e):
    k = e[0]
    if k == 'str': return vs(e[1])
    if k == 'path': return path(e[1])
    if k == 'list': return '[' + ', '.join(emit(x) for x in e[1]) + ']'
    if k == 'call':
        n, a = e[1], e[2]
        if n == 'TypeDef::Object': return 'tobj(' + emit(a[0]) + ')'
        if n == 'Method': return 'PropDef(' + emit(a[0]) + ', true, ' + emit(a[1]) + ', rc_hir.TPoly)'
        if n == 'Value': return 'PropDef(' + emit(a[0]) + ', false, MethodDef(), ' + emit(a[1]) + ')'
        if n == 'ApplyArgConfig::Place': return emit(a[0])
        if n == 'Some': return emit(a[0])
        raise Exception('call ' + n)
    if k == 'struct':
        n, fs = e[1], e[2]
        if n.startswith('AliasingEffectConfig::'):
            var = n.split('::')[1]
            parts = ['kind: AC_' + snake(var)]
            for fn_, fe in fs:
                if var == 'Create' and fn_ == 'value': parts.append('value: ' + emit(fe))
                elif fn_ == 'reason': parts.append('reason: ' + emit(fe))
                elif fn_ == 'function': parts.append('function: ' + emit(fe))
                elif fn_ == 'mutates_function': parts.append('mutates_function: ' + emit(fe))
                elif fn_ == 'args':
                    parts.append('args: [' + ', '.join('""' if x == ('path', 'ApplyArgConfig::Hole') else emit(x) for x in fe[1]) + ']')
                else: parts.append(AEC_FIELDS[fn_] + ': ' + emit(fe))
            return 'AEC(' + ', '.join(parts) + ')'
        name = {'AliasingSignatureConfig': 'AliasSig'}.get(n, n)
        return name + '(' + ', '.join(f + ': ' + field(f, x) for f, x in fs) + ')'
    raise Exception(k)

def table(name):
    m = re.search(r'const ' + name + r':[^=]*=\s*', src)
    p = P(tokens(src[m.end():]))
    return p.expr()

out = [open(sys.argv[3]).read()]
for cname in ['PURE_PRIMITIVE_FN', 'SYMBOL_FN', 'FREEZE_ARGS_FN']:
    out.append('fn %s() -> MethodDef:' % cname.lower())
    out.append('  return ' + emit(table(cname)))
    out.append('')
for tname, ty in [('BUILTIN_SHAPE_DEFS', 'ShapeDef'), ('STATE_SHAPE_DEFS', 'StateShapeDef'), ('REACT_HOOK_DEFS', 'HookDef'),
                  ('TYPED_GLOBAL_OBJECTS', 'GlobalObjectDef'), ('UNTYPED_GLOBALS', 'Str'), ('PRIMITIVE_GLOBAL_FNS', 'Str')]:
    t = table(tname)
    out.append('fn %s() -> [%s]:' % (tname.lower(), ty))
    out.append('  var r: [%s] = []' % ty)
    for item in t[1]:
        if item[0] == 'struct' and item[1] in ('ShapeDef', 'GlobalObjectDef'):
            fs = dict(item[2])
            key = 'id' if item[1] == 'ShapeDef' else 'name'
            out.append('  var p%d: [PropDef] = []' % len(out))
            pv = 'p%d' % (len(out) - 1)
            for pr in fs['props'][1]:
                out.append('  %s.push(%s)' % (pv, emit(pr)))
            out.append('  r.push(%s(%s, %s))' % (item[1], emit(fs[key]), pv))
        else:
            out.append('  r.push(%s)' % emit(item))
    out.append('  return r')
    out.append('')
open(sys.argv[2], 'w').write('\n'.join(out))
