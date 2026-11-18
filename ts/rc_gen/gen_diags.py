#!/usr/bin/env python3
# Translates oxc_react_compiler's diagnostics.rs constructors into Vu (rc_diags.vu).
# Handles: diagnostic(ErrorCategory::X, STR) then .with_help(STR), .with_note(STR),
# .with_label(SPAN.primary_label(STR)), .with_labels(SPAN.map(|span| span.primary_label(STR))),
# .with_labels(labels) (generic labels: one optional span), where STR is "..." or
# format!("...", args). Anything else becomes a stub listed on stderr.
import re, sys
src = open(sys.argv[1]).read()
out_path = sys.argv[2]

def rust_string(s, i):
    # a Rust string literal at s[i] ("..." or r"..."/r#"..."#): (value, end)
    if s[i] == 'r':
        j = i + 1; h = 0
        while s[j] == '#': h += 1; j += 1
        end = s.index('"' + '#' * h, j + 1)
        return s[j+1:end], end + 1 + h
    assert s[i] == '"'
    j = i + 1; out = ''
    while s[j] != '"':
        if s[j] == '\\':
            nx = s[j+1]
            if nx == '\n':
                j += 2
                while s[j] in ' \t\n': j += 1
                continue
            m = {'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}
            out += m.get(nx, nx); j += 2
        else:
            out += s[j]; j += 1
    return out, j + 1

def skip_ws(s, i):
    while i < len(s) and s[i] in ' \t\n,': i += 1
    return i

def balanced(s, i):
    d = 0; j = i
    while j < len(s):
        c = s[j]
        if c == '"' or (c == 'r' and s[j+1] in '#"' and not s[j-1].isalnum()):
            _, j = rust_string(s, j); continue
        if c in '([{': d += 1
        elif c in ')]}':
            d -= 1
            if d == 0: return j + 1
        j += 1
    return j

def vu_lit(text):
    # a Vu string for literal text: quotes and backslashes escaped, braces doubled
    t = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('{', '{{').replace('}', '}}')
    return '"' + t + '"'

class Unsupported(Exception): pass

def str_expr(e, params):
    # a Rust string expression -> Vu expression
    e = e.strip().rstrip(',').strip()
    if e.startswith('"') or e.startswith('r"') or e.startswith('r#'):
        v, end = rust_string(e, 0)
        if e[end:].strip(): raise Unsupported(e)
        return vu_lit(v)
    m = re.match(r'format!\((.*)\)$', e, re.S)
    if m:
        body = m.group(1)
        i = skip_ws(body, 0)
        fmt, j = rust_string(body, i)
        rest = body[j:].strip().lstrip(',').strip()
        args = []
        if rest:
            # split top-level commas
            d = 0; cur = ''
            for ch in rest:
                if ch in '([{': d += 1
                elif ch in ')]}': d -= 1
                if ch == ',' and d == 0: args.append(cur.strip()); cur = ''
                else: cur += ch
            if cur.strip(): args.append(cur.strip())
        out = ''; k = 0; ai = 0
        while k < len(fmt):
            c = fmt[k]
            if c == '{' and k + 1 < len(fmt) and fmt[k+1] == '{': out += '{{'; k += 2; continue
            if c == '}' and k + 1 < len(fmt) and fmt[k+1] == '}': out += '}}'; k += 2; continue
            if c == '{':
                end = fmt.index('}', k)
                inner = fmt[k+1:end]
                name = inner.split(':')[0]
                if name == '':
                    if ai >= len(args): raise Unsupported(e)
                    a = args[ai]; ai += 1
                else:
                    a = name
                a = conv_arg(a, params)
                out += '{' + a + '}'
                k = end + 1; continue
            if c == '"': out += '\\"'
            elif c == '\\': out += '\\\\'
            elif c == '\n': out += '\\n'
            else: out += c
            k += 1
        return '"' + out + '"'
    if e in params: return conv_arg(e, params)
    raise Unsupported(e)

def conv_arg(a, params):
    a = a.strip()
    if re.match(r'^[a-z_][a-z0-9_]*$', a): return a
    m = re.match(r'^([a-z_][a-z0-9_]*)\.as_str\(\)$', a)
    if m: return m.group(1)
    raise Unsupported(a)

def conv_params(sig):
    # (name: type, ...) -> Vu params, and the names
    ps = []; names = {}
    d = 0; cur = ''
    for ch in sig:
        if ch in '<([': d += 1
        elif ch in '>)]': d -= 1
        if ch == ',' and d == 0: ps.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): ps.append(cur.strip())
    out = []
    for p in ps:
        if not p: continue
        n, t = [x.strip() for x in p.split(':', 1)]
        if t in ('Span', 'Option<Span>'): vt = 'Sp'
        elif t == 'T' or t.startswith('impl Into<oxc_diagnostics::LabeledSpan>') or t == 'impl Into<LabeledSpan>': vt = 'Sp'
        elif t in ('&str', 'impl Display', 'impl AsRef<str>', 'String', '&String', 'impl std::fmt::Display', 'impl Into<String>'): vt = 'Str'
        elif t in ('bool',): vt = 'Bool'
        elif t in ('u32', 'usize', 'i64', 'u64'): vt = 'Int'
        else: raise Unsupported(t)
        out.append('%s: %s' % (n, vt)); names[n] = vt
    return ', '.join(out), names

cats = {}
fns = []
pos = 0
for m in re.finditer(r'pub fn ([a-z0-9_]+)(<[^>]*>)?\(', src):
    name = m.group(1)
    if name in ('as_str',): continue
    i = m.end() - 1
    j = balanced(src, i)
    sig = src[i+1:j-1]
    k = src.index('{', j)
    if 'OxcDiagnostic' not in src[j:k]: continue
    e = balanced(src, k)
    body = src[k+1:e-1].strip()
    fns.append((name, sig, body))

lines = ['# Generated by gen_diags.py from oxc_react_compiler 1.90.0 diagnostics.rs: the compiler\'s',
         '# diagnostic constructors, one per Rust function, with the same names. A span parameter is a',
         '# Sp (start -1: none).', '', 'import rc_env', 'from rc_hir import Sp', 'from rc_env import Diag', '']
stubs = []
for name, sig, body in fns:
    try:
        vparams, names = conv_params(sig)
        b = re.sub(r'\s+', ' ', body)
        b = re.sub(r'\|span\| \{ (span\.primary_label\(.*?\)) \}', r'|span| \1', b)
        mh = re.match(r'^diagnostic_with_help_and_label\(\s*ErrorCategory::([A-Za-z]+)\s*,\s*(.*)\)$', b)
        if mh:
            # (category, message, help, span, label)
            args = []; d = 0; cur = ''; k2 = 0; txt = mh.group(2)
            while k2 < len(txt):
                ch = txt[k2]
                if ch == '"':
                    _, e2 = rust_string(txt, k2); cur += txt[k2:e2]; k2 = e2; continue
                if ch in '([{': d += 1
                elif ch in ')]}': d -= 1
                if ch == ',' and d == 0: args.append(cur.strip()); cur = ''
                else: cur += ch
                k2 += 1
            if cur.strip(): args.append(cur.strip())
            if len(args) != 4 or args[2] not in names: raise Unsupported('help_and_label')
            catn = re.sub(r'(?<!^)(?=[A-Z])', '_', mh.group(1)).upper()
            expr = 'rc_env.with_label(rc_env.with_help(rc_env.diag(rc_env.EC_%s, %s), %s), %s, %s)' % (catn, str_expr(args[0], names), str_expr(args[1], names), args[2], str_expr(args[3], names))
            lines.append('fn %s(%s) -> Diag:' % (name, vparams))
            lines.append('  return ' + expr)
            lines.append('')
            continue
        m = re.match(r'^diagnostic\(\s*ErrorCategory::([A-Za-z]+)\s*,\s*', b)
        if not m: raise Unsupported('start')
        cat = m.group(1)
        i = m.end() - 1
        # the reason: up to the matching ')' of diagnostic(
        start = b.index('(')
        end = balanced(b, start)
        reason = b[m.end():end-1].strip()
        expr = 'rc_env.diag(rc_env.EC_%s, %s)' % (re.sub(r'(?<!^)(?=[A-Z])', '_', cat).upper(), str_expr(reason, names))
        rest = b[end:].strip()
        while rest:
            mm = re.match(r'^\.with_(help|note)\(', rest)
            if mm:
                s0 = rest.index('(')
                s1 = balanced(rest, s0)
                expr = 'rc_env.with_%s(%s, %s)' % (mm.group(1), expr, str_expr(rest[s0+1:s1-1], names))
                rest = rest[s1:].strip(); continue
            mm = re.match(r'^\.with_label\(\s*([a-z_]+)\.primary_label\(', rest)
            if mm:
                s0 = rest.index('(')
                s1 = balanced(rest, s0)
                inner = rest[s0+1:s1-1].strip()
                pl = inner.index('primary_label(') + len('primary_label')
                pe = balanced(inner, pl)
                expr = 'rc_env.with_label(%s, %s, %s)' % (expr, mm.group(1), str_expr(inner[pl+1:pe-1], names))
                rest = rest[s1:].strip(); continue
            mm = re.match(r'^\.with_labels\(\s*([a-z_]+)\.map\(\|([a-z_]+)\|\s*([a-z_]+)\.primary_label\(', rest)
            if mm:
                s0 = rest.index('(')
                s1 = balanced(rest, s0)
                inner = rest[s0+1:s1-1].strip()
                pl = inner.index('primary_label(') + len('primary_label')
                pe = balanced(inner, pl)
                expr = 'rc_env.with_label(%s, %s, %s)' % (expr, mm.group(1), str_expr(inner[pl+1:pe-1], names))
                rest = rest[s1:].strip(); continue
            mm = re.match(r'^\.with_label\(\s*primary_label\(\s*([a-z_]+)\s*\)\s*\)', rest)
            if mm and mm.group(1) in names:
                expr = 'rc_env.with_label_plain(%s, %s)' % (expr, mm.group(1))
                rest = rest[mm.end():].strip(); continue
            mm = re.match(r'^\.with_label\(\s*([a-z_]+)\s*\)', rest)
            if mm and mm.group(1) in names:
                expr = 'rc_env.with_label_plain(%s, %s)' % (expr, mm.group(1))
                rest = rest[mm.end():].strip(); continue
            mm = re.match(r'^\.with_labels\(\s*([a-z_]+)\s*\)', rest)
            if mm and mm.group(1) in names:
                expr = 'rc_env.with_label_plain(%s, %s)' % (expr, mm.group(1))
                rest = rest[mm.end():].strip(); continue
            raise Unsupported(rest[:80])
        lines.append('fn %s(%s) -> Diag:' % (name, vparams))
        lines.append('  return ' + expr)
        lines.append('')
    except Unsupported as ex:
        stubs.append((name, str(ex)[:100]))
# (a Rust string continuation after \\n leaves no leading space: diagnostic_with_help_and_label's help goes through a path that keeps one)
open(out_path, 'w').write('\n'.join(lines).replace('\\n * ', '\\n* '))
print('translated %d, by hand %d' % (len(fns) - len(stubs), len(stubs)), file=sys.stderr)
for n, why in stubs: print('  %s: %s' % (n, why), file=sys.stderr)
