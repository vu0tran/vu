#!/usr/bin/env python3
"""Vu v0 compiler: translates .vu source to C, then builds a native binary with the C compiler.

Usage:
  vu check FILE.vu [--time] [--json]
      report errors only: no binary and no C compiler, so it takes milliseconds
  vu run [--release] [--json] FILE.vu [ARGS...]
      quick unoptimized build (-O0), then run it with ARGS; --release builds optimized first.
      A panic prints the chain of calls that led to it (in quick builds).
  vu build FILE.vu [-o OUT] [--debug] [--malloc] [--san] [--san-pool] [--tsan] [--emit-c FILE] [--time]
      optimized binary (-O3); --debug builds quickly instead
  --json: compile errors and panics are printed to stderr as one JSON object per line
"""
import copy
import os
import re
import subprocess
import sys
import tempfile
import time


class VuError(Exception):
    def __init__(self, line, msg):
        super().__init__(msg)
        self.line, self.msg = line, msg


def err(line, msg):
    raise VuError(line, msg)


# ----------------------------------------------------------------------------- lexer

KEYWORDS = {'fn', 'type', 'let', 'var', 'const', 'if', 'elif', 'else', 'while', 'for', 'in', 'by',
            'return', 'break', 'continue', 'and', 'or', 'not', 'true', 'false', 'nil', 'par', 'match', 'fail',
            'throws'}

TOKEN_RE = re.compile(r'''
    (?P<ws>[ \t]+) | (?P<comment>\#.*) |
    (?P<float>\d[\d_]*\.\d[\d_]*(?:[eE][+-]?\d+)? | \d[\d_]*[eE][+-]?\d+) |
    (?P<int>0[xX]_*[0-9a-fA-F][0-9a-fA-F_]* | \d[\d_]*) |
    (?P<name>[A-Za-z_][A-Za-z0-9_]*) |
    (?P<str>"(?:[^"\\]|\\.)*") |
    (?P<char>'(?:[^'\\]|\\.)') |
    (?P<op>\.\.=|\.\.|->|=>|<<|>>|==|!=|<=|>=|\+=|-=|\*=|/=|%=|\|=|&=|\^=|[-+*/%<>=()\[\]{},:.?&|^])
''', re.X | re.ASCII)

# Source text is ASCII: only these count as whitespace (a non-breaking space is an unexpected character).
WS = ' \t\n\r\x0b\x0c'


class Tok:
    __slots__ = ('k', 'v', 'line')

    def __init__(self, k, v, line):
        self.k, self.v, self.line = k, v, line


def desc(t):
    return {'NL': 'end of line', 'INDENT': 'an indented block', 'DEDENT': 'end of block',
            'EOF': 'end of file'}.get(t.k, repr(t.v))


def char_desc(ch):
    """Printable ASCII as Python would quote it; anything else (invisible, non-ASCII) by code point."""
    return repr(ch) if '!' <= ch <= '~' else f'U+{ord(ch):04X}'


def lex(src, at_line=None, base=0):
    """at_line: lexing an interpolation inside a string on that line; errors point there.
    base: the file's index << 24, added to every line (0 for the main file; see LINE_BITS)."""
    toks, indents, depth = [], [0], 0
    lines = src.split('\n')
    for ln, raw in enumerate(lines, 1):
        if at_line is not None:
            ln = at_line
        else:
            ln += base
        line = raw.rstrip(WS)
        body = line.lstrip(' \t')
        if depth == 0:
            if not body or body.startswith('#'):
                continue
            lead = line[:len(line) - len(body)]
            if '\t' in lead:
                err(ln, 'indent with spaces, not tabs')
            ind = len(lead)
            if ind > indents[-1]:
                indents.append(ind)
                toks.append(Tok('INDENT', None, ln))
            else:
                while ind < indents[-1]:
                    indents.pop()
                    toks.append(Tok('DEDENT', None, ln))
                if ind != indents[-1]:
                    err(ln, 'indentation does not line up with any enclosing block')
        pos = len(line) - len(body)
        while pos < len(line):
            if line[pos] == '"':
                end = scan_string(line, pos)
                if end > 0:   # (otherwise the plain rule below reports what's wrong, as it always has)
                    toks.append(Tok('str', line[pos:end], ln))
                    pos = end
                    continue
            m = TOKEN_RE.match(line, pos)
            if not m:
                err(ln, f'unexpected character {char_desc(line[pos])}')
            kind, text, pos = m.lastgroup, m.group(), m.end()
            if kind in ('ws', 'comment'):
                continue
            # Names from modules are module__name, and a module's name starts with a letter, so only a
            # '__' after leading underscores could clash.
            if kind == 'name' and '__' in text.lstrip('_'):
                err(ln, f"'{text}': names can't contain '__' (Vu uses it to name things from modules)")
            if kind == 'name' and text in KEYWORDS:
                kind = 'kw'
            if kind == 'op' and text in ('(', '[', '{'):
                depth += 1
            elif kind == 'op' and text in (')', ']', '}'):
                depth = max(0, depth - 1)
            toks.append(Tok(kind, text, ln))
        if depth == 0 and toks and toks[-1].k not in ('NL', 'INDENT', 'DEDENT'):
            toks.append(Tok('NL', None, ln))
    end = at_line if at_line is not None else base + len(lines)
    if toks and toks[-1].k not in ('NL', 'INDENT', 'DEDENT'):
        toks.append(Tok('NL', None, end))
    while len(indents) > 1:
        indents.pop()
        toks.append(Tok('DEDENT', None, end))
    toks.append(Tok('EOF', None, end))
    return toks


# ----------------------------------------------------------------------------- parser

class Node:
    is_elif = False
    par = False

    def __init__(self, k, line, **kw):
        self.k, self.line = k, line
        self.__dict__.update(kw)


ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"', '0': '\0'}
COMPARE = ('==', '!=', '<', '>', '<=', '>=')
ASSIGN_OPS = ('=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=')


def scan_string(s, i):
    """One past the closing quote of the string literal starting at s[i], or -1 if it isn't closed
    on this line. An interpolation may contain strings of its own, as in Python 3.12: "{m["k"]}"."""
    j = i + 1
    while j < len(s):
        c = s[j]
        if c == '\\':
            j += 2
        elif c == '"':
            return j + 1
        elif c == '{' and s[j + 1:j + 2] == '{':
            j += 2
        elif c == '{':
            j = scan_interp(s, j + 1)
            if j < 0:
                return -1
        else:
            j += 1
    return -1


def scan_interp(s, j):
    """From just after an interpolation's '{' to just after its '}', skipping the strings, Byte
    literals and braces inside it; -1 if it doesn't close."""
    depth = 0
    while j < len(s):
        c = s[j]
        if c == '"':
            j = scan_string(s, j)
            if j < 0:
                return -1
            continue
        if c == "'":
            j += 1
            j += 2 if s[j:j + 1] == '\\' else 1
            if s[j:j + 1] == "'":
                j += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            if depth == 0:
                return j + 1
            depth -= 1
        j += 1
    return -1


def parse_interp(raw, line):
    """Split a string literal body into text pieces and (expr, precision) pieces."""
    parts, buf, i = [], [], 0
    while i < len(raw):
        c = raw[i]
        if c == '\\':
            nxt = raw[i + 1:i + 2]
            if nxt not in ESCAPES:
                err(line, f"unknown escape '\\{nxt}' in string")
            buf.append(ESCAPES[nxt])
            i += 2
        elif c == '{':
            if raw[i + 1:i + 2] == '{':
                buf.append('{')
                i += 2
                continue
            j = scan_interp(raw, i + 1) - 1   # the matching '}'
            if j < 0:
                err(line, "unclosed '{' in string (write '{{' for a literal brace)")
            inner, spec = raw[i + 1:j].strip(WS), ('', '', None, '')
            # Python-style format spec: {x:8} width, {x:08x} zero-padded hex, {x:.9} decimals
            m = re.fullmatch(r'(.*):(0?)(\d*)(?:\.(\d+))?(x?)', inner, re.S | re.ASCII)
            if m and any(m.group(k) for k in (2, 3, 4, 5)):
                inner = m.group(1).strip(WS)
                spec = (m.group(2), m.group(3), None if m.group(4) is None else int(m.group(4)), m.group(5))
                if spec[1] and int(spec[1]) > 1000:
                    err(line, f'format width {spec[1]} is too large (at most 1000)')
                if spec[2] is not None and spec[2] > 100:
                    err(line, f'format precision {spec[2]} is too large (at most 100)')
            if not inner:
                err(line, "empty '{}' in string")
            if buf:
                parts.append(''.join(buf))
                buf = []
            toks = lex(inner, line)
            for t in toks:
                t.line = line
            p = Parser(toks)
            p.depth = PARSE_DEPTH[0]
            e = p.expr()
            p.expect('NL', what="'}'")
            parts.append((e, spec))
            i = j + 1
        elif c == '}':
            if raw[i + 1:i + 2] == '}':
                buf.append('}')
                i += 2
                continue
            err(line, "single '}' in string (write '}}' for a literal brace)")
        else:
            buf.append(c)
            i += 1
    if buf:
        parts.append(''.join(buf))
    return parts


PARSE_DEPTH = [0]   # the depth of the parser that is reading the string, for its interpolations
MAX_NESTING = 4000   # deeper expressions or blocks are reported as "nested too deeply"
MAX_LINES = 16777215   # panic locations keep the line in 24 bits


class Parser:
    def __init__(self, toks):
        self.t, self.i, self.depth = toks, 0, 0

    def deeper(self):
        self.depth += 1
        if self.depth > MAX_NESTING:
            raise RecursionError()

    def peek(self, o=0):
        return self.t[min(self.i + o, len(self.t) - 1)]

    def at(self, k, v=None):
        t = self.t[self.i]
        return t.k == k and (v is None or t.v == v)

    def at_op(self, v):
        return self.at('op', v)

    def at_kw(self, v):
        return self.at('kw', v)

    def next(self):
        t = self.t[self.i]
        self.i += 1
        return t

    def expect(self, k, v=None, what=None):
        t = self.t[self.i]
        if t.k != k or (v is not None and t.v != v):
            want = what or (repr(v) if v else {'NL': 'end of line', 'name': 'a name'}.get(k, k))
            err(t.line, f'expected {want}, found {desc(t)}')
        self.i += 1
        return t

    def accept_op(self, v):
        if self.at_op(v):
            self.i += 1
            return True
        return False

    # -- declarations
    def program(self):
        items = []
        while not self.at('EOF'):
            if self.at_kw('fn'):
                items.append(self.fn_decl())
            elif self.at_kw('type'):
                items.append(self.type_decl())
            elif self.at_kw('const'):
                items.append(self.const_decl())
            elif self.at('name') and self.peek().v == 'extern' and self.peek(1).k == 'str':
                items += self.extern_decl()
            elif self.at('name') and self.peek().v == 'import' and self.peek(1).k == 'name':
                ln = self.next().line
                items.append(Node('import', ln, name=self.expect('name').v, names=None))
                self.expect('NL')
            elif (self.at('name') and self.peek().v == 'from' and self.peek(1).k == 'name'
                  and self.peek(2).k == 'name' and self.peek(2).v == 'import'):
                ln = self.next().line
                mod = self.expect('name').v
                self.next()
                names = [self.expect('name').v]
                while self.accept_op(','):
                    names.append(self.expect('name').v)
                self.expect('NL')
                items.append(Node('import', ln, name=mod, names=names))
            else:
                err(self.peek().line, "expected 'fn', 'type', 'const', 'import' or 'extern' at top level")
        return items

    def extern_decl(self):
        """extern "glue.c": a C file compiled into the program, the libraries it needs, and the handle
        types and functions it provides (see SPEC.md, Calling C)."""
        ln = self.next().line
        t = self.next()
        path = t.v[1:-1]
        if not path or any(ch in path for ch in '{}\\"'):
            err(t.line, 'an extern file name is a plain string, like "glue.c"')
        self.expect('op', ':')
        self.expect('NL')
        self.expect('INDENT', what="an indented list of 'link', 'type' and 'fn' lines")
        links, items = [], []
        while not self.at('DEDENT'):
            if self.at('name') and self.peek().v == 'link' and self.peek(1).k == 'str':
                self.next()
                lt = self.next()
                lib = lt.v[1:-1]
                if not lib or not all((c.isascii() and c.isalnum()) or c in '_+-.' for c in lib):
                    err(lt.line, 'a library is named like "sqlite3" (it is linked with -lsqlite3)')
                links.append(lib)
                self.expect('NL')
            elif self.at_kw('type'):
                tl = self.next().line
                name = self.expect('name').v
                if not (self.at('name') and self.peek().v == 'drop' and self.peek(1).k == 'name'):
                    err(tl, f"an extern type names the C function that frees it: type {name} drop {name.lower()}_free")
                self.next()
                d = self.next().v
                self.expect('NL')
                items.append(Node('exttype', tl, name=name, drop=d))
            elif self.at_kw('fn'):
                fl = self.next().line
                name = self.expect('name').v
                self.expect('op', '(')
                params = self.typed_names(True, ('op', ')'))
                self.expect('op', ')')
                ret = ('void',)
                if self.accept_op('->'):
                    ret = self.type_expr()
                throws, err_ty = False, None
                if self.at_kw('throws'):
                    self.next()
                    throws = True
                    if self.at('name'):
                        err(fl, "an extern function fails with a message; it can't name an error type")
                if self.at_op(':'):
                    err(fl, "an extern function has no body here: its code is in the C file")
                self.expect('NL')
                items.append(Node('fn', fl, name=name, params=params, ret=ret, throws=throws, err_ty=None, body=None,
                                  cname=name))
            else:
                err(self.peek().line, "an extern block holds 'link \"lib\"', 'type Name drop free_fn' and 'fn' lines")
        self.next()
        return [Node('extern', ln, path=path, links=links)] + items

    def const_decl(self):
        ln = self.next().line
        name = self.expect('name').v
        self.expect('op', '=')
        e = self.expr()
        self.expect('NL')
        return Node('const', ln, name=name, expr=e)

    def typed_names(self, allow_var, closer):
        """`a, b: T, var c: U` -> [(name, type, is_var, line)]; parameters (allow_var) also get
        is_own: `own d: V` takes ownership of the argument. 'own' is only special there, before a name."""
        items, pending = [], []
        while not self.at(*closer):
            is_var = is_own = False
            if allow_var and self.at_kw('var'):
                self.next()
                is_var = True
            elif allow_var and self.at('name') and self.peek().v == 'own' and self.peek(1).k == 'name':
                self.next()
                is_own = True
            nt = self.expect('name')
            pending.append([nt.v, None, is_var, nt.line] + ([is_own] if allow_var else []))
            if self.accept_op(':'):
                ty = self.type_expr()
                for p in pending:
                    p[1] = ty
                items += pending
                pending = []
            if not self.accept_op(','):
                break
        if pending:
            err(pending[-1][3], f"missing type for '{pending[-1][0]}' (write '{pending[-1][0]}: Type')")
        return [tuple(p) for p in items]

    def type_decl(self):
        ln = self.next().line
        name = self.expect('name').v
        tparams = self.type_params()
        self.expect('op', ':')
        self.expect('NL')
        self.expect('INDENT', what='an indented list of fields')
        # An enum lists variants: `Num(value: Int)` or a bare `End`. A struct lists `name: Type` fields.
        if self.at('name') and (self.peek(1).k == 'NL' or (self.peek(1).k == 'op' and self.peek(1).v == '(')):
            variants = []
            while not self.at('DEDENT'):
                vt = self.expect('name', what='a variant name')
                vfields = []
                if self.accept_op('('):
                    vfields = self.typed_names(False, ('op', ')'))
                    self.expect('op', ')')
                self.expect('NL')
                variants.append((vt.v, vfields, vt.line))
            self.next()
            return Node('enum', ln, name=name, variants=variants, tparams=tparams)
        fields = []
        while not self.at('DEDENT'):
            fields += self.typed_names(False, ('NL',))
            self.expect('NL')
        self.next()
        return Node('type', ln, name=name, fields=fields, tparams=tparams)

    def type_expr(self):
        t = self.peek()
        if self.at_kw('fn'):
            # a function type: fn(Int, Str) -> Bool, fn(Str) -> Int throws, fn() (returns nothing)
            self.next()
            self.expect('op', '(')
            ps = []
            while not self.at_op(')'):
                ps.append(self.type_expr())
                if not self.accept_op(','):
                    break
            self.expect('op', ')')
            ret = ('void',)
            if self.accept_op('->'):
                ret = self.type_expr()
            throws = False
            if self.at_kw('throws'):
                self.next()
                throws = True
                if self.at('name'):
                    err(t.line, "a function type fails with a message (throws); typed errors (throws E) are only "
                                "for named functions")
            return ('fnty', ps, ret, throws, t.line)
        if self.accept_op('('):
            ty = self.type_expr()   # (fn(Int) -> Int)? : parentheses group a type
            self.expect('op', ')')
        elif self.accept_op('['):
            inner = self.type_expr()
            self.expect('op', ']')
            ty = ('list', inner)
        elif self.accept_op('{'):
            k = self.type_expr()
            self.expect('op', ':')
            v = self.type_expr()
            self.expect('op', '}')
            ty = ('map', k, v)
        else:
            n = self.expect('name', what='a type').v
            if n == 'Chan' and self.at_op('['):
                self.next()
                inner = self.type_expr()
                self.expect('op', ']')
                ty = ('chan', inner)
                if self.accept_op('?'):
                    ty = ('opt', ty)
                return ty
            if self.at_op('.') and self.peek(1).k == 'name':
                self.next()
                n += '.' + self.next().v   # a type from a module: geo.Point
            if self.at_op('['):
                # a generic type with its type arguments: Pair[Int, Str]
                self.next()
                args = [self.type_expr()]
                while self.accept_op(','):
                    args.append(self.type_expr())
                self.expect('op', ']')
                ty = ('gapp', n, args, t.line)
            else:
                ty = {'Int': ('int',), 'Float': ('float',), 'Bool': ('bool',), 'Byte': ('byte',), 'Str': ('str',),
                      'Fs': ('cap', 'Fs'), 'Net': ('cap', 'Net'), 'Os': ('cap', 'Os'),
                      'Ffi': ('cap', 'Ffi')}.get(n, ('named', n, t.line))
        if self.accept_op('?'):
            ty = ('opt', ty)
        return ty

    def type_params(self):
        """[T, U] after a function's or a type's name: its type parameters."""
        ps = []
        if self.accept_op('['):
            while True:
                tk = self.expect('name', what='a type parameter name')
                if tk.v in ps:
                    err(tk.line, f"type parameter '{tk.v}' is listed twice")
                ps.append(tk.v)
                if not self.accept_op(','):
                    break
            self.expect('op', ']')
        return ps

    def fn_decl(self):
        ln = self.next().line
        name = self.expect('name').v
        tparams = self.type_params()
        self.expect('op', '(')
        params = self.typed_names(True, ('op', ')'))
        self.expect('op', ')')
        ret = ('void',)
        if self.accept_op('->'):
            ret = self.type_expr()
        throws, err_ty = False, None
        if self.at_kw('throws'):
            self.next()
            throws = True
            if self.at('name'):
                err_ty = self.type_expr()   # throws ParseError: fails with values of that enum
        return Node('fn', ln, name=name, params=params, ret=ret, throws=throws, err_ty=err_ty, body=self.block(),
                    tparams=tparams)

    def closure(self, own, named):
        """After 'fn' (or 'own fn'): a closure. As an expression, fn(x: Int) -> Int => x * k (parameter and
        return types can be left out when the context says them); as a statement (named), a nested
        function with a block body: fn name(x: Int) -> Int: ..."""
        ln = self.next().line
        name = self.expect('name').v if named else None
        self.expect('op', '(')
        params = []
        while not self.at_op(')'):
            if self.at_kw('var') or (self.at('name') and self.peek().v == 'own' and self.peek(1).k == 'name'):
                err(self.peek().line, "a closure's parameters are read-only: they can't be 'var' or 'own'")
            nt = self.expect('name', what='a parameter name')
            pt = None
            if self.accept_op(':'):
                pt = self.type_expr()
            elif named:
                err(nt.line, f"missing type for '{nt.v}' (write '{nt.v}: Type')")
            params.append((nt.v, pt, nt.line))
            if not self.accept_op(','):
                break
        self.expect('op', ')')
        ret = None
        if self.accept_op('->'):
            ret = self.type_expr()
        throws = False
        if self.at_kw('throws'):
            self.next()
            throws = True
            if self.at('name'):
                err(ln, "a closure fails with a message (throws); typed errors (throws E) are only for top-level "
                        "functions")
        if named:
            return Node('lambda', ln, params=params, ret=ret or ('void',), throws=throws, own=own, name=name,
                        body=None, block=self.block())
        self.expect('op', '=>', what="'=>' and the closure's value (fn(x) => x + 1)")
        return Node('lambda', ln, params=params, ret=ret, throws=throws, own=own, name=None,
                    body=self.handled(self.expr()), block=None)

    def block(self):
        self.expect('op', ':')
        self.deeper()
        if self.at('NL'):
            self.next()
            self.expect('INDENT', what='an indented block')
            stmts = []
            while not self.at('DEDENT'):
                stmts.append(self.stmt())
            self.next()
            self.depth -= 1
            return stmts
        st = self.simple_stmt()
        self.expect('NL')
        self.depth -= 1
        return [st]

    # -- statements
    def stmt(self):
        t = self.peek()
        if t.k == 'kw' and t.v == 'if':
            return self.if_stmt()
        if t.k == 'kw' and t.v == 'while':
            self.next()
            cond = self.expr()
            return Node('while', t.line, cond=cond, body=self.block())
        if t.k == 'kw' and t.v == 'for':
            return self.for_stmt()
        if t.k == 'kw' and t.v == 'match':
            return self.match_stmt()
        if t.k == 'kw' and t.v == 'fn' and self.peek(1).k == 'name':
            return Node('fnstmt', t.line, lam=self.closure(False, True))
        if t.k == 'name' and t.v == 'own' and self.peek(1).k == 'kw' and self.peek(1).v == 'fn' \
                and self.peek(2).k == 'name':
            self.next()
            return Node('fnstmt', t.line, lam=self.closure(True, True))
        if t.k == 'kw' and t.v == 'par':
            self.next()
            if not self.at_kw('for'):
                err(t.line, "'par' must be followed by a range loop: par for i in 0..n:")
            node = self.for_stmt()
            if node.k != 'range':
                err(t.line, "par loops run over a range of indexes: par for i in 0..xs.len:")
            node.par = True
            return node
        st = self.simple_stmt()
        self.expect('NL')
        return st

    def if_stmt(self):
        t = self.next()
        bind, mut = None, False
        if self.at_kw('var') and self.peek(1).k == 'name' and self.peek(2).k == 'op' and self.peek(2).v == '=':
            self.next()
            mut = True
        if self.at('name') and self.peek(1).k == 'op' and self.peek(1).v == '=':
            bind = self.next().v
            self.next()
        elif mut:
            err(t.line, "expected 'if var name = optional:'")
        cond = self.expr()
        body = self.block()
        els = None
        if self.at_kw('elif'):
            els = [self.if_stmt()]
            els[0].is_elif = True
        elif self.at_kw('else'):
            self.next()
            els = self.block()
        return Node('if', t.line, bind=bind, mut=mut, cond=cond, body=body, els=els)

    def match_stmt(self):
        t = self.next()
        mut = False
        if self.at_kw('var'):
            self.next()
            mut = True
        subj = self.expr()
        self.expect('op', ':')
        self.expect('NL')
        self.expect('INDENT', what='indented match arms, like  Num(v): ...')
        arms = []
        while not self.at('DEDENT'):
            pt = self.expect('name', what='a pattern like Num(v) or _')
            pname = pt.v
            if self.at_op('.') and self.peek(1).k == 'name':
                self.next()
                pname += '.' + self.next().v   # a variant of an enum from a module: geo.Circle(r)
            binds = None
            if self.accept_op('('):
                binds = []
                while not self.at_op(')'):
                    binds.append(self.expect('name').v)
                    if not self.accept_op(','):
                        break
                self.expect('op', ')')
            arms.append((pname, binds, self.block(), pt.line))
        self.next()
        return Node('match', t.line, mut=mut, subj=subj, arms=arms)

    def handled(self, e):
        """`f(x) else default`: a statement-level fallback for a call that can fail. The fallback can
        also leave: `else return [value]`, `else break`, `else continue`, `else fail value`."""
        if self.at_kw('else'):
            ln = self.next().line
            j = self.peek()
            if j.k == 'kw' and j.v == 'return':
                self.next()
                return Node('orelse', ln, e=e, d=None,
                            jump=Node('return', j.line, expr=None if self.at('NL') else self.expr()))
            if j.k == 'kw' and j.v in ('break', 'continue'):
                self.next()
                return Node('orelse', ln, e=e, d=None, jump=Node(j.v, j.line))
            if j.k == 'kw' and j.v == 'fail':
                self.next()
                return Node('orelse', ln, e=e, d=None, jump=Node('fail', j.line, expr=self.expr()))
            return Node('orelse', ln, e=e, d=self.expr(), jump=None)
        return e

    def for_stmt(self):
        t = self.next()
        mut = False
        if self.at_kw('var'):
            self.next()
            mut = True
        name = self.expect('name').v
        name2 = None
        if self.accept_op(','):
            if mut:
                err(t.line, "a map's keys can't be changed in a loop; to change the values write: for k, var v in m")
            if self.at_kw('var'):
                self.next()
                mut = True
            name2 = self.expect('name').v
        self.expect('kw', 'in')
        a = self.expr()
        if self.at_op('..') or self.at_op('..='):
            if name2:
                err(t.line, 'a range loop has one counter: for i in a..b')
            incl = self.next().v == '..='
            b = self.expr()
            step = None
            if self.at_kw('by'):
                self.next()
                step = self.expr()
            if mut:
                err(t.line, "a range loop counter can't be 'var'")
            return Node('range', t.line, name=name, start=a, end=b, incl=incl, step=step, body=self.block())
        return Node('each', t.line, name=name, name2=name2, mut=mut, seq=a, body=self.block())

    def simple_stmt(self):
        t = self.peek()
        if t.k == 'kw' and t.v in ('let', 'var'):
            self.next()
            name = self.expect('name').v
            ty = None
            if self.accept_op(':'):
                ty = self.type_expr()
            self.expect('op', '=', what="'=' (variables must be given a value)")
            return Node('let', t.line, name=name, mut=t.v == 'var', ty=ty, expr=self.handled(self.expr()))
        if t.k == 'kw' and t.v == 'return':
            self.next()
            return Node('return', t.line, expr=None if self.at('NL') else self.handled(self.expr()))
        if t.k == 'kw' and t.v == 'fail':
            self.next()
            return Node('fail', t.line, expr=self.expr())
        if t.k == 'name' and t.v == 'spawn' and self.peek(1).k == 'name':
            self.next()
            return Node('spawn', t.line, expr=self.handled(self.expr()))
        if t.k == 'kw' and t.v in ('break', 'continue'):
            self.next()
            return Node(t.v, t.line)
        if t.k == 'kw' and t.v in ('if', 'while', 'for', 'elif', 'else', 'match', 'par'):
            err(t.line, f"'{t.v}' must start its own line")
        e = self.expr()
        if self.peek().k == 'op' and self.peek().v in ASSIGN_OPS:
            op = self.next().v
            return Node('assign', t.line, target=e, op=op, expr=self.handled(self.expr()))
        return Node('exprstmt', t.line, expr=self.handled(e))

    # -- expressions (lowest to highest precedence)
    def expr(self):
        self.deeper()
        e = self.or_()
        self.depth -= 1
        return e

    def or_(self):
        left = self.and_()
        while self.at_kw('or'):
            ln = self.next().line
            left = Node('bin', ln, op='or', l=left, r=self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.at_kw('and'):
            ln = self.next().line
            left = Node('bin', ln, op='and', l=left, r=self.not_())
        return left

    def not_(self):
        if self.at_kw('not'):
            ln = self.next().line
            self.deeper()
            e = self.not_()
            self.depth -= 1
            return Node('un', ln, op='not', e=e)
        return self.cmp()

    def at_compare(self):
        return (self.peek().k == 'op' and self.peek().v in COMPARE) or self.at_kw('in')

    def cmp(self):
        left = self.binary(0)
        if self.at_compare():
            t = self.next()
            left = Node('bin', t.line, op=t.v, l=left, r=self.binary(0))
            if self.at_compare():
                err(t.line, "comparisons can't be chained; use 'and'")
        return left

    LEVELS = (('|',), ('^',), ('&',), ('<<', '>>'), ('+', '-'), ('*', '/', '%'))

    def binary(self, level):
        if level == len(self.LEVELS):
            return self.unary()
        left = self.binary(level + 1)
        while self.peek().k == 'op' and self.peek().v in self.LEVELS[level]:
            t = self.next()
            left = Node('bin', t.line, op=t.v, l=left, r=self.binary(level + 1))
        return left

    def unary(self):
        if self.at_op('-'):
            ln = self.next().line
            self.deeper()
            e = self.unary()
            self.depth -= 1
            return Node('un', ln, op='-', e=e)
        if self.at_op('&'):
            ln = self.next().line
            self.deeper()
            e = self.unary()
            self.depth -= 1
            return Node('ref', ln, e=e)
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            if self.at_op('('):
                ln = self.next().line
                args = []
                while not self.at_op(')'):
                    nm = None
                    if self.at('name') and self.peek(1).k == 'op' and self.peek(1).v == ':':
                        nm = self.next().v
                        self.next()
                    if len(args) == 1 and e.k == 'name' and e.name == 'from_json':
                        # from_json(text, Type): the second argument is a type, like [Order] or Int?
                        args.append((nm, Node('typearg', self.peek().line, t=self.type_expr())))
                    else:
                        args.append((nm, self.expr()))
                    if not self.accept_op(','):
                        break
                self.expect('op', ')')
                e = Node('call', ln, fn=e, args=args)
            elif self.at_op('.'):
                ln = self.next().line
                e = Node('field', ln, e=e, name=self.expect('name').v)
            elif self.at_op('['):
                ln = self.next().line
                i = self.expr()
                if self.at_op('..'):
                    self.next()
                    hi = self.expr()
                    self.expect('op', ']')
                    e = Node('slice', ln, e=e, lo=i, hi=hi)
                    continue
                self.expect('op', ']')
                e = Node('index', ln, e=e, i=i)
            elif self.at_op('?'):
                ln = self.next().line
                e = Node('try', ln, e=e)
            else:
                return e

    def primary(self):
        t = self.next()
        if t.k == 'int':
            return Node('int', t.line, v=int(t.v.replace('_', ''), 16 if t.v[:2] in ('0x', '0X') else 10))
        if t.k == 'float':
            return Node('float', t.line, v=t.v.replace('_', ''))
        if t.k == 'str':
            PARSE_DEPTH[0] = self.depth
            return Node('str', t.line, parts=parse_interp(t.v[1:-1], t.line))
        if t.k == 'char':
            body = t.v[1:-1]
            if body.startswith('\\'):
                ch = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', "'": "'", '0': '\0'}.get(body[1:])
            else:
                ch = body
            if ch is None or len(ch) != 1 or ord(ch) > 127:
                err(t.line, f"{t.v} isn't a single ASCII character (Byte literals are like 'a', '\\n', '\\'')")
            return Node('char', t.line, v=ord(ch))
        if t.k == 'kw' and t.v == 'fn':
            self.i -= 1
            return self.closure(False, False)
        if t.k == 'name' and t.v == 'own' and self.at_kw('fn'):
            return self.closure(True, False)
        if t.k == 'name':
            return Node('name', t.line, name=t.v)
        if t.k == 'kw' and t.v in ('true', 'false'):
            return Node('bool', t.line, v=t.v == 'true')
        if t.k == 'kw' and t.v == 'nil':
            return Node('nil', t.line)
        if t.k == 'op' and t.v == '(':
            e = self.expr()
            self.expect('op', ')')
            return e
        if t.k == 'op' and t.v == '[':
            items = []
            while not self.at_op(']'):
                items.append(self.expr())
                if not self.accept_op(','):
                    break
            self.expect('op', ']')
            return Node('list', t.line, items=items)
        if t.k == 'op' and t.v == '{':
            pairs = []
            while not self.at_op('}'):
                k = self.expr()
                self.expect('op', ':')
                pairs.append((k, self.expr()))
                if not self.accept_op(','):
                    break
            self.expect('op', '}')
            return Node('map', t.line, pairs=pairs)
        err(t.line, f'expected an expression, found {desc(t)}')


# ----------------------------------------------------------------------------- checker + C codegen

INT, FLOAT, BOOL, VOID, NIL = ('int',), ('float',), ('bool',), ('void',), ('nil',)
BYTE, STR, FS, OS, NET = ('byte',), ('str',), ('cap', 'Fs'), ('cap', 'Os'), ('cap', 'Net')
SCALARS = (INT, FLOAT, BOOL, BYTE)
INTEGERS = (INT, BYTE)
INT_OPS = {'+': 'vu_add', '-': 'vu_sub', '*': 'vu_mul', '/': 'vu_div', '%': 'vu_mod', '<<': 'vu_shl', '>>': 'vu_shr'}
BYTE_OPS = {'+': 'vu_badd', '-': 'vu_bsub', '*': 'vu_bmul', '/': 'vu_bdiv', '%': 'vu_bmod', '<<': 'vu_bshl',
            '>>': 'vu_bshr'}
BUILTINS = {'print', 'panic', 'sqrt', 'float', 'int', 'min', 'max', 'abs', 'arg', 'byte', 'write', 'str', 'bytes',
            'exit', 'eprint', 'args', 'swap', 'sorted', 'chan', 'to_json', 'from_json'}
STR_METHODS = ('split', 'join', 'strip', 'lstrip', 'rstrip', 'startswith', 'endswith')
# What sorted(), .sort(), min(xs) and max(xs) work on, and the runtime function for each element type.
SORT_FN = {INT: 'i64', FLOAT: 'f64', BYTE: 'u8', BOOL: 'bool', STR: 'str'}
MAP_KEYS = (INT, BYTE, BOOL, STR)
PURE_BUILTINS = {'sqrt', 'float', 'int', 'byte', 'min', 'max', 'abs'}
NET_METHODS = ('listen', 'accept', 'connect', 'recv', 'send', 'port', 'tls_connect', 'tls_listen')
NET_FAILS = ('listen', 'accept', 'connect', 'recv', 'send', 'tls_connect', 'tls_listen')
CHAN_METHODS = ('send', 'recv', 'close', 'share')
BUILTIN_TYPES = ('Int', 'Float', 'Bool', 'Byte', 'Str', 'Fs', 'Net', 'Os', 'Ffi', 'Conn', 'Listener', 'Chan')
CONN, LISTENER = ('ext', 'Conn'), ('ext', 'Listener')
FFI = ('cap', 'Ffi')
# Names the C side of an extern block can't use: C keywords, and the generated code's own names.
C_KEYWORDS = set('auto break case char const continue default do double else enum extern float for goto if '
                 'inline int long register restrict return short signed sizeof static struct switch typedef '
                 'union unsigned void volatile while bool true false main'.split())


def c_name_problem(n):
    if n in C_KEYWORDS:
        return f"'{n}' is a C keyword"
    if n.startswith(('vu_', 'fn_', 'drop_')):
        return f"names starting with vu_, fn_ or drop_ belong to the generated C ('{n}')"
    return None


def tn(t):
    k = t[0]
    if k in ('int', 'float', 'bool', 'byte', 'str'):
        return k.capitalize()
    if k in ('cap', 'enum', 'ext'):
        return disp(t[1])
    if k == 'map':
        return '{' + tn(t[1]) + ': ' + tn(t[2]) + '}'
    if k == 'res':
        return tn(t[1])
    if k == 'void':
        return 'nothing'
    if k == 'nil':
        return 'nil'
    if k == 'struct':
        return disp(t[1])
    if k == 'list':
        return f'[{tn(t[1])}]'
    if k == 'chan':
        return f'Chan[{tn(t[1])}]'
    if k in ('fn', 'lfn'):
        out = 'fn(' + ', '.join(tn(p) for p in t[1]) + ')'
        if t[2] != ('void',):
            out += ' -> ' + tn(t[2])
        return out + (' throws' if t[3] else '')
    if t[1][0] == 'fn':
        return f'({tn(t[1])})?'
    return f'{tn(t[1])}?'


def cf(name):
    return 'f_' + name   # a prefix, so no field name can clash with C or with another field


def cstr(text):
    out = []
    for ch in text:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\t':
            out.append('\\t')
        elif ' ' <= ch <= '~':
            out.append(ch)
        else:
            out.extend(f'\\{b:03o}' for b in ch.encode('utf-8'))
    return '"' + ''.join(out) + '"'


class Var:
    def __init__(self, name, ty, cname, kind, mutable, ptr, line):
        # kind: 'local' (owned), 'param' (borrowed), 'ref' (for/if binding), 'view' (let of a part), 'loop' (range counter)
        self.name, self.ty, self.cname, self.kind = name, ty, cname, kind
        self.mutable, self.ptr, self.line = mutable, ptr, line
        self.state, self.moved_line, self.frozen = 'no', None, []

    @property
    def lv(self):
        return f'(*{self.cname})' if self.ptr else self.cname


class LamCtx:
    """A closure being generated, inside the one it was written in (outer), if any."""
    def __init__(self, outer, name):
        self.outer, self.name = outer, name


class Place:
    def __init__(self, root, code, ty, is_name):
        self.root, self.code, self.ty, self.is_name = root, code, ty, is_name


class Scope:
    def __init__(self, loop=False):
        self.vars, self.order, self.loop = {}, [], loop
        self.unfreeze = []   # variables frozen by `let` views declared in this scope


class EnumInfo:
    def __init__(self, node):
        self.name, self.line, self.variants, self.copy = node.name, node.line, [], True

    def index(self, v):
        return [n for n, _ in self.variants].index(v)

    def fields_of(self, v):
        return self.variants[self.index(v)][1]

    @property
    def plain(self):
        return all(not fs for _, fs in self.variants)

    @property
    def fields(self):
        return [(f, ft) for _, fs in self.variants for f, ft in fs]


class StructInfo:
    def __init__(self, node):
        self.name, self.line, self.fields, self.copy = node.name, node.line, [], True

    def field(self, name):
        for f, t in self.fields:
            if f == name:
                return t
        return None


RUNTIME = r'''/* generated by vu */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <errno.h>
#include <time.h>
#include <sys/random.h>
#include <signal.h>
#include <unistd.h>
#include <sys/resource.h>
#include <pthread.h>
#include <spawn.h>
#include <sys/wait.h>
extern char **environ;
static int vu_argc;
static char **vu_argv;
/* Where a panic happened. A location is (file index << 24) | line; vu_files names the files.
   Quick builds (vu run, --debug) define VU_TRACE: every function then keeps a frame on a per-thread
   shadow stack holding the line it is running, so a panic can print the whole chain of calls.
   Optimized builds compile VU_ENTER and VU_AT away and report only the panic's own line. */
static const char *const *vu_files;
static bool vu_json;   /* report panics as JSON (vu run --json, or VU_PANIC=json at run time) */
typedef struct vu_frame { const char *name; int loc; struct vu_frame *prev; } vu_frame;
static __thread vu_frame *vu_top;
static inline void vu_leave(vu_frame *f) { vu_top = f->prev; }
#ifdef VU_TRACE
#define VU_ENTER(n) vu_frame vu_fr __attribute__((cleanup(vu_leave))) = {n, 0, vu_top}; vu_top = &vu_fr
#define VU_AT(l) (vu_fr.loc = (l))
/* par loop worker threads chain their calls to the frame of the function running the loop */
#define VU_PAR_TOP(t) vu_frame *const t = vu_top
#define VU_PAR_JOIN(t) (vu_top = (t))
#else
#define VU_ENTER(n) ((void)0)
#define VU_AT(l) ((void)0)
#define VU_PAR_TOP(t) ((void)0)
#define VU_PAR_JOIN(t) ((void)0)
#endif
/* The report is built with write() only, so the stack-overflow signal handler can use it too. */
static char vu_pbuf[4096];
static size_t vu_plen;
static void vu_pflush(void) {
    size_t at = 0;
    while (at < vu_plen) { ssize_t w = write(2, vu_pbuf + at, vu_plen - at); if (w <= 0) break; at += (size_t)w; }
    vu_plen = 0;
}
static void vu_pput(const char *s, size_t n) {
    while (n) {
        if (vu_plen == sizeof vu_pbuf) vu_pflush();
        size_t k = sizeof vu_pbuf - vu_plen < n ? sizeof vu_pbuf - vu_plen : n;
        memcpy(vu_pbuf + vu_plen, s, k); vu_plen += k; s += k; n -= k;
    }
}
static void vu_pstr(const char *s) { vu_pput(s, strlen(s)); }
static void vu_pint(long long v) {
    char t[24]; int i = 24; unsigned long long u = v < 0 ? 0ull - (unsigned long long)v : (unsigned long long)v;
    do { t[--i] = (char)('0' + u % 10); u /= 10; } while (u);
    if (v < 0) t[--i] = '-';
    vu_pput(t + i, (size_t)(24 - i));
}
/* Length of the valid UTF-8 sequence at s (Unicode table 3-7), or 0 if it isn't one. */
static size_t vu_utf8_len(const unsigned char *s, size_t n) {
    unsigned char b = s[0], lo = 0x80, hi = 0xBF;
    size_t k;
    if (b < 0x80) return 1;
    if (b >= 0xC2 && b <= 0xDF) k = 1;
    else if (b == 0xE0) { k = 2; lo = 0xA0; }
    else if (b == 0xED) { k = 2; hi = 0x9F; }
    else if (b >= 0xE1 && b <= 0xEF) k = 2;
    else if (b == 0xF0) { k = 3; lo = 0x90; }
    else if (b == 0xF4) { k = 3; hi = 0x8F; }
    else if (b >= 0xF1 && b <= 0xF3) k = 3;
    else return 0;
    if (k >= n) return 0;
    if (s[1] < lo || s[1] > hi) return 0;
    for (size_t i = 2; i <= k; i++) if (s[i] < 0x80 || s[i] > 0xBF) return 0;
    return k + 1;
}
/* A JSON string. Strings are bytes, but JSON must be UTF-8: invalid bytes become U+FFFD. */
static void vu_pjson(const char *s, size_t n) {
    static const char hex[] = "0123456789abcdef";
    const unsigned char *u = (const unsigned char *)s;
    vu_pput("\"", 1);
    for (size_t i = 0; i < n;) {
        unsigned char c = u[i];
        size_t k = vu_utf8_len(u + i, n - i);
        if (!k) { vu_pput("\\ufffd", 6); i++; continue; }
        if (c == '"' || c == '\\') { char e[2] = {'\\', (char)c}; vu_pput(e, 2); }
        else if (c < 0x20) { char e[6] = {'\\', 'u', '0', '0', hex[c >> 4], hex[c & 15]}; vu_pput(e, 6); }
        else vu_pput((const char *)u + i, k);
        i += k;
    }
    vu_pput("\"", 1);
}
static const char *vu_file_of(int loc) { return vu_files ? vu_files[loc >> 24] : "?"; }
static void vu_ploc(int loc) { vu_pstr(vu_file_of(loc)); vu_pput(":", 1); vu_pint(loc & 0xFFFFFF); }
/* One report at a time. A thread that panics while another is reporting waits for the process to
   exit; the thread already reporting (re-entered by a signal) carries on. */
static uintptr_t vu_reporter;
static __thread char vu_tid;   /* its address identifies the thread */
static void vu_report_lock(void) {
    uintptr_t me = (uintptr_t)&vu_tid, expected = 0;
    if (__atomic_compare_exchange_n(&vu_reporter, &expected, me, false, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) return;
    if (expected == me) return;
    for (;;) pause();
}
#define VU_MAX_TRACE 12
/* Calls with the same function and line in a row (deep recursion) are reported once, with a count. */
static vu_frame *vu_run_end(vu_frame *g, int loc, long long *times) {
    *times = 1;
    while (g->prev && g->prev->name == g->name && g->prev->loc == loc) { g = g->prev; (*times)++; }
    return g;
}
/* panic: <msg>, then "at file:line in fn" and one "called from" line per caller. */
static void vu_report(const char *msg, size_t n, int loc) {
    vu_report_lock();
    vu_frame *f = vu_top;
    if (!loc && f) loc = f->loc;
    int shown = 0;
    long long more = 0, times;
    if (vu_json) {
        vu_pstr("{\"type\": \"panic\", \"message\": "); vu_pjson(msg, n);
        if (loc) { vu_pstr(", \"file\": "); vu_pjson(vu_file_of(loc), strlen(vu_file_of(loc))); vu_pstr(", \"line\": "); vu_pint(loc & 0xFFFFFF); }
        vu_pstr(", \"backtrace\": [");
        for (vu_frame *g = f; g; g = g->prev) {
            int l = g == f ? loc : g->loc;
            vu_frame *e = vu_run_end(g, l, &times);
            if (shown == VU_MAX_TRACE * 4) { more += times; g = e; continue; }
            if (shown++) vu_pstr(", ");
            vu_pstr("{\"function\": "); vu_pjson(g->name, strlen(g->name));
            vu_pstr(", \"file\": "); vu_pjson(vu_file_of(l), strlen(vu_file_of(l)));
            vu_pstr(", \"line\": "); vu_pint(l & 0xFFFFFF);
            if (times > 1) { vu_pstr(", \"times\": "); vu_pint(times); }
            vu_pstr("}");
            g = e;
        }
        vu_pstr("]");
        if (more) { vu_pstr(", \"more_calls\": "); vu_pint(more); }
        vu_pstr("}\n");
        vu_pflush();
        return;
    }
    vu_pstr("panic: "); vu_pput(msg, n); vu_pput("\n", 1);
    if (!f) {
        if (loc) { vu_pstr("  at "); vu_ploc(loc); vu_pput("\n", 1); }
        vu_pflush();
        return;
    }
    vu_frame *last = f;
    while (last->prev) last = last->prev;
    for (vu_frame *g = f; g; g = g->prev) {
        int l = g == f ? loc : g->loc;
        vu_frame *e = vu_run_end(g, l, &times);
        if (shown == VU_MAX_TRACE && g != last) {
            /* skip to the outermost call (usually main), counting what's left out */
            for (vu_frame *h = g; h != last; h = h->prev) more++;
            vu_pstr("  ... "); vu_pint(more); vu_pstr(more == 1 ? " more call\n" : " more calls\n");
            g = last; l = g->loc; e = vu_run_end(g, l, &times);
        }
        vu_pstr(g == f ? "  at " : "  called from "); vu_ploc(l);
        vu_pstr(" in "); vu_pstr(g->name);
        if (times > 1) { vu_pstr(" ("); vu_pint(times); vu_pstr(" times in a row)"); }
        vu_pput("\n", 1);
        shown++;
        g = e;
    }
    vu_pflush();
}
__attribute__((noreturn, cold, noinline)) static void vu_fail(int line, const char *fmt, ...) {
    va_list ap;
    char small[512];
    fflush(stdout);
    va_start(ap, fmt);
    int n = vsnprintf(small, sizeof small, fmt, ap);
    va_end(ap);
    if (n < 0) n = 0;
    if ((size_t)n < sizeof small) { vu_report(small, (size_t)n, line); exit(101); }
    char *big = malloc((size_t)n + 1);
    if (!big) { vu_report(small, sizeof small - 1, line); exit(101); }
    va_start(ap, fmt); vsnprintf(big, (size_t)n + 1, fmt, ap); va_end(ap);
    vu_report(big, (size_t)n, line);
    exit(101);
}
/* panic(msg): the message exactly, zero bytes included, up to 1,000,000 bytes. */
__attribute__((noreturn, cold, noinline)) static void vu_panic(int line, const char *msg, int64_t n) {
    fflush(stdout);
    vu_report(msg, (size_t)(n > 1000000 ? 1000000 : n), line);
    exit(101);
}
/* main returned an error instead of handling it. */
static int vu_uncaught(const char *msg, size_t n) {
    fflush(stdout);
    vu_report_lock();
    if (vu_json) { vu_pstr("{\"type\": \"error\", \"message\": "); vu_pjson(msg, n); vu_pstr("}\n"); }
    else { vu_pstr("error: "); vu_pput(msg, n); vu_pput("\n", 1); }
    vu_pflush();
    return 1;
}
__attribute__((noreturn, cold, noinline)) static void vu_oob(int64_t i, int64_t n, int line) {
    vu_fail(line, "index %lld out of bounds for a list of length %lld", (long long)i, (long long)n);
}
__attribute__((noreturn, cold, noinline)) static void vu_oom(void) { fputs("out of memory\n", stderr); exit(102); }
/* Integer arithmetic is checked: overflow stops the program instead of silently wrapping. */
__attribute__((noreturn, cold, noinline)) static void vu_overflow(int line) { vu_fail(line, "integer overflow"); }
static inline int64_t vu_add(int64_t a, int64_t b, int line) {
    /* With a constant step (i += 1) the check is a plain comparison, which the C compiler can prove
       false from a loop condition like i < n and remove. */
    if (__builtin_constant_p(b) && b >= 0) { if (__builtin_expect(a > INT64_MAX - b, 0)) vu_overflow(line); return a + b; }
    if (__builtin_constant_p(b) && b < 0) { if (__builtin_expect(a < INT64_MIN - b, 0)) vu_overflow(line); return a + b; }
    int64_t r; if (__builtin_expect(__builtin_add_overflow(a, b, &r), 0)) vu_overflow(line); return r;
}
static inline int64_t vu_sub(int64_t a, int64_t b, int line) {
    int64_t r; if (__builtin_expect(__builtin_sub_overflow(a, b, &r), 0)) vu_overflow(line); return r;
}
static inline int64_t vu_mul(int64_t a, int64_t b, int line) {
    int64_t r; if (__builtin_expect(__builtin_mul_overflow(a, b, &r), 0)) vu_overflow(line); return r;
}
static inline int64_t vu_neg(int64_t a, int line) {
    if (__builtin_expect(a == INT64_MIN, 0)) vu_overflow(line);
    return -a;
}
static inline int64_t vu_div(int64_t a, int64_t b, int line) {
    if (__builtin_expect(b == 0, 0)) vu_fail(line, "division by zero");
    if (__builtin_expect(b == -1 && a == INT64_MIN, 0)) vu_overflow(line);
    return a / b;
}
static inline int64_t vu_mod(int64_t a, int64_t b, int line) {
    if (__builtin_expect(b == 0, 0)) vu_fail(line, "division by zero");
    if (__builtin_expect(b == -1 && a == INT64_MIN, 0)) vu_overflow(line);
    return b == -1 ? 0 : a % b;
}
static inline uint8_t vu_byte(int64_t v, int line) {
    if (__builtin_expect((uint64_t)v > 255, 0)) vu_fail(line, "%lld does not fit in a Byte (0..255)", (long long)v);
    return (uint8_t)v;
}
static inline uint8_t vu_badd(uint8_t a, uint8_t b, int line) { return vu_byte((int64_t)a + b, line); }
static inline uint8_t vu_bsub(uint8_t a, uint8_t b, int line) { return vu_byte((int64_t)a - b, line); }
static inline uint8_t vu_bmul(uint8_t a, uint8_t b, int line) { return vu_byte((int64_t)a * b, line); }
static inline uint8_t vu_bdiv(uint8_t a, uint8_t b, int line) {
    if (__builtin_expect(b == 0, 0)) vu_fail(line, "division by zero");
    return a / b;
}
static inline uint8_t vu_bmod(uint8_t a, uint8_t b, int line) {
    if (__builtin_expect(b == 0, 0)) vu_fail(line, "division by zero");
    return a % b;
}
static inline uint8_t vu_bshl(uint8_t a, int64_t b, int line) {
    if (__builtin_expect((uint64_t)b > 7, 0)) vu_fail(line, "Byte shift by %lld", (long long)b);
    return (uint8_t)(a << b);
}
static inline uint8_t vu_bshr(uint8_t a, int64_t b, int line) {
    if (__builtin_expect((uint64_t)b > 7, 0)) vu_fail(line, "Byte shift by %lld", (long long)b);
    return (uint8_t)(a >> b);
}
static inline int64_t vu_shl(int64_t a, int64_t b, int line) {
    if (__builtin_expect((uint64_t)b > 63, 0)) vu_fail(line, "shift by %lld", (long long)b);
    return (int64_t)((uint64_t)a << b);
}
static inline int64_t vu_shr(int64_t a, int64_t b, int line) {
    if (__builtin_expect((uint64_t)b > 63, 0)) vu_fail(line, "shift by %lld", (long long)b);
    return a >> b;
}
static inline int64_t vu_ftoi(double f, int line) {
    if (!(f >= -9223372036854775808.0 && f < 9223372036854775808.0)) vu_fail(line, "%g does not fit in an Int", f);
    return (int64_t)f;
}
static inline int64_t vu_iabs(int64_t a, int line) { return a < 0 ? vu_neg(a, line) : a; }
static inline int64_t vu_imin(int64_t a, int64_t b) { return a < b ? a : b; }
static inline int64_t vu_imax(int64_t a, int64_t b) { return a > b ? a : b; }
static inline double vu_fmin(double a, double b) { return a < b ? a : b; }
static inline double vu_fmax(double a, double b) { return a > b ? a : b; }
static int64_t vu_arg(int64_t i, int64_t d, int line) {
    if (i < 0 || i >= vu_argc) return d;
    char *end;
    errno = 0;
    long long v = strtoll(vu_argv[i], &end, 10);
    if (end == vu_argv[i] || *end || errno == ERANGE)
        vu_fail(line, "command-line argument %lld is not a valid Int: %s", (long long)i, vu_argv[i]);
    return v;
}
/* The shortest text that reads back as exactly the same Float (0.1 -> "0.1", not 0.10000000000000001). */
static const char *vu_shortest(double v, char *buf) {
    /* 15 digits always read back exactly for normal numbers, so start there; subnormals have less
       precision and can need fewer digits (5e-324), so search them from 1. */
    if (isnan(v)) return strcpy(buf, "nan");   /* as Python prints it, whatever the sign bit */
    int first = (v != 0 && fabs(v) < 2.2250738585072014e-308) ? 1 : 15;
    for (int p = first; p <= 17; p++) {
        snprintf(buf, 40, "%.*g", p, v);
        if (strtod(buf, NULL) == v) break;
    }
    return buf;
}
/* printf prints a NaN with its sign bit set as "-nan"; Python prints every NaN as "nan". */
static inline double vu_nan_plain(double v) { return isnan(v) ? __builtin_nan("") : v; }
static void *vu_malloc(size_t n) { void *p = malloc(n); if (!p) vu_oom(); return p; }
/* Each thread carves tree nodes from its own blocks and keeps its own free lists, so no locking is needed. */
static __thread char *vu_cur, *vu_end;
static void *vu_bump(size_t n) {
    n = (n + 15) & ~(size_t)15;
    if (!vu_cur || (size_t)(vu_end - vu_cur) < n) {
        size_t c = n > ((size_t)1 << 20) ? n : ((size_t)1 << 20);
        vu_cur = (char *)vu_malloc(c);
        vu_end = vu_cur + c;
    }
    void *p = vu_cur;
    vu_cur += n;
    return p;
}
#if defined(__SANITIZE_ADDRESS__) && !defined(VU_MALLOC)
#include <sanitizer/asan_interface.h>
#define VU_POISON(p, n) ASAN_POISON_MEMORY_REGION((p), (n))
#define VU_UNPOISON(p, n) ASAN_UNPOISON_MEMORY_REGION((p), (n))
#else
#define VU_POISON(p, n) ((void)0)
#define VU_UNPOISON(p, n) ((void)0)
#endif
/* move: copy the value out and zero the source so its later drop is a no-op */
#define VU_MV(x) ({ __typeof__(x) vu_mv_ = (x); memset(&(x), 0, sizeof(x)); vu_mv_; })

/* Str: an owned byte string. cap == 0 means the bytes are static text that is never freed;
   the first change copies them into an owned buffer. */
typedef struct { uint8_t *data; int64_t len, cap; } vu_str;
/* Short strings' buffers (up to 256 bytes) are kept on per-thread free lists by size class
   (16, 32, ... 256 bytes) and reused, so building and dropping many short strings rarely calls
   malloc. The buffers themselves come from malloc. In a program with par loops each list keeps
   at most VU_SKEEP of them (past that they go back to free), so strings made on one thread and
   freed on another can't pile up. */
#ifndef VU_SKEEP
#define VU_SKEEP 4096
#endif
static __thread void *vu_sfree[5];
static __thread int32_t vu_snum[5];
static inline int vu_sclass(int64_t c) { return c <= 16 ? 0 : c <= 32 ? 1 : c <= 64 ? 2 : c <= 128 ? 3 : c <= 256 ? 4 : -1; }
/* A buffer of at least *cap bytes; *cap becomes its real size. */
static inline uint8_t *vu_salloc(int64_t *cap) {
#ifndef VU_MALLOC
    int k = vu_sclass(*cap);
    if (k >= 0) {
        *cap = (int64_t)16 << k;
        void *p = vu_sfree[k];
        if (p) {
            VU_UNPOISON(p, (size_t)*cap);
            memcpy(&vu_sfree[k], p, sizeof(void *));
            vu_snum[k]--;
            return (uint8_t *)p;
        }
    }
#endif
    uint8_t *d = (uint8_t *)malloc((size_t)*cap);
    if (!d) vu_oom();
    return d;
}
static inline void vu_sfree_(uint8_t *p, int64_t cap) {
#ifndef VU_MALLOC
    int k = vu_sclass(cap);
#ifdef _OPENMP
    if (k >= 0 && vu_snum[k] < VU_SKEEP) {
#else
    if (k >= 0) {   /* one thread: the list never outgrows what was once alive at the same time */
#endif
        memcpy(p, &vu_sfree[k], sizeof(void *));
        vu_sfree[k] = p;
        vu_snum[k]++;
        VU_POISON(p, (size_t)cap);   /* any later access to this freed buffer is reported */
        return;
    }
#endif
    free(p);
}
static void drop_Str(vu_str *s) { if (s->cap > 0) vu_sfree_(s->data, s->cap); }
static vu_str vu_str_lit(const char *p, int64_t n) { vu_str s = { (uint8_t *)p, n, 0 }; return s; }
static void vu_str_reserve(vu_str *s, int64_t extra) {
    if (extra < 0 || s->len > INT64_MAX / 2 - extra) vu_oom();
    int64_t need = s->len + extra;
    if (need <= s->cap) return;
    /* The first allocation is exactly what's needed: most strings are built once (a slice, a parsed
       token) and never grow. A string that does keep growing doubles from there. */
    int64_t c = need;
    if (s->cap > 0) { c = s->cap; while (c < need) c *= 2; }
    uint8_t *d;
#ifdef VU_MALLOC
    bool small = false;
#else
    bool small = vu_sclass(s->cap) >= 0;
#endif
    if (s->cap > 0 && !small) {   /* a large buffer grows in place when it can */
        d = (uint8_t *)realloc(s->data, (size_t)c);
        if (!d) vu_oom();
    } else {
        d = vu_salloc(&c);
        if (s->len) memcpy(d, s->data, (size_t)s->len);
        if (s->cap > 0) vu_sfree_(s->data, s->cap);
    }
    s->data = d;
    s->cap = c;
}
static void vu_str_reserve_n(vu_str *s, int64_t n, int line) {
    if (n < 0) vu_fail(line, "reserve(%lld): the count can't be negative", (long long)n);
    vu_str_reserve(s, n);
}
static void vu_str_cat_bytes(vu_str *s, const uint8_t *p, int64_t n) {
    vu_str_reserve(s, n);
    if (n) memcpy(s->data + s->len, p, (size_t)n);
    s->len += n;
}
static void vu_str_cat(vu_str *s, const vu_str *t) {
    if (s == t) {  /* s += s: copy the length first, since growing s moves its bytes */
        int64_t n = s->len;
        vu_str_reserve(s, n);
        memcpy(s->data + n, s->data, (size_t)n);
        s->len += n;
        return;
    }
    vu_str_cat_bytes(s, t->data, t->len);
}
__attribute__((format(printf, 2, 3))) static void vu_str_catf(vu_str *s, const char *fmt, ...) {
    /* usually one pass into a stack buffer; a second only for long output */
    char b[128];
    va_list ap;
    va_start(ap, fmt); int n = vsnprintf(b, sizeof b, fmt, ap); va_end(ap);
    if (n < 0) { fputs("formatting a number failed\n", stderr); exit(101); }
    if ((size_t)n < sizeof b) { vu_str_cat_bytes(s, (const uint8_t *)b, n); return; }
    vu_str_reserve(s, n + 1);
    va_start(ap, fmt); vsnprintf((char *)s->data + s->len, (size_t)n + 1, fmt, ap); va_end(ap);
    s->len += n;
}
/* An integer in decimal, as "%lld" would write it. */
static void vu_str_cat_int(vu_str *s, long long v) {
    char b[24];
    char *p = b + sizeof b;
    unsigned long long u = v < 0 ? 0ULL - (unsigned long long)v : (unsigned long long)v;
    do { *--p = (char)('0' + u % 10); u /= 10; } while (u);
    if (v < 0) *--p = '-';
    vu_str_cat_bytes(s, (const uint8_t *)p, (int64_t)(b + sizeof b - p));
}
static vu_str vu_str_concat(const vu_str *a, const vu_str *b) {
    vu_str r = {0};
    vu_str_reserve(&r, a->len + b->len);
    vu_str_cat_bytes(&r, a->data, a->len);
    vu_str_cat_bytes(&r, b->data, b->len);
    return r;
}
static bool vu_str_eq(const vu_str *a, const vu_str *b) {
    return a->len == b->len && (a->len == 0 || memcmp(a->data, b->data, (size_t)a->len) == 0);
}
static int vu_str_cmp(const vu_str *a, const vu_str *b) {
    int64_t n = a->len < b->len ? a->len : b->len;
    int c = n ? memcmp(a->data, b->data, (size_t)n) : 0;
    return c ? c : (a->len > b->len) - (a->len < b->len);
}
static inline uint8_t vu_str_at(const vu_str *s, int64_t i, int line) {
    /* Two signed comparisons rather than one unsigned: a loop condition like i < s.len then
       removes the second, leaving only i < 0. */
    if (__builtin_expect(i < 0 || i >= s->len, 0))
        vu_fail(line, "index %lld out of bounds for a string of length %lld", (long long)i, (long long)s->len);
    return s->data[i];
}
static vu_str vu_str_slice(const vu_str *s, int64_t a, int64_t b, int line) {
    if (a < 0 || b < a || b > s->len)
        vu_fail(line, "slice %lld..%lld out of bounds for a string of length %lld", (long long)a, (long long)b, (long long)s->len);
    vu_str r = {0};
    vu_str_cat_bytes(&r, s->data + a, b - a);
    return r;
}
/* s += t[a..b] in one copy, with no temporary string. When t is s itself, growing s moves its bytes,
   so the source is addressed by offset after growing. */
static void vu_str_cat_slice(vu_str *s, const vu_str *t, int64_t a, int64_t b, int line) {
    if (a < 0 || b < a || b > t->len)
        vu_fail(line, "slice %lld..%lld out of bounds for a string of length %lld", (long long)a, (long long)b, (long long)t->len);
    int64_t n = b - a;
    vu_str_reserve(s, n);
    if (n) memmove(s->data + s->len, t->data + a, (size_t)n);
    s->len += n;
}
static void vu_write(const uint8_t *p, int64_t n) { if (n) fwrite(p, 1, (size_t)n, stdout); }
/* Freeing nested values (nodes that own nodes, lists that own lists) goes through a per-thread
   to-do list worked by a loop, so however deep the nesting, the C stack stays shallow. */
typedef struct { void (*fn)(void *, int64_t); void *p; int64_t n; } vu_job;
static __thread vu_job vu_jobs_small[64];
static __thread vu_job *vu_jobs;
static __thread int64_t vu_njobs, vu_capjobs;
static __thread int vu_draining;
/* Shallow nesting is freed by direct calls (fast); past this depth the to-do list takes over. */
#define VU_MAX_DROP_DEPTH 1000
static __thread int vu_drop_depth;
__attribute__((noinline, cold)) static void vu_defer(void (*fn)(void *, int64_t), void *p, int64_t n) {
    if (!vu_jobs) { vu_jobs = vu_jobs_small; vu_capjobs = 64; }
    if (vu_njobs == vu_capjobs) {
        if (vu_capjobs > INT64_MAX / 2 / (int64_t)sizeof(vu_job)) vu_oom();
        vu_job *nj = (vu_job *)vu_malloc((size_t)vu_capjobs * 2 * sizeof(vu_job));
        memcpy(nj, vu_jobs, (size_t)vu_njobs * sizeof(vu_job));
        if (vu_jobs != vu_jobs_small) free(vu_jobs);
        vu_jobs = nj;
        vu_capjobs *= 2;
    }
    vu_jobs[vu_njobs++] = (vu_job){fn, p, n};
    if (vu_draining) return;
    vu_draining = 1;
    while (vu_njobs) { vu_job j = vu_jobs[--vu_njobs]; j.fn(j.p, j.n); }
    vu_draining = 0;
    if (vu_jobs != vu_jobs_small) { free(vu_jobs); vu_jobs = vu_jobs_small; vu_capjobs = 64; }
}

static vu_str vu_str_dup(const vu_str *s) { vu_str r = {0}; vu_str_cat_bytes(&r, s->data, s->len); return r; }
/* ---- Python's string methods. Strings are bytes; whitespace is ASCII (space \t \n \r \v \f). */
static inline bool vu_is_ws(uint8_t c) { return c == ' ' || (c >= '\t' && c <= '\r'); }
static bool vu_in_set(uint8_t c, const vu_str *chars) {
    return chars ? memchr(chars->data ? chars->data : (const uint8_t *)"", c, (size_t)chars->len) != NULL : vu_is_ws(c);
}
/* strip/lstrip/rstrip: chars NULL means whitespace; otherwise any byte that appears in chars */
static vu_str vu_strip(const vu_str *s, const vu_str *chars, bool left, bool right) {
    int64_t a = 0, b = s->len;
    if (left) while (a < b && vu_in_set(s->data[a], chars)) a++;
    if (right) while (b > a && vu_in_set(s->data[b - 1], chars)) b--;
    vu_str r = {0};
    vu_str_cat_bytes(&r, s->data ? s->data + a : NULL, b - a);
    return r;
}
static bool vu_startswith(const vu_str *s, const vu_str *p) {
    return p->len <= s->len && (p->len == 0 || memcmp(s->data, p->data, (size_t)p->len) == 0);
}
static bool vu_endswith(const vu_str *s, const vu_str *p) {
    return p->len <= s->len && (p->len == 0 || memcmp(s->data + (s->len - p->len), p->data, (size_t)p->len) == 0);
}
/* split: one piece per call. sep NULL splits on runs of whitespace and skips empty pieces (like
   Python's s.split()); otherwise every occurrence of sep separates (s.split(sep)). *pos starts at 0
   and is -1 once the last piece has been returned. */
static bool vu_split_next(const vu_str *s, const vu_str *sep, int64_t *pos, vu_str *out, int line) {
    int64_t i = *pos;
    if (i < 0) return false;
    if (!sep) {
        while (i < s->len && vu_is_ws(s->data[i])) i++;
        if (i >= s->len) { *pos = -1; return false; }
        int64_t j = i;
        while (j < s->len && !vu_is_ws(s->data[j])) j++;
        *out = (vu_str){0};
        vu_str_cat_bytes(out, s->data + i, j - i);
        *pos = j;
        return true;
    }
    if (sep->len == 0) vu_fail(line, "split() separator can't be empty");
    int64_t j = i;
    const uint8_t *hit = NULL;
    while (j + sep->len <= s->len) {
        hit = memchr(s->data + j, sep->data[0], (size_t)(s->len - sep->len - j + 1));
        if (!hit) break;
        j = hit - s->data;
        if (memcmp(hit, sep->data, (size_t)sep->len) == 0) break;
        hit = NULL;
        j++;
    }
    int64_t end = hit ? j : s->len;
    *out = (vu_str){0};
    vu_str_cat_bytes(out, s->data ? s->data + i : NULL, end - i);
    *pos = hit ? end + sep->len : -1;
    return true;
}
static vu_str vu_join(const vu_str *sep, const vu_str *items, int64_t n) {
    vu_str r = {0};
    int64_t total = 0;
    for (int64_t i = 0; i < n; i++) {
        if (items[i].len > INT64_MAX - total) vu_oom();
        total += items[i].len;
    }
    if (n > 1 && sep->len > 0 && (n - 1) > (INT64_MAX - total) / sep->len) vu_oom();
    total += n > 1 ? (n - 1) * sep->len : 0;
    vu_str_reserve(&r, total);
    for (int64_t i = 0; i < n; i++) {
        if (i) vu_str_cat_bytes(&r, sep->data, sep->len);
        vu_str_cat_bytes(&r, items[i].data, items[i].len);
    }
    return r;
}
/* ---- sorting: a stable merge sort. Floats sort NaN after every number. With rev the order is
   reversed but still stable (equal elements keep their order), as in Python's sorted(reverse=True). */
#define VU_LT_NUM(x, y) ((x) < (y))
#define VU_LT_F64(x, y) (!isnan(x) && (isnan(y) || (x) < (y)))
#define VU_LT_STR(x, y) (vu_str_cmp(&(x), &(y)) < 0)
#define VU_SORT_FN(NAME, T, LT) \
static void NAME(T *a, int64_t n, bool rev) { \
    if (n < 2) return; \
    if (n > (int64_t)(PTRDIFF_MAX / sizeof(T))) vu_oom(); \
    T *buf = (T *)vu_malloc((size_t)n * sizeof(T)); \
    for (int64_t w = 1; w < n; w = w > n / 2 ? n : w * 2) { \
        for (int64_t lo = 0; lo < n - w; lo += 2 * w) { \
            int64_t mid = lo + w, hi = mid + w < n ? mid + w : n, i = lo, j = mid, k = lo; \
            while (i < mid && j < hi) { \
                bool take_right = rev ? LT(a[i], a[j]) : LT(a[j], a[i]); \
                buf[k++] = take_right ? a[j++] : a[i++]; \
            } \
            while (i < mid) buf[k++] = a[i++]; \
            while (j < hi) buf[k++] = a[j++]; \
            memcpy(a + lo, buf + lo, (size_t)(hi - lo) * sizeof(T)); \
        } \
    } \
    free(buf); \
}
VU_SORT_FN(vu_sort_i64, int64_t, VU_LT_NUM)
VU_SORT_FN(vu_sort_u8, uint8_t, VU_LT_NUM)
VU_SORT_FN(vu_sort_bool, bool, VU_LT_NUM)
VU_SORT_FN(vu_sort_f64, double, VU_LT_F64)
VU_SORT_FN(vu_sort_str, vu_str, VU_LT_STR)
/* min(xs) / max(xs): the first smallest (largest) element, in the same order as sorting. */
#define VU_PICK_FN(NAME, T, LT) \
static int64_t NAME(const T *a, int64_t n, bool want_max, int line) { \
    if (n == 0) vu_fail(line, want_max ? "max() of an empty list" : "min() of an empty list"); \
    int64_t best = 0; \
    for (int64_t i = 1; i < n; i++) if (want_max ? LT(a[best], a[i]) : LT(a[i], a[best])) best = i; \
    return best; \
}
VU_PICK_FN(vu_pick_i64, int64_t, VU_LT_NUM)
VU_PICK_FN(vu_pick_u8, uint8_t, VU_LT_NUM)
VU_PICK_FN(vu_pick_f64, double, VU_LT_F64)
VU_PICK_FN(vu_pick_str, vu_str, VU_LT_STR)

/* Map hashing: SipHash-1-3 with a random key per run, so an attacker who controls the keys can't
   make them all collide (hash flooding). Iteration order is insertion order, so it doesn't leak. */
static uint64_t vu_sip_k0, vu_sip_k1;
/* Deep recursion runs into the guard page below the stack. Like Rust, catch that on a separate
   signal stack and stop with a clear message (exit 101) instead of dying from a bare signal. */
static uintptr_t vu_stack_top, vu_stack_size;
static __thread uintptr_t vu_t_lo, vu_t_hi;   /* this par worker's stack, once guarded */
static __thread void *vu_t_alt;
static __thread bool vu_t_guarded;
__attribute__((cold, noinline)) static void vu_thread_guard_slow(void) {
    vu_t_guarded = true;
    pthread_attr_t at;
    void *addr;
    size_t sz;
    if (pthread_getattr_np(pthread_self(), &at) == 0) {
        if (pthread_attr_getstack(&at, &addr, &sz) == 0) { vu_t_lo = (uintptr_t)addr; vu_t_hi = vu_t_lo + sz; }
        pthread_attr_destroy(&at);
    }
    stack_t cur;
    if (sigaltstack(NULL, &cur) == 0 && !(cur.ss_flags & SS_DISABLE)) return;   /* main thread: has one */
    vu_t_alt = malloc(1 << 16);
    if (!vu_t_alt) return;
    stack_t ss = {.ss_sp = vu_t_alt, .ss_size = 1 << 16, .ss_flags = 0};
    sigaltstack(&ss, NULL);
}
/* Each type of tree node has a free list per thread. Nodes built on one thread and freed on another
   (par loops) would pile up on the freeing thread's list while the building thread carves new ones,
   so at the start of every par loop each thread hands its free lists to a shared pool, and a thread
   whose list is empty takes from the pool before carving. (A program without par loops has one
   thread, whose lists never hold more nodes than were once alive at the same time.) */
#define VU_TAKE 1024
typedef struct vu_pool { void (*give)(void); struct vu_pool *next; } vu_pool;
static vu_pool *vu_pools;   /* every node type's pool, linked at startup */
static void vu_share_free(void) { for (vu_pool *p = vu_pools; p; p = p->next) p->give(); }
static inline void vu_thread_guard(void) {
    if (__builtin_expect(!vu_t_guarded, 0)) vu_thread_guard_slow();
#ifndef VU_MALLOC
    vu_share_free();
#endif
}
static void vu_segv(int sig, siginfo_t *si, void *ctx) {
    (void)sig; (void)ctx;
    uintptr_t a = (uintptr_t)si->si_addr;
    static const char over[] = "stack overflow (recursion too deep)";
    static const char other[] = "segmentation fault (this is a bug in the Vu compiler; please report it)";
    bool is_over = (a < vu_stack_top && vu_stack_top - a < vu_stack_size + (1u << 20))
                || (vu_t_hi && a < vu_t_hi && a + (1u << 20) >= vu_t_lo);
    vu_report_lock();   /* before touching the buffer: another thread may be writing its report */
    vu_plen = 0;        /* this thread may have been interrupted halfway through its own report */
    vu_report(is_over ? over : other, is_over ? sizeof over - 1 : sizeof other - 1, 0);
    _exit(101);
}
static void vu_guard_init(void *top) {
    static char altstack[1 << 16];
    struct rlimit rl;
    vu_stack_top = (uintptr_t)top;
    vu_stack_size = (getrlimit(RLIMIT_STACK, &rl) == 0 && rl.rlim_cur != RLIM_INFINITY) ? (uintptr_t)rl.rlim_cur
                                                                                        : ((uintptr_t)1 << 30);
    stack_t ss = {.ss_sp = altstack, .ss_size = sizeof altstack, .ss_flags = 0};
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_sigaction = vu_segv;
    sa.sa_flags = SA_SIGINFO | SA_ONSTACK;
    sigemptyset(&sa.sa_mask);
    if (sigaltstack(&ss, NULL) == 0) { sigaction(SIGSEGV, &sa, NULL); sigaction(SIGBUS, &sa, NULL); }
}
#define VU_SMALL_MAP 16
/* main runs on a thread with a 256 MB stack (reserved, not committed), so deeply recursive code such
   as parsers and compilers works; recursion past that still stops cleanly with "stack overflow". */
#define VU_MAIN_STACK ((size_t)256 << 20)
static int (*vu_main_fn)(void);
static int vu_main_rc;
static void vu_thread_guard(void);
/* The main thread exits the process itself, while it's still alive: its thread-local free lists then
   still count as reachable for LeakSanitizer. */
static void *vu_main_thread(void *arg) { (void)arg; vu_thread_guard(); vu_main_rc = vu_main_fn(); fflush(stdout); exit(vu_main_rc); }
static void vu_seed_init(void);
static void vu_guard_init(void *top);
static int vu_start(int argc, char **argv, int (*fn)(void), const char *const *files) {
    vu_argc = argc;
    vu_argv = argv;
    vu_files = files;
#ifdef VU_JSON_PANIC
    vu_json = true;
#else
    const char *pj = getenv("VU_PANIC");
    vu_json = pj && strcmp(pj, "json") == 0;
#endif
    vu_seed_init();
    vu_guard_init(__builtin_frame_address(0));
    vu_main_fn = fn;
    pthread_attr_t at;
    pthread_t t;
    if (pthread_attr_init(&at) == 0 && pthread_attr_setstacksize(&at, VU_MAIN_STACK) == 0 &&
        pthread_create(&t, &at, vu_main_thread, NULL) == 0) {
        pthread_join(t, NULL);
        return vu_main_rc;
    }
    return fn();   /* no thread available: run on the normal stack */
}
static void vu_seed_init(void) {
    uint64_t k[2];
    if (getrandom(k, sizeof k, 0) != (ssize_t)sizeof k) { k[0] = (uint64_t)time(NULL); k[1] = (uint64_t)(uintptr_t)&k; }
    vu_sip_k0 = k[0];
    vu_sip_k1 = k[1];
}
#define VU_ROTL(x, b) (uint64_t)(((x) << (b)) | ((x) >> (64 - (b))))
#define VU_SIPROUND do { v0 += v1; v1 = VU_ROTL(v1, 13); v1 ^= v0; v0 = VU_ROTL(v0, 32); v2 += v3; \
    v3 = VU_ROTL(v3, 16); v3 ^= v2; v0 += v3; v3 = VU_ROTL(v3, 21); v3 ^= v0; v2 += v1; v1 = VU_ROTL(v1, 17); \
    v1 ^= v2; v2 = VU_ROTL(v2, 32); } while (0)
static uint64_t vu_siphash(const uint8_t *in, size_t len) {
    static const uint8_t empty[1];
    if (!in) in = empty;
    uint64_t v0 = 0x736f6d6570736575ULL ^ vu_sip_k0, v1 = 0x646f72616e646f6dULL ^ vu_sip_k1;
    uint64_t v2 = 0x6c7967656e657261ULL ^ vu_sip_k0, v3 = 0x7465646279746573ULL ^ vu_sip_k1;
    uint64_t b = ((uint64_t)len) << 56;
    size_t full = len - (len % 8);
    for (size_t i = 0; i < full; i += 8) { uint64_t m; memcpy(&m, in + i, 8); v3 ^= m; VU_SIPROUND; v0 ^= m; }
    for (size_t i = 0; i < len % 8; i++) b |= ((uint64_t)in[full + i]) << (8 * i);
    v3 ^= b; VU_SIPROUND; v0 ^= b;
    v2 ^= 0xff; VU_SIPROUND; VU_SIPROUND; VU_SIPROUND;
    return v0 ^ v1 ^ v2 ^ v3;
}
static inline uint64_t vu_hash_int(int64_t v) { return vu_siphash((const uint8_t *)&v, 8); }

/* Capabilities: zero-size tokens. Only main receives them, so only code handed one can use it. */
typedef struct { char unused; } vu_cap;
/* A function value: the C function, cast back to its real type at each call (vu_call_<type>), and the
   closure's captured variables. An own closure's env is on the heap and drop frees it; a closure that
   borrows has its env on the stack (drop is NULL), and a named function has none. */
typedef struct { void (*fn)(void); void *env; void (*drop)(void *); } vu_fn;
static void vu_fn_drop(vu_fn *p) { if (p->drop) p->drop(p->env); p->drop = NULL; p->env = NULL; }
static vu_str vu_arg_str(int64_t i, vu_str d) {
    if (i < 0 || i >= vu_argc) return d;
    drop_Str(&d);
    vu_str r = {0};
    vu_str_cat_bytes(&r, (const uint8_t *)vu_argv[i], (int64_t)strlen(vu_argv[i]));
    return r;
}
static vu_str vu_str_from_c(const char *p) {
    vu_str r = {0};
    vu_str_cat_bytes(&r, (const uint8_t *)p, (int64_t)strlen(p));
    return r;
}
/* exit() takes the report lock too: if a par worker panics at the same moment, one of them wins, and
   the output and the exit code agree. */
__attribute__((noreturn)) static void vu_exit(int64_t code) { vu_report_lock(); fflush(stdout); exit((int)(code & 255)); }
static void vu_eprint(const uint8_t *p, int64_t n) {
    fflush(stdout);
    if (n) fwrite(p, 1, (size_t)n, stderr);
    fputc('\n', stderr);
}
static vu_str vu_errf(const char *fmt, ...) {
    char buf[1200];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    vu_str r = {0};
    if (n > 0) vu_str_cat_bytes(&r, (const uint8_t *)buf, n < (int)sizeof buf ? n : (int)sizeof buf - 1);
    return r;
}
/* float(s) and int(s): the whole string must be a number written the plain way (no spaces, no hex,
   no "inf"/"nan"). Conversion is exact (strtod rounds correctly). */
static bool vu_parse_int(const vu_str *s, int64_t *out, vu_str *err) {
    const uint8_t *d = s->data;
    int64_t n = s->len, i = 0;
    bool neg = false;
    if (n > 1 && (d[0] == '-' || d[0] == '+')) { neg = d[0] == '-'; i = 1; }
    bool ok = n > 0;
    uint64_t v = 0;
    bool big = false;
    for (; ok && i < n; i++) {
        unsigned c = (unsigned)d[i] - '0';
        if (c > 9) { ok = false; break; }
        if (v > (UINT64_MAX - c) / 10) big = true;
        else v = v * 10 + c;
    }
    if (!ok) { *err = vu_errf("not an Int: '%.*s'", (int)(n > 100 ? 100 : n), (const char *)(d ? d : (const uint8_t *)"")); return false; }
    if (big || v > (neg ? (uint64_t)INT64_MAX + 1 : (uint64_t)INT64_MAX)) {
        *err = vu_errf("'%.*s' is too large for an Int", (int)(n > 100 ? 100 : n), (const char *)d);
        return false;
    }
    *out = neg ? (int64_t)(0 - v) : (int64_t)v;
    return true;
}
static void vu_slice_check(const vu_str *s, int64_t a, int64_t b, int line) {
    if (a < 0 || b < a || b > s->len)
        vu_fail(line, "slice %lld..%lld out of bounds for a string of length %lld", (long long)a, (long long)b, (long long)s->len);
}
/* A view of the bytes (cap 0: not owned, never freed or stored); the parsers copy what they read. */
static bool vu_parse_int_at(const vu_str *s, int64_t a, int64_t b, int64_t *out, vu_str *err, int line) {
    vu_slice_check(s, a, b, line);
    vu_str view = {s->data ? s->data + a : NULL, b - a, 0};
    return vu_parse_int(&view, out, err);
}
/* A NUL-terminated copy of a path, or NULL (with *err set) if the path can't be one. */
static char *vu_cpath(const vu_str *p, vu_str *err) {
    if (p->len && memchr(p->data, 0, (size_t)p->len)) { *err = vu_errf("file path contains a zero byte"); return NULL; }
    char *s = (char *)vu_malloc((size_t)p->len + 1);
    if (p->len) memcpy(s, p->data, (size_t)p->len);
    s[p->len] = 0;
    return s;
}
/* File operations fail with an error value (handled with ?, else or match), never a crash. */
static bool vu_fs_read(vu_cap fs, const vu_str *path, vu_str *out, vu_str *err) {
    (void)fs;
    char *p = vu_cpath(path, err);
    if (!p) return false;
    FILE *f = fopen(p, "rb");
    if (!f) { *err = vu_errf("can't read '%.1000s': %s", p, strerror(errno)); free(p); return false; }
    vu_str s = {0};
    uint8_t buf[65536];
    size_t n;
    errno = 0;
    while ((n = fread(buf, 1, sizeof buf, f)) > 0) vu_str_cat_bytes(&s, buf, (int64_t)n);
    int e = errno;
    bool bad = ferror(f);
    fclose(f);
    if (bad) { *err = vu_errf("can't read '%.1000s': %s", p, strerror(e ? e : EIO)); drop_Str(&s); free(p); return false; }
    free(p);
    *out = s;
    return true;
}
static bool vu_fs_temp_dir(vu_cap fs, vu_str *out, vu_str *err) {
    (void)fs;
    const char *base = getenv("TMPDIR");
    if (!base || !*base) base = "/tmp";
    char buf[4096];
    if (snprintf(buf, sizeof buf, "%s/vu-XXXXXX", base) >= (int)sizeof buf) { *err = vu_errf("TMPDIR is too long"); return false; }
    if (!mkdtemp(buf)) { *err = vu_errf("can't make a temporary directory in '%.1000s': %s", base, strerror(errno)); return false; }
    *out = vu_str_from_c(buf);
    return true;
}
/* The operating-system capability: running programs, reading environment variables, the clock. */
static double vu_os_clock(vu_cap os) {
    (void)os;
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}
/* Seconds since 1970-01-01 00:00 UTC, from the wall clock (which can jump; os.clock can't). */
static double vu_os_time(vu_cap os) {
    (void)os;
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}
static vu_str vu_os_env(vu_cap os, const vu_str *name) {
    (void)os;
    vu_str err = {0};
    char *n = vu_cpath(name, &err);
    if (!n) { drop_Str(&err); return (vu_str){0}; }
    const char *v = getenv(n);
    free(n);
    return v ? vu_str_from_c(v) : (vu_str){0};
}
/* Runs a program (found on PATH) with the given arguments and waits for it. The result is its exit
   code, or 128 + the signal number if a signal stopped it. */
static bool vu_os_run(vu_cap os, const vu_str *items, int64_t n, int64_t *out, vu_str *err) {
    (void)os;
    if (n <= 0) { *err = vu_errf("os.run() needs at least the program to run"); return false; }
    char **argv = (char **)vu_malloc(((size_t)n + 1) * sizeof(char *));
    for (int64_t i = 0; i < n; i++) {
        argv[i] = vu_cpath(&items[i], err);
        if (!argv[i]) {
            for (int64_t j = 0; j < i; j++) free(argv[j]);
            free(argv);
            drop_Str(err);
            *err = vu_errf("argument %lld contains a zero byte", (long long)i);
            return false;
        }
    }
    argv[n] = NULL;
    fflush(stdout);
    fflush(stderr);
    pid_t pid;
    int rc = posix_spawnp(&pid, argv[0], NULL, NULL, argv, environ);
    bool ok = rc == 0;
    if (!ok) *err = vu_errf("can't run '%.1000s': %s", argv[0], strerror(rc));
    for (int64_t i = 0; i < n; i++) free(argv[i]);
    free(argv);
    if (!ok) return false;
    int status;
    while (waitpid(pid, &status, 0) < 0) {
        if (errno != EINTR) { *err = vu_errf("waiting for a program failed: %s", strerror(errno)); return false; }
    }
    *out = WIFEXITED(status) ? WEXITSTATUS(status) : WIFSIGNALED(status) ? 128 + WTERMSIG(status) : 1;
    return true;
}
static bool vu_fs_write(vu_cap fs, const vu_str *path, const uint8_t *data, int64_t n, vu_str *err) {
    (void)fs;
    char *p = vu_cpath(path, err);
    if (!p) return false;
    FILE *f = fopen(p, "wb");
    if (!f) { *err = vu_errf("can't write '%.1000s': %s", p, strerror(errno)); free(p); return false; }
    bool ok = !(n && fwrite(data, 1, (size_t)n, f) != (size_t)n);
    if (fclose(f) != 0) ok = false;
    if (!ok) *err = vu_errf("error writing '%.1000s'", p);
    free(p);
    return ok;
}
'''


FLOAT_RT = r'''/* Reading floats from text. Three steps, each exact:
   1. Clinger: the digits form m < 2^53 and the power of ten is at most 22, so m and 10^e are exact
      doubles and one multiply or divide is correctly rounded.
   2. Eisel-Lemire: up to 19 significant digits, using a table of 128-bit powers of ten. It either
      produces the correctly rounded result or reports that it can't decide.
   3. Otherwise, strtod.
   All three give the same double strtod would. */
static bool vu_eisel_lemire(uint64_t man, int64_t e10, bool neg, double *out) {
    if (man == 0) { *out = neg ? -0.0 : 0.0; return true; }
    if (e10 < -348 || e10 > 347) return false;
    int clz = __builtin_clzll(man);
    man <<= clz;
    uint64_t ret_exp2 = (uint64_t)(((217706 * e10) >> 16) + 64 + 1023) - (uint64_t)clz;
    const uint64_t *pw = vu_pow10_128[e10 + 348];
    unsigned __int128 x = (unsigned __int128)man * pw[1];
    uint64_t x_hi = (uint64_t)(x >> 64), x_lo = (uint64_t)x;
    if ((x_hi & 0x1FF) == 0x1FF && x_lo + man < man) {
        unsigned __int128 y = (unsigned __int128)man * pw[0];
        uint64_t y_hi = (uint64_t)(y >> 64), y_lo = (uint64_t)y;
        uint64_t merged_hi = x_hi, merged_lo = x_lo + y_hi;
        if (merged_lo < x_lo) merged_hi++;
        if ((merged_hi & 0x1FF) == 0x1FF && merged_lo + 1 == 0 && y_lo + man < man) return false;
        x_hi = merged_hi;
        x_lo = merged_lo;
    }
    uint64_t msb = x_hi >> 63;
    uint64_t ret_man = x_hi >> (msb + 9);
    ret_exp2 -= 1 ^ msb;
    if (x_lo == 0 && (x_hi & 0x1FF) == 0 && (ret_man & 3) == 1) return false;
    ret_man += ret_man & 1;
    ret_man >>= 1;
    if (ret_man >> 53 > 0) { ret_man >>= 1; ret_exp2 += 1; }
    if (ret_exp2 - 1 >= 0x7FF - 1) return false;
    uint64_t bits = ret_exp2 << 52 | (ret_man & 0x000FFFFFFFFFFFFFULL);
    if (neg) bits |= 0x8000000000000000ULL;
    memcpy(out, &bits, sizeof *out);
    return true;
}
static bool vu_float_fast(const uint8_t *d, int64_t n, double *out) {
    static const double p10[] = {1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11,
                                 1e12, 1e13, 1e14, 1e15, 1e16, 1e17, 1e18, 1e19, 1e20, 1e21, 1e22};
    int64_t i = 0;
    bool neg = false;
    if (i < n && (d[i] == '-' || d[i] == '+')) { neg = d[i] == '-'; i++; }
    uint64_t m = 0;
    int digits = 0, ndig = 0;
    int64_t scale = 0;
    for (; i < n && d[i] >= '0' && d[i] <= '9'; i++, ndig++) {
        if (m || d[i] != '0') { if (++digits > 19) return false; m = m * 10 + (uint64_t)(d[i] - '0'); }
    }
    if (i < n && d[i] == '.') {
        for (i++; i < n && d[i] >= '0' && d[i] <= '9'; i++, ndig++) {
            if (m || d[i] != '0') { if (++digits > 19) return false; m = m * 10 + (uint64_t)(d[i] - '0'); }
            scale--;
        }
    }
    if (ndig == 0) return false;
    if (i < n && (d[i] == 'e' || d[i] == 'E')) {
        i++;
        bool eneg = false;
        if (i < n && (d[i] == '-' || d[i] == '+')) { eneg = d[i] == '-'; i++; }
        if (i >= n) return false;
        int64_t e = 0;
        for (; i < n && d[i] >= '0' && d[i] <= '9'; i++) { if (e > 100000) return false; e = e * 10 + (d[i] - '0'); }
        scale += eneg ? -e : e;
    }
    if (i != n) return false;
    if (m <= (1ULL << 53) && scale >= -22 && scale <= 22) {
        double v = (double)m;
        v = scale < 0 ? v / p10[-scale] : v * p10[scale];
        *out = neg ? -v : v;
        return true;
    }
    return vu_eisel_lemire(m, scale, neg, out);
}
static bool vu_parse_float(const vu_str *s, double *out, vu_str *err) {
    if (s->len > 0 && vu_float_fast(s->data, s->len, out)) return true;
    char buf[400];
    if (s->len <= 0 || s->len >= (int64_t)sizeof buf) { *err = vu_errf("not a number (%lld bytes)", (long long)s->len); return false; }
    bool digit = false;
    for (int64_t i = 0; i < s->len; i++) {
        uint8_t c = s->data[i];
        if (c >= '0' && c <= '9') digit = true;
        else if (c != '+' && c != '-' && c != '.' && c != 'e' && c != 'E') { digit = false; break; }
    }
    memcpy(buf, s->data, (size_t)s->len);
    buf[s->len] = 0;
    char *end;
    double v = digit ? strtod(buf, &end) : 0;
    if (!digit || *end) { *err = vu_errf("not a number: '%.100s'", buf); return false; }
    *out = v;
    return true;
}
static bool vu_parse_float_at(const vu_str *s, int64_t a, int64_t b, double *out, vu_str *err, int line) {
    vu_slice_check(s, a, b, line);
    vu_str view = {s->data ? s->data + a : NULL, b - a, 0};
    return vu_parse_float(&view, out, err);
}
'''


def pow10_table():
    """128-bit approximations (rounded down) of 10^e for e in -348..347, for Eisel-Lemire."""
    rows = []
    for e in range(-348, 348):
        if e >= 0:
            v = 10 ** e
            b = v.bit_length()
            m = v << (128 - b) if b <= 128 else v >> (b - 128)
        else:
            v = 10 ** -e
            m = (1 << (127 + v.bit_length())) // v
        rows.append('{0x%016xULL, 0x%016xULL}' % (m & (2 ** 64 - 1), m >> 64))
    return 'static const uint64_t vu_pow10_128[696][2] = {\n' + ',\n'.join(rows) + '};\n'


POW10_TABLE = pow10_table()

FFI_RT = r'''/* The C side of extern blocks (SPEC.md, Calling C). A glue file can use these, vu_str, and
   vu_errf(fmt, ...) to build error messages. */
extern int omp_in_parallel(void) __attribute__((weak));
/* A new Str holding a copy of n bytes at p. */
static vu_str vu_str_from(const void *p, int64_t n) {
    vu_str s = {0};
    if (n > 0) vu_str_cat_bytes(&s, (const uint8_t *)p, n);
    return s;
}
/* A NUL-terminated copy of s for C APIs (free it with free()); NULL if s contains a zero byte. */
static char *vu_cstr(const vu_str *s) {
    if (s->len && memchr(s->data, 0, (size_t)s->len)) return NULL;
    char *p = (char *)vu_malloc((size_t)s->len + 1);
    if (s->len) memcpy(p, s->data, (size_t)s->len);
    p[s->len] = 0;
    return p;
}
static void vu_ffi_here(const char *fn, int line) {
    if (omp_in_parallel && omp_in_parallel()) {
        char m[300];
        int n = snprintf(m, sizeof m, "%.200s() is C code, which can't be called inside a par loop", fn);
        vu_panic(line, m, n);
    }
}
__attribute__((noreturn)) static void vu_ffi_null(const char *fn, int line) {
    char m[300];
    int n = snprintf(m, sizeof m, "%.200s() returned no handle (NULL) without reporting an error", fn);
    vu_panic(line, m, n);
}'''

JSON_RT = r'''/* JSON for to_json and from_json: string escaping for the encoder, and the decoder's scanner. The
   code for each type (vu_jenc_T, vu_jdec_T) is generated; these handle the plain values. */
static void vu_jcat(vu_str *o, const char *s, int64_t n) { vu_str_cat_bytes(o, (const uint8_t *)s, n); }
/* A JSON string: quotes, backslashes and control characters escaped; bytes that aren't UTF-8 become U+FFFD. */
static void vu_jenc_bytes(vu_str *o, const uint8_t *s, int64_t n) {
    static const char hex[] = "0123456789abcdef";
    vu_str_reserve(o, n + 2);
    vu_jcat(o, "\"", 1);
    int64_t i = 0, run = 0;
    while (i < n) {
        uint8_t c = s[i];
        if (c >= 0x20 && c < 0x80 && c != '"' && c != '\\') { i++; continue; }
        if (i > run) vu_str_cat_bytes(o, s + run, i - run);
        if (c == '"' || c == '\\') { char e[2] = {'\\', (char)c}; vu_jcat(o, e, 2); i++; }
        else if (c < 0x20) {
            const char *sh = c == '\n' ? "\\n" : c == '\t' ? "\\t" : c == '\r' ? "\\r" : c == '\b' ? "\\b" : c == '\f' ? "\\f" : NULL;
            if (sh) vu_jcat(o, sh, 2);
            else { char e[6] = {'\\', 'u', '0', '0', hex[c >> 4], hex[c & 15]}; vu_jcat(o, e, 6); }
            i++;
        } else {
            size_t k = vu_utf8_len(s + i, (size_t)(n - i));
            if (!k) { vu_jcat(o, "\\ufffd", 6); i++; }
            else { vu_str_cat_bytes(o, s + i, (int64_t)k); i += (int64_t)k; }
        }
        run = i;
    }
    if (i > run) vu_str_cat_bytes(o, s + run, i - run);
    vu_jcat(o, "\"", 1);
}
static void vu_jenc_Str(vu_str *o, const vu_str *v) { vu_jenc_bytes(o, v->data, v->len); }
static void vu_jenc_Int(vu_str *o, const int64_t *v) {
    char b[24];
    int n = snprintf(b, sizeof b, "%lld", (long long)*v);
    vu_jcat(o, b, n);
}
static void vu_jenc_Byte(vu_str *o, const uint8_t *v) { int64_t x = *v; vu_jenc_Int(o, &x); }
static void vu_jenc_Bool(vu_str *o, const bool *v) { if (*v) vu_jcat(o, "true", 4); else vu_jcat(o, "false", 5); }
/* NaN and the infinities have no JSON form: they become null, as in JavaScript. */
static void vu_jenc_Float(vu_str *o, const double *v) {
    if (!isfinite(*v)) { vu_jcat(o, "null", 4); return; }
    char b[40];
    const char *q = vu_shortest(*v, b);
    vu_jcat(o, q, (int64_t)strlen(q));
}
#define VU_JSON_DEPTH 1000
typedef struct {
    const uint8_t *s, *p, *end;
    int depth;
    vu_str err;    /* what went wrong, and where */
    vu_str path;   /* where in the value: items[3].qty (built as the decoders return) */
} vu_jp;
static bool vu_jfail(vu_jp *j, const char *what) {
    if (!j->err.len) {
        drop_Str(&j->err);
        j->err = vu_errf("%s at byte %lld", what, (long long)(j->p - j->s));
    }
    return false;
}
/* Puts a field name or a list index in front of the path to the error. Past 200 bytes the outer
   part is left out ("...") so deep data can't make a huge message. */
static void vu_jpath(vu_jp *j, const char *name, int64_t n, int64_t index) {
    if (j->path.len >= 200) {
        if (j->path.data[0] != '.') { vu_str p = {0}; vu_jcat(&p, "...", 3); vu_str_cat_bytes(&p, j->path.data, j->path.len); drop_Str(&j->path); j->path = p; }
        return;
    }
    vu_str p = {0};
    if (name) vu_str_cat_bytes(&p, (const uint8_t *)name, n);
    else { char b[32]; int k = snprintf(b, sizeof b, "[%lld]", (long long)index); vu_jcat(&p, b, k); }
    if (j->path.len && j->path.data[0] != '[') vu_jcat(&p, ".", 1);
    vu_str_cat_bytes(&p, j->path.data, j->path.len);
    drop_Str(&j->path);
    j->path = p;
}
static void vu_jws(vu_jp *j) {
    while (j->p < j->end && (*j->p == ' ' || *j->p == '\n' || *j->p == '\r' || *j->p == '\t')) j->p++;
}
static bool vu_jword(vu_jp *j, const char *w, size_t n) {
    if ((size_t)(j->end - j->p) >= n && memcmp(j->p, w, n) == 0) { j->p += n; return true; }
    return false;
}
/* Is the next value null? (Then it's read.) */
static bool vu_jnull(vu_jp *j) {
    vu_jws(j);
    return j->p < j->end && *j->p == 'n' && vu_jword(j, "null", 4);
}
static bool vu_jdec_Bool(vu_jp *j, bool *out) {
    vu_jws(j);
    if (vu_jword(j, "true", 4)) { *out = true; return true; }
    if (vu_jword(j, "false", 5)) { *out = false; return true; }
    return vu_jfail(j, "expected true or false");
}
/* The extent of a JSON number: -?(0|[1-9][0-9]*)(.[0-9]+)?([eE][+-]?[0-9]+)?; whole says it has no
   fraction or exponent. */
static bool vu_jnum(vu_jp *j, const uint8_t **a, bool *whole) {
    vu_jws(j);
    const uint8_t *p = j->p, *e = j->end;
    *a = p;
    *whole = true;
    if (p < e && *p == '-') p++;
    if (p < e && *p == '0') p++;
    else if (p < e && *p >= '1' && *p <= '9') { while (p < e && *p >= '0' && *p <= '9') p++; }
    else return vu_jfail(j, "expected a number");
    if (p < e && *p == '.') {
        p++;
        *whole = false;
        if (!(p < e && *p >= '0' && *p <= '9')) { j->p = p; return vu_jfail(j, "expected a digit after '.'"); }
        while (p < e && *p >= '0' && *p <= '9') p++;
    }
    if (p < e && (*p == 'e' || *p == 'E')) {
        p++;
        *whole = false;
        if (p < e && (*p == '+' || *p == '-')) p++;
        if (!(p < e && *p >= '0' && *p <= '9')) { j->p = p; return vu_jfail(j, "expected a digit in the exponent"); }
        while (p < e && *p >= '0' && *p <= '9') p++;
    }
    j->p = p;
    return true;
}
static bool vu_jdec_Int(vu_jp *j, int64_t *out) {
    const uint8_t *a;
    bool whole;
    if (!vu_jnum(j, &a, &whole)) return false;
    if (!whole) { j->p = a; return vu_jfail(j, "expected a whole number"); }
    bool neg = *a == '-';
    uint64_t v = 0, lim = neg ? (uint64_t)INT64_MAX + 1 : (uint64_t)INT64_MAX;
    for (const uint8_t *q = a + neg; q < j->p; q++) {
        uint64_t d = (uint64_t)(*q - '0');
        if (v > (lim - d) / 10) { j->p = a; return vu_jfail(j, "number too large for an Int"); }
        v = v * 10 + d;
    }
    *out = neg ? (int64_t)(0 - v) : (int64_t)v;
    return true;
}
static bool vu_jdec_Byte(vu_jp *j, uint8_t *out) {
    const uint8_t *a = j->p;
    int64_t v;
    if (!vu_jdec_Int(j, &v)) return false;
    if (v < 0 || v > 255) { j->p = a; vu_jws(j); return vu_jfail(j, "expected a number from 0 to 255"); }
    *out = (uint8_t)v;
    return true;
}
static bool vu_jdec_Float(vu_jp *j, double *out) {
    const uint8_t *a;
    bool whole;
    if (!vu_jnum(j, &a, &whole)) return false;
    vu_str view = {(uint8_t *)a, (int64_t)(j->p - a), 0}, e = {0};
    if (!vu_parse_float(&view, out, &e)) { drop_Str(&e); j->p = a; return vu_jfail(j, "expected a number"); }
    if (!isfinite(*out)) { j->p = a; return vu_jfail(j, "number too large for a Float"); }
    return true;
}
static int vu_jhex4(const uint8_t *p) {
    int v = 0;
    for (int i = 0; i < 4; i++) {
        int c = p[i], d = c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1;
        if (d < 0) return -1;
        v = v * 16 + d;
    }
    return v;
}
static void vu_jutf8(vu_str *o, int cp) {
    uint8_t b[4];
    int n;
    if (cp < 0x80) { b[0] = (uint8_t)cp; n = 1; }
    else if (cp < 0x800) { b[0] = (uint8_t)(0xC0 | (cp >> 6)); b[1] = (uint8_t)(0x80 | (cp & 0x3F)); n = 2; }
    else if (cp < 0x10000) { b[0] = (uint8_t)(0xE0 | (cp >> 12)); b[1] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F)); b[2] = (uint8_t)(0x80 | (cp & 0x3F)); n = 3; }
    else { b[0] = (uint8_t)(0xF0 | (cp >> 18)); b[1] = (uint8_t)(0x80 | ((cp >> 12) & 0x3F)); b[2] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F)); b[3] = (uint8_t)(0x80 | (cp & 0x3F)); n = 4; }
    vu_str_cat_bytes(o, b, n);
}
/* A string (the opening quote is next): escapes decoded, UTF-8 checked. */
static bool vu_jdec_Str(vu_jp *j, vu_str *out) {
    vu_jws(j);
    if (j->p >= j->end || *j->p != '"') return vu_jfail(j, "expected a string");
    const uint8_t *p = ++j->p, *e = j->end;
    vu_str s = {0};
    for (;;) {
        const uint8_t *run = p;
        while (p < e && *p >= 0x20 && *p != '"' && *p != '\\' && *p < 0x80) p++;
        if (p > run) vu_str_cat_bytes(&s, run, (int64_t)(p - run));
        if (p >= e) { j->p = p; drop_Str(&s); return vu_jfail(j, "unterminated string"); }
        uint8_t c = *p;
        if (c == '"') { j->p = p + 1; *out = s; return true; }
        if (c < 0x20) { j->p = p; drop_Str(&s); return vu_jfail(j, "control character in a string"); }
        if (c >= 0x80) {
            size_t k = vu_utf8_len(p, (size_t)(e - p));
            if (!k) { j->p = p; drop_Str(&s); return vu_jfail(j, "invalid UTF-8 in a string"); }
            vu_str_cat_bytes(&s, p, (int64_t)k);
            p += k;
            continue;
        }
        /* a backslash */
        if (p + 1 >= e) { j->p = p; drop_Str(&s); return vu_jfail(j, "unterminated string"); }
        uint8_t x = p[1];
        const char *simple = x == '"' ? "\"" : x == '\\' ? "\\" : x == '/' ? "/" : x == 'n' ? "\n" : x == 't' ? "\t"
                           : x == 'r' ? "\r" : x == 'b' ? "\b" : x == 'f' ? "\f" : NULL;
        if (simple) { vu_jcat(&s, simple, 1); p += 2; continue; }
        if (x != 'u') { j->p = p; drop_Str(&s); return vu_jfail(j, "bad escape in a string"); }
        int cp = e - p >= 6 ? vu_jhex4(p + 2) : -1;
        if (cp < 0) { j->p = p; drop_Str(&s); return vu_jfail(j, "bad \\u escape"); }
        p += 6;
        if (cp >= 0xD800 && cp < 0xDC00) {
            int lo = e - p >= 6 && p[0] == '\\' && p[1] == 'u' ? vu_jhex4(p + 2) : -1;
            if (lo < 0xDC00 || lo >= 0xE000) { j->p = p - 6; drop_Str(&s); return vu_jfail(j, "unpaired surrogate in a string"); }
            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
            p += 6;
        } else if (cp >= 0xDC00 && cp < 0xE000) { j->p = p - 6; drop_Str(&s); return vu_jfail(j, "unpaired surrogate in a string"); }
        vu_jutf8(&s, cp);
    }
}
static bool vu_jdeeper(vu_jp *j) {
    if (++j->depth > VU_JSON_DEPTH) return vu_jfail(j, "nested deeper than 1000 levels");
    return true;
}
/* Arrays: begin reads '['; next says whether a value follows (1), the array ended (0), or it's malformed (-1). */
static bool vu_jarr_begin(vu_jp *j) {
    vu_jws(j);
    if (j->p >= j->end || *j->p != '[') return vu_jfail(j, "expected a list");
    j->p++;
    return vu_jdeeper(j);
}
static int vu_jarr_next(vu_jp *j, bool first) {
    vu_jws(j);
    if (j->p < j->end && *j->p == ']') { j->p++; j->depth--; return 0; }
    if (!first) {
        if (j->p >= j->end || *j->p != ',') { vu_jfail(j, "expected ',' or ']'"); return -1; }
        j->p++;
    }
    return 1;
}
/* Objects: next reads a key and its ':' (1), the end '}' (0), or fails (-1). */
static bool vu_jobj_begin(vu_jp *j) {
    vu_jws(j);
    if (j->p >= j->end || *j->p != '{') return vu_jfail(j, "expected an object");
    j->p++;
    return vu_jdeeper(j);
}
static int vu_jobj_next(vu_jp *j, bool first, vu_str *key) {
    vu_jws(j);
    if (j->p < j->end && *j->p == '}') { j->p++; j->depth--; return 0; }
    if (!first) {
        if (j->p >= j->end || *j->p != ',') { vu_jfail(j, "expected ',' or '}'"); return -1; }
        j->p++;
        vu_jws(j);
    }
    if (!vu_jdec_Str(j, key)) return -1;
    vu_jws(j);
    if (j->p >= j->end || *j->p != ':') { drop_Str(key); vu_jfail(j, "expected ':'"); return -1; }
    j->p++;
    return 1;
}
static bool vu_jkey(const vu_str *k, const char *name, int64_t n) { return k->len == n && memcmp(k->data, name, (size_t)n) == 0; }
/* Skips any value (a field the type doesn't have). */
static bool vu_jskip(vu_jp *j) {
    vu_jws(j);
    if (j->p >= j->end) return vu_jfail(j, "expected a value");
    uint8_t c = *j->p;
    if (c == '"') { vu_str s = {0}; if (!vu_jdec_Str(j, &s)) return false; drop_Str(&s); return true; }
    if (c == 't' || c == 'f') { bool b; return vu_jdec_Bool(j, &b); }
    if (c == 'n') { if (vu_jnull(j)) return true; return vu_jfail(j, "expected a value"); }
    if (c == '[') {
        if (!vu_jarr_begin(j)) return false;
        for (bool first = true;; first = false) {
            int r = vu_jarr_next(j, first);
            if (r <= 0) return r == 0;
            if (!vu_jskip(j)) return false;
        }
    }
    if (c == '{') {
        if (!vu_jobj_begin(j)) return false;
        for (bool first = true;; first = false) {
            vu_str k = {0};
            int r = vu_jobj_next(j, first, &k);
            if (r <= 0) return r == 0;
            drop_Str(&k);
            if (!vu_jskip(j)) return false;
        }
    }
    const uint8_t *a;
    bool whole;
    return vu_jnum(j, &a, &whole);
}
/* After the whole value: only whitespace may follow. Then the error, if any, gets its path. */
static bool vu_jdone(vu_jp *j, bool ok, vu_str *err) {
    if (ok) {
        vu_jws(j);
        if (j->p != j->end) ok = vu_jfail(j, "extra data after the JSON value");
    }
    if (!ok) {
        if (j->path.len) {
            vu_str m = {0};
            vu_str_cat_bytes(&m, j->path.data, j->path.len);
            vu_jcat(&m, ": ", 2);
            vu_str_cat_bytes(&m, j->err.data, j->err.len);
            drop_Str(&j->err);
            *err = m;
        } else *err = j->err;
        j->err = (vu_str){0};
    }
    drop_Str(&j->path);
    return ok;
}'''

TASK_RT = r'''/* Tasks (spawn): lightweight threads sharing the main thread. A task runs until it waits for the
   network, a channel or a timer; then a task that is ready runs. Each task has its own stack
   (VU_TASK_STACK of address space, used as it grows) and its own call stack for backtraces.
   Values move into a task and through channels, and Vu has no globals, so tasks share nothing. */
#include <sys/mman.h>
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <limits.h>
#if defined(__SANITIZE_ADDRESS__)
#define VU_ASAN_FIBERS 1
#elif defined(__has_feature)
#if __has_feature(address_sanitizer)
#define VU_ASAN_FIBERS 1
#endif
#endif
#if defined(__SANITIZE_THREAD__)
#define VU_TSAN_FIBERS 1
#elif defined(__has_feature)
#if __has_feature(thread_sanitizer)
#define VU_TSAN_FIBERS 1
#endif
#endif
#ifdef VU_ASAN_FIBERS
#include <sanitizer/common_interface_defs.h>
#include <sanitizer/lsan_interface.h>
/* A switched-out task's locals can sit in AddressSanitizer's "fake stack" (used to catch returns of
   pointers to locals, which Vu code can't make), and LeakSanitizer doesn't look there: it would
   report what a waiting task holds as leaked. */
const char *__asan_default_options(void) { return "detect_stack_use_after_return=0"; }
#endif
#ifdef VU_TSAN_FIBERS
#include <sanitizer/tsan_interface.h>
#endif
#ifndef __x86_64__
#include <ucontext.h>
#endif
extern int omp_in_parallel(void) __attribute__((weak));
#define VU_TASK_STACK ((size_t)8 << 20)
#define VU_TASK_GUARD ((size_t)64 << 10)
enum { VU_W_NONE, VU_W_FD, VU_W_CHAN, VU_W_SLEEP };
typedef struct vu_task vu_task;
struct vu_task {
    void *sp;                     /* saved stack pointer while switched out (x86-64) */
#ifndef __x86_64__
    ucontext_t uc;
#endif
    char *mem;                    /* the mapping: guard, then the stack; NULL for the main task */
    void (*entry)(void *);
    void *arg;
    vu_task *next;                /* in the ready queue or a channel's wait list */
    vu_frame *top;                /* its call stack, for backtraces */
    uintptr_t lo, hi;             /* its stack, for stack-overflow reports */
    int64_t deadline;             /* when a timed wait ends (ns) */
    int64_t heap_at;              /* its place in the timer heap, or -1 */
    int line;                     /* where it was spawned */
    int wait_kind, wait_line;
    void *wait_obj;               /* the socket or channel it waits on */
    bool timed_out, writing;
    void *fake_stack;             /* AddressSanitizer's per-fiber state */
    void *tsan_fiber;
};
typedef struct vu_sock { int fd; vu_task *reader, *writer; void *ssl, *tls_ctx; bool hs; } vu_sock;
static vu_task vu_main_task;
static vu_task *vu_cur_task, *vu_ready_head, *vu_ready_tail, *vu_dead;
static vu_task **vu_heap;
static int64_t vu_nheap, vu_capheap, vu_io_waiters;
static int vu_ep = -1;
static char *vu_stack_pool[16];
static int vu_nstack_pool;
static uint8_t vu_iobuf[65536];

static int64_t vu_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}
static void vu_tasks_init(void) {
    if (vu_cur_task) return;
    vu_thread_guard();
    vu_main_task.heap_at = -1;
    vu_main_task.lo = vu_t_lo;
    vu_main_task.hi = vu_t_hi;
#ifdef VU_TSAN_FIBERS
    vu_main_task.tsan_fiber = __tsan_get_current_fiber();
#endif
    vu_cur_task = &vu_main_task;
}
/* Every task operation: tasks share the main thread, so par loop threads can't use them. */
static void vu_task_here(const char *what, int line) {
    if (omp_in_parallel && omp_in_parallel()) {
        char m[200];
        int n = snprintf(m, sizeof m, "%s can't be used inside a par loop", what);
        vu_panic(line, m, n);
    }
    vu_tasks_init();
}
/* -- the timer heap: tasks waiting with a deadline, earliest first */
static void vu_heap_swap(int64_t i, int64_t j) {
    vu_task *t = vu_heap[i];
    vu_heap[i] = vu_heap[j];
    vu_heap[j] = t;
    vu_heap[i]->heap_at = i;
    vu_heap[j]->heap_at = j;
}
static void vu_heap_up(int64_t i) {
    while (i > 0 && vu_heap[(i - 1) / 2]->deadline > vu_heap[i]->deadline) { vu_heap_swap(i, (i - 1) / 2); i = (i - 1) / 2; }
}
static void vu_heap_down(int64_t i) {
    for (;;) {
        int64_t l = 2 * i + 1, r = l + 1, m = i;
        if (l < vu_nheap && vu_heap[l]->deadline < vu_heap[m]->deadline) m = l;
        if (r < vu_nheap && vu_heap[r]->deadline < vu_heap[m]->deadline) m = r;
        if (m == i) return;
        vu_heap_swap(i, m);
        i = m;
    }
}
static void vu_heap_add(vu_task *t) {
    if (vu_nheap == vu_capheap) {
        vu_capheap = vu_capheap ? vu_capheap * 2 : 64;
        vu_heap = (vu_task **)realloc(vu_heap, (size_t)vu_capheap * sizeof *vu_heap);
        if (!vu_heap) vu_oom();
    }
    t->heap_at = vu_nheap;
    vu_heap[vu_nheap++] = t;
    vu_heap_up(t->heap_at);
}
static void vu_heap_remove(vu_task *t) {
    int64_t i = t->heap_at;
    if (i < 0) return;
    t->heap_at = -1;
    vu_nheap--;
    if (i == vu_nheap) return;
    vu_heap[i] = vu_heap[vu_nheap];
    vu_heap[i]->heap_at = i;
    vu_heap_down(i);
    vu_heap_up(i);
}
/* -- the ready queue */
static void vu_ready(vu_task *t) {
    t->next = NULL;
    if (vu_ready_tail) vu_ready_tail->next = t;
    else vu_ready_head = t;
    vu_ready_tail = t;
}
static vu_task *vu_ready_pop(void) {
    vu_task *t = vu_ready_head;
    if (t) {
        vu_ready_head = t->next;
        if (!vu_ready_head) vu_ready_tail = NULL;
        t->next = NULL;
    }
    return t;
}
/* -- switching */
#ifdef __x86_64__
/* Saves the callee-saved registers and the floating-point control words on the current stack,
   stores the stack pointer in *from, and continues on the stack to. */
__attribute__((naked, noinline)) static void vu_ctx_switch(void **from, void *to) {
    __asm__ volatile(
        "pushq %rbp\n\tpushq %rbx\n\tpushq %r12\n\tpushq %r13\n\tpushq %r14\n\tpushq %r15\n\t"
        "subq $8, %rsp\n\tstmxcsr (%rsp)\n\tfnstcw 4(%rsp)\n\t"
        "movq %rsp, (%rdi)\n\tmovq %rsi, %rsp\n\t"
        "ldmxcsr (%rsp)\n\tfldcw 4(%rsp)\n\taddq $8, %rsp\n\t"
        "popq %r15\n\tpopq %r14\n\tpopq %r13\n\tpopq %r12\n\tpopq %rbx\n\tpopq %rbp\n\tret\n\t");
}
#endif
static void vu_task_boot(void);
static void vu_reap(void) {
    vu_task *d = vu_dead;
    if (!d) return;
    vu_dead = NULL;
#ifdef VU_TSAN_FIBERS
    __tsan_destroy_fiber(d->tsan_fiber);
#endif
    if (vu_nstack_pool < 16) vu_stack_pool[vu_nstack_pool++] = d->mem;
    else {
#ifdef VU_ASAN_FIBERS
        __lsan_unregister_root_region(d->mem + VU_TASK_GUARD, VU_TASK_STACK);
#endif
        munmap(d->mem, VU_TASK_GUARD + VU_TASK_STACK);
    }
    free(d);
}
static void vu_switch_to(vu_task *t) {
    vu_task *from = vu_cur_task;
    if (t == from) return;
    bool dying = from == vu_dead;
    from->top = vu_top;
    vu_top = t->top;
    vu_t_lo = t->lo;
    vu_t_hi = t->hi;
    vu_cur_task = t;
#ifdef VU_ASAN_FIBERS
    __sanitizer_start_switch_fiber(dying ? NULL : &from->fake_stack, (const void *)t->lo, t->hi - t->lo);
#endif
#ifdef VU_TSAN_FIBERS
    __tsan_switch_to_fiber(t->tsan_fiber, 0);
#endif
#ifdef __x86_64__
    vu_ctx_switch(&from->sp, t->sp);
#else
    swapcontext(&from->uc, &t->uc);
#endif
    (void)dying;
    /* back in from, which was woken */
#ifdef VU_ASAN_FIBERS
    __sanitizer_finish_switch_fiber(from->fake_stack, NULL, NULL);
#endif
    vu_reap();
}
static __attribute__((noreturn, cold)) void vu_deadlock(void) {
    static const char m[] = "deadlock: every task is waiting on a channel, and none can be woken";
    vu_panic(vu_cur_task->wait_line, m, sizeof m - 1);   /* reported by the last task to wait */
}
/* Waits for sockets and timers, and makes the tasks they wake ready. */
static void vu_poll(void) {
    int timeout = -1;
    if (vu_nheap) {
        int64_t d = vu_heap[0]->deadline - vu_now_ns();
        timeout = d <= 0 ? 0 : (d / 1000000 + 1 > INT_MAX ? INT_MAX : (int)(d / 1000000 + 1));
    }
    if (timeout < 0 && vu_io_waiters == 0) vu_deadlock();
    if (vu_ep >= 0) {
        struct epoll_event ev[256];
        int n = epoll_wait(vu_ep, ev, 256, timeout);
        for (int i = 0; i < n; i++) {
            vu_sock *s = (vu_sock *)ev[i].data.ptr;
            uint32_t e = ev[i].events;
            if (s->reader && (e & (EPOLLIN | EPOLLERR | EPOLLHUP | EPOLLRDHUP))) {
                vu_task *t = s->reader;
                s->reader = NULL;
                vu_io_waiters--;
                vu_heap_remove(t);
                t->wait_kind = VU_W_NONE;
                vu_ready(t);
            }
            if (s->writer && (e & (EPOLLOUT | EPOLLERR | EPOLLHUP))) {
                vu_task *t = s->writer;
                s->writer = NULL;
                vu_io_waiters--;
                vu_heap_remove(t);
                t->wait_kind = VU_W_NONE;
                vu_ready(t);
            }
        }
    } else if (timeout > 0) {
        struct timespec ts = {timeout / 1000, (long)(timeout % 1000) * 1000000};
        nanosleep(&ts, NULL);
    }
    int64_t now = vu_now_ns();
    while (vu_nheap && vu_heap[0]->deadline <= now) {
        vu_task *t = vu_heap[0];
        vu_heap_remove(t);
        t->timed_out = true;
        if (t->wait_kind == VU_W_FD) {
            vu_sock *s = (vu_sock *)t->wait_obj;
            if (s->reader == t) s->reader = NULL;
            if (s->writer == t) s->writer = NULL;
            vu_io_waiters--;
        } else if (t->wait_kind == VU_W_CHAN) {
            vu_task **q = (vu_task **)t->wait_obj;
            while (*q && *q != t) q = &(*q)->next;
            if (*q) *q = t->next;
        }
        t->wait_kind = VU_W_NONE;
        vu_ready(t);
    }
}
/* The current task has put itself on a wait list (or is finished): run others until it is woken. */
static void vu_block(void) {
    for (;;) {
        vu_task *t = vu_ready_pop();
        if (t) {
            vu_switch_to(t);
            return;
        }
        vu_poll();
    }
}
static int64_t vu_deadline(double seconds, bool has, int line) {
    if (!has) return -1;
    if (!(seconds >= 0)) vu_fail(line, "a timeout is 0 or more seconds, not %g", seconds);
    if (seconds > 1e9) seconds = 1e9;
    return vu_now_ns() + (int64_t)(seconds * 1e9);
}
static void vu_wait_until(int64_t deadline) {
    vu_task *t = vu_cur_task;
    t->timed_out = false;
    if (deadline >= 0) {
        t->deadline = deadline;
        vu_heap_add(t);
    }
}
/* Waits until socket s is readable (or writable); false if the deadline passed first. */
static bool vu_wait_fd(vu_sock *s, bool write, int64_t deadline, int line) {
    vu_task *t = vu_cur_task;
    if (write) s->writer = t;
    else s->reader = t;
    t->wait_kind = VU_W_FD;
    t->wait_obj = s;
    t->wait_line = line;
    vu_io_waiters++;
    vu_wait_until(deadline);
    vu_block();
    return !t->timed_out;
}
/* -- spawning */
static void vu_task_exit(void) {
    vu_dead = vu_cur_task;
    vu_block();   /* never returns: the next task to run frees this one */
    __builtin_unreachable();
}
static void vu_task_boot(void) {
#ifdef VU_ASAN_FIBERS
    __sanitizer_finish_switch_fiber(NULL, NULL, NULL);
#endif
    vu_reap();
    vu_task *t = vu_cur_task;
#ifdef VU_TRACE
    vu_frame base = {"spawn", t->line, NULL};
    vu_top = &base;
#endif
    t->entry(t->arg);
    vu_task_exit();
}
static void vu_task_spawn(void (*entry)(void *), void *arg, int line) {
    vu_task_here("spawn", line);
    vu_task *t = (vu_task *)calloc(1, sizeof *t);
    if (!t) vu_oom();
    char *mem = vu_nstack_pool ? vu_stack_pool[--vu_nstack_pool] : NULL;
    if (!mem) {
        mem = (char *)mmap(NULL, VU_TASK_GUARD + VU_TASK_STACK, PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_STACK, -1, 0);
        if (mem == MAP_FAILED) vu_fail(line, "can't start a task: out of memory for its stack");
        mprotect(mem, VU_TASK_GUARD, PROT_NONE);
#ifdef VU_ASAN_FIBERS
        /* LeakSanitizer looks for pointers on thread stacks; a task's stack is memory of its own */
        __lsan_register_root_region(mem + VU_TASK_GUARD, VU_TASK_STACK);
#endif
    }
    t->mem = mem;
    t->entry = entry;
    t->arg = arg;
    t->line = line;
    t->heap_at = -1;
    t->lo = (uintptr_t)(mem + VU_TASK_GUARD);
    t->hi = (uintptr_t)(mem + VU_TASK_GUARD + VU_TASK_STACK);
#ifdef VU_TSAN_FIBERS
    t->tsan_fiber = __tsan_create_fiber(0);
#endif
#ifdef __x86_64__
    /* The first switch "returns" into vu_task_boot, with the stack as a call would leave it. */
    uintptr_t *sp = (uintptr_t *)t->hi;
    *--sp = 0;                          /* vu_task_boot's (never used) return address */
    *--sp = (uintptr_t)vu_task_boot;
    for (int i = 0; i < 6; i++) *--sp = 0;   /* rbp rbx r12 r13 r14 r15 */
    uint32_t cw[2] = {0x1F80, 0x037F};  /* the default MXCSR and x87 control word */
    sp--;
    memcpy(sp, cw, 8);
    t->sp = sp;
#else
    getcontext(&t->uc);
    t->uc.uc_stack.ss_sp = (void *)t->lo;
    t->uc.uc_stack.ss_size = VU_TASK_STACK;
    t->uc.uc_link = NULL;
    makecontext(&t->uc, vu_task_boot, 0);
#endif
    vu_ready(t);
}
/* os.sleep(seconds): lets other tasks run meanwhile. */
static void vu_task_sleep(vu_cap os, double seconds, int line) {
    (void)os;
    vu_task_here("os.sleep()", line);
    int64_t d = vu_deadline(seconds, true, line);
    vu_task *t = vu_cur_task;
    t->wait_kind = VU_W_SLEEP;
    t->wait_line = line;
    vu_wait_until(d);
    vu_block();
}
/* -- channels: a queue of up to cap values, shared by the tasks holding it (counted references) */
typedef struct vu_chan {
    int64_t refs, cap, len, head;
    size_t esz;
    char *buf;
    bool closed;
    vu_task *rq, *sq;             /* tasks waiting to receive / to send */
    void (*drop)(void *);         /* frees a value left in the channel */
} vu_chan;
static vu_chan *vu_chan_new(int64_t cap, size_t esz, void (*drop)(void *), int line) {
    if (cap < 1 || cap > ((int64_t)1 << 40) / (int64_t)(esz ? esz : 1))
        vu_fail(line, "chan(%lld): a channel holds 1 or more values", (long long)cap);
    vu_chan *c = (vu_chan *)calloc(1, sizeof *c);
    if (!c) vu_oom();
    c->refs = 1;
    c->cap = cap;
    c->esz = esz;
    c->drop = drop;
    c->buf = (char *)vu_malloc((size_t)cap * esz + 1);
    return c;
}
static vu_chan *vu_chan_share(vu_chan *c) { c->refs++; return c; }
static void vu_chan_release(vu_chan **p) {
    vu_chan *c = *p;
    if (!c) return;
    *p = NULL;
    if (--c->refs > 0) return;
    if (c->drop)
        for (int64_t i = 0; i < c->len; i++) c->drop(c->buf + (size_t)((c->head + i) % c->cap) * c->esz);
    free(c->buf);
    free(c);
}
static void vu_chan_wait(vu_task **head, int64_t deadline, int line) {
    vu_task *t = vu_cur_task;
    t->next = NULL;
    vu_task **q = head;
    while (*q) q = &(*q)->next;
    *q = t;
    t->wait_kind = VU_W_CHAN;
    t->wait_obj = (void *)head;   /* the list's head: a timeout removes t from wherever it is then */
    t->wait_line = line;
    vu_wait_until(deadline);
    vu_block();
}
static void vu_chan_wake(vu_task **q) {
    vu_task *t = *q;
    if (!t) return;
    *q = t->next;
    vu_heap_remove(t);
    t->wait_kind = VU_W_NONE;
    vu_ready(t);
}
static void vu_chan_send(vu_chan *c, const void *v, int line) {
    vu_task_here("send() on a channel", line);
    while (!c->closed && c->len == c->cap) vu_chan_wait(&c->sq, -1, line);
    if (c->closed) vu_fail(line, "send() on a closed channel");
    memcpy(c->buf + (size_t)((c->head + c->len) % c->cap) * c->esz, v, c->esz);
    c->len++;
    vu_chan_wake(&c->rq);
}
static bool vu_chan_recv(vu_chan *c, void *out, double timeout, bool has, vu_str *err, int line) {
    vu_task_here("recv() on a channel", line);
    int64_t deadline = vu_deadline(timeout, has, line);
    while (c->len == 0) {
        if (c->closed) { *err = vu_errf("the channel is closed"); return false; }
        if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
        vu_chan_wait(&c->rq, deadline, line);
    }
    memcpy(out, c->buf + (size_t)c->head * c->esz, c->esz);
    c->head = (c->head + 1) % c->cap;
    c->len--;
    vu_chan_wake(&c->sq);
    if (c->len > 0) vu_chan_wake(&c->rq);   /* another receiver can take the next value */
    return true;
}
static void vu_chan_close(vu_chan *c, int line) {
    vu_task_here("close() on a channel", line);
    c->closed = true;
    while (c->rq) vu_chan_wake(&c->rq);
    while (c->sq) vu_chan_wake(&c->sq);
}
/* -- the network: Listener and Conn are sockets registered once, edge-triggered, with the poller */
static void vu_tls_free(vu_sock *s);
static void vu_sock_drop(void *p) {
    vu_sock *s = (vu_sock *)p;
    if (s->ssl || s->tls_ctx) vu_tls_free(s);
    close(s->fd);   /* also leaves the epoll set */
    free(s);
}
static vu_sock *vu_sock_new(int fd, vu_str *err) {
    if (vu_ep < 0) {
        vu_ep = epoll_create1(EPOLL_CLOEXEC);
        if (vu_ep < 0) { *err = vu_errf("can't start the network poller: %s", strerror(errno)); close(fd); return NULL; }
    }
    vu_sock *s = (vu_sock *)calloc(1, sizeof *s);
    if (!s) vu_oom();
    s->fd = fd;
    struct epoll_event ev = {.events = EPOLLIN | EPOLLOUT | EPOLLRDHUP | EPOLLET, .data = {.ptr = s}};
    if (epoll_ctl(vu_ep, EPOLL_CTL_ADD, fd, &ev) < 0) {
        *err = vu_errf("can't watch a socket: %s", strerror(errno));
        close(fd);
        free(s);
        return NULL;
    }
    return s;
}
static bool vu_tls_accepted(vu_sock *l, vu_sock *s, vu_str *err);
static bool vu_tls_recv(vu_sock *c, int64_t deadline, vu_str *out, vu_str *err, int line);
static bool vu_tls_send(vu_sock *c, const uint8_t *data, int64_t len, int64_t deadline, vu_str *err, int line);
static bool vu_net_listen(vu_cap net, int64_t port, void **out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.listen()", line);
    if (port < 0 || port > 65535) { *err = vu_errf("port %lld is not in 0..65535", (long long)port); return false; }
    int fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (fd < 0) { *err = vu_errf("can't listen on port %lld: %s", (long long)port, strerror(errno)); return false; }
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in a;
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    a.sin_port = htons((uint16_t)port);
    if (bind(fd, (struct sockaddr *)&a, sizeof a) < 0 || listen(fd, SOMAXCONN) < 0) {
        int e = errno;
        close(fd);
        *err = vu_errf("can't listen on port %lld: %s", (long long)port, strerror(e));
        return false;
    }
    vu_sock *s = vu_sock_new(fd, err);
    if (!s) return false;
    *out = s;
    return true;
}
/* The port a listener is on (useful after listening on port 0, which picks a free one). */
static int64_t vu_net_port(vu_cap net, void *l) {
    (void)net;
    struct sockaddr_in a;
    socklen_t n = sizeof a;
    if (getsockname(((vu_sock *)l)->fd, (struct sockaddr *)&a, &n) < 0) return 0;
    return ntohs(a.sin_port);
}
static bool vu_net_accept(vu_cap net, void *lp, double timeout, bool has, void **out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.accept()", line);
    vu_sock *l = (vu_sock *)lp;
    int64_t deadline = vu_deadline(timeout, has, line);
    for (;;) {
        int c = accept4(l->fd, NULL, NULL, SOCK_NONBLOCK | SOCK_CLOEXEC);
        if (c >= 0) {
            int one = 1;
            setsockopt(c, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
            vu_sock *s = vu_sock_new(c, err);
            if (!s) return false;
            if (l->tls_ctx && !vu_tls_accepted(l, s, err)) { vu_sock_drop(s); return false; }
            *out = s;
            return true;
        }
        if (errno == EINTR || errno == ECONNABORTED) continue;
        if (errno == EMFILE || errno == ENFILE || errno == ENOBUFS || errno == ENOMEM) {
            /* out of file descriptors: try again shortly (closing connections frees some) */
            vu_task *t = vu_cur_task;
            t->wait_kind = VU_W_SLEEP;
            t->wait_line = line;
            int64_t soon = vu_now_ns() + 10000000;
            vu_wait_until(deadline >= 0 && deadline < soon ? deadline : soon);
            vu_block();
            if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
            continue;
        }
        if (errno != EAGAIN && errno != EWOULDBLOCK) { *err = vu_errf("accept failed: %s", strerror(errno)); return false; }
        if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
        if (!vu_wait_fd(l, false, deadline, line)) { *err = vu_errf("timed out"); return false; }
    }
}
/* The bytes that have arrived (at least one, at most about 1 MB), or "" once the other side has
   closed the connection. */
static bool vu_net_recv(vu_cap net, void *cp, double timeout, bool has, vu_str *out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.recv()", line);
    vu_sock *c = (vu_sock *)cp;
    int64_t deadline = vu_deadline(timeout, has, line);
    if (c->ssl) return vu_tls_recv(c, deadline, out, err, line);
    vu_str s = {0};
    for (;;) {
        ssize_t n = read(c->fd, vu_iobuf, sizeof vu_iobuf);
        if (n > 0) {
            vu_str_cat_bytes(&s, vu_iobuf, (int64_t)n);
            if ((size_t)n < sizeof vu_iobuf || s.len >= (1 << 20)) break;
            continue;
        }
        if (n == 0) break;
        if (errno == EINTR) continue;
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            if (s.len) break;
            if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
            if (!vu_wait_fd(c, false, deadline, line)) { *err = vu_errf("timed out"); return false; }
            continue;
        }
        if (s.len) break;   /* report the error on the next call */
        if (errno == ECONNRESET) break;   /* the other side is gone: like a close */
        *err = vu_errf("recv failed: %s", strerror(errno));
        return false;
    }
    *out = s;
    return true;
}
/* Sends all of data; other tasks run while the connection is full. */
static bool vu_net_send(vu_cap net, void *cp, const uint8_t *data, int64_t len, double timeout, bool has,
                        vu_str *err, int line) {
    (void)net;
    vu_task_here("net.send()", line);
    vu_sock *c = (vu_sock *)cp;
    int64_t deadline = vu_deadline(timeout, has, line);
    if (c->ssl) return vu_tls_send(c, data, len, deadline, err, line);
    while (len > 0) {
        ssize_t n = send(c->fd, data, (size_t)len, MSG_NOSIGNAL);
        if (n > 0) { data += n; len -= n; continue; }
        if (n < 0 && errno == EINTR) continue;
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
            if (!vu_wait_fd(c, true, deadline, line)) { *err = vu_errf("timed out"); return false; }
            continue;
        }
        *err = errno == EPIPE || errno == ECONNRESET ? vu_errf("the connection is closed")
                                                     : vu_errf("send failed: %s", strerror(errno));
        return false;
    }
    return true;
}
/* -- connecting out. Names are looked up on a helper thread, so other tasks keep running. */
typedef struct vu_dns {
    char *host;
    char port[8];
    struct addrinfo *res;
    int rc, efd;
    int state;   /* 0 running, 1 done, 2 abandoned (the task gave up; the thread frees everything) */
} vu_dns;
static void vu_dns_free(vu_dns *d) {
    if (d->res) freeaddrinfo(d->res);
    close(d->efd);
    free(d->host);
    free(d);
}
static void *vu_dns_thread(void *p) {
    vu_dns *d = (vu_dns *)p;
    struct addrinfo hints;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    d->rc = getaddrinfo(d->host, d->port, &hints, &d->res);
    if (__atomic_exchange_n(&d->state, 1, __ATOMIC_ACQ_REL) == 2) { vu_dns_free(d); return NULL; }
    uint64_t one = 1;
    if (write(d->efd, &one, 8) < 0) { /* the eventfd can't be full */ }
    return NULL;
}
static bool vu_resolve(const char *host, int64_t port, int64_t deadline, struct addrinfo **res, vu_str *err, int line) {
    struct addrinfo hints;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_NUMERICHOST;
    char ps[8];
    snprintf(ps, sizeof ps, "%lld", (long long)port);
    if (getaddrinfo(host, ps, &hints, res) == 0) return true;   /* an address, no lookup needed */
    vu_dns *d = (vu_dns *)calloc(1, sizeof *d);
    if (!d) vu_oom();
    d->host = strdup(host);
    memcpy(d->port, ps, sizeof ps);
    d->efd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
    if (d->efd < 0 || !d->host) { *err = vu_errf("can't look up '%.200s': %s", host, strerror(errno)); free(d->host); free(d); return false; }
    vu_str e2 = {0};
    vu_sock *w = vu_sock_new(dup(d->efd), &e2);
    if (!w) { *err = e2; vu_dns_free(d); return false; }
    pthread_t th;
    pthread_attr_t at;
    pthread_attr_init(&at);
    pthread_attr_setdetachstate(&at, PTHREAD_CREATE_DETACHED);
    if (pthread_create(&th, &at, vu_dns_thread, d) != 0) {
        pthread_attr_destroy(&at);
        vu_sock_drop(w);
        vu_dns_free(d);
        *err = vu_errf("can't look up '%.200s': no thread available", host);
        return false;
    }
    pthread_attr_destroy(&at);
    while (__atomic_load_n(&d->state, __ATOMIC_ACQUIRE) == 0) {
        if ((deadline >= 0 && vu_now_ns() >= deadline) || !vu_wait_fd(w, false, deadline, line)) {
            if (__atomic_exchange_n(&d->state, 2, __ATOMIC_ACQ_REL) == 1) vu_dns_free(d);   /* finished just now */
            vu_sock_drop(w);
            *err = vu_errf("timed out looking up '%.200s'", host);
            return false;
        }
    }
    vu_sock_drop(w);
    if (d->rc != 0) {
        *err = vu_errf("can't look up '%.200s': %s", host, gai_strerror(d->rc));
        vu_dns_free(d);
        return false;
    }
    *res = d->res;
    d->res = NULL;
    vu_dns_free(d);
    return true;
}
/* Connects to h:port (h a C string the caller frees) by the deadline. */
static bool vu_connect_to(const char *h, int64_t port, int64_t deadline, void **out, vu_str *err, int line) {
    struct addrinfo *res = NULL;
    if (!vu_resolve(h, port, deadline, &res, err, line)) return false;
    int last = ECONNREFUSED;
    for (struct addrinfo *a = res; a; a = a->ai_next) {
        int fd = socket(a->ai_family, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
        if (fd < 0) { last = errno; continue; }
        vu_str e2 = {0};
        if (connect(fd, a->ai_addr, a->ai_addrlen) < 0 && errno != EINPROGRESS) { last = errno; close(fd); continue; }
        vu_sock *s = vu_sock_new(fd, &e2);
        if (!s) { drop_Str(&e2); last = errno; continue; }
        for (;;) {
            int soerr = 0;
            socklen_t sl = sizeof soerr;
            getsockopt(fd, SOL_SOCKET, SO_ERROR, &soerr, &sl);
            if (soerr == 0) {
                struct sockaddr_storage peer;
                socklen_t pl = sizeof peer;
                if (getpeername(fd, (struct sockaddr *)&peer, &pl) == 0) {
                    int one = 1;
                    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
                    freeaddrinfo(res);
                    *out = s;
                    return true;
                }
                if (errno != ENOTCONN) { soerr = errno; }
            }
            if (soerr != 0) { last = soerr; break; }
            if ((deadline >= 0 && vu_now_ns() >= deadline) || !vu_wait_fd(s, true, deadline, line)) {
                vu_sock_drop(s);
                freeaddrinfo(res);
                *err = vu_errf("timed out connecting to %.200s:%lld", h, (long long)port);
                return false;
            }
        }
        vu_sock_drop(s);
    }
    freeaddrinfo(res);
    *err = vu_errf("can't connect to %.200s:%lld: %s", h, (long long)port, strerror(last));
    return false;
}
static bool vu_net_connect(vu_cap net, const vu_str *host, int64_t port, double timeout, bool has, void **out,
                           vu_str *err, int line) {
    (void)net;
    vu_task_here("net.connect()", line);
    if (port < 1 || port > 65535) { *err = vu_errf("port %lld is not in 1..65535", (long long)port); return false; }
    char *h = vu_cpath(host, err);
    if (!h) { drop_Str(err); *err = vu_errf("a host name can't contain a zero byte"); return false; }
    int64_t deadline = vu_deadline(timeout, has, line);
    bool ok = vu_connect_to(h, port, deadline, out, err, line);
    free(h);
    return ok;
}
#ifndef VU_TLS
static void vu_tls_free(vu_sock *s) { (void)s; }
static bool vu_tls_accepted(vu_sock *l, vu_sock *s, vu_str *err) { (void)l; (void)s; (void)err; return true; }
static bool vu_tls_recv(vu_sock *c, int64_t deadline, vu_str *out, vu_str *err, int line) {
    (void)c; (void)deadline; (void)out; (void)err; (void)line; return false;
}
static bool vu_tls_send(vu_sock *c, const uint8_t *data, int64_t len, int64_t deadline, vu_str *err, int line) {
    (void)c; (void)data; (void)len; (void)deadline; (void)err; (void)line; return false;
}
#else
/* -- TLS (OpenSSL), compiled in when a program calls net.tls_connect or net.tls_listen. A TLS Conn is a
   plain one with an SSL object on top: recv and send go through it, and wait for the socket the same
   way. OpenSSL's error queue is per thread and every task runs on this one, so each call clears it. */
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/x509v3.h>
#include <arpa/inet.h>
/* A socket BIO that sends with MSG_NOSIGNAL: a write to a closed connection is an error, never SIGPIPE. */
static int vu_bio_write(BIO *b, const char *d, int n) {
    BIO_clear_retry_flags(b);
    ssize_t r = send((int)(intptr_t)BIO_get_data(b), d, (size_t)n, MSG_NOSIGNAL);
    if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) BIO_set_retry_write(b);
    return (int)r;
}
static int vu_bio_read(BIO *b, char *d, int n) {
    BIO_clear_retry_flags(b);
    ssize_t r = recv((int)(intptr_t)BIO_get_data(b), d, (size_t)n, 0);
    if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) BIO_set_retry_read(b);
    return (int)r;
}
static long vu_bio_ctrl(BIO *b, int cmd, long num, void *ptr) {
    (void)b; (void)num; (void)ptr;
    return cmd == BIO_CTRL_FLUSH ? 1 : 0;
}
static int vu_bio_create(BIO *b) { BIO_set_init(b, 1); return 1; }
static BIO_METHOD *vu_bio_method;
static SSL_CTX *vu_tls_system;   /* clients that trust the system's certificates share one context */
static bool vu_tls_attach(vu_sock *s, SSL_CTX *ctx, vu_str *err) {
    if (!vu_bio_method) {
        vu_bio_method = BIO_meth_new(BIO_get_new_index() | BIO_TYPE_SOURCE_SINK, "vu socket");
        BIO_meth_set_write(vu_bio_method, vu_bio_write);
        BIO_meth_set_read(vu_bio_method, vu_bio_read);
        BIO_meth_set_ctrl(vu_bio_method, vu_bio_ctrl);
        BIO_meth_set_create(vu_bio_method, vu_bio_create);
    }
    SSL *ssl = SSL_new(ctx);
    BIO *b = ssl ? BIO_new(vu_bio_method) : NULL;
    if (!b) {
        if (ssl) SSL_free(ssl);
        ERR_clear_error();
        *err = vu_errf("can't start TLS: out of memory");
        return false;
    }
    BIO_set_data(b, (void *)(intptr_t)s->fd);
    SSL_set_bio(ssl, b, b);
    s->ssl = ssl;
    return true;
}
static void vu_tls_free(vu_sock *s) {
    if (s->ssl) {
        ERR_clear_error();
        if (s->hs) SSL_shutdown((SSL *)s->ssl);   /* one try at close_notify; the socket closes either way */
        SSL_free((SSL *)s->ssl);
    }
    if (s->tls_ctx) SSL_CTX_free((SSL_CTX *)s->tls_ctx);
    ERR_clear_error();
}
static SSL_CTX *vu_tls_ctx(bool server) {
    SSL_CTX *ctx = SSL_CTX_new(server ? TLS_server_method() : TLS_client_method());
    if (!ctx) vu_oom();
    SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION);
    /* A peer that closes without close_notify reads as a close, as with plain TCP. Idle connections
       give their buffers back (RELEASE_BUFFERS): 26 KB each instead of 37, at no measured cost. */
    SSL_CTX_set_options(ctx, SSL_OP_IGNORE_UNEXPECTED_EOF);
    SSL_CTX_set_mode(ctx, SSL_MODE_ENABLE_PARTIAL_WRITE | SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER | SSL_MODE_RELEASE_BUFFERS);
    if (!server) SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    return ctx;
}
static int vu_no_password(char *b, int n, int rw, void *u) { (void)b; (void)n; (void)rw; (void)u; return 0; }
static BIO *vu_pem_bio(const vu_str *pem) {
    return BIO_new_mem_buf(pem->data ? (const void *)pem->data : (const void *)"", (int)pem->len);
}
/* What OpenSSL says went wrong, as words ("certificate verify failed"), or fallback. */
static const char *vu_tls_reason(const char *fallback) {
    unsigned long e = ERR_peek_last_error();
    const char *r = e ? ERR_reason_error_string(e) : NULL;
    return r ? r : fallback;
}
/* After an SSL call returned r <= 0: 1 when it should be tried again (it waited for the socket),
   -1 when the deadline passed, 0 on an error (*kind is SSL_get_error's answer). */
static int vu_tls_again(vu_sock *s, int r, int64_t deadline, int line, int *kind) {
    int k = SSL_get_error((SSL *)s->ssl, r);
    *kind = k;
    if (k != SSL_ERROR_WANT_READ && k != SSL_ERROR_WANT_WRITE) return 0;
    if (deadline >= 0 && vu_now_ns() >= deadline) return -1;
    if (!vu_wait_fd(s, k == SSL_ERROR_WANT_WRITE, deadline, line)) return -1;
    return 1;
}
/* Runs the handshake if it hasn't happened yet (a server's connections do it on first use). */
static bool vu_tls_handshake(vu_sock *s, int64_t deadline, vu_str *err, int line) {
    while (!s->hs) {
        ERR_clear_error();
        int r = SSL_do_handshake((SSL *)s->ssl);
        if (r == 1) { s->hs = true; break; }
        int k, a = vu_tls_again(s, r, deadline, line, &k);
        if (a > 0) continue;
        if (a < 0) { *err = vu_errf("timed out"); return false; }
        long v = SSL_get_verify_result((SSL *)s->ssl);
        if (v != X509_V_OK && !SSL_is_server((SSL *)s->ssl))
            *err = vu_errf("can't verify the server's certificate: %s", X509_verify_cert_error_string(v));
        else if (k == SSL_ERROR_SYSCALL || k == SSL_ERROR_ZERO_RETURN)
            *err = vu_errf("the TLS handshake failed: the connection closed");
        else
            *err = vu_errf("the TLS handshake failed: %s", vu_tls_reason("unknown error"));
        ERR_clear_error();
        return false;
    }
    return true;
}
static bool vu_tls_accepted(vu_sock *l, vu_sock *s, vu_str *err) {
    if (!vu_tls_attach(s, (SSL_CTX *)l->tls_ctx, err)) return false;
    SSL_set_accept_state((SSL *)s->ssl);
    return true;
}
static bool vu_tls_recv(vu_sock *c, int64_t deadline, vu_str *out, vu_str *err, int line) {
    if (!vu_tls_handshake(c, deadline, err, line)) return false;
    vu_str s = {0};
    for (;;) {
        ERR_clear_error();
        int n = SSL_read((SSL *)c->ssl, vu_iobuf, (int)sizeof vu_iobuf);
        if (n > 0) {
            vu_str_cat_bytes(&s, vu_iobuf, (int64_t)n);
            /* Stop after a short record with nothing left decrypted: reading on would only find the
               socket empty (one wasted syscall per request). Full records usually have more behind them. */
            if (s.len >= (1 << 20) || (n < 16384 && SSL_pending((SSL *)c->ssl) == 0)) break;
            continue;
        }
        int k = SSL_get_error((SSL *)c->ssl, n);
        if (k == SSL_ERROR_ZERO_RETURN) break;   /* closed */
        if (k == SSL_ERROR_WANT_READ || k == SSL_ERROR_WANT_WRITE) {
            if (s.len) break;
            if ((deadline >= 0 && vu_now_ns() >= deadline) || !vu_wait_fd(c, k == SSL_ERROR_WANT_WRITE, deadline, line)) {
                *err = vu_errf("timed out");
                return false;
            }
            continue;
        }
        if (s.len) break;   /* report the error on the next call */
        if (k == SSL_ERROR_SYSCALL && (errno == 0 || errno == ECONNRESET)) break;   /* the other side is gone */
        *err = vu_errf("recv failed: %s", vu_tls_reason(k == SSL_ERROR_SYSCALL ? strerror(errno) : "TLS error"));
        ERR_clear_error();
        return false;
    }
    ERR_clear_error();
    *out = s;
    return true;
}
static bool vu_tls_send(vu_sock *c, const uint8_t *data, int64_t len, int64_t deadline, vu_str *err, int line) {
    if (!vu_tls_handshake(c, deadline, err, line)) return false;
    while (len > 0) {
        ERR_clear_error();
        int n = SSL_write((SSL *)c->ssl, data, len > (1 << 30) ? (1 << 30) : (int)len);
        if (n > 0) { data += n; len -= n; continue; }
        int k, a = vu_tls_again(c, n, deadline, line, &k);
        if (a > 0) continue;
        if (a < 0) { *err = vu_errf("timed out"); return false; }
        if (k == SSL_ERROR_ZERO_RETURN || (k == SSL_ERROR_SYSCALL && (errno == EPIPE || errno == ECONNRESET || errno == 0)))
            *err = vu_errf("the connection is closed");
        else
            *err = vu_errf("send failed: %s", vu_tls_reason("TLS error"));
        ERR_clear_error();
        return false;
    }
    return true;
}
/* net.tls_listen(port, cert: pem, key: pem): the certificate (then any intermediate certificates) and
   its private key, as PEM text. */
static bool vu_net_tls_listen(vu_cap net, int64_t port, const vu_str *cert, const vu_str *key, void **out, vu_str *err,
                              int line) {
    vu_task_here("net.tls_listen()", line);
    if (cert->len > (1 << 24) || key->len > (1 << 24)) { *err = vu_errf("the certificate or key is too long"); return false; }
    ERR_clear_error();
    SSL_CTX *ctx = vu_tls_ctx(true);
    BIO *b = vu_pem_bio(cert);
    X509 *x = b ? PEM_read_bio_X509(b, NULL, vu_no_password, NULL) : NULL;
    if (!x || SSL_CTX_use_certificate(ctx, x) != 1) {
        if (x) X509_free(x);
        if (b) BIO_free(b);
        SSL_CTX_free(ctx);
        ERR_clear_error();
        *err = vu_errf("cert: no certificate found in the PEM text");
        return false;
    }
    X509_free(x);
    while ((x = PEM_read_bio_X509(b, NULL, vu_no_password, NULL)))
        if (SSL_CTX_add_extra_chain_cert(ctx, x) != 1) X509_free(x);   /* on success the context owns it */
    BIO_free(b);
    ERR_clear_error();
    b = vu_pem_bio(key);
    EVP_PKEY *k = b ? PEM_read_bio_PrivateKey(b, NULL, vu_no_password, NULL) : NULL;
    if (b) BIO_free(b);
    if (!k) {
        SSL_CTX_free(ctx);
        ERR_clear_error();
        *err = vu_errf("key: no private key found in the PEM text (keys protected by a password aren't supported)");
        return false;
    }
    int used = SSL_CTX_use_PrivateKey(ctx, k);
    EVP_PKEY_free(k);
    if (used != 1 || SSL_CTX_check_private_key(ctx) != 1) {
        SSL_CTX_free(ctx);
        ERR_clear_error();
        *err = vu_errf("key: the private key doesn't match the certificate");
        return false;
    }
    if (!vu_net_listen(net, port, out, err, line)) { SSL_CTX_free(ctx); return false; }
    ((vu_sock *)*out)->tls_ctx = ctx;
    return true;
}
/* net.tls_connect(host, port, ca: pem, timeout: s): checks the server's certificate against the system's
   certificates (or only the ones in ca) and that it is for host. */
static bool vu_net_tls_connect(vu_cap net, const vu_str *host, int64_t port, const vu_str *ca, double timeout, bool has,
                               void **out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.tls_connect()", line);
    if (port < 1 || port > 65535) { *err = vu_errf("port %lld is not in 1..65535", (long long)port); return false; }
    char *h = vu_cpath(host, err);
    if (!h) { drop_Str(err); *err = vu_errf("a host name can't contain a zero byte"); return false; }
    int64_t deadline = vu_deadline(timeout, has, line);
    ERR_clear_error();
    SSL_CTX *ctx;
    if (ca) {
        if (ca->len > (1 << 24)) { free(h); *err = vu_errf("ca: the PEM text is too long"); return false; }
        ctx = vu_tls_ctx(false);
        X509_STORE *st = SSL_CTX_get_cert_store(ctx);
        BIO *b = vu_pem_bio(ca);
        int n = 0;
        X509 *x;
        while (b && (x = PEM_read_bio_X509(b, NULL, vu_no_password, NULL))) { X509_STORE_add_cert(st, x); X509_free(x); n++; }
        if (b) BIO_free(b);
        ERR_clear_error();
        if (!n) { SSL_CTX_free(ctx); free(h); *err = vu_errf("ca: no certificate found in the PEM text"); return false; }
    } else {
        if (!vu_tls_system) {
            vu_tls_system = vu_tls_ctx(false);
            SSL_CTX_set_default_verify_paths(vu_tls_system);
            ERR_clear_error();
        }
        ctx = vu_tls_system;
        SSL_CTX_up_ref(ctx);
    }
    void *sp = NULL;
    if (!vu_connect_to(h, port, deadline, &sp, err, line)) { SSL_CTX_free(ctx); free(h); return false; }
    vu_sock *s = (vu_sock *)sp;
    bool ok = vu_tls_attach(s, ctx, err);
    SSL_CTX_free(ctx);   /* the SSL object keeps its own reference */
    if (ok) {
        SSL *ssl = (SSL *)s->ssl;
        unsigned char ip[16];
        bool is_ip = inet_pton(AF_INET, h, ip) == 1 || inet_pton(AF_INET6, h, ip) == 1;
        if (is_ip) X509_VERIFY_PARAM_set1_ip_asc(SSL_get0_param(ssl), h);
        else { SSL_set_tlsext_host_name(ssl, h); SSL_set1_host(ssl, h); }
        SSL_set_connect_state(ssl);
        ok = vu_tls_handshake(s, deadline, err, line);
        if (!ok) {
            vu_str e = *err;
            *err = vu_errf("%.200s:%lld: %.*s", h, (long long)port, (int)e.len, (const char *)e.data);
            drop_Str(&e);
        }
    }
    free(h);
    if (!ok) { vu_sock_drop(s); return false; }
    *out = s;
    return true;
}
#endif
static void drop_X_Conn(void **p) { if (*p) { vu_sock_drop(*p); *p = NULL; } }
static void drop_X_Listener(void **p) { if (*p) { vu_sock_drop(*p); *p = NULL; } }'''

def box_code(x, T=None):
    """The node pool for boxes of C type T (T_x by default): optional values and big enum payloads."""
    T = T or f'T_{x}'
    return f'''#define VU_NODE_{x} (sizeof({T}) < 2 * sizeof(void *) ? 2 * sizeof(void *) : sizeof({T}))
static __thread {T} *vu_free_{x};
/* Free nodes shared between threads (see vu_share_free): chunks, each a whole free list whose first
   node links the next chunk in its second word. */
static void *vu_chunks_{x};
static pthread_mutex_t vu_chunks_lock_{x} = PTHREAD_MUTEX_INITIALIZER;
/* Takes up to VU_TAKE nodes from the first chunk (the rest of it stays shared), so that threads
   share a big list instead of one of them taking all of it. */
__attribute__((noinline)) static void vu_take_chunk_{x}(void) {{
    pthread_mutex_lock(&vu_chunks_lock_{x});
    char *c = (char *)vu_chunks_{x};
    if (c) {{
        void *next_chunk, *rest;
        VU_UNPOISON(c, 2 * sizeof(void *));
        memcpy(&next_chunk, c + sizeof(void *), sizeof(void *));
        VU_POISON(c, 2 * sizeof(void *));
        char *p = c;
        for (int i = 1;; i++) {{
            VU_UNPOISON(p, sizeof(void *));
            memcpy(&rest, p, sizeof(void *));
            if (!rest || i == VU_TAKE) {{
                memset(p, 0, sizeof(void *));   /* p ends the list this thread takes */
                VU_POISON(p, sizeof(void *));
                break;
            }}
            VU_POISON(p, sizeof(void *));
            p = (char *)rest;
        }}
        if (rest) {{
            VU_UNPOISON((char *)rest + sizeof(void *), sizeof(void *));
            memcpy((char *)rest + sizeof(void *), &next_chunk, sizeof(void *));
            VU_POISON((char *)rest + sizeof(void *), sizeof(void *));
            next_chunk = rest;
        }}
        __atomic_store_n(&vu_chunks_{x}, next_chunk, __ATOMIC_RELAXED);
        vu_free_{x} = ({T} *)c;
    }}
    pthread_mutex_unlock(&vu_chunks_lock_{x});
}}
static void vu_give_chunk_{x}(void) {{
    char *c = (char *)vu_free_{x};
    if (!c) return;
    pthread_mutex_lock(&vu_chunks_lock_{x});
    VU_UNPOISON(c + sizeof(void *), sizeof(void *));
    memcpy(c + sizeof(void *), &vu_chunks_{x}, sizeof(void *));
    VU_POISON(c + sizeof(void *), sizeof(void *));
    __atomic_store_n(&vu_chunks_{x}, (void *)c, __ATOMIC_RELAXED);
    pthread_mutex_unlock(&vu_chunks_lock_{x});
    vu_free_{x} = NULL;
}}
static vu_pool vu_pool_{x} = {{ vu_give_chunk_{x}, NULL }};
__attribute__((constructor)) static void vu_pool_init_{x}(void) {{ vu_pool_{x}.next = vu_pools; vu_pools = &vu_pool_{x}; }}
static inline {T} *vu_box_{x}({T} v) {{
#ifdef VU_MALLOC
    {T} *p = ({T} *)vu_malloc(sizeof({T}));
#else
#ifdef _OPENMP
    if (!vu_free_{x} && __atomic_load_n(&vu_chunks_{x}, __ATOMIC_RELAXED)) vu_take_chunk_{x}();
#endif
    {T} *p = vu_free_{x};
    if (p) {{ VU_UNPOISON(p, VU_NODE_{x}); memcpy(&vu_free_{x}, p, sizeof(void *)); }}
    else p = ({T} *)vu_bump(VU_NODE_{x});
#endif
    *p = v;
    return p;
}}
static inline void vu_release_{x}({T} *p) {{
#ifdef VU_MALLOC
    free(p);
#else
    memcpy(p, &vu_free_{x}, sizeof(void *));
    vu_free_{x} = p;
    VU_POISON(p, VU_NODE_{x});   /* any later access to this freed node is reported */
#endif
}}'''


def list_code(m, L, E):
    return f'''static inline {E} *vu_at_{m}({L} *l, int64_t i, int line) {{
    if (__builtin_expect(i < 0 || i >= l->len, 0)) vu_oob(i, l->len, line);
    return &l->data[i];
}}
static void vu_grow_{m}({L} *l) {{
    if (l->cap > (int64_t)(PTRDIFF_MAX / sizeof({E}) / 2)) vu_oom();
    int64_t c = l->cap ? l->cap * 2 : 4;
    {E} *d = ({E} *)realloc(l->data, (size_t)c * sizeof({E}));
    if (!d) vu_oom();
    l->data = d;
    l->cap = c;
}}
static void vu_reserve_{m}({L} *l, int64_t n, int line) {{
    if (n < 0) vu_fail(line, "reserve(%lld): the count can't be negative", (long long)n);
    if (n <= l->cap - l->len) return;
    if (n > (int64_t)(PTRDIFF_MAX / sizeof({E})) - l->len) vu_oom();
    int64_t c = l->len + n;
    {E} *d = ({E} *)realloc(l->data, (size_t)c * sizeof({E}));
    if (!d) vu_oom();
    l->data = d;
    l->cap = c;
}}
static inline {E} vu_pop_{m}({L} *l, int line) {{
    if (__builtin_expect(l->len == 0, 0)) vu_fail(line, "pop() from an empty list");
    return l->data[--l->len];
}}
static inline void vu_push_{m}({L} *l, {E} v) {{
    if (l->len == l->cap) vu_grow_{m}(l);
    l->data[l->len++] = v;
}}
static {L} vu_rep_{m}({L} src, int64_t n, int line) {{
    {L} r = {{0}};
    if (n > 0 && src.len > 0) {{
        if (n > INT64_MAX / src.len || src.len * n > (int64_t)(PTRDIFF_MAX / sizeof({E})))
            vu_fail(line, "list of %lld x %lld elements is too large", (long long)src.len, (long long)n);
        int64_t total = src.len * n;
        r.data = ({E} *)vu_malloc((size_t)total * sizeof({E}));
        r.len = r.cap = total;
        if (src.len == 1) {{ {E} v = src.data[0]; for (int64_t k = 0; k < total; k++) r.data[k] = v; }}
        else for (int64_t k = 0; k < n; k++) memcpy(r.data + k * src.len, src.data, (size_t)src.len * sizeof({E}));
    }}
    free(src.data);
    return r;
}}'''


class Gen:
    def __init__(self, items, paths=('main.vu',)):
        self.items = items
        self.paths = list(paths)   # each file by index, named in #line directives and panic reports
        self.cpaths = [cstr(p) for p in self.paths]
        self.keep = []   # nodes the compiler makes itself (min(a, b, c)), kept alive for the id caches
        self.prefix = ''
        self.hoisted = {}   # id(? node) -> the hidden variable holding its value (see hoist_tries)
        self.ntry = 0
        self.src_line = 0   # the Vu line being generated (0: none, e.g. runtime and type code)
        self.structs, self.fns, self.consts, self.top = {}, {}, {}, {}
        self.enums, self.variants = {}, {}   # enum name -> EnumInfo; variant name -> enum name
        self.types, self.struct_order = [], []
        self.tmpn = 0
        self.par, self.uses_par = None, False
        self.uses_float_parse = False
        self.uses_tasks = False
        self.spawned = []   # functions run by spawn, each once
        self.jtypes = []    # types that to_json / from_json need code for
        self.uses_tls = False
        self.fn_err = {}    # function -> the enum it fails with (throws E); others fail with messages
        self.err_enums = []
        self.externs = [it for it in items if it.k == 'extern']
        self.links = []
        for it in self.externs:
            self.links += [l for l in it.links if l not in self.links]
        self.exttypes = {it.name: it for it in items if it.k == 'exttype'}
        # generics: templates by name; each instance (Pair__G3_Int3_Str) is an ordinary struct, enum or
        # function made from its template with the type parameters bound (see instantiate_type/_fn)
        self.gfns, self.gtypes = {}, {}
        self.inst_of = {}      # instance name -> (template name, [type arguments])
        self.tenv = {}         # type parameter -> type, while resolving or generating an instance
        self.inst_env, self.inst_line = {}, {}   # instance function -> its bindings, the line that first used it
        self.fn_queue = []     # functions to generate, in order (instances are added as they're used)
        self.collecting, self.inst_depth, self.new_insts = True, 0, []
        self.gcache = {}       # id(call) -> the instance a generic call means
        # closures: each is a C function vu_lam<n> (n by first use) with its captured variables in vu_env<n>
        self.lam_ids, self.lam_fns, self.lam_envs, self.lam_drops = {}, {}, {}, {}
        self.lam_caps = {}   # id(closure) -> the variables a borrowing closure points to
        self.lam = None      # the closure being generated (LamCtx), if any
        self.thunks = []     # named functions used as values: each gets vu_th_<name>
        self.tcache = {}   # id(expression) -> its type when generated without an expected type
        self.ecache = {}   # id(expression) -> whether evaluating it could change state
        self.collect()

    # ---- declarations
    def collect(self):
        def define(name, line):
            if name in self.top:
                err(line, f"'{disp(name)}' is already defined on line {ln(self.top[name])}")
            # (a module's geo__print is still print to the code in that module)
            cut = name.find('__')
            bare = name[cut + 2:] if cut > 0 else name
            if bare in BUILTINS or bare in BUILTIN_TYPES:
                err(line, f"'{bare}' is a built-in name")
            self.top[name] = line
        for it in self.items:
            if it.k == 'extern':
                continue
            define(it.name, it.line)
            if it.k == 'enum':
                for vname, _, vline in it.variants:
                    define(vname, vline)
                    self.variants[vname] = it.name
        for it in self.exttypes.values():
            bad = c_name_problem(it.drop)
            if bad:
                err(it.line, f"{bad}, so it can't be the C function that frees a {disp(it.name)}")
        for it in self.items:
            if it.k in ('type', 'enum') and getattr(it, 'tparams', None):
                self.gtypes[it.name] = it
            elif it.k == 'type':
                self.structs[it.name] = StructInfo(it)
            elif it.k == 'enum':
                self.enums[it.name] = EnumInfo(it)
        for it in self.items:
            if it.k in ('type', 'enum', 'fn') and getattr(it, 'tparams', None):
                for tp in it.tparams:
                    if tp in self.structs or tp in self.enums or tp in self.gtypes or tp in BUILTIN_TYPES:
                        err(it.line, f"type parameter '{tp}' has the name of a type; pick another (T, U, K, V...)")
        for it in self.items:
            if getattr(it, 'tparams', None):
                continue
            if it.k == 'type':
                info, seen = self.structs[it.name], set()
                for fname, fty, _, fline in it.fields:
                    if fname in seen:
                        err(fline, f"duplicate field '{fname}'")
                    seen.add(fname)
                    info.fields.append((fname, self.resolve(fty, fline)))
            elif it.k == 'enum':
                info = self.enums[it.name]
                for vname, vfields, vline in it.variants:
                    seen, fs = set(), []
                    for fname, fty, _, fline in vfields:
                        if fname in seen:
                            err(fline, f"duplicate field '{fname}'")
                        seen.add(fname)
                        fs.append((fname, self.resolve(fty, fline)))
                    info.variants.append((vname, fs))
        state = {}
        infos = {**self.structs, **self.enums}

        def visit(name, line):
            if state.get(name) == 1:
                err(line, f"type '{disp(name)}' contains itself directly; use an optional field ({disp(name)}?) or a list")
            if state.get(name) == 2:
                return
            state[name] = 1
            for _, ft in infos[name].fields:
                if ft[0] in ('struct', 'enum'):
                    visit(ft[1], infos[name].line)
            state[name] = 2
            self.struct_order.append(name)

        for n in infos:
            visit(n, infos[n].line)
        changed = True
        while changed:
            changed = False
            for info in infos.values():
                if info.copy and not all(self.is_copy(ft) for _, ft in info.fields):
                    info.copy, changed = False, True
        self.plan_boxes()
        self.collecting, self.new_insts = False, []   # instances made from now on are finished as they're made
        for it in self.items:
            if it.k == 'fn' and getattr(it, 'tparams', None):
                if it.name == 'main':
                    err(it.line, "main can't have type parameters")
                self.gfns[it.name] = it
            elif it.k == 'fn':
                params, ret = self.fn_sig(it, it.name)
                if it.name == 'main':
                    if ret != VOID:
                        err(it.line, 'main returns nothing')
                    for pn, pt, pv, pl, po in params:
                        if pt[0] != 'cap' or pv or po:
                            err(pl, "main's parameters can only be capabilities, like 'fs: Fs' "
                                    "(read command-line numbers with arg(i, default))")
                self.fns[it.name] = (params, ret, it)
        if 'main' not in self.fns:
            err(1, "no 'fn main():' found")
        self.fn_queue = list(self.fns)

    def fn_sig(self, it, name):
        """A function's parameters and return type, resolved (with self.tenv for an instance)."""
        params, seen = [], set()
        for pn, pt, pv, pl, po in it.params:
            if pn in seen:
                err(pl, f"duplicate parameter '{pn}'")
            seen.add(pn)
            params.append((pn, self.resolve(pt, pl), pv, pl, po))
        ret = self.resolve(it.ret, it.line)
        if self.has_cap(ret) and not any(self.has_cap(pt) for _, pt, _, _, _ in params):
            err(it.line, f"'{it.name}' returns a capability but isn't given one; a function can only "
                         f"return a capability (Fs, Os) it received as a parameter")
        if it.body is None:
            self.check_extern(it, params, ret)
        if it.err_ty is not None:
            et = self.resolve(it.err_ty, it.line)
            if et[0] != 'enum':
                err(it.line, f"throws names the enum its errors come from (throws ParseError), not {tn(et)}")
            self.fn_err[name] = et
            if et[1] not in self.err_enums:
                self.err_enums.append(et[1])
        if it.throws:
            self.reg(self.res_of(name, ret))
        return params, ret

    # ---- generics
    def template_of(self, n):
        return self.inst_of[n][0] if n in self.inst_of else n

    def type_arg_check(self, a, line):
        if a[0] in ('cap', 'void', 'res', 'nil', 'lfn'):
            err(line, f"{tn(a)} can't be a type argument")
        if self.type_depth(a) > 32:
            err(line, "a type argument is nested more than 32 deep: does a generic function or type use itself "
                      "with ever bigger type arguments?")

    def type_depth(self, t):
        """How deeply a type nests (Int: 1, [Int]: 2, Pair[[Int], Str]: 4)."""
        k = t[0]
        if k in ('list', 'opt', 'chan'):
            return 1 + self.type_depth(t[1])
        if k == 'map':
            return 1 + max(self.type_depth(t[1]), self.type_depth(t[2]))
        if k in ('struct', 'enum') and t[1] in self.inst_of:
            return 1 + max(self.type_depth(a) for a in self.inst_of[t[1]][1])
        return 1

    def inst_name(self, n, args):
        return n + '__G' + ''.join(f'{len(m)}_{m}' for m in (self.mg(a) for a in args))

    def instantiate_type(self, n, args, line):
        """The struct or enum made from generic type n with these type arguments (made once)."""
        it = self.gtypes[n]
        if len(args) != len(it.tparams):
            err(line, f"{disp(n)} takes {len(it.tparams)} type argument(s) ({', '.join(it.tparams)}), not {len(args)}")
        for a in args:
            self.type_arg_check(a, line)
        inst = self.inst_name(n, args)
        kind = 'struct' if it.k == 'type' else 'enum'
        if inst in self.inst_of:
            return (kind, inst)
        if len(self.inst_of) >= 2000:
            err(line, "too many generic instances (2000): does a generic type or function use itself with "
                      "ever bigger type arguments?")
        self.inst_of[inst] = (n, list(args))
        info = StructInfo(it) if it.k == 'type' else EnumInfo(it)
        info.name = inst
        (self.structs if it.k == 'type' else self.enums)[inst] = info
        self.new_insts.append(inst)
        saved, self.tenv = self.tenv, dict(zip(it.tparams, args))
        self.inst_depth += 1
        if it.k == 'type':
            seen = set()
            for fname, fty, _, fline in it.fields:
                if fname in seen:
                    err(fline, f"duplicate field '{fname}'")
                seen.add(fname)
                info.fields.append((fname, self.resolve(fty, fline)))
        else:
            for vname, vfields, vline in it.variants:
                seen, fs = set(), []
                for fname, fty, _, fline in vfields:
                    if fname in seen:
                        err(fline, f"duplicate field '{fname}'")
                    seen.add(fname)
                    fs.append((fname, self.resolve(fty, fline)))
                info.variants.append((vname, fs))
        self.inst_depth -= 1
        self.tenv = saved
        if self.inst_depth == 0 and not self.collecting:
            self.finish_insts()
        return (kind, inst)

    def finish_insts(self):
        """Orders new instances after the types they contain, works out which are plain data, and
        plans their enum payloads (collect does all of this for the instances it makes)."""
        new, self.new_insts = self.new_insts, []
        names, state, order = set(new), {}, []

        def visit(n, line):
            if state.get(n) == 1:
                err(line, f"type '{disp(n)}' contains itself directly; use an optional field ({disp(n)}?) or a list")
            if state.get(n) == 2:
                return
            state[n] = 1
            info = self.structs.get(n) or self.enums[n]
            for _, ft in info.fields:
                if ft[0] in ('struct', 'enum') and ft[1] in names:
                    visit(ft[1], info.line)
            state[n] = 2
            order.append(n)
        for n in new:
            visit(n, (self.structs.get(n) or self.enums[n]).line)
        self.struct_order += order
        infos = [self.structs.get(n) or self.enums[n] for n in order]
        changed = True
        while changed:
            changed = False
            for info in infos:
                if info.copy and not all(self.is_copy(ft) for _, ft in info.fields):
                    info.copy, changed = False, True
        for n in order:
            if n in self.enums:
                self.plan_box(n)

    def instantiate_fn(self, n, args, line):
        """The function made from generic function n with these type arguments (made once, generated later)."""
        it = self.gfns[n]
        for a in args:
            self.type_arg_check(a, line)
        inst = self.inst_name(n, args)
        if inst in self.fns:
            return inst
        if len(self.inst_env) >= 2000:
            err(line, "too many generic instances (2000): does a generic type or function use itself with "
                      "ever bigger type arguments?")
        node = copy.deepcopy(it)
        self.keep.append(node)
        env = dict(zip(it.tparams, args))
        saved, self.tenv = self.tenv, env
        params, ret = self.fn_sig(node, inst)
        self.tenv = saved
        self.fns[inst] = (params, ret, node)
        self.inst_env[inst], self.inst_line[inst] = env, line
        self.fn_queue.append(inst)
        return inst

    def unify(self, syn, actual, tps, b):
        """Binds the type parameters (tps) in syntax syn to the parts of type actual that they stand for."""
        if actual is None or actual == NIL:
            return
        k = syn[0]
        if k == 'named' and syn[1] in tps:
            if syn[1] not in b:
                if actual[0] == 'lfn':
                    actual = ('fn',) + actual[1:]
                b[syn[1]] = actual   # (a capability or nothing is refused when the instance is made)
            return
        if k == 'fnty' and actual[0] in ('fn', 'lfn') and len(syn[1]) == len(actual[1]):
            for s, a in zip(syn[1], actual[1]):
                self.unify(s, a, tps, b)
            self.unify(syn[2], actual[2], tps, b)
            return
        if k == 'opt':
            self.unify(syn[1], actual[1] if actual[0] == 'opt' else actual, tps, b)
        elif k in ('list', 'chan') and actual[0] == k:
            self.unify(syn[1], actual[1], tps, b)
        elif k == 'map' and actual[0] == 'map':
            self.unify(syn[1], actual[1], tps, b)
            self.unify(syn[2], actual[2], tps, b)
        elif k == 'gapp' and actual[0] in ('struct', 'enum') and actual[1] in self.inst_of:
            tmpl, targs = self.inst_of[actual[1]]
            if tmpl == syn[1] and len(targs) == len(syn[2]):
                for s, a in zip(syn[2], targs):
                    self.unify(s, a, tps, b)

    def tparams_in(self, syn, tps):
        """The type parameters (of tps) that type syntax syn mentions."""
        if syn is None or not isinstance(syn, tuple):
            return []
        if syn[0] == 'named':
            return [syn[1]] if syn[1] in tps else []
        if syn[0] == 'gapp':
            return [x for a in syn[2] for x in self.tparams_in(a, tps)]
        if syn[0] == 'fnty':
            return [x for a in list(syn[1]) + [syn[2]] for x in self.tparams_in(a, tps)]
        return [x for a in syn[1:] for x in self.tparams_in(a, tps)]

    def arg_type(self, a):
        """An argument's type for inference, or None when it alone doesn't say (nil, [] or {})."""
        if a.k == 'ref':
            return self.probe_type(a.e)
        if a.k == 'nil' or (a.k == 'list' and not a.items) or (a.k == 'map' and not a.pairs):
            return None
        return self.probe_type(a)

    def expect_of(self, expect, n):
        """The instance of generic type n that the expected type is (or is optionally), or None."""
        if expect is not None and expect[0] == 'opt':
            expect = expect[1]
        if expect is not None and expect[0] in ('struct', 'enum') and self.template_of(expect[1]) == n \
                and expect[1] in self.inst_of:
            return expect[1]
        return None

    def gcall(self, e, expect):
        """A call to generic function e.fn.name: works out the type arguments from the arguments (and the
        expected result) and makes that instance, once per call."""
        if id(e) in self.gcache:
            return self.gcache[id(e)]
        name = e.fn.name
        it = self.gfns[name]
        args = e.args
        if any(a[0] for a in args):
            err(e.line, 'named arguments are only used when creating a struct')
        if len(args) != len(it.params):
            plist = ', '.join(pn for pn, _, _, _, _ in it.params)
            err(e.line, f'{disp(name)}() takes {len(it.params)} argument(s) ({plist}) but got {len(args)}')
        b = {}
        for (_, pt, _, _, _), (_, a) in zip(it.params, args):
            if a.k != 'lambda':
                self.unify(pt, self.arg_type(a), it.tparams, b)
        if expect is not None:
            self.unify(it.ret, expect, it.tparams, b)
        for (_, pt, _, _, _), (_, a) in zip(it.params, args):
            # a closure argument: its parameter types come from what's known so far (or are written
            # out), and its result then tells the rest: map(xs, fn(x) => x * 2) makes U an Int
            if a.k == 'lambda' and pt[0] == 'fnty' and len(pt[1]) == len(a.params):
                ptys = []
                for s, (pn, ann, pl) in zip(pt[1], a.params):
                    if ann is not None:
                        t = self.resolve(ann, pl)
                        self.unify(s, t, it.tparams, b)
                    elif all(x in b for x in self.tparams_in(s, it.tparams)):
                        saved, self.tenv = self.tenv, {**self.tenv, **b}
                        t = self.resolve(s, pl)
                        self.tenv = saved
                    else:
                        t = None
                    ptys.append(t)
                if None not in ptys:
                    snap = self.snapshot()
                    _, lt = self.g_lambda(a, ('fnhint', tuple(ptys), pt[3]))
                    self.restore(snap)
                    self.unify(pt[2], lt[2], it.tparams, b)
        for tp in it.tparams:
            if tp not in b:
                err(e.line, f"can't tell what {tp} is in this call to {disp(name)}(); the arguments don't say, so "
                            f"give the result a type (let x: [Int] = {disp(name)}(...)) or pass a typed value")
        inst = self.instantiate_fn(name, [b[tp] for tp in it.tparams], e.line)
        self.gcache[id(e)] = inst   # this call means that instance from now on
        return inst

    def ginfer(self, e, n, fields, what, expect):
        """The instance of generic type n that a struct or variant literal makes, from its field values
        (fields: the template's (name, type syntax)) and the expected type."""
        known = self.expect_of(expect, n)
        if known is not None:
            return known
        it = self.gtypes[n]
        b = {}
        args = e.args
        named = any(a[0] for a in args)
        for i, (nm, a) in enumerate(args):
            syn = None
            if named:
                syn = next((ft for fn_, ft in fields if fn_ == nm), None)
            elif i < len(fields):
                syn = fields[i][1]
            if syn is not None:
                self.unify(syn, self.arg_type(a), it.tparams, b)
        for tp in it.tparams:
            if tp not in b:
                err(e.line, f"can't tell what {tp} is in this {what}; the values don't say, so give it a type, "
                            f"like: let x: {disp(n)}[{', '.join(it.tparams)}] = ... (with real types)")
        return self.instantiate_type(n, [b[tp] for tp in it.tparams], e.line)[1]

    def check_extern(self, it, params, ret):
        """An extern function crosses into C, so its signature uses only types with a plain C form."""
        d = disp(it.name)
        bad = c_name_problem(it.cname)
        if bad:
            err(it.line, f"{bad}, so it can't name a C function; pick another name (in Vu and in the C file)")
        if not params or params[0][1] != FFI or params[0][2] or params[0][4]:
            err(it.line, f"an extern function's first parameter is the C capability, 'ffi: Ffi', so only code "
                         f"that was handed it can call C: fn {d}(ffi: Ffi, ...)")
        for pn, pt, pv, pl, po in params[1:]:
            if pv:
                err(pl, f"an extern function can't take a 'var' parameter ('{pn}'); return the new value instead")
            if po and pt[0] != 'ext':
                err(pl, f"only an extern handle type can be passed 'own' to C, not {tn(pt)}")
            if pt not in (INT, FLOAT, BOOL, BYTE, STR) and pt[0] != 'ext':
                err(pl, f"an extern function's parameters can be Int, Float, Bool, Byte, Str or an extern type, "
                        f"not {tn(pt)} ('{pn}')")
        if ret not in (INT, FLOAT, BOOL, BYTE, STR, VOID) and ret[0] != 'ext':
            err(it.line, f"an extern function can return Int, Float, Bool, Byte, Str, an extern type or nothing, "
                         f"not {tn(ret)}")

    def csize(self, t):
        """(size, alignment) of a type in the generated C, used to decide which enum payloads to box."""
        if t in (INT, FLOAT):
            return 8, 8
        if t in (BOOL, BYTE) or t[0] == 'cap':
            return 1, 1
        if t == STR or t[0] == 'list':
            return 24, 8
        if t[0] == 'opt':
            return 8, 8
        if t[0] == 'map':
            return 48, 8
        if t[0] == 'struct':
            return self.layout([ft for _, ft in self.structs[t[1]].fields])
        if t[0] == 'enum':
            return self.enum_size[t[1]], 8 if self.enum_size[t[1]] > 4 else 4
        return 8, 8

    def layout(self, types):
        off, al = 0, 1
        for ft in types:
            s, a = self.csize(ft)
            off = (off + a - 1) // a * a + s
            al = max(al, a)
        return (off + al - 1) // al * al, al

    def plan_boxes(self):
        """A moving enum is as big as its largest variant, so one big variant (a map, a struct of many
        fields) makes every value of the enum big. Variants whose payload is over 24 bytes, when some
        other variant is smaller, are stored behind a pointer instead (one allocation, 8 bytes inline)."""
        self.boxed, self.enum_size = set(), {}
        for n in self.struct_order:
            if n in self.enums:
                self.plan_box(n)

    def plan_box(self, n):
        info = self.enums[n]
        sizes = [self.layout([ft for _, ft in fs])[0] if fs else 0 for _, fs in info.variants]
        if not info.copy:
            for k, s in enumerate(sizes):
                if s > 24 and min(sizes) < s:
                    self.boxed.add((n, k))
                    sizes[k] = 8
        biggest = max(sizes) if sizes else 0
        self.enum_size[n] = 4 if biggest == 0 else (8 + biggest + 7) // 8 * 8

    def payload(self, en, k, ptr):
        """C expression for variant k's fields, given a pointer to the enum value."""
        return f'{ptr}->u.b{k}->' if (en, k) in self.boxed else f'{ptr}->u.v{k}.'

    def has_cap(self, t, seen=None):
        """Whether a value of type t can hold a capability (directly or inside fields and lists)."""
        if t[0] == 'cap':
            return True
        if t[0] in ('list', 'opt', 'res', 'chan'):
            return self.has_cap(t[1], seen)
        if t[0] == 'map':
            return self.has_cap(t[2], seen)
        if t[0] in ('struct', 'enum'):
            seen = seen or set()
            if t[1] in seen:
                return False
            seen.add(t[1])
            info = self.structs[t[1]] if t[0] == 'struct' else self.enums[t[1]]
            return any(self.has_cap(ft, seen) for _, ft in info.fields)
        return False

    def resolve(self, t, line):
        k = t[0]
        if k == 'named' and t[1] in self.tenv:
            return self.tenv[t[1]]
        if k == 'named' and t[1] in self.gtypes:
            err(t[2], f"{disp(t[1])} takes type arguments: {disp(t[1])}[{', '.join(self.gtypes[t[1]].tparams)}]")
        if k == 'gapp':
            if t[1] not in self.gtypes:
                if t[1] in self.structs or t[1] in self.enums or t[1] in self.exttypes:
                    err(t[3], f"{disp(t[1])} has no type parameters, so it takes no [...]")
                err(t[3], f"unknown type '{t[1]}'")
            return self.instantiate_type(t[1], [self.resolve(a, line) for a in t[2]], t[3])
        if k == 'named':
            if t[1] in self.enums:
                return ('enum', t[1])
            if t[1] in self.exttypes:
                return ('ext', t[1])
            if t[1] in ('Conn', 'Listener'):
                self.uses_tasks = True
                return ('ext', t[1])
            if t[1] not in self.structs:
                err(t[2], f"unknown type '{t[1]}'")
            return ('struct', t[1])
        if k == 'list':
            return self.reg(('list', self.resolve(t[1], line)))
        if k == 'chan':
            self.uses_tasks = True
            return self.reg(('chan', self.resolve(t[1], line)))
        if k == 'map':
            key, val = self.resolve(t[1], line), self.resolve(t[2], line)
            if key not in MAP_KEYS:
                err(line, f"map keys can be Int, Byte, Bool or Str, not {tn(key)}")
            return self.reg(('map', key, val))
        if k == 'fnty':
            return self.fn_type(tuple(self.resolve(a, t[4]) for a in t[1]), self.resolve(t[2], t[4]), t[3])
        if k == 'opt':
            inner = self.resolve(t[1], line)
            if inner[0] in ('opt', 'cap', 'void'):
                err(line, f"{tn(inner)} can't be optional" + (" (one ? is enough)" if inner[0] == 'opt' else ""))
            return self.reg(('opt', inner))
        return t

    def fn_type(self, params, ret, throws):
        """('fn', parameter types, return type, throws), registered with its result type."""
        if throws:
            self.reg(('res', ret))
        return self.reg(('fn', tuple(params), ret, throws))

    @staticmethod
    def by_value(t):
        """Whether a borrowed parameter of type t is passed by value in C (else by pointer)."""
        return t in SCALARS or t[0] in ('opt', 'cap', 'fn', 'lfn')

    def pdecl(self, t, name):
        return f'{self.ct(t)} {name}' if self.by_value(t) else f'{self.ct(t)} *{name}'

    def reg(self, t):
        if t not in self.types:
            for inner in t[1:]:
                if isinstance(inner, tuple) and inner and inner[0] in ('list', 'opt', 'map', 'chan'):
                    self.reg(inner)
            self.types.append(t)
        return t

    # ---- type helpers
    def is_copy(self, t):
        if t in SCALARS or t == NIL or t[0] in ('cap', 'lfn'):
            return True
        if t[0] == 'enum':
            return self.enums[t[1]].copy
        return t[0] == 'struct' and self.structs[t[1]].copy

    def ct(self, t):
        k = t[0]
        if k == 'int':
            return 'int64_t'
        if k == 'float':
            return 'double'
        if k == 'bool':
            return 'bool'
        if k == 'void':
            return 'void'
        if k == 'byte':
            return 'uint8_t'
        if k == 'str':
            return 'vu_str'
        if k == 'cap':
            return 'vu_cap'
        if k == 'ext':
            return 'void *'
        if k in ('struct', 'enum'):
            return 'T_' + t[1]
        if k == 'list':
            return 'L_' + self.mg(t[1])
        if k == 'chan':
            return 'vu_chan *'
        if k in ('fn', 'lfn'):
            return 'vu_fn'
        if k in ('map', 'res'):
            return self.mg(t)
        return self.ct(t[1]) + '*'

    def mg(self, t):
        k = t[0]
        if k in ('int', 'float', 'bool', 'byte', 'str'):
            return k.capitalize()
        if k == 'cap':
            return 'Cap'
        if k == 'ext':
            return 'X_' + t[1]
        if k == 'void':
            return 'Void'
        if k == 'struct':
            return 'S_' + t[1]
        if k == 'enum':
            return 'E_' + t[1]
        if k == 'list':
            return 'L_' + self.mg(t[1])
        if k == 'map':
            a, b = self.mg(t[1]), self.mg(t[2])
            return f'M{len(a)}_{a}{b}'   # the length keeps every key/value pair's name distinct
        if k == 'res':
            if len(t) == 3:
                a, b = self.mg(t[1]), self.mg(t[2])
                return f'RE{len(a)}_{a}{b}'
            return 'R_' + self.mg(t[1])
        if k == 'chan':
            return 'C_' + self.mg(t[1])
        if k in ('fn', 'lfn'):
            ps = [self.mg(p) for p in t[1]]
            return f'F{"E" if t[3] else "P"}{len(ps)}_' + ''.join(f'{len(m)}_{m}' for m in ps) + self.mg(t[2])
        return 'O_' + self.mg(t[1])

    def drop(self, t, lv):
        return f'drop_{self.mg(t)}(&{lv});'

    def res_of(self, name, ret):
        """The result type of a call to name: the value, or an error (a message, and an E for throws E)."""
        e = self.fn_err.get(name)
        return ('res', ret) if e is None else ('res', ret, e)

    def drop_err(self, rt, rv):
        """C statements freeing the error in failed result rv."""
        code = f'drop_Str(&{rv}.err);'
        if len(rt) == 3 and not self.is_copy(rt[2]):
            code += ' ' + self.drop(rt[2], f'{rv}.eval')
        return code

    def etext(self, n):
        """vu_etext_E(v): the message of an error value: its variant, with its plain fields in parentheses."""
        cases = []
        for k, (vn, fs) in enumerate(self.enums[n].variants):
            parts = [f'vu_str_cat_bytes(&s, (const uint8_t *){cstr(disp(vn))}, {len(disp(vn).encode())});']
            for i, (f, ft) in enumerate(fs):
                sep = '(' if i == 0 else ', '
                parts.append(f'vu_str_cat_bytes(&s, (const uint8_t *)"{sep}", {len(sep)});')
                fv = self.payload(n, k, 'v') + cf(f)
                if ft == STR:
                    parts.append(f'vu_str_cat_bytes(&s, {fv}.data, {fv}.len);')
                elif ft in INTEGERS:
                    parts.append(f'{{ char b[32]; int m = snprintf(b, sizeof b, "%lld", (long long){fv}); '
                                 f'vu_str_cat_bytes(&s, (const uint8_t *)b, m); }}')
                elif ft == FLOAT:
                    parts.append(f'{{ char b[40]; const char *q = vu_shortest({fv}, b); '
                                 f'vu_str_cat_bytes(&s, (const uint8_t *)q, (int64_t)strlen(q)); }}')
                elif ft == BOOL:
                    parts.append(f'vu_str_cat_bytes(&s, (const uint8_t *)({fv} ? "true" : "false"), {fv} ? 4 : 5);')
                else:
                    parts.append('vu_str_cat_bytes(&s, (const uint8_t *)"...", 3);')
            if fs:
                parts.append('vu_str_cat_bytes(&s, (const uint8_t *)")", 1);')
            cases.append(f'case {k}: {" ".join(parts)} break;')
        return (f'static vu_str vu_etext_{n}(const T_{n} *v) {{ vu_str s = {{0}}; switch (v->tag) {{ '
                f'{" ".join(cases)} default: break; }} return s; }}')

    def box_name(self, t):
        """The suffix of the box pool for values of type t: the type's name for a struct or enum."""
        return t[1] if t[0] in ('struct', 'enum') else self.mg(t)

    def tmp(self):
        self.tmpn += 1
        return f'_t{self.tmpn}'

    def field_type(self, bt, name, line):
        if bt[0] == 'opt':
            err(line, f"this value is a {tn(bt)} and may be nil; unwrap it first: if x = ...:")
        if bt[0] == 'list':
            err(line, f"lists have .len and .push(x), not .{name}")
        if bt == STR:
            err(line, f"strings have .len, not .{name}")
        if bt == OS:
            err(line, "Os has the methods .run(args), .env(name), .clock(), .time() and .sleep(seconds)")
        if bt == NET:
            err(line, "Net has the methods .listen(port), .accept(listener), .connect(host, port), .recv(conn), "
                      ".send(conn, data), .port(listener), .tls_connect(host, port) and .tls_listen(port, cert:, key:)")
        if bt[0] == 'cap':
            err(line, f"{tn(bt)} has the methods .read(path), .write(path, data) and .temp_dir()")
        if bt[0] == 'enum':
            err(line, f"a {bt[1]} has no fields to read directly; use match to see which variant it is")
        if bt[0] == 'map':
            err(line, f"maps have .len, .get(key, default) and .remove(key), not .{name}")
        if bt[0] != 'struct':
            err(line, f"{tn(bt)} has no fields")
        ft = self.structs[bt[1]].field(name)
        if ft is None:
            names = ', '.join(f for f, _ in self.structs[bt[1]].fields)
            err(line, f"type {bt[1]} has no field '{name}' (it has: {names})")
        return ft

    # ---- output
    def emit(self, line):
        if self.src_line:
            # Every C line gets the Vu line it came from, so gdb, sanitizers and the C compiler point
            # at the Vu source exactly, even for statements that turn into several lines of C.
            self.lines.append(f'{"    " * self.ind}#line {ln(self.src_line)} {self.cpaths[self.src_line >> LINE_BITS]}')
        self.lines.append('    ' * self.ind + line)

    def open(self, line):
        self.emit(line)
        self.ind += 1

    def close(self, line='}'):
        self.ind -= 1
        self.emit(line)

    # ---- scopes and ownership state
    def lookup(self, name):
        for sc in reversed(self.scopes):
            if name in sc.vars:
                return sc.vars[name]
        return None

    def var_cname(self, name):
        # user names always start with v_; _ and the hidden variables of hoisted ? ($t1) get temporaries
        return 'v_' + name if name != '_' and name[0] != '$' else 'u' + self.tmp()

    def declare(self, v):
        if v.name != '_':
            prev = self.lookup(v.name)
            if prev:
                err(v.line, f"'{v.name}' is already defined on line {ln(prev.line)}; use a different name")
            # A local may shadow a function, a constant or a built-in (let text = ..., let max = ...);
            # types and variants stay reserved, since a bare variant name is also a value.
            key = self.prefix + v.name
            if key in self.structs or key in self.enums or key in self.variants or key in self.gtypes:
                err(v.line, f"'{v.name}' is already defined at top level (line {ln(self.top[key])})")
        self.scopes[-1].vars[v.name if v.name != '_' else v.cname] = v
        self.scopes[-1].order.append(v)

    def snapshot(self):
        return {v: (v.state, v.moved_line) for sc in self.scopes for v in sc.order}

    def restore(self, snap):
        for v, (st, ml) in snap.items():
            v.state, v.moved_line = st, ml

    def merge(self, snaps):
        for v in snaps[0]:
            entries = [sn[v] for sn in snaps if v in sn]
            sts = [e[0] for e in entries]
            st = sts[0] if all(x == sts[0] for x in sts) else 'maybe'
            ml = next((e[1] for e in entries if e[1]), None)
            v.state, v.moved_line = st, (ml if st != 'no' else None)

    def emit_drops(self, scopes):
        for sc in reversed(scopes):
            for v in reversed(sc.order):
                if v.kind == 'local' and not self.is_copy(v.ty) and v.state != 'yes':
                    self.emit(self.drop(v.ty, v.cname))

    def read_check(self, p, line):
        v = p.root
        for mode, fl in v.frozen:
            if mode == 'lock':
                err(line, f"'{v.name}' can't be used here: the 'var' binding on line {ln(fl)} has exclusive "
                          f"access to it; use that binding instead")
            if mode == 'part':
                i = self.par['var'] if self.par else 'i'
                err(line, f"'{v.name}' is split between the threads of the par loop on line {ln(fl)}: each iteration "
                          f"owns only {v.name}[{i}], so use just that element inside the loop")
        if v.state == 'yes':
            err(line, f"'{v.name}' was moved on line {ln(v.moved_line)} and can't be used afterwards")
        if v.state == 'maybe':
            err(line, f"'{v.name}' may have been moved on line {ln(v.moved_line)} (on some path) and can't be used here")

    def write_check(self, p, line, whole_ok=False):
        v = p.root
        if not v.mutable:
            if v.kind == 'param':
                msg = f"parameter '{v.name}' is read-only; declare it as 'var {v.name}: ...' to modify it"
            elif v.kind == 'ref':
                msg = f"'{v.name}' is a read-only binding; write 'var {v.name}' in the for/if to modify it"
            elif v.kind == 'view':
                msg = f"'{v.name}' is a read-only view into another value (a `let` of a field or element); modify that value directly once this block ends"
            elif v.kind == 'loop':
                msg = f"loop counter '{v.name}' can't be modified"
            elif v.kind == 'capture':
                msg = (f"'{v.name}' is captured by this closure, which can only read it; to change state, "
                       f"return the new value, or pass it to a function with a 'var' parameter")
            else:
                msg = f"'{v.name}' can't be modified; declare it with 'var' instead of 'let'"
            err(line, msg)
        if v.frozen:
            mode, fl = v.frozen[-1]
            if mode in ('par', 'part'):
                err(line, f"'{v.name}' can't be modified inside the par loop on line {ln(fl)}: its iterations run at "
                          f"the same time on different threads. Store each iteration's result in its own list "
                          f"element (out[i] = ...) and combine them after the loop")
            err(line, f"'{v.name}' can't be modified while the loop/binding on line {ln(fl)} is borrowing it")
        if not (p.is_name and whole_ok):
            self.read_check(p, line)

    def move(self, p, line):
        v = p.root
        if p.ty == STR and (not p.is_name or v.kind != 'local' or v.frozen):
            # Strings are immutable, so a string that can't be moved (it's borrowed, or part of a
            # field or list element) is copied instead.
            return f'vu_str_dup(&{p.code})'
        if not p.is_name:
            err(line, f"can't move a {tn(p.ty)} out of a field or list element; build the value where it's needed")
        if v.kind == 'view':
            err(line, f"can't move '{v.name}': it's a read-only view into another value (a `let` of a field or element); pass that value itself, or build a new one")
        if v.kind == 'param':
            err(line, f"can't move '{v.name}': this function only borrows it. Declare the parameter "
                      f"'own {v.name}: {tn(v.ty)}' to take ownership, or return or store a new value instead")
        if v.kind == 'ref':
            err(line, f"can't move '{v.name}': it's bound (by for, if or match) to part of a value that still owns "
                      f"it. To keep a call's result, write 'let {v.name} = f(...) else ...' (else can also return, "
                      f"break or continue)")
        if v.kind == 'capture':
            err(line, f"can't move '{v.name}' out of this closure: it can be called again, so what it captured "
                      f"stays in it. Build a new value instead")
        if v.kind != 'local':
            err(line, f"can't move '{v.name}': this function only borrows it. Return or store a new value instead")
        if v.frozen:
            err(line, f"'{v.name}' can't be moved while the loop/binding on line {ln(v.frozen[-1][1])} is borrowing it")
        v.state, v.moved_line = 'yes', line
        return f'VU_MV({v.cname})'

    # ---- expressions
    def place(self, e):
        if e.k == 'try' and id(e) in self.hoisted:
            v = self.lookup(self.hoisted[id(e)])
            return Place(v, v.lv, v.ty, True)
        if e.k == 'name':
            v = self.lookup(e.name)
            return Place(v, v.lv, v.ty, True) if v else None
        if e.k == 'field':
            b = self.place(e.e)
            if b is None or (b.ty[0] in ('list', 'map') and e.name == 'len') or b.ty == STR:
                return None
            return Place(b.root, f'{b.code}.{cf(e.name)}', self.field_type(b.ty, e.name, e.line), False)
        if e.k == 'index':
            if self.par and e.e.k == 'name' and e.i.k == 'name' and e.i.name == self.par['var']:
                v = self.lookup(e.e.name)
                if v is not None and any(m == 'part' for m, _ in v.frozen):
                    return self.par_elem(v, e)
            self.pure_index(e.i)
            b = self.place(e.e)
            if b is None or b.ty == STR:
                return None
            if b.ty[0] == 'map':
                kr = self.key_ref(e.i, b.ty[1], e.line)
                if kr is None:
                    return None   # a computed Str key: readable through a temporary, but not a place
                return Place(b.root, f'(*vu_mget_{self.mg(b.ty)}(&{b.code}, {kr}, {e.line}))', b.ty[2], False)
            if b.ty[0] != 'list':
                err(e.line, f"can't index a {tn(b.ty)}; only lists, strings and maps can be indexed")
            i, _ = self.value(e.i, INT)
            return Place(b.root, f'(*vu_at_{self.mg(b.ty)}(&{b.code}, {i}, {e.line}))', b.ty[1], False)
        return None

    def key_ref(self, e, key, line):
        """A pointer to a map key, written inline (inside m[k], no temporaries can be made)."""
        if key == STR:
            p = self.place(e)
            if p is not None:
                self.read_check(p, line)
                if p.ty != STR:
                    err(line, f'this map has Str keys, not {tn(p.ty)}')
                return f'&{p.code}'
            if e.k == 'str' and all(isinstance(x, str) for x in e.parts):
                text = ''.join(e.parts)
                return f'&(vu_str){{(uint8_t *){cstr(text)}, {len(text.encode("utf-8"))}, 0}}'
            return None
        c, _ = self.value(e, key)
        return f'&({self.ct(key)}){{{c}}}'

    def key_arg(self, e, key, use):
        """Borrow a map key for a call like k in m / m.get(k, d); use(pointer) -> (code, type)."""
        def inner(kc, kt, kp):
            if kt != key:
                err(e.line, f'this map has {tn(key)} keys, not {tn(kt)}')
            return use(f'&{kc}' if (kp is not None or key == STR) else f'&({self.ct(key)}){{{kc}}}')
        return self.with_borrow(e, inner, key)

    def computed_key(self, e):
        """Is e (or the place it is part of) m[k] with a computed Str key? Those can be read but not changed."""
        while e.k in ('field', 'index'):
            if e.k == 'index':
                mt = self.probe_type(e.e)
                if mt is not None and mt[0] == 'map' and mt[1] == STR and self.place(e.e) is not None \
                        and self.place(e) is None:
                    return True
            e = e.e
        return False

    def par_elem(self, v, e):
        """xs[i] inside `par for i`: iteration i owns this element, so it may read and write it."""
        if v.ty[0] != 'list':
            err(e.line, f"can't index a {tn(v.ty)}; only lists can be indexed")
        pv = self.par['elems'].get(v)
        if pv is None:
            pv = Var(f"{v.name}[{self.par['var']}]", v.ty[1], None, 'elem', v.mutable, False, e.line)
            pv.base = v
            pv.frozen = [f for f in v.frozen if f[0] not in ('par', 'part')]
            pv.state, pv.moved_line = v.state, v.moved_line
            self.par['elems'][v] = pv
        i = self.lookup(self.par['var'])
        return Place(pv, f'(*vu_at_{self.mg(v.ty)}(&{v.lv}, {i.cname}, {e.line}))', v.ty[1], False)

    def probe_type(self, e):
        """The type of e, without keeping any ownership effects of generating it. Types are remembered
        per expression, so nested probes (long chains like a + b + c + ...) stay linear."""
        t = self.tcache.get(id(e)) or self.static_type(e)
        if t is not None:
            return t
        snap = self.snapshot()
        _, t, _ = self.gen(e)
        self.restore(snap)
        return t

    def static_type(self, e):
        """The type of e worked out from the syntax alone, without generating code; None when that
        isn't enough (the caller then generates the code to find out). Remembered per expression."""
        key = ('s', id(e))
        if key not in self.tcache:
            self.tcache[key] = self.static_type_uncached(e)
        return self.tcache[key]

    def static_type_uncached(self, e):
        k = e.k
        simple = {'int': INT, 'float': FLOAT, 'bool': BOOL, 'char': BYTE, 'str': STR, 'nil': NIL, 'slice': STR}
        if k in simple:
            return simple[k]
        if k == 'name':
            v = self.lookup(e.name)
            if v:
                return v.ty
            if e.name in self.variants:
                return None if self.variants[e.name] in self.gtypes else ('enum', self.variants[e.name])
            return self.consts.get(e.name)
        if k in ('try', 'orelse'):
            return self.static_type(e.e)
        if k == 'un':
            return BOOL if e.op == 'not' else self.static_type(e.e)
        if k == 'bin':
            if e.op in ('and', 'or', '==', '!=', '<', '>', '<=', '>=', 'in'):
                return BOOL
            if e.op == '*' and e.l.k == 'list':
                return None
            if self.is_lit(e.l):
                rt = INT if self.is_lit(e.r) else self.static_type(e.r)
                return None if rt is None else (rt if rt in (FLOAT, BYTE) else INT)
            return self.static_type(e.l)
        if k == 'field':
            bt = self.static_type(e.e)
            if bt is None:
                return None
            if (bt[0] in ('list', 'map') or bt == STR) and e.name == 'len':
                return INT
            return self.structs[bt[1]].field(e.name) if bt[0] == 'struct' else None
        if k == 'index':
            bt = self.static_type(e.e)
            if bt == STR:
                return BYTE
            if bt is not None and bt[0] == 'map':
                return bt[2]
            return bt[1] if bt is not None and bt[0] == 'list' else None
        if k == 'call':
            f = e.fn
            if f.k == 'name' and self.lookup(f.name) is not None:
                v = self.lookup(f.name)
                return v.ty[2] if v.ty[0] in ('fn', 'lfn') else None
            if f.k in ('field', 'index', 'call'):
                ft = self.static_type(f)
                if ft is not None and ft[0] in ('fn', 'lfn'):
                    return ft[2]
            if f.k == 'name':
                if f.name in self.fns:
                    return self.fns[f.name][1]
                if f.name in self.gfns:
                    return self.fns[self.gcache[id(e)]][1] if id(e) in self.gcache else None
                if f.name in self.structs:
                    return ('struct', f.name)
                if f.name in self.variants:
                    return None if self.variants[f.name] in self.gtypes else ('enum', self.variants[f.name])
                return {'str': STR, 'sqrt': FLOAT, 'float': FLOAT, 'int': INT, 'byte': BYTE, 'arg': INT}.get(f.name)
            if f.k == 'field' and f.name == 'read':
                return STR
            if f.k == 'field' and f.name == 'remove':
                return BOOL
            if f.k == 'field' and f.name == 'get':
                mt = self.static_type(f.e)
                return mt[2] if mt is not None and mt[0] == 'map' else None
        return None

    @staticmethod
    def walk(x):
        if isinstance(x, Node):
            yield x
            for v in x.__dict__.values():
                yield from Gen.walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                yield from Gen.walk(v)

    def gen(self, e, expect=None):
        """-> (code, type, place or None). Places are checked for readability, not moved."""
        p = self.place(e)
        if p is not None:
            self.read_check(p, e.line)
            self.tcache[id(e)] = p.ty
            return p.code, p.ty, p
        code, t = getattr(self, 'g_' + e.k)(e, expect)
        if expect is None:
            self.tcache[id(e)] = t
        return code, t, None

    def value(self, e, expect=None):
        """Evaluate e for ownership by the consumer: moves non-copy places, coerces to expect."""
        code, t, p = self.gen(e, expect)
        if t == VOID:
            err(e.line, "this call doesn't produce a value")
        if p is not None and not self.is_copy(t):
            code = self.move(p, e.line)
        return self.coerce(code, t, expect, e.line)

    def coerce(self, code, t, expect, line):
        if expect is None or t == expect:
            return code, t
        if t[0] == 'lfn':
            self.lfn_escape(line)
        if expect[0] == 'opt':
            if t == NIL:
                return 'NULL', expect
            if t == expect[1]:
                return f'vu_box_{self.box_name(t)}({code})', expect
        hint = {frozenset((INT, FLOAT)): '; convert with float(x) or int(x)',
                frozenset((INT, BYTE)): '; convert with byte(x) or int(x)'}.get(frozenset((t, expect)), '')
        err(line, f'expected {tn(expect)}, found {tn(t)}{hint}')

    def lfn_escape(self, line):
        err(line, "this closure borrows local variables, so it can only be called, bound with let, or passed to "
                  "a function (it can't be stored, returned or sent); write 'own fn' to give it its own copies "
                  "of them")

    def with_borrow(self, e, use, expect=None):
        """Read e without taking ownership. use(code, type, place) -> (code, type).
        A temporary that owns resources is dropped after use."""
        code, t, p = self.gen(e, expect)
        if p is not None and self.effects(e):
            # The place's index calls a function: evaluate it once, into a pointer, since use() may
            # mention the place more than once.
            pv = self.tmp()
            rc, rt = use(f'(*{pv})', t, p)
            if p.root.state != 'no':
                err(e.line, f"'{p.root.name}' is used here and moved by another part of the same expression")
            if rt == VOID:
                return f'({{ {self.ct(t)} *{pv} = &{code}; {rc}; }})', VOID
            rv = self.tmp()
            return f'({{ {self.ct(t)} *{pv} = &{code}; {self.ct(rt)} {rv} = {rc}; {rv}; }})', rt
        if p is not None or self.is_copy(t):
            result = use(code, t, p)
            if p is not None and p.root.state != 'no':
                err(e.line, f"'{p.root.name}' is used here and moved by another part of the same expression")
            return result
        tv = self.tmp()
        rc, rt = use(tv, t, None)
        dr = self.drop(t, tv)
        if rt == VOID:
            return f'({{ {self.ct(t)} {tv} = {code}; {rc}; {dr} }})', VOID
        rv = self.tmp()
        return f'({{ {self.ct(t)} {tv} = {code}; {self.ct(rt)} {rv} = {rc}; {dr} {rv}; }})', rt

    def wrap(self, pre, expr, post, ret):
        if not pre and not post:
            return expr, ret
        body = ' '.join(pre)
        if ret == VOID:
            return f'({{ {body} {expr}; {" ".join(post)} }})', VOID
        rv = self.tmp()
        return f'({{ {body} {self.ct(ret)} {rv} = {expr}; {" ".join(post)} {rv}; }})', ret

    def effects(self, e):
        """True if evaluating e could change state (calls, moves), so evaluation order matters.
        Remembered per expression, so nested checks stay linear."""
        if e.k == 'try' and id(e) in self.hoisted:
            return False   # already evaluated, into its hidden variable
        r = self.ecache.get(id(e))
        if r is None:
            r = self.ecache[id(e)] = self.effects_uncached(e)
        return r

    def effects_uncached(self, e):
        k = e.k
        if k in ('int', 'float', 'bool', 'nil', 'char'):
            return False
        if k == 'str':
            return any(self.effects(p[0]) for p in e.parts if not isinstance(p, str))
        if k == 'slice':
            return (e.e.k != 'name' and self.effects(e.e)) or self.effects(e.lo) or self.effects(e.hi)
        if k == 'name':
            v = self.lookup(e.name)
            return v is not None and not self.is_copy(v.ty)
        if k == 'call':
            if e.fn.k == 'name' and e.fn.name in PURE_BUILTINS:
                return any(self.effects(a) for _, a in e.args)
            return True
        if k in ('field', 'ref'):
            return e.e.k != 'name' and self.effects(e.e)
        if k == 'index':
            return (e.e.k != 'name' and self.effects(e.e)) or self.effects(e.i)
        if k == 'un':
            return self.effects(e.e)
        if k == 'bin':
            return self.effects(e.l) or self.effects(e.r)
        return True

    @staticmethod
    def is_lit(e):
        return e.k == 'int' or (e.k == 'un' and e.op == '-' and e.e.k == 'int')

    def g_int(self, e, expect):
        if e.v > 2 ** 63 - 1:
            err(e.line, 'integer literal is too large for Int')
        if expect == FLOAT:
            return f'{e.v}.0', FLOAT
        if expect == BYTE:
            if e.v > 255:
                err(e.line, f'{e.v} does not fit in a Byte (0..255)')
            return f'((uint8_t){e.v})', BYTE
        return (str(e.v) if e.v < 2 ** 31 else f'INT64_C({e.v})'), INT

    def g_char(self, e, expect):
        return f'((uint8_t){e.v})', BYTE

    def g_float(self, e, expect):
        if float(e.v) == float('inf'):
            err(e.line, f'{e.v} is too large for a Float')
        return e.v, FLOAT

    def g_bool(self, e, expect):
        return ('true' if e.v else 'false'), BOOL

    def g_nil(self, e, expect):
        return 'NULL', NIL

    def g_name(self, e, expect):
        if e.name in self.variants:
            en = self.variants[e.name]
            if en in self.gtypes:
                known = self.expect_of(expect, en)
                if known is None:
                    if any(vn == e.name and fs for vn, fs, _ in self.gtypes[en].variants):
                        err(e.line, f"{disp(e.name)} holds values; create it with {disp(e.name)}(...)")
                    err(e.line, f"can't tell which {disp(en)} this {disp(e.name)} is; give it a type, like: "
                                f"let x: {disp(en)}[{', '.join(self.gtypes[en].tparams)}] = {disp(e.name)} (with real types)")
                en = known
            if self.enums[en].fields_of(e.name):
                err(e.line, f"{disp(e.name)} holds values; create it with {disp(e.name)}(...)")
            return f'((T_{en}){{.tag = {self.enums[en].index(e.name)}}})', ('enum', en)
        if e.name in self.enums or (e.name in self.gtypes and self.gtypes[e.name].k == 'enum'):
            err(e.line, f"'{disp(e.name)}' is an enum type; use one of its variants")
        if e.name in self.consts:
            return f'C_{e.name}', self.consts[e.name]
        if e.name in self.fns or e.name in self.gfns:
            return self.fn_value(e, expect)
        if e.name in self.structs:
            err(e.line, f"'{disp(e.name)}' is a type; create one with {disp(e.name)}(...)")
        err(e.line, f"unknown name '{disp(e.name)}'")

    def fn_value(self, e, expect):
        """A named function used as a value (handlers.push(on_get)): a vu_fn of its thunk, vu_th_<name>."""
        name = e.name
        exp = expect if expect is not None and expect[0] in ('fn', 'lfn') else None
        if name in self.gfns:
            it = self.gfns[name]
            b = {}
            if exp is not None and len(exp[1]) == len(it.params):
                for (_, pt, _, _, _), a in zip(it.params, exp[1]):
                    self.unify(pt, a, it.tparams, b)
                self.unify(it.ret, exp[2], it.tparams, b)
            if any(tp not in b for tp in it.tparams):
                err(e.line, f"'{disp(name)}' is a generic function; to use it as a value, say which instance, with "
                            f"a type: let f: fn(...) -> ... = {disp(name)}")
            name = self.instantiate_fn(name, [b[tp] for tp in it.tparams], e.line)
        params, ret, node = self.fns[name]
        d = disp(e.name)
        if name == 'main':
            err(e.line, "main can't be used as a value")
        if node.body is None:
            err(e.line, f"{d}() is an extern function, so it can't be used as a value; wrap it in a closure: "
                        f"fn(...) => {d}(...)")
        for pn, _, pv, _, po in params:
            if pv or po:
                err(e.line, f"{d}() has a '{'var' if pv else 'own'}' parameter ('{pn}'), so it can't be used as a value "
                            f"(a function value's parameters are read-only); wrap it in a closure: fn(...) => {d}(...)")
        if name in self.fn_err:
            err(e.line, f"{d}() fails with {tn(self.fn_err[name])} values, and a function value fails with a message; "
                        f"wrap it in a closure that turns the error into a message")
        if name not in self.thunks:
            self.thunks.append(name)
        return (f'((vu_fn){{(void (*)(void))vu_th_{name}, NULL, NULL}})',
                self.fn_type([pt for _, pt, _, _, _ in params], ret, node.throws))

    def g_lambda(self, e, expect):
        """A closure: its body becomes the C function vu_lam<n>, and its value a vu_fn holding it with the
        variables it captures. A closure that captures nothing is a plain fn value; one that captures and
        is 'own' copies (or moves) what it captures into a heap env and is a fn value too; otherwise it
        points at the variables (a stack env) and is a borrowing closure ('lfn'), which can't outlive
        them. expect is the fn type wanted, or ('fnhint', parameter types, throws) while inferring."""
        hint = expect if expect is not None and expect[0] == 'fnhint' else None
        if expect is not None and expect[0] == 'opt':
            expect = expect[1]   # (the fn value is then boxed by coerce)
        exp = expect if expect is not None and expect[0] in ('fn', 'lfn') else None
        what = f"'{e.name}'" if e.name else 'this closure'
        if exp is not None and len(exp[1]) != len(e.params):
            err(e.line, f"{what} takes {len(e.params)} parameter(s), but a {tn(exp)} takes {len(exp[1])}")
        ptys = []
        for i, (pn, pt, pl) in enumerate(e.params):
            if pt is not None:
                t = self.resolve(pt, pl)
                if exp is not None and t != exp[1][i]:
                    err(pl, f"parameter '{pn}' is a {tn(t)}, but a {tn(exp)} passes a {tn(exp[1][i])}")
            elif exp is not None:
                t = exp[1][i]
            elif hint is not None:
                t = hint[1][i]
            else:
                err(pl, f"give parameter '{pn}' a type, like fn({pn}: Int) => ...; nothing here says what it is")
            ptys.append(t)
        ret = self.resolve(e.ret, e.line) if e.ret is not None else (exp[2] if exp is not None else None)
        if e.ret is not None and exp is not None and ret != exp[2]:
            err(e.line, f"{what} returns {tn(ret)}, but a {tn(exp)} returns {tn(exp[2])}")
        if e.throws and exp is not None and not exp[3]:
            err(e.line, f"{what} is marked throws, but a {tn(exp)} can't fail")
        throws = e.throws or (exp is not None and exp[3]) or (hint is not None and hint[2])
        if id(e) not in self.lam_ids:
            self.lam_ids[id(e)] = len(self.lam_ids) + 1
        num = self.lam_ids[id(e)]
        # What it captures: every variable visible here that its body names (a name inside can't mean
        # anything else, since a local can't reuse a visible name), in name order. Inside, each is a
        # read-only variable in the env (a pointer to the variable, if the closure borrows).
        names = sorted({x.name for x in self.walk(e.block if e.block is not None else e.body) if x.k == 'name'})
        caps = []
        for nm in names:
            ov = self.lookup(nm)
            if ov is not None:
                caps.append((ov, Var(nm, ov.ty, f'env->c{len(caps)}', 'capture', False, not e.own, ov.line)))
        ctx = LamCtx(self.lam, e.name)
        saved = (self.lines, self.ind, self.scopes, self.loops, self.par, self.rest, self.throws, self.ret,
                 self.rett, self.is_main, self.lam, self.src_line)
        self.lines, self.ind = [], 1
        self.scopes, self.loops, self.par, self.rest = [Scope()], [], None, []
        self.lam, self.throws, self.is_main, self.src_line = ctx, throws, False, e.line
        for _, iv in caps:
            self.declare(iv)
        self.scopes.append(Scope())
        cps = []
        for (pn, _, pl), t in zip(e.params, ptys):
            cps.append(self.pdecl(t, 'v_' + pn))
            self.declare(Var(pn, t, 'v_' + pn, 'param', False, not self.by_value(t), pl))
        if e.block is not None:
            stmts = e.block
        else:
            if ret is None:
                ret = self.probe_type(e.body.e if e.body.k == 'try' else e.body)
                if ret == NIL:
                    err(e.line, f"can't tell the type of nil; give {what} a return type: fn(...) -> Type? => ...")
            key = 'syn_x' if ret == VOID else 'syn_r'
            if getattr(e, key, None) is None:
                setattr(e, key, [Node('exprstmt' if ret == VOID else 'return', e.line, expr=e.body)])
            stmts = getattr(e, key)
        self.ret = ret
        self.rett = self.reg(('res', ret)) if throws else ret
        self.emit(f'VU_ENTER({cstr(e.name if e.name else "closure")});')
        div = self.stmts(stmts)
        if not div:
            if ret != VOID:
                err(e.line, f"{what} must end with a return (it returns {tn(ret)})")
            self.emit_drops(self.scopes)
            if throws:
                self.emit(f'return ({self.ct(self.rett)}){{0}};')
        lines, rett = self.lines, self.rett
        (self.lines, self.ind, self.scopes, self.loops, self.par, self.rest, self.throws, self.ret,
         self.rett, self.is_main, self.lam, self.src_line) = saved
        head = f'    vu_env{num} *env = (vu_env{num} *)vu_envp;' if caps else '    (void)vu_envp;'
        self.lam_fns[num] = (f'static {self.ct(rett)} vu_lam{num}(void *vu_envp{"".join(", " + c for c in cps)})',
                             [head] + lines)
        ft = self.fn_type(ptys, ret, throws)
        fnp = f'(void (*)(void))vu_lam{num}'
        self.lam_caps[id(e)] = []
        if not caps:
            self.lam_envs[num] = None
            return f'((vu_fn){{{fnp}, NULL, NULL}})', ft
        fields, inits = [], []
        for i, (ov, iv) in enumerate(caps):
            p = Place(ov, ov.lv, ov.ty, True)
            self.read_check(p, e.line)
            if e.own:
                if ov.ty[0] == 'lfn':
                    err(e.line, f"'{ov.name}' is a closure that borrows local variables, so an own closure can't "
                                f"keep it")
                fields.append(f'{self.ct(ov.ty)} c{i};')
                inits.append(ov.lv if self.is_copy(ov.ty) else self.move(p, e.line))
            else:
                fields.append(f'{self.ct(ov.ty)} *c{i};')
                inits.append(ov.cname if ov.ptr else f'&{ov.cname}')
        self.lam_envs[num] = f'typedef struct {{ {" ".join(fields)} }} vu_env{num};'
        if e.own:
            drops = ''.join(self.drop(ov.ty, f'e->c{i}') + ' ' for i, (ov, _) in enumerate(caps)
                            if not self.is_copy(ov.ty))
            self.lam_drops[num] = (f'static void vu_envdrop{num}(void *p) {{ vu_env{num} *e = (vu_env{num} *)p; '
                                   f'{drops}free(e); }}')
            tv = self.tmp()
            sets = ' '.join(f'{tv}->c{i} = {c};' for i, c in enumerate(inits))
            return (f'({{ vu_env{num} *{tv} = (vu_env{num} *)vu_malloc(sizeof *{tv}); {sets} '
                    f'(vu_fn){{{fnp}, {tv}, vu_envdrop{num}}}; }})', ft)
        self.lam_caps[id(e)] = [ov for ov, _ in caps]
        return f'((vu_fn){{{fnp}, &(vu_env{num}){{{", ".join(inits)}}}, NULL}})', ('lfn',) + ft[1:]

    def s_fnstmt(self, n):
        """fn name(...): ... inside a function: a closure bound to name, like a let."""
        lam = n.lam
        code, t = self.g_lambda(lam, None)
        v = Var(lam.name, t, self.var_cname(lam.name), 'local', False, False, n.line)
        self.declare(v)
        self.emit(f'vu_fn {v.cname} = {code};')
        self.freeze_caps(lam, n.line)
        return False

    def freeze_caps(self, lam, line):
        """A borrowing closure bound to a name points at what it captures until its block ends, so those
        variables can be read meanwhile but not changed or moved."""
        for v in self.lam_caps.get(id(lam), []):
            v.frozen.append(('read', line))
            self.scopes[-1].unfreeze.append(v)

    def g_str(self, e, expect):
        return self.str_build(e)

    def str_build(self, e):
        """A string literal, with any {interpolations}, as an owned Str value."""
        texts = [p for p in e.parts if isinstance(p, str)]
        if len(texts) == len(e.parts):
            text = ''.join(texts)
            return f'vu_str_lit({cstr(text)}, {len(text.encode("utf-8"))})', STR
        tv = self.tmp()
        stmts = [f'vu_str {tv} = {{0}};']
        for p in e.parts:
            if isinstance(p, str):
                stmts.append(f'vu_str_cat_bytes(&{tv}, (const uint8_t *){cstr(p)}, {len(p.encode("utf-8"))});')
                continue
            x, spec = p
            if self.probe_type(x) == STR:
                if any(spec[k] for k in (0, 1, 3)) or spec[2] is not None:
                    err(x.line, 'format specs like :8 apply to numbers, not strings')
                code, _ = self.with_borrow(x, lambda c, t, _p: (f'vu_str_cat(&{tv}, &{c})', VOID))
                stmts.append(code + ';')
            else:
                fmt, val = self.fmt_one(x, spec)
                if fmt == '%lld':   # a plain {n}: digits without printf
                    stmts.append(f'vu_str_cat_int(&{tv}, {val});')
                else:
                    stmts.append(f'vu_str_catf(&{tv}, {cstr(fmt)}, {val});')
        return '({ ' + ' '.join(stmts) + f' {tv}; }})', STR

    def str_op(self, e):
        """Str + Str (a new string) and string comparisons, without taking ownership of either side."""
        def use_l(lc, lt, lp):
            def use_r(rc, rt, rp):
                if rt != STR:
                    err(e.line, f"can't use '{e.op}' on Str and {tn(rt)}; put values in a string with \"{{x}}\"")
                if e.op == '+':
                    return f'vu_str_concat(&{lc}, &{rc})', STR
                if e.op in ('==', '!='):
                    return f'({"" if e.op == "==" else "!"}vu_str_eq(&{lc}, &{rc}))', BOOL
                return f'(vu_str_cmp(&{lc}, &{rc}) {e.op} 0)', BOOL
            return self.with_borrow(e.r, use_r)
        return self.with_borrow(e.l, use_l)

    def g_ref(self, e, expect):
        err(e.line, "'&' marks an argument for a 'var' parameter; it can only appear directly in a call")

    def g_un(self, e, expect):
        if e.op == '-':
            c, t = self.value(e.e, expect if expect in (INT, FLOAT) else None)
            if t not in (INT, FLOAT):
                err(e.line, f"can't negate a {tn(t)}")
            return (f'vu_neg({c}, {e.line})' if t == INT else f'(-{c})'), t
        c, _ = self.value(e.e, BOOL)
        return f'(!{c})', BOOL

    def operands(self, L, R, expect=None):
        """Generate both operands; an Int literal next to a Float becomes a Float."""
        if self.is_lit(L) and not self.is_lit(R):
            r, rt = self.value(R)
            l, lt = self.value(L, rt if rt in (FLOAT, BYTE) else None)
        else:
            both_lit = self.is_lit(L) and self.is_lit(R)
            l, lt = self.value(L, expect if (expect in (FLOAT, BYTE) and both_lit) else None)
            r, rt = self.value(R, lt if (lt in (FLOAT, BYTE) and self.is_lit(R)) else None)
        return l, lt, r, rt

    def g_bin(self, e, expect):
        op = e.op
        if op in ('and', 'or'):
            l, _ = self.value(e.l, BOOL)
            snap = self.snapshot()
            r, _ = self.value(e.r, BOOL)
            self.merge([snap, self.snapshot()])
            return f'({l} {"&&" if op == "and" else "||"} {r})', BOOL
        if op in ('==', '!=') and (e.l.k == 'nil' or e.r.k == 'nil'):
            other = e.r if e.l.k == 'nil' else e.l

            def use(c, t, p):
                if t[0] != 'opt':
                    err(e.line, f'only optional values can be compared with nil (this is {tn(t)})')
                return f'({c} {op} NULL)', BOOL
            return self.with_borrow(other, use)
        if op == '*' and e.l.k == 'list':
            return self.repeat(e, expect)
        if op == 'in':
            def use_m(mc, mt, mp):
                if mt[0] != 'map':
                    err(e.line, f"'in' checks whether a key is in a map; this is {tn(mt)}")
                return self.key_arg(e.l, mt[1], lambda kr: (f'vu_mhas_{self.mg(mt)}(&{mc}, {kr})', BOOL))
            return self.with_borrow(e.r, use_m)
        if op in ('+', '==', '!=', '<', '>', '<=', '>=') and self.probe_type(e.l) == STR:
            return self.str_op(e)
        l, lt, r, rt = self.operands(e.l, e.r, expect)
        conv = {frozenset((INT, FLOAT)): '; convert with float(x) or int(x)',
                frozenset((INT, BYTE)): '; convert with byte(x) or int(x)'}.get(frozenset((lt, rt)), '')
        if op in ('==', '!=') and lt == rt and lt[0] == 'enum':
            if not self.enums[lt[1]].plain:
                err(e.line, f"{lt[1]} variants hold values, so compare them with match instead of '{op}'")
            return f'({l}.tag {op} {r}.tag)', BOOL
        if op in ('==', '!='):
            if lt != rt or lt not in SCALARS:
                err(e.line, f"can't compare {tn(lt)} with {tn(rt)} using '{op}'{conv}")
            res = BOOL
        elif op in ('<', '>', '<=', '>='):
            if lt != rt or lt not in (INT, FLOAT, BYTE):
                err(e.line, f"can't compare {tn(lt)} with {tn(rt)} using '{op}'{conv}")
            res = BOOL
        elif op in ('<<', '>>'):
            if lt not in INTEGERS or rt not in INTEGERS:
                err(e.line, f"'{op}' needs an Int or Byte on the left and a shift amount on the right")
            res = lt
        elif op in ('&', '|', '^'):
            if lt != rt or lt not in INTEGERS:
                hint = " (use 'and' / 'or' for Bool)" if BOOL in (lt, rt) else conv
                err(e.line, f"'{op}' needs two Ints or two Bytes{hint}")
            res = lt
        else:
            if lt != rt or lt not in (INT, FLOAT, BYTE):
                err(e.line, f"can't apply '{op}' to {tn(lt)} and {tn(rt)}{conv}")
            if op == '%' and lt == FLOAT:
                err(e.line, "'%' needs Int operands")
            res = lt
        pre = []
        if self.effects(e.l) or self.effects(e.r):
            a, b = self.tmp(), self.tmp()
            pre = [f'{self.ct(lt)} {a} = {l};', f'{self.ct(rt)} {b} = {r};']
            l, r = a, b
        fn = None
        if lt == INT and res == INT:
            fn = INT_OPS.get(op)
        elif lt == BYTE and res == BYTE:
            fn = BYTE_OPS.get(op)
        if fn:
            x = f'{fn}({l}, {r}, {e.line})'
        else:
            x = f'((uint8_t)({l} {op} {r}))' if res == BYTE else f'({l} {op} {r})'
        if pre:
            x = '({ ' + ' '.join(pre) + f' {x}; }})'
        return x, res

    def repeat(self, e, expect):
        """[a, b] * n -> a new list holding n copies of the elements (plain-data elements only)."""
        lc, lt = self.g_list(e.l, expect)
        if not self.is_copy(lt[1]):
            err(e.line, f"only lists of plain values (Int, Float, Bool, plain structs) can be repeated with '*', "
                        f"not {tn(lt)}")
        n, _ = self.value(e.r, INT)
        tv = self.tmp()
        return f'({{ {self.ct(lt)} {tv} = {lc}; vu_rep_{self.mg(lt)}({tv}, {n}, {e.line}); }})', lt

    def g_field(self, e, expect):
        if e.name == 'len' and e.e.k == 'name':
            v = self.lookup(e.e.name)
            if v is not None and v.ty[0] == 'list' and any(m == 'part' for m, _ in v.frozen):
                return f'({v.lv}).len', INT   # the length never changes inside a par loop

        def use(c, t, p):
            if t == STR:
                if e.name != 'len':
                    self.field_type(t, e.name, e.line)
                return f'({c}).len', INT
            if t[0] == 'list':
                if e.name != 'len':
                    self.field_type(t, e.name, e.line)
                return f'({c}).len', INT
            if t[0] == 'map':
                if e.name != 'len':
                    self.field_type(t, e.name, e.line)
                return f'({c}).live', INT
            ft = self.field_type(t, e.name, e.line)
            if p is None and not self.is_copy(t) and ft == STR:
                # The temporary is freed right after this, so the string is copied out first.
                return f'vu_str_dup(&({c}).{cf(e.name)})', ft
            if p is None and not self.is_copy(t) and not self.is_copy(ft):
                err(e.line, f"can't take field '{e.name}' out of a temporary {tn(t)}; store it in a variable first")
            return f'({c}).{cf(e.name)}', ft
        return self.with_borrow(e.e, use)

    def g_index(self, e, expect):
        def use(c, t, p):
            self.pure_index(e.i)
            if t == STR:
                i, _ = self.value(e.i, INT)
                return f'vu_str_at(&{c}, {i}, {e.line})', BYTE
            if t[0] == 'map':
                if p is None and t[2] == STR:
                    return self.key_arg(e.i, t[1], lambda kr: (f'vu_str_dup(vu_mget_{self.mg(t)}(&{c}, {kr}, {e.line}))', STR))
                if p is None and not self.is_copy(t[2]):
                    err(e.line, "can't take a value out of a temporary map; store the map in a variable first")
                if not self.is_copy(t[2]) and t[1] == STR and self.key_ref(e.i, STR, e.line) is None:
                    # Not a place, so the value would be treated as a fresh copy while the map still owns it.
                    err(e.line, f"to use a {tn(t[2])} stored in a map, put the key in a variable first: "
                                f"let k = ...; then m[k]")
                return self.key_arg(e.i, t[1], lambda kr: (f'(*vu_mget_{self.mg(t)}(&{c}, {kr}, {e.line}))', t[2]))
            if t[0] != 'list':
                err(e.line, f"can't index a {tn(t)}; only lists and strings can be indexed")
            if p is None and t[1] == STR:
                i, _ = self.value(e.i, INT)
                return f'vu_str_dup(vu_at_{self.mg(t)}(&{c}, {i}, {e.line}))', STR
            if p is None and not self.is_copy(t[1]):
                err(e.line, "can't take an element out of a temporary list; store the list in a variable first")
            i, _ = self.value(e.i, INT)
            return f'(*vu_at_{self.mg(t)}(&{c}, {i}, {e.line}))', t[1]
        return self.with_borrow(e.e, use)

    def g_slice(self, e, expect):
        def use(c, t, p):
            if t != STR:
                err(e.line, f'slices like s[a..b] work on strings in v0, not {tn(t)}')
            self.pure_index(e.lo, e.hi)
            lo, _ = self.value(e.lo, INT)
            hi, _ = self.value(e.hi, INT)
            return f'vu_str_slice(&{c}, {lo}, {hi}, {e.line})', STR
        return self.with_borrow(e.e, use)

    def g_list(self, e, expect):
        if expect and expect[0] == 'opt':
            expect = expect[1]   # a list where an optional list goes: built as a list, then boxed
        et = expect[1] if expect and expect[0] == 'list' else None
        if not e.items and et is None:
            err(e.line, "can't tell the type of an empty list; write it like: let xs: [Int] = []")
        codes = []
        for it in e.items:
            c, t = self.value(it, et)
            if et is None:
                if t == NIL:
                    err(it.line, "can't tell the type of nil here; give the list a type: let xs: [T?] = [...]")
                et = t
            codes.append(c)
        lt = self.reg(('list', et))
        tv, m = self.tmp(), self.mg(lt)
        pushes = ' '.join(f'vu_push_{m}(&{tv}, {c});' for c in codes)
        return f'({{ {self.ct(lt)} {tv} = {{0}}; {pushes} {tv}; }})', lt

    def g_map(self, e, expect):
        if expect is not None and expect[0] == 'opt':
            expect = expect[1]
        if expect is not None and expect[0] == 'map':
            key, val = expect[1], expect[2]
        elif not e.pairs:
            err(e.line, "can't tell the type of an empty map; write it like: let m: {Str: Int} = {}")
        else:
            key, val = self.probe_type(e.pairs[0][0]), self.probe_type(e.pairs[0][1])
            if key not in MAP_KEYS:
                err(e.line, f"map keys can be Int, Byte, Bool or Str, not {tn(key)}")
        mt = self.reg(('map', key, val))
        tv, m = self.tmp(), self.mg(mt)
        stmts = []
        for ke, ve in e.pairs:
            vc, _ = self.value(ve, val)
            vt = self.tmp()
            put, _ = self.key_arg(ke, key, lambda kr: (f'vu_mset_{m}(&{tv}, {kr}, {vt}, {e.line})', VOID))
            stmts.append(f'{{ {self.ct(val)} {vt} = {vc}; {put}; }}')
        return f'({{ {m} {tv} = {{0}}; {" ".join(stmts)} {tv}; }})', mt

    def map_method(self, e):
        name, args = e.fn.name, [a for _, a in e.args]
        if any(nm for nm, _ in e.args):
            err(e.line, f'.{name}() takes positional arguments')
        if name == 'remove':
            if len(args) != 1:
                err(e.line, 'm.remove(key) takes one key')
            p = self.place(e.fn.e)
            if p is None or p.ty[0] != 'map':
                err(e.line, '.remove(key) works on a map stored in a variable')
            self.write_check(p, e.line)
            return self.key_arg(args[0], p.ty[1], lambda kr: (f'vu_mremove_{self.mg(p.ty)}(&{p.code}, {kr})', BOOL))
        if len(args) != 2:
            err(e.line, 'm.get(key, default) takes a key and a default value')

        def use_m(mc, mt, mp):
            if mt[0] != 'map':
                err(e.line, f'.get(key, default) works on maps, not {tn(mt)}')
            if not self.is_copy(mt[2]):
                err(e.line, f"m.get(key, default) needs plain values; for {tn(mt[2])} values use 'if k in m' and m[k]")

            def use_k(kr):
                d, _ = self.value(args[1], mt[2])
                return f'vu_mgetor_{self.mg(mt)}(&{mc}, {kr}, {d})', mt[2]
            return self.key_arg(args[0], mt[1], use_k)
        return self.with_borrow(e.fn.e, use_m)

    def construct_variant(self, e, vname, expect=None):
        en = self.variants[vname]
        if en in self.gtypes:
            vf = next(fs for vn, fs, _ in self.gtypes[en].variants if vn == vname)
            en = self.ginfer(e, en, [(f, ft) for f, ft, _, _ in vf], f'{disp(vname)}(...)', expect)
        info = self.enums[en]
        k = info.index(vname)
        fields = info.fields_of(vname)
        if not fields:
            err(e.line, f"{vname} holds no values; write it without parentheses")
        pre, inits = self.field_inits(e, vname, fields)
        if (en, k) in self.boxed:
            lit = f'((T_{en}){{.tag = {k}, .u.b{k} = vu_box_{k}_{en}((T_{k}_{en}){{{", ".join(inits)}}})}})'
        else:
            lit = f'((T_{en}){{.tag = {k}, .u.v{k} = {{{", ".join(inits)}}}}})'
        if pre:
            lit = '({ ' + ' '.join(pre) + f' {lit}; }})'
        return lit, ('enum', en)

    def g_try(self, e, expect):
        err(e.line, "'?' must be applied to a whole value on its own: let v = f(x)?, x = f(x)?, return f(x)?, "
                    "or f(x)? on its own line")

    def from_json_call(self, e):
        return e.k == 'call' and e.fn.k == 'name' and e.fn.name == 'from_json' and not self.lookup('from_json')

    # ---- JSON
    def json_need(self, t, line, seen=None, where=''):
        """Registers t (and what it's made of) for JSON code; types with no JSON form are errors.
        where names the field that holds t, for the message."""
        seen = set() if seen is None else seen
        at = f' (field {where})' if where else ''
        if t in seen:
            return
        seen.add(t)
        k = t[0]
        if t in (INT, FLOAT, BOOL, BYTE, STR):
            return
        if k in ('list', 'opt'):
            self.json_need(t[1], line, seen, where)
        elif k == 'map':
            if t[1] != STR:
                err(line, f"a map becomes a JSON object, whose keys are strings, so its keys must be Str, not "
                          f"{tn(t[1])}{at}")
            self.json_need(t[2], line, seen, where)
        elif k == 'struct':
            for f, ft in self.structs[t[1]].fields:
                self.json_need(ft, line, seen, f'{disp(t[1])}.{f}')
        elif k == 'enum':
            for vn, fs in self.enums[t[1]].variants:
                for f, ft in fs:
                    self.json_need(ft, line, seen, f'{disp(t[1])}.{jname(vn)}.{f}')
        else:
            err(line, f"{tn(t)}{at} has no JSON form (to_json and from_json take numbers, Bool, Str, lists, "
                      f"maps with Str keys, structs, enums and optionals of those)")
        if t not in self.jtypes:
            self.jtypes.append(t)

    def type_from_expr(self, x):
        """from_json's second argument, which the parser reads as a type."""
        if x.k != 'typearg':
            err(x.line, "from_json(text, Type): the second argument is the type to read, like Order, [Order] or {Str: Order}")
        return self.resolve(x.t, x.line)

    def b_to_json(self, e, args, expect):
        """to_json(x) -> Str: x as JSON (struct fields in order; nil and non-finite floats as null)."""
        self.nargs(e, args, 1, 'to_json')

        def use(c, t, _p):
            self.json_need(t, e.line)
            self.uses_float_parse = True   # the JSON runtime's decoders read numbers with it
            m, tv, o = self.mg(t), self.tmp(), self.tmp()
            return f'({{ {self.ct(t)} {tv} = {c}; vu_str {o} = {{0}}; vu_jenc_{m}(&{o}, &{tv}); {o}; }})', STR
        return self.with_borrow(args[0], use)

    def b_from_json(self, e, args, expect, handled=False):
        """from_json(text, Type) -> Type, which can fail (malformed JSON, a missing field, a wrong type)."""
        if not handled:
            err(e.line, "from_json() can fail, so handle its error: from_json(...)? passes it on, "
                        "from_json(...) else <default> replaces it, or match from_json(...): with ok(v) and err(e) arms")
        if any(a[0] for a in e.args):
            err(e.line, "from_json() doesn't take named arguments")
        if len(args) != 2:
            err(e.line, "from_json(text, Type) takes the JSON text and the type to read, like from_json(body, Order)")
        t = self.type_from_expr(args[1])
        self.json_need(t, e.line)
        self.uses_float_parse = True

        def use(c, st, _p):
            if st != STR:
                err(e.line, f'from_json reads JSON from a Str, not {tn(st)}')
            rt = self.reg(('res', t))
            r, j, v, ok = self.tmp(), self.tmp(), self.tmp(), self.tmp()
            return (f'({{ {self.ct(rt)} {r} = {{0}}; vu_jp {j} = {{({c}).data, ({c}).data, ({c}).data + ({c}).len, 0, '
                    f'{{0}}, {{0}}}}; {self.ct(t)} {v} = {{0}}; bool {ok} = vu_jdec_{self.mg(t)}(&{j}, &{v}); '
                    f'{r}.bad = !vu_jdone(&{j}, {ok}, &{r}.err); if (!{r}.bad) {r}.val = {v}; '
                    + ('' if self.is_copy(t) else f'else if ({ok}) {self.drop(t, v)} ') + f'{r}; }})', rt)
        return self.with_borrow(args[0], use)

    def json_code(self):
        """vu_jenc_T / vu_jdec_T for every type that to_json / from_json use."""
        protos, defs = [], []
        for t in self.jtypes:
            m, c = self.mg(t), self.ct(t)
            protos.append(f'static void vu_jenc_{m}(vu_str *o, {c} const *v);')
            protos.append(f'static bool vu_jdec_{m}(vu_jp *j, {c} *out);')
            defs.append(self.jenc(t))
            defs.append(self.jdec(t))
        return protos + defs

    def jenc(self, t):
        m, c, k = self.mg(t), self.ct(t), t[0]
        head = f'static void vu_jenc_{m}(vu_str *o, {c} const *v) {{ '
        if k == 'list':
            return (head + f'vu_jcat(o, "[", 1); for (int64_t i = 0; i < v->len; i++) {{ if (i) vu_jcat(o, ",", 1); '
                    f'vu_jenc_{self.mg(t[1])}(o, &v->data[i]); }} vu_jcat(o, "]", 1); }}')
        if k == 'map':
            return (head + f'vu_jcat(o, "{{", 1); int64_t n = 0; for (int64_t i = 0; i < v->nents; i++) {{ '
                    f'if (!v->ents[i].live) continue; if (n++) vu_jcat(o, ",", 1); vu_jenc_Str(o, &v->ents[i].key); '
                    f'vu_jcat(o, ":", 1); vu_jenc_{self.mg(t[2])}(o, &v->ents[i].val); }} vu_jcat(o, "}}", 1); }}')
        if k == 'opt':
            return head + f'if (!*v) vu_jcat(o, "null", 4); else vu_jenc_{self.mg(t[1])}(o, *v); }}'
        if k == 'struct':
            return head + self.jenc_fields(self.structs[t[1]].fields, 'v->') + ' }'
        cases = []
        for kk, (vn, fs) in enumerate(self.enums[t[1]].variants):
            name = jname(vn)
            if not fs:
                lit = json_str(name)
                cases.append(f'case {kk}: vu_jcat(o, {cstr(lit)}, {len(lit.encode())}); break;')
            else:
                lit = '{' + json_str(name) + ':'
                cases.append(f'case {kk}: vu_jcat(o, {cstr(lit)}, {len(lit.encode())}); '
                             f'{self.jenc_fields(fs, self.payload(t[1], kk, "v"))} vu_jcat(o, "}}", 1); break;')
        return head + f'switch (v->tag) {{ {" ".join(cases)} default: break; }} }}'

    def jenc_fields(self, fs, ptr):
        parts = []
        for i, (f, ft) in enumerate(fs):
            lit = ('{' if i == 0 else ',') + json_str(f) + ':'
            parts.append(f'vu_jcat(o, {cstr(lit)}, {len(lit.encode())}); vu_jenc_{self.mg(ft)}(o, &{ptr}{cf(f)});')
        if not fs:
            parts.append('vu_jcat(o, "{", 1);')
        parts.append('vu_jcat(o, "}", 1);')
        return ' '.join(parts)

    def jdec(self, t):
        m, c, k = self.mg(t), self.ct(t), t[0]
        head = f'static bool vu_jdec_{m}(vu_jp *j, {c} *out) {{ '
        if k == 'list':
            et = t[1]
            return (head + f'{c} r = {{0}}; if (!vu_jarr_begin(j)) return false; for (int64_t i = 0;; i++) {{ '
                    f'int k = vu_jarr_next(j, i == 0); if (k == 0) break; {self.ct(et)} x = {{0}}; '
                    f'if (k < 0 || !vu_jdec_{self.mg(et)}(j, &x)) {{ if (k > 0) vu_jpath(j, NULL, 0, i); '
                    f'{self.drop(t, "r")} return false; }} vu_push_{m}(&r, x); }} *out = r; return true; }}')
        if k == 'map':
            vt = t[2]
            return (head + f'{c} r = {{0}}; if (!vu_jobj_begin(j)) return false; for (bool first = true;; first = false) {{ '
                    f'vu_str key = {{0}}; int k = vu_jobj_next(j, first, &key); if (k == 0) break; '
                    f'if (k < 0) {{ {self.drop(t, "r")} return false; }} {self.ct(vt)} x = {{0}}; '
                    f'if (!vu_jdec_{self.mg(vt)}(j, &x)) {{ vu_jpath(j, (const char *)key.data, key.len, 0); '
                    f'drop_Str(&key); {self.drop(t, "r")} return false; }} vu_mtake_{m}(&r, &key, x, 0); }} '
                    f'*out = r; return true; }}')
        if k == 'opt':
            it = t[1]
            return (head + f'if (vu_jnull(j)) {{ *out = NULL; return true; }} {self.ct(it)} x = {{0}}; '
                    f'if (!vu_jdec_{self.mg(it)}(j, &x)) return false; *out = vu_box_{self.box_name(it)}(x); return true; }}')
        if k == 'struct':
            n = t[1]
            fs = self.structs[n].fields
            return head + self.jdec_fields(fs, f'*out = (T_{n}){{{", ".join(f"v{i}" for i in range(len(fs)))}}};') + ' }'
        n = t[1]
        variants = self.enums[n].variants
        plain = []
        for kk, (vn, fs) in enumerate(variants):
            if not fs:
                name = jname(vn)
                plain.append(f'if (vu_jkey(&s, {cstr(name)}, {len(name.encode())})) {{ drop_Str(&s); '
                             f'*out = (T_{n}){{.tag = {kk}}}; return true; }}')
        names = ', '.join(jname(vn) for vn, _ in variants)
        with_fs = ', '.join(jname(vn) for vn, fs in variants if fs)
        helpers = []
        pl = [jname(vn) for vn, fs in variants if not fs]
        plain_msg = (f"expected one of: {', '.join(pl)}" if pl else "expected an object") + \
                    (f" ({with_fs} {'is' if ', ' not in with_fs else 'are'} written as an object, like {{\"{jname(next(vn for vn, fs in variants if fs))}\": {{...}}}})" if with_fs else '')
        body = (f'vu_jws(j); const uint8_t *a = j->p; (void)a; if (j->p < j->end && *j->p == \'"\') {{ vu_str s = {{0}}; if (!vu_jdec_Str(j, &s)) return false; '
                f'{" ".join(plain)} drop_Str(&s); j->p = a; return vu_jfail(j, {cstr(plain_msg)}); }} '
                f'if (j->p >= j->end || *j->p != \'{{\') return vu_jfail(j, {cstr("expected a variant of " + disp(n) + " (" + names + ")")}); '
                f'if (!vu_jobj_begin(j)) return false; vu_str key = {{0}}; int k = vu_jobj_next(j, true, &key); '
                f'if (k <= 0) {{ if (k == 0) vu_jfail(j, "expected a variant name"); return false; }} ')
        for kk, (vn, fs) in enumerate(variants):
            if not fs:
                continue
            name = jname(vn)
            if (n, kk) in self.boxed:
                build = (f'*out = (T_{n}){{.tag = {kk}, .u.b{kk} = vu_box_{kk}_{n}((T_{kk}_{n}){{'
                         f'{", ".join(f"v{i}" for i in range(len(fs)))}}})}};')
            else:
                build = f'*out = (T_{n}){{.tag = {kk}, .u.v{kk} = {{{", ".join(f"v{i}" for i in range(len(fs)))}}}}};'
            helpers.append(f'static bool vu_jdec_{m}_{kk}(vu_jp *j, {c} *out) {{ {self.jdec_fields(fs, build)} }}\n')
            body += (f'if (vu_jkey(&key, {cstr(name)}, {len(name.encode())})) {{ drop_Str(&key); '
                     f'bool ok = vu_jdec_{m}_{kk}(j, out); if (!ok) {{ vu_jpath(j, {cstr(name)}, '
                     f'{len(name.encode())}, 0); return false; }} vu_str k2 = {{0}}; int e = vu_jobj_next(j, false, &k2); '
                     f'if (e != 0) {{ if (e > 0) {{ drop_Str(&k2); vu_jfail(j, "expected one variant"); }} {"" if self.is_copy(t) else self.drop(t, "(*out)")} '
                     f'*out = (T_{n}){{0}}; return false; }} return true; }} ')
        body += f'drop_Str(&key); return vu_jfail(j, {cstr(("expected one of: " + with_fs) if with_fs else ("expected one of: " + names + ", as a string"))}); }}'
        return ''.join(helpers) + head + body

    def jdec_fields(self, fs, build):
        """Reads an object into one local per field (v0, v1...), then runs build. Missing fields are errors,
        except optionals (nil); unknown fields are skipped; a repeated field keeps its last value."""
        decl = ' '.join(f'{self.ct(ft)} v{i} = {{0}}; bool s{i} = false;' for i, (_, ft) in enumerate(fs))
        drops = ' '.join(self.drop(ft, f'v{i}') for i, (_, ft) in enumerate(fs) if not self.is_copy(ft))
        arms = []
        for i, (f, ft) in enumerate(fs):
            again = '' if self.is_copy(ft) else f'if (s{i}) {{ {self.drop(ft, f"v{i}")} v{i} = ({self.ct(ft)}){{0}}; }} '
            arms.append(f'if (vu_jkey(&key, {cstr(f)}, {len(f.encode())})) {{ {again}'
                        f'if (!vu_jdec_{self.mg(ft)}(j, &v{i})) {{ vu_jpath(j, {cstr(f)}, {len(f.encode())}, 0); '
                        f'drop_Str(&key); goto fail; }} s{i} = true; }}')
        arms.append('if (!vu_jskip(j)) { drop_Str(&key); goto fail; }')
        need = ' '.join(f'if (!s{i}) {{ vu_jfail(j, {cstr(f"missing field {chr(39)}{f}{chr(39)}")}); goto fail; }}'
                        for i, (f, ft) in enumerate(fs) if ft[0] != 'opt')
        return (f'{decl} if (!vu_jobj_begin(j)) goto fail; for (bool first = true;; first = false) {{ '
                f'vu_str key = {{0}}; int k = vu_jobj_next(j, first, &key); if (k == 0) break; if (k < 0) goto fail; '
                f'{" else ".join(arms)} drop_Str(&key); }} {need} {build} return true; fail: {drops} return false;')

    def parse_call(self, e):
        """float(s) / int(s) on a Str: reading a number from text, which can fail."""
        return (e.k == 'call' and e.fn.k == 'name' and e.fn.name in ('float', 'int') and len(e.args) == 1
                and not self.lookup(e.fn.name) and self.probe_type(e.args[0][1]) == STR)

    def not_shadowed(self, e):
        """Calling a function whose name a local variable has taken in this scope."""
        if e.k == 'call' and e.fn.k == 'name':
            v = self.lookup(e.fn.name)
            if v is not None and v.ty[0] not in ('fn', 'lfn') and (e.fn.name in BUILTINS or e.fn.name in self.fns or e.fn.name in self.gfns):
                err(e.line, f"'{e.fn.name}' is a variable here (line {ln(v.line)}), so the function {disp(e.fn.name)}() "
                            f"can't be called in this scope; rename the variable")

    def throwing_call(self, e):
        self.not_shadowed(e)
        if e.k == 'call' and self.fn_value_type(e) is not None:
            return self.fn_value_type(e)[3]
        if e.k == 'call' and e.fn.k == 'field' and e.fn.name in ('read', 'write', 'temp_dir'):
            return self.probe_type(e.fn.e) == FS
        if e.k == 'call' and e.fn.k == 'field' and e.fn.name == 'run':
            return self.probe_type(e.fn.e) == OS
        if e.k == 'call' and e.fn.k == 'field' and e.fn.name in NET_FAILS and self.probe_type(e.fn.e) == NET:
            return True
        if e.k == 'call' and e.fn.k == 'field' and e.fn.name == 'recv' and (self.probe_type(e.fn.e) or ('',))[0] == 'chan':
            return True
        if self.parse_call(e) or self.from_json_call(e):
            return True
        return (e.k == 'call' and e.fn.k == 'name' and
                ((e.fn.name in self.fns and self.fns[e.fn.name][2].throws) or
                 (e.fn.name in self.gfns and self.gfns[e.fn.name].throws)))

    def throw_code(self, call, expect=None):
        """Code for a call that can fail, as a result value (R_T) whose .bad says whether it failed."""
        if self.fn_value_type(call) is not None:
            return self.call_value(call, allow_throw=True)
        if call.fn.k == 'field' and call.fn.name == 'run':
            return self.os_call(call, handled=True)
        if call.fn.k == 'field' and call.fn.name in NET_FAILS and self.probe_type(call.fn.e) == NET:
            return self.net_call(call, handled=True)
        if call.fn.k == 'field' and call.fn.name == 'recv' and (self.probe_type(call.fn.e) or ('',))[0] == 'chan':
            return self.chan_method(call, handled=True)
        if call.fn.k == 'field':
            return self.fs_call(call, handled=True)
        if self.from_json_call(call):
            return self.b_from_json(call, [a for _, a in call.args], None, handled=True)
        if self.parse_call(call):
            t = FLOAT if call.fn.name == 'float' else INT
            if t == FLOAT:
                self.uses_float_parse = True
            rt = self.reg(('res', t))
            r = self.tmp()
            arg = call.args[0][1]
            if arg.k == 'slice' and self.probe_type(arg.e) == STR:
                # No temporary string: read the number from the slice's bytes in place.
                def use_s(c, _t, _p):
                    self.pure_index(arg.lo, arg.hi)
                    lo, _ = self.value(arg.lo, INT)
                    hi, _ = self.value(arg.hi, INT)
                    return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_parse_{call.fn.name}_at(&{c}, {lo}, {hi}, '
                            f'&{r}.val, &{r}.err, {call.line}); {r}; }})', rt)
                return self.with_borrow(arg.e, use_s)

            def use(c, _t, _p):
                return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_parse_{call.fn.name}(&{c}, &{r}.val, &{r}.err); '
                        f'{r}; }})', rt)
            return self.with_borrow(call.args[0][1], use)
        if call.fn.name in self.gfns:
            return self.call_user(call, self.gcall(call, expect), allow_throw=True)
        return self.call_user(call, call.fn.name, allow_throw=True)

    def g_orelse(self, e, expect):
        call = e.e
        if not self.throwing_call(call):
            err(e.line, "'else' after a value handles the error of a call to a function marked throws, "
                        "and this isn't one")
        code, rt = self.throw_code(call, expect)
        t, rv = rt[1], self.tmp()
        snap = self.snapshot()
        if e.jump is not None:
            # else return / break / continue / fail: on failure, free what's live and leave
            saved, saved_ind = self.lines, self.ind
            self.lines, self.ind = [], 0
            getattr(self, 's_' + e.jump.k)(e.jump)
            body = ' '.join(l.strip() for l in self.lines if not l.lstrip().startswith('#line'))
            self.lines, self.ind = saved, saved_ind
            self.restore(snap)
            if t == VOID:
                return f'({{ {self.ct(rt)} {rv} = {code}; if ({rv}.bad) {{ {self.drop_err(rt, rv)} {body} }} }})', VOID
            return f'({{ {self.ct(rt)} {rv} = {code}; if ({rv}.bad) {{ {self.drop_err(rt, rv)} {body} }} {rv}.val; }})', t
        d = e.d
        diverges = d.k == 'call' and d.fn.k == 'name' and d.fn.name in ('panic', 'exit')
        if t == VOID or diverges:
            dc, dt, _ = self.gen(d)
            if dt == VOID:
                dstmt = dc + ';'
            elif self.is_copy(dt):
                dstmt = f'(void){dc};'
            else:
                dv = self.tmp()
                dstmt = f'{{ {self.ct(dt)} {dv} = {dc}; {self.drop(dt, dv)} }}'
            self.merge([snap, self.snapshot()])
            if t == VOID:
                return f'({{ {self.ct(rt)} {rv} = {code}; if ({rv}.bad) {{ {self.drop_err(rt, rv)} {dstmt} }} }})', VOID
            return f'({{ {self.ct(rt)} {rv} = {code}; if ({rv}.bad) {{ {self.drop_err(rt, rv)} {dstmt} }} {rv}.val; }})', t
        dc, _ = self.value(d, t)
        self.merge([snap, self.snapshot()])
        tv = self.tmp()
        return (f'({{ {self.ct(rt)} {rv} = {code}; {self.ct(t)} {tv}; if ({rv}.bad) {{ {self.drop_err(rt, rv)} '
                f'{tv} = {dc}; }} else {tv} = {rv}.val; {tv}; }})'), t

    def g_call(self, e, expect):
        f = e.fn
        if self.fn_value_type(e) is not None:
            return self.call_value(e)
        if f.k == 'field':
            if f.name == 'push':
                return self.push(e)
            if f.name == 'reserve':
                return self.reserve(e)
            if f.name == 'pop':
                return self.pop(e)
            if f.name in STR_METHODS:
                return self.str_method(e)
            if f.name == 'sort':
                return self.sort_method(e)
            if f.name in ('run', 'env', 'clock', 'time', 'sleep'):
                return self.os_call(e)
            if f.name in NET_METHODS and self.probe_type(f.e) == NET:
                return self.net_call(e)
            if f.name in CHAN_METHODS and (self.probe_type(f.e) or ('',))[0] == 'chan':
                return self.chan_method(e)
            if f.name == 'temp_dir':
                return self.fs_call(e)
            if f.name in ('get', 'remove'):
                return self.map_method(e)
            if f.name in ('read', 'write'):
                return self.fs_call(e)
            rt = self.probe_type(f.e)
            if rt == STR:
                err(e.line, f'Str has no .{f.name}(); its methods are .split(), .join(items), .strip(), .lstrip(), '
                            f'.rstrip(), .startswith(prefix) and .endswith(suffix), and it has .len')
            if rt[0] == 'list':
                err(e.line, f'lists have .push(x), .pop(), .sort(), .reserve(n) and .len; there is no .{f.name}()')
            if rt[0] == 'map':
                err(e.line, f'maps have .get(key, default), .remove(key) and .len; there is no .{f.name}()')
            if rt[0] == 'struct' and (self.structs[rt[1]].field(f.name) or ('',))[0] == 'fn':
                return self.call_value(e)
            err(e.line, f'{tn(rt)} has no .{f.name}(): Vu has functions, not methods, so write {f.name}(x, ...)')
        if f.k != 'name':
            err(e.line, 'only named functions can be called')
        n = f.name
        if n in BUILTIN_TYPES:
            if n in ('Fs', 'Net', 'Os', 'Ffi'):
                err(e.line, f"a {n} can't be created: main receives it (fn main(fs: Fs, os: Os)) and passes it only "
                            f"to the functions that need it")
            err(e.line, {'Byte': 'convert with byte(x)', 'Int': 'convert with int(x)',
                         'Float': 'convert with float(x)', 'Str': 'make strings with "..." or str(bytes)',
                         'Bool': 'use true or false'}[n])
        if n in self.structs:
            return self.construct(e, n)
        if n in self.gtypes and self.gtypes[n].k == 'type':
            return self.construct(e, self.ginfer(e, n, [(f, ft) for f, ft, _, _ in self.gtypes[n].fields],
                                                 f'{disp(n)}(...)', expect))
        if n in self.gtypes:
            err(e.line, f"'{disp(n)}' is an enum type; use one of its variants")
        if n in self.exttypes:
            err(e.line, f"a {disp(n)} is a C handle: only the extern functions that return one can make it")
        if n in self.variants:
            return self.construct_variant(e, n, expect)
        self.not_shadowed(e)
        if self.lookup(n):
            err(e.line, f"'{n}' is a variable, not a function")
        if n == 'sorted':
            return self.b_sorted(e)
        if n in BUILTINS:
            if any(a[0] for a in e.args):
                err(e.line, f"{n}() doesn't take named arguments")
            return getattr(self, 'b_' + n)(e, [a for _, a in e.args], expect)
        if n in self.gfns:
            return self.call_user(e, self.gcall(e, expect))
        lam = self.lam
        while lam is not None:
            if lam.name == n:
                err(e.line, f"'{n}' can't call itself: a nested function isn't visible inside its own body; make it "
                            f"a top-level function to recurse")
            lam = lam.outer
        if n in self.fns:
            return self.call_user(e, n)
        if self.lookup(n):
            err(e.line, f"'{n}' is a variable, not a function")
        err(e.line, f"unknown function '{disp(n)}'")

    def construct(self, e, name):
        pre, inits = self.field_inits(e, name, self.structs[name].fields)
        lit = f'((T_{name}){{{", ".join(inits)}}})'
        if pre:
            lit = '({ ' + ' '.join(pre) + f' {lit}; }})'
        return lit, ('struct', name)

    def field_inits(self, e, name, fields):
        names = [f for f, _ in fields]
        ftypes = dict(fields)
        args = e.args
        if any(a[0] for a in args):
            if not all(a[0] for a in args):
                err(e.line, 'use either all named or all positional arguments')
            given = set()
            for nm, a in args:
                if nm not in ftypes:
                    err(a.line, f"{name} has no field '{nm}'")
                if nm in given:
                    err(a.line, f"field '{nm}' is given twice")
                given.add(nm)
            missing = [f for f in names if f not in given]
            if missing:
                err(e.line, f"missing field(s) for {name}: {', '.join(missing)}")
            ordered = list(args)
        else:
            if len(args) != len(names):
                err(e.line, f"{name} has {len(names)} field(s) ({', '.join(names)}) but got {len(args)} value(s)")
            ordered = [(f, a) for f, (_, a) in zip(names, args)]
        hoist = len(ordered) > 1 and any(self.effects(a) for _, a in ordered)
        pre, inits = [], []
        for fname, a in ordered:
            c, _ = self.value(a, ftypes[fname])
            if hoist:
                tv = self.tmp()
                pre.append(f'{self.ct(ftypes[fname])} {tv} = {c};')
                c = tv
            inits.append(f'.{cf(fname)} = {c}')
        return pre, inits

    def fs_call(self, e, handled=False):
        if not handled and e.fn.name in ('read', 'write', 'temp_dir') and self.probe_type(e.fn.e) == FS:
            err(e.line, f"fs.{e.fn.name}() can fail, so handle its error: fs.{e.fn.name}(...)? passes it on, "
                        f"fs.{e.fn.name}(...) else <default> replaces it, or match fs.{e.fn.name}(...): with "
                        f"ok(v) and err(e) arms")
        code, t, _ = self.gen(e.fn.e)
        if t != FS:
            err(e.line, f".{e.fn.name}() is a file operation: call it on the file-system capability "
                        f"(fs.{e.fn.name}(...)), which main receives as 'fs: Fs'")
        if any(nm for nm, _ in e.args):
            err(e.line, 'file operations take positional arguments')
        args = [a for _, a in e.args]
        if e.fn.name == 'temp_dir':
            if args:
                err(e.line, 'fs.temp_dir() takes no arguments')
            rt = self.reg(('res', STR))
            r = self.tmp()
            return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_fs_temp_dir({code}, &{r}.val, &{r}.err); '
                    f'{r}; }})', rt)
        if e.fn.name == 'read':
            if len(args) != 1:
                err(e.line, 'fs.read(path) takes one path')

            def use(c, pt, _p):
                if pt != STR:
                    err(e.line, f'a file path is a Str, not {tn(pt)}')
                rt = self.reg(('res', STR))
                r = self.tmp()
                return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_fs_read({code}, &{c}, &{r}.val, &{r}.err); '
                        f'{r}; }})', rt)
            return self.with_borrow(args[0], use)
        if len(args) != 2:
            err(e.line, 'fs.write(path, data) takes a path and a Str or [Byte]')

        def use_path(pc, pt, _p):
            if pt != STR:
                err(e.line, f'a file path is a Str, not {tn(pt)}')

            def use_data(dc, dt, _d):
                if dt != STR and dt != ('list', BYTE):
                    err(e.line, f'fs.write writes a Str or [Byte], not {tn(dt)}')
                rt = self.reg(('res', VOID))
                r = self.tmp()
                return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_fs_write({code}, &{pc}, ({dc}).data, '
                        f'({dc}).len, &{r}.err); {r}; }})', rt)
            return self.with_borrow(args[1], use_data)
        return self.with_borrow(args[0], use_path)

    def pop(self, e):
        """xs.pop(): remove the last element and return it (the caller owns it)."""
        if e.args:
            err(e.line, '.pop() takes no arguments')
        p = self.place(e.fn.e)
        if p is None or p.ty[0] != 'list':
            err(e.line, '.pop() works on a list stored in a variable')
        self.write_check(p, e.line)
        return f'vu_pop_{self.mg(p.ty)}(&{p.code}, {e.line})', p.ty[1]

    def str_method(self, e):
        """Python's string methods: s.split(), s.split(sep), sep.join(items), s.strip(), s.strip(chars),
        lstrip, rstrip, s.startswith(p), s.endswith(p)."""
        name = e.fn.name
        if any(nm for nm, _ in e.args):
            err(e.line, f'.{name}() takes positional arguments')
        args = [a for _, a in e.args]
        usage = {'split': 's.split() splits on whitespace; s.split(sep) splits on a Str separator',
                 'join': 'sep.join(items) joins a [Str] list with sep between the items',
                 'startswith': 's.startswith(prefix) takes one Str', 'endswith': 's.endswith(suffix) takes one Str'}
        usage['strip'] = usage['lstrip'] = usage['rstrip'] = (f's.{name}() removes whitespace; s.{name}(chars) '
                                                              f'removes any of the bytes in chars')
        optional = name in ('split', 'strip', 'lstrip', 'rstrip')
        if len(args) > 1 or (not args and not optional):
            err(e.line, usage[name])

        def on_recv(rc, rt, _p):
            if rt != STR:
                if name == 'join' and rt == ('list', STR):
                    err(e.line, 'join is called on the separator, as in Python: ", ".join(items)')
                err(e.line, f'.{name}() is a Str method; this is {tn(rt)}')
            if not args:
                if name == 'split':
                    return self.split_code(rc, 'NULL', e.line)
                return f'vu_strip(&({rc}), NULL, {int(name != "rstrip")}, {int(name != "lstrip")})', STR

            def on_arg(ac, at, _q):
                if name == 'join':
                    if at != ('list', STR):
                        err(e.line, f'join() takes a [Str] list, not {tn(at)}')
                    return f'vu_join(&({rc}), ({ac}).data, ({ac}).len)', STR
                if at != STR:
                    err(e.line, f'{usage[name]}, not {tn(at)}')
                if name == 'split':
                    return self.split_code(rc, f'&({ac})', e.line)
                if name in ('startswith', 'endswith'):
                    return f'vu_{name}(&({rc}), &({ac}))', BOOL
                return f'vu_strip(&({rc}), &({ac}), {int(name != "rstrip")}, {int(name != "lstrip")})', STR
            return self.with_borrow(args[0], on_arg)
        return self.with_borrow(e.fn.e, on_recv)

    def split_code(self, rc, sep, line):
        lt = self.reg(('list', STR))
        r, pos, piece = self.tmp(), self.tmp(), self.tmp()
        return (f'({{ {self.ct(lt)} {r} = {{0}}; int64_t {pos} = 0; vu_str {piece}; '
                f'while (vu_split_next(&({rc}), {sep}, &{pos}, &{piece}, {line})) vu_push_{self.mg(lt)}(&{r}, {piece}); '
                f'{r}; }})'), lt

    def reverse_arg(self, e, what):
        """The reverse: flag of sorted(xs, reverse: b) and xs.sort(reverse: b); '0' when it's left out."""
        rev = '0'
        for nm, a in e.args[1 if what == 'sorted' else 0:]:
            if nm != 'reverse':
                err(e.line, 'sorted(xs) takes a list, and optionally reverse: true')
            rev, rt = self.value(a, BOOL)
            if rt != BOOL:
                err(e.line, f'reverse: takes a Bool, not {tn(rt)}')
        return rev

    def sort_method(self, e):
        """xs.sort() and xs.sort(reverse: true): sort the list in place (stable)."""
        p = self.place(e.fn.e)
        if p is None or p.ty[0] != 'list':
            err(e.line, '.sort() works on a list stored in a variable; sorted(xs) returns a sorted copy of any list')
        if p.ty[1] not in SORT_FN:
            err(e.line, f'.sort() works on lists of Int, Float, Byte, Bool or Str, not {tn(p.ty)}')
        if len(e.args) > 1 or (e.args and e.args[0][0] != 'reverse'):
            err(e.line, 'sort() takes no arguments, or reverse: true')
        self.write_check(p, e.line)
        rev = self.reverse_arg(e, 'sort')
        return f'vu_sort_{SORT_FN[p.ty[1]]}(({p.code}).data, ({p.code}).len, {rev})', VOID

    def b_sorted(self, e):
        """sorted(xs) and sorted(xs, reverse: true): a sorted copy (stable); xs is unchanged."""
        if not e.args or e.args[0][0] or len(e.args) > 2:
            err(e.line, 'sorted(xs) takes a list, and optionally reverse: true')

        def use(c, t, _p):
            if t[0] != 'list' or t[1] not in SORT_FN:
                err(e.line, f'sorted() works on lists of Int, Float, Byte, Bool or Str, not {tn(t)}')
            rev = self.reverse_arg(e, 'sorted')
            r, i = self.tmp(), self.tmp()
            m, et = self.mg(t), self.ct(t[1])
            if t[1] == STR:
                fill = f'for (int64_t {i} = 0; {i} < ({c}).len; {i}++) {r}.data[{i}] = vu_str_dup(&({c}).data[{i}]);'
            else:
                fill = f'if (({c}).len) memcpy({r}.data, ({c}).data, (size_t)({c}).len * sizeof({et}));'
            return (f'({{ {self.ct(t)} {r} = {{0}}; vu_reserve_{m}(&{r}, ({c}).len, {e.line}); {fill} '
                    f'{r}.len = ({c}).len; vu_sort_{SORT_FN[t[1]]}({r}.data, {r}.len, {rev}); {r}; }})'), t
        return self.with_borrow(e.args[0][1], use)

    def os_call(self, e, handled=False):
        """os.run(args) -> Int (can fail), os.env(name) -> Str, os.clock() -> Float (monotonic seconds),
        os.time() -> Float (seconds since 1970, UTC), os.sleep(seconds)."""
        name = e.fn.name
        if not handled and name == 'run' and self.probe_type(e.fn.e) == OS:
            err(e.line, "os.run() can fail, so handle its error: os.run(...)? passes it on, "
                        "os.run(...) else <default> replaces it, or match os.run(...): with ok(v) and err(e) arms")
        code, t, _ = self.gen(e.fn.e)
        if t != OS:
            err(e.line, f".{name}() needs the operating-system capability (os.{name}(...)), which main "
                        f"receives as 'os: Os'")
        if any(nm for nm, _ in e.args):
            err(e.line, f'os.{name}() takes positional arguments')
        args = [a for _, a in e.args]
        if name in ('clock', 'time'):
            if args:
                err(e.line, f'os.{name}() takes no arguments')
            return f'vu_os_{name}({code})', FLOAT
        if len(args) != 1:
            err(e.line, f"os.{name}() takes one argument")
        if name == 'sleep':
            sc, _ = self.value(args[0], FLOAT)
            self.uses_tasks = True
            return f'vu_task_sleep({code}, {sc}, {e.line})', VOID
        if name == 'env':
            def use(c, t2, _p):
                if t2 != STR:
                    err(e.line, f'os.env(name) takes a Str, not {tn(t2)}')
                return f'vu_os_env({code}, &{c})', STR
            return self.with_borrow(args[0], use)

        def use_run(c, t2, _p):
            if t2 != ('list', STR):
                err(e.line, f'os.run(args) takes a [Str] list (the program, then its arguments), not {tn(t2)}')
            rt = self.reg(('res', INT))
            r = self.tmp()
            return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_os_run({code}, ({c}).data, ({c}).len, &{r}.val, '
                    f'&{r}.err); {r}; }})', rt)
        return self.with_borrow(args[0], use_run, self.reg(('list', STR)))

    def split_timeout(self, e, allowed, what):
        """The positional arguments of a call, and its timeout: argument (seconds) as a node or None."""
        args, timeout = [], None
        for nm, a in e.args:
            if nm is None:
                if timeout is not None:
                    err(a.line, f'{what}: the timeout comes last')
                args.append(a)
            elif nm == 'timeout' and allowed and timeout is None:
                timeout = a
            elif nm == 'timeout' and allowed:
                err(a.line, f'{what} takes one timeout')
            elif allowed:
                err(a.line, f"{what} takes 'timeout: seconds' as its only named argument, not '{nm}'")
            else:
                err(a.line, f'{what} takes positional arguments')
        return args, timeout

    def timeout_code(self, timeout):
        """C arguments (seconds, given) for a timeout node or None."""
        if timeout is None:
            return '0.0, false'
        c, _ = self.value(timeout, FLOAT)
        return f'{c}, true'

    def net_call(self, e, handled=False):
        """Each of these can fail: net.listen(port) -> Listener, net.accept(listener) -> Conn,
        net.connect(host, port) -> Conn, net.recv(conn) -> Str ("" once it's closed), net.send(conn, data).
        accept, connect, recv and send also take timeout: seconds. net.port(listener) -> Int."""
        name = e.fn.name
        if not handled and name in NET_FAILS:
            err(e.line, f"net.{name}() can fail, so handle its error: net.{name}(...)? passes it on, "
                        f"net.{name}(...) else <default> replaces it, or match net.{name}(...): with ok(v) and err(e) arms")
        code, _, _ = self.gen(e.fn.e)
        if name in ('tls_connect', 'tls_listen'):
            return self.tls_call(e, name, code)
        args, timeout = self.split_timeout(e, name in ('accept', 'connect', 'recv', 'send'), f'net.{name}()')
        want = {'listen': 1, 'accept': 1, 'connect': 2, 'recv': 1, 'send': 2, 'port': 1}[name]
        if len(args) != want:
            err(e.line, {'listen': 'net.listen(port) takes one port number (0 picks a free port)',
                         'accept': 'net.accept(listener) takes the Listener from net.listen',
                         'connect': 'net.connect(host, port) takes a host name or address and a port',
                         'recv': 'net.recv(conn) takes one connection',
                         'send': 'net.send(conn, data) takes a connection and a Str or [Byte]',
                         'port': 'net.port(listener) takes the Listener from net.listen'}[name])
        self.uses_tasks = True
        if name == 'listen':
            c, _ = self.value(args[0], INT)
            rt = self.reg(('res', LISTENER))
            r = self.tmp()
            return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_net_listen({code}, {c}, &{r}.val, &{r}.err, '
                    f'{e.line}); {r}; }})', rt)
        if name == 'connect':
            def use_host(hc, ht, _p):
                if ht != STR:
                    err(e.line, f'net.connect(host, port): the host is a Str, not {tn(ht)}')
                pc, _ = self.value(args[1], INT)
                rt = self.reg(('res', CONN))
                r = self.tmp()
                return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_net_connect({code}, &{hc}, {pc}, '
                        f'{self.timeout_code(timeout)}, &{r}.val, &{r}.err, {e.line}); {r}; }})', rt)
            return self.with_borrow(args[0], use_host)
        sock = CONN if name in ('recv', 'send') else LISTENER

        def use(sc, st, _p):
            if st != sock:
                err(e.line, f'net.{name}() takes a {tn(sock)}, not {tn(st)}')
            if name == 'port':
                return f'vu_net_port({code}, {sc})', INT
            if name == 'send':
                def use_data(dc, dt, _d):
                    if dt != STR and dt != ('list', BYTE):
                        err(e.line, f'net.send sends a Str or [Byte], not {tn(dt)}')
                    rt = self.reg(('res', VOID))
                    r = self.tmp()
                    return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_net_send({code}, {sc}, ({dc}).data, '
                            f'({dc}).len, {self.timeout_code(timeout)}, &{r}.err, {e.line}); {r}; }})', rt)
                return self.with_borrow(args[1], use_data)
            rt = self.reg(('res', CONN if name == 'accept' else STR))
            r = self.tmp()
            fn = 'vu_net_accept' if name == 'accept' else 'vu_net_recv'
            return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !{fn}({code}, {sc}, {self.timeout_code(timeout)}, '
                    f'&{r}.val, &{r}.err, {e.line}); {r}; }})', rt)
        return self.with_borrow(args[0], use, sock)

    def tls_call(self, e, name, code):
        """net.tls_connect(host, port, ca: pem, timeout: s) -> Conn and net.tls_listen(port, cert: pem, key: pem)
        -> Listener: TLS connections, used with recv and send like plain ones. Certificates are PEM text."""
        usage = {'tls_connect': 'net.tls_connect(host, port) takes a host name and a port, and optionally ca: '
                                '(PEM text of the certificates to trust instead of the system\'s) and timeout: seconds',
                 'tls_listen': 'net.tls_listen(port, cert: pem, key: pem) takes a port and the server\'s certificate '
                               'and private key as PEM text'}[name]
        allowed = ('ca', 'timeout') if name == 'tls_connect' else ('cert', 'key')
        args, named = [], {}
        for nm, a in e.args:
            if nm is None:
                if named:
                    err(a.line, f'net.{name}(): named arguments come last')
                args.append(a)
            elif nm not in allowed or nm in named:
                err(a.line, usage)
            else:
                named[nm] = a
        if len(args) != (2 if name == 'tls_connect' else 1) or (name == 'tls_listen' and len(named) != 2):
            err(e.line, usage)
        self.uses_tasks = True
        self.uses_tls = True
        if name == 'tls_listen':
            pc, _ = self.value(args[0], INT)

            def use_cert(cc, ctt, _p):
                if ctt != STR:
                    err(e.line, f'net.tls_listen(): cert is PEM text (a Str), not {tn(ctt)}')

                def use_key(kc, kt, _q):
                    if kt != STR:
                        err(e.line, f'net.tls_listen(): key is PEM text (a Str), not {tn(kt)}')
                    rt = self.reg(('res', LISTENER))
                    r = self.tmp()
                    return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_net_tls_listen({code}, {pc}, &{cc}, &{kc}, '
                            f'&{r}.val, &{r}.err, {e.line}); {r}; }})', rt)
                return self.with_borrow(named['key'], use_key)
            return self.with_borrow(named['cert'], use_cert)

        def use_host(hc, ht, _p):
            if ht != STR:
                err(e.line, f'net.tls_connect(host, port): the host is a Str, not {tn(ht)}')
            pc, _ = self.value(args[1], INT)

            def finish(cac):
                rt = self.reg(('res', CONN))
                r = self.tmp()
                return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_net_tls_connect({code}, &{hc}, {pc}, {cac}, '
                        f'{self.timeout_code(named.get("timeout"))}, &{r}.val, &{r}.err, {e.line}); {r}; }})', rt)
            if 'ca' not in named:
                return finish('NULL')

            def use_ca(cc, cat, _q):
                if cat != STR:
                    err(e.line, f'net.tls_connect(): ca is PEM text (a Str), not {tn(cat)}')
                return finish(f'&{cc}')
            return self.with_borrow(named['ca'], use_ca)
        return self.with_borrow(args[0], use_host)

    def chan_method(self, e, handled=False):
        """ch.send(v) (moves v in; waits while the channel is full), ch.recv() -> T (can fail: closed, or
        timeout: seconds passed), ch.close(), ch.share() -> another handle to the same channel."""
        name = e.fn.name
        if not handled and name == 'recv':
            err(e.line, "recv() can fail (the channel is closed, or the timeout passed), so handle its error: "
                        "ch.recv()? passes it on, ch.recv() else <default> replaces it, or match ch.recv(): "
                        "with ok(v) and err(e) arms")
        args, timeout = self.split_timeout(e, name == 'recv', f'.{name}()')
        if len(args) != (1 if name == 'send' else 0):
            err(e.line, {'send': '.send(value) takes one value', 'recv': '.recv() takes no value (only timeout:)',
                         'close': '.close() takes no arguments', 'share': '.share() takes no arguments'}[name])
        self.uses_tasks = True

        def use(cc, ct, _p):
            inner = ct[1]
            if name == 'send':
                vc, _ = self.value(args[0], inner)
                tv = self.tmp()
                return f'({{ {self.ct(inner)} {tv} = {vc}; vu_chan_send({cc}, &{tv}, {e.line}); }})', VOID
            if name == 'close':
                return f'vu_chan_close({cc}, {e.line})', VOID
            if name == 'share':
                return f'vu_chan_share({cc})', ct
            rt = self.reg(('res', inner))
            r = self.tmp()
            return (f'({{ {self.ct(rt)} {r} = {{0}}; {r}.bad = !vu_chan_recv({cc}, &{r}.val, '
                    f'{self.timeout_code(timeout)}, &{r}.err, {e.line}); {r}; }})', rt)
        return self.with_borrow(e.fn.e, use)

    def b_chan(self, e, args, expect):
        """chan(n): a new channel holding up to n values; its type comes from where it goes."""
        if expect is not None and expect[0] == 'opt':
            expect = expect[1]
        if expect is None or expect[0] != 'chan':
            err(e.line, "chan(n) makes a channel; say what it carries where it goes: let ch: Chan[Int] = chan(16)")
        self.nargs(e, args, 1, 'chan')
        n, _ = self.value(args[0], INT)
        self.uses_tasks = True
        inner = expect[1]
        drop = 'NULL' if self.is_copy(inner) else f'vu_cdrop_{self.mg(expect)}'
        return f'vu_chan_new({n}, sizeof({self.ct(inner)}), {drop}, {e.line})', expect

    def reserve(self, e):
        """s.reserve(n) / xs.reserve(n): make room for n more bytes or elements in one allocation."""
        if len(e.args) != 1 or e.args[0][0]:
            err(e.line, '.reserve takes one count: s.reserve(n)')
        p = self.place(e.fn.e)
        if p is None or (p.ty != STR and p.ty[0] != 'list'):
            err(e.line, '.reserve(n) works on a string or list stored in a variable')
        self.write_check(p, e.line)
        n, _ = self.value(e.args[0][1], INT)
        if p.ty == STR:
            return f'vu_str_reserve_n(&{p.code}, {n}, {e.line})', VOID
        return f'vu_reserve_{self.mg(p.ty)}(&{p.code}, {n}, {e.line})', VOID

    def push(self, e):
        if len(e.args) != 1 or e.args[0][0]:
            err(e.line, '.push takes one value')
        p = self.place(e.fn.e)
        if p is None:
            if self.computed_key(e.fn.e):
                err(e.line, "to change a map value, put the key in a variable first: let k = ...; m[k].push(...)")
            err(e.line, 'can only push to a list stored in a variable')
        if p.ty[0] != 'list':
            err(e.line, f'{tn(p.ty)} has no .push')
        self.write_check(p, e.line)
        c, _ = self.value(e.args[0][1], p.ty[1])
        tv = self.tmp()
        return f'({{ {self.ct(p.ty[1])} {tv} = {c}; vu_push_{self.mg(p.ty)}(&{p.code}, {tv}); }})', VOID

    def pure_index(self, *exprs):
        """Indexes are evaluated while other parts of the statement may point into the same list,
        so an index may not change any variable."""
        for x in exprs:
            if self.mutated_roots(x):
                err(x.line, "an index can't change variables (it passes '&' or calls .push); "
                            "compute it into a variable first")

    def walk_unhoisted(self, x):
        """walk, leaving out ? nodes already moved before the statement (they have run already)."""
        if isinstance(x, Node):
            if x.k == 'try' and id(x) in self.hoisted:
                return
            yield x
            for v in x.__dict__.values():
                yield from self.walk_unhoisted(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                yield from self.walk_unhoisted(v)

    def mutated_roots(self, e):
        """Variables that evaluating e may change: arguments marked '&' and lists given .push(...)."""
        out = set()
        for x in self.walk_unhoisted(e):
            target = None
            if x.k == 'ref':
                target = x.e
            elif x.k == 'call' and x.fn.k == 'field' and x.fn.name in ('push', 'remove', 'reserve', 'pop', 'sort'):
                target = x.fn.e
            while target is not None and target.k in ('field', 'index', 'slice'):
                target = target.e
            if target is not None and target.k == 'name':
                v = self.lookup(target.name)
                if v is not None:
                    out.add(v)
        return out

    def call_user(self, e, name, allow_throw=False, spawn_line=None):
        params, ret, node = self.fns[name]
        if node.throws:
            if not allow_throw:
                d = disp(name)
                err(e.line, f"{d}() can fail, so handle its error: {d}(...)? passes it on, "
                            f"{d}(...) else <default> replaces it, or match {d}(...): with ok(v) and err(e) arms")
            ret = self.res_of(name, ret)
        args = e.args
        if any(a[0] for a in args):
            err(e.line, 'named arguments are only used when creating a struct')
        if len(args) != len(params):
            plist = ', '.join(pn for pn, _, _, _, _ in params)
            err(e.line, f'{disp(name)}() takes {len(params)} argument(s) ({plist}) but got {len(args)}')
        pre, post, codes = self.call_args(e, params, [])
        if spawn_line is not None:
            return self.wrap(pre, f'vu_spawn_{name}({", ".join([str(spawn_line)] + codes)})', post, VOID)
        return self.wrap(pre, f'fn_{name}({", ".join(codes)})', post, ret)

    def call_args(self, e, params, roots):
        """The arguments of call e for params (name, type, var, line, own): (statements before the call,
        statements after it, the argument codes). roots: what the call already borrows (a function value
        it calls), as (variable, False, line)."""
        args = e.args
        roots = list(roots)
        by_ref = [(v, e.fn) for v, _, _ in roots]
        # A variable passed to an owned parameter is moved after the other arguments are evaluated
        # (so consume(items, items.len) works); to keep that order in C, such calls evaluate every
        # argument into a temporary first.
        moves_name = any(po and a.k == 'name' and pt not in SCALARS and pt[0] != 'cap'
                         for (_, pt, _, _, po), (_, a) in zip(params, args))
        hoist = len(args) > 1 and (moves_name or any(self.effects(a) for _, a in args))
        pre, post, codes, deferred = [], [], [], []
        for (pn, pt, pv, _, po), (_, a) in zip(params, args):
            if po:
                # An owned parameter: the argument is moved into the call (or copied, for a Str that's
                # used again, as with map keys), and the function frees it.
                if a.k == 'ref':
                    err(a.line, f"parameter '{pn}' takes ownership, so pass the value itself (no '&'); "
                                f"the argument is moved into the call")
                if pt in SCALARS or pt[0] == 'cap':
                    c, _ = self.value(a, pt)
                    cty = self.ct(pt)
                else:
                    keep = self.last_use(a) if pt == STR else None
                    if keep is not None and self.statement_mentions(a.name) > 1:
                        keep = None   # also used elsewhere in this statement: copy, don't move
                    code, t, p = self.gen(a, pt)
                    if t[0] == 'lfn':
                        self.lfn_escape(a.line)
                    if p is not None:
                        if t != pt:
                            err(a.line, f'expected {tn(pt)}, found {tn(t)}')
                        if pt[0] == 'chan':
                            c = f'vu_chan_share({p.code})'   # both keep using the channel
                        elif pt == STR and keep is None:
                            c = f'vu_str_dup(&{p.code})'
                        else:
                            deferred.append((len(codes), p, a.line, pt))
                            codes.append(None)
                            continue
                    else:
                        c, _ = self.coerce(code, t, pt, a.line)
                    cty = self.ct(pt)
            elif pv:
                if a.k != 'ref':
                    err(a.line, f"parameter '{pn}' is 'var', so mark the argument with '&' to show it may be modified")
                p = self.place(a.e)
                if p is None:
                    err(a.line, "'&' needs a variable, field, or list element")
                self.write_check(p, a.line)
                if p.ty != pt:
                    err(a.line, f'expected {tn(pt)}, found {tn(p.ty)}')
                roots.append((p.root, True, a.line))
                by_ref.append((getattr(p.root, 'base', p.root), a))
                c, cty = f'&{p.code}', self.ct(pt) + '*'
            elif a.k == 'ref':
                err(a.line, f"parameter '{pn}' is read-only, so its argument doesn't take '&'")
            elif pt in SCALARS or pt[0] == 'cap':
                c, _ = self.value(a, pt)
                cty = self.ct(pt)
            else:
                code, t, p = self.gen(a, pt)
                # a borrowing closure can be passed where a function value is borrowed
                lent = t[0] == 'lfn' and pt == ('fn',) + t[1:]
                if p is not None:
                    if t != pt and not lent:
                        err(a.line, f'expected {tn(pt)}, found {tn(t)}')
                    roots.append((p.root, False, a.line))
                    by_ref.append((getattr(p.root, 'base', p.root), a))
                    if self.by_value(pt):
                        c, cty = p.code, self.ct(pt)
                    else:
                        c, cty = f'&{p.code}', self.ct(pt) + '*'
                else:
                    if lent:
                        # it points at variables: they're borrowed by this call like an argument is
                        for v in self.lam_caps.get(id(a), []):
                            roots.append((v, False, a.line))
                            by_ref.append((v, a))
                    else:
                        code, _ = self.coerce(code, t, pt, a.line)
                    tv = self.tmp()
                    pre.append(f'{self.ct(pt)} {tv} = {code};')
                    if not self.is_copy(pt) and not lent:
                        post.append(self.drop(pt, tv))
                    codes.append(tv if self.by_value(pt) else f'&{tv}')
                    continue
            if hoist:
                tv = self.tmp()
                pre.append(f'{cty} {tv} = {c};')
                c = tv
            codes.append(c)
        for i, p, line, pt in deferred:
            self.read_check(p, line)   # another argument may have moved it meanwhile
            c = self.move(p, line)
            if hoist:
                tv = self.tmp()
                pre.append(f'{self.ct(pt)} {tv} = {c};')
                c = tv
            codes[i] = c
        for v, mut, line in roots:
            if mut and sum(1 for r, _, _ in roots if r is v) > 1:
                err(line, f"'{v.name}' is passed with '&' and also in another argument of the same call; "
                          f"a 'var' argument needs exclusive access")
        # An argument passed by reference points into its variable while the remaining arguments are
        # evaluated, so none of them may change that variable (e.g. show(xs[0], grow(&xs))).
        for v, a in by_ref:
            if v.state != 'no':
                err(a.line, f"'{v.name}' is borrowed by one argument of this call and moved by another")
            for _, other in args:
                if other is not a and v in self.mutated_roots(other):
                    err(other.line, f"'{v.name}' is borrowed by one argument of this call while another argument "
                                    f"changes it; compute that argument into a variable first")
        return pre, post, codes

    def fn_value_type(self, e):
        """The function type of what call e calls, when that's a function value (a variable, a field, an
        element or a call's result), else None."""
        f = e.fn
        if f.k == 'name':
            v = self.lookup(f.name)
            return v.ty if v is not None and v.ty[0] in ('fn', 'lfn') else None
        if f.k == 'lambda':
            return ('fn', None, None, f.throws)
        if f.k in ('field', 'index', 'call'):
            t = self.static_type(f)
            return t if t is not None and t[0] in ('fn', 'lfn') else None
        return None

    def call_value(self, e, allow_throw=False):
        """A call through a function value: vu_call_<type>(f, args...)."""
        f = e.fn
        code, ft, p = self.gen(f)
        if ft[0] not in ('fn', 'lfn'):
            err(e.line, f"a {tn(ft)} can't be called")
        _, ptys, ret, throws = ft
        what = f"'{f.name}'" if f.k == 'name' else 'this function value'
        rt = ret
        if throws:
            if not allow_throw:
                err(e.line, f"{what} can fail, so handle its error: (...)? passes it on, (...) else <default> "
                            f"replaces it, or match with ok(v) and err(e) arms")
            rt = self.reg(('res', ret))
        if any(a[0] for a in e.args):
            err(e.line, 'named arguments are only used when creating a struct')
        if len(e.args) != len(ptys):
            err(e.line, f'{what} takes {len(ptys)} argument(s) but got {len(e.args)}')
        params = [(f'#{i + 1}', pt, False, e.line, False) for i, pt in enumerate(ptys)]
        pre, post, codes = self.call_args(e, params, [] if p is None else [(p.root, False, f.line)])
        if p is None:
            # a temporary (make_adder(2)(3)): kept while the call runs, then freed
            tv = self.tmp()
            pre.insert(0, f'vu_fn {tv} = {code};')
            if ft[0] == 'fn':
                post.append(f'vu_fn_drop(&{tv});')
            code = tv
        return self.wrap(pre, f'vu_call_{self.mg(ft)}({", ".join([code] + codes)})', post, rt)

    # ---- built-ins
    def nargs(self, e, args, n, name):
        if len(args) != n:
            err(e.line, f'{name}() takes {n} argument(s)')

    def fmt_parts(self, e, args, name):
        if len(args) != 1 or args[0].k != 'str':
            err(e.line, f'{name}() takes one string, e.g. {name}("x = {{x}}")')
        parts = args[0].parts
        exprs = [p for p in parts if not isinstance(p, str)]
        hoist = len(exprs) > 1 and any(self.effects(x) for x, _ in exprs)  # keep left-to-right order
        fmt, vals, pre = [], [], []
        for p in parts:
            if isinstance(p, str):
                fmt.append(p.replace('%', '%%'))
                continue
            x, spec = p
            f1, c = self.fmt_one(x, spec)
            fmt.append(f1)
            cty = {'d': 'long long', 'x': 'unsigned long long', 'f': 'double', 'g': 'double', 's': 'const char *'}[f1[-1]]
            if hoist:
                tv = self.tmp()
                pre.append(f'{cty} {tv} = {c};')
                c = tv
            vals.append(c)
        return ''.join(fmt), vals, pre

    def fmt_one(self, x, spec):
        """printf conversion and argument for one interpolated number or Bool."""
        zero, width, prec, hexa = spec
        c, t, _ = self.gen(x)
        if t not in INTEGERS and hexa:
            err(x.line, "':x' (hexadecimal) only applies to Int and Byte values")
        if t in INTEGERS:
            if prec is not None:
                err(x.line, 'precision (:.N) only applies to Float values')
            if hexa:
                return f'%{zero}{width}llx', f'(unsigned long long)({c})'
            return f'%{zero}{width}lld', f'(long long)({c})'
        if t == FLOAT:
            if prec is not None:
                return f'%{zero}{width}.{prec}f', f'vu_nan_plain({c})'
            return f'%{width}s', f'vu_shortest({c}, (char[40]){{0}})'
        if t == BOOL:
            return f'%{width}s', f'(({c}) ? "true" : "false")'
        err(x.line, f'only numbers, Bool and Str can be put in a string, not {tn(t)}')

    def has_str_parts(self, s):
        return any(not isinstance(p, str) and self.probe_type(p[0]) == STR for p in s.parts)

    def b_print(self, e, args, expect):
        self.nargs(e, args, 1, 'print')
        plain = args[0].k == 'str' and not any(isinstance(x, str) and '\0' in x for x in args[0].parts)
        if plain and not self.has_str_parts(args[0]):
            fmt, vals, pre = self.fmt_parts(e, args, 'print')
            return self.wrap(pre, f'printf({cstr(fmt + chr(10))}{"".join(", " + v for v in vals)})', [], VOID)

        def use(c, t, p):
            if t != STR:
                err(e.line, f'print() takes a string; to show a {tn(t)} x, write print("{{x}}")')
            return f'(vu_write(({c}).data, ({c}).len), putchar(10))', VOID
        return self.with_borrow(args[0], use)

    def b_write(self, e, args, expect):
        self.nargs(e, args, 1, 'write')

        def use(c, t, p):
            if t != STR and t != ('list', BYTE):
                err(e.line, f'write() outputs a Str or [Byte] exactly as is, not {tn(t)}')
            return f'vu_write(({c}).data, ({c}).len)', VOID
        return self.with_borrow(args[0], use)

    def b_panic(self, e, args, expect):
        self.nargs(e, args, 1, 'panic')
        if args[0].k == 'str' and not self.has_str_parts(args[0]):
            fmt, vals, pre = self.fmt_parts(e, args, 'panic')
            return self.wrap(pre, f'vu_fail({e.line}, {cstr(fmt)}{"".join(", " + v for v in vals)})', [], VOID)

        def use(c, t, p):
            if t != STR:
                err(e.line, 'panic() takes a string message')
            # The message's bytes go to the reporter as they are (printf's %s would stop at a zero byte).
            return f'vu_panic({e.line}, (const char *)({c}).data, ({c}).len)', VOID
        return self.with_borrow(args[0], use)

    def b_str(self, e, args, expect):
        self.nargs(e, args, 1, 'str')

        def use(c, t, p):
            if t != ('list', BYTE):
                err(e.line, f'str() makes a Str from a [Byte] list; put other values in a string with "{{x}}"')
            tv = self.tmp()
            return f'({{ vu_str {tv} = {{0}}; vu_str_cat_bytes(&{tv}, ({c}).data, ({c}).len); {tv}; }})', STR
        return self.with_borrow(args[0], use, self.reg(('list', BYTE)))

    def b_bytes(self, e, args, expect):
        self.nargs(e, args, 1, 'bytes')
        lt = self.reg(('list', BYTE))

        def use(c, t, p):
            if t != STR:
                err(e.line, f'bytes() copies a Str into a [Byte] list, not a {tn(t)}')
            tv = self.tmp()
            return (f'({{ L_Byte {tv} = {{0}}; if (({c}).len) {{ {tv}.data = (uint8_t *)vu_malloc((size_t)({c}).len); '
                    f'memcpy({tv}.data, ({c}).data, (size_t)({c}).len); {tv}.len = {tv}.cap = ({c}).len; }} {tv}; }})'), lt
        return self.with_borrow(args[0], use)

    def b_byte(self, e, args, expect):
        self.nargs(e, args, 1, 'byte')
        c, t = self.value(args[0])
        if t == BYTE:
            return c, BYTE
        if t != INT:
            err(e.line, f'byte() converts an Int, not a {tn(t)}')
        return f'vu_byte({c}, {e.line})', BYTE

    def b_exit(self, e, args, expect):
        self.nargs(e, args, 1, 'exit')
        c, _ = self.value(args[0], INT)
        return f'vu_exit({c})', VOID

    def b_eprint(self, e, args, expect):
        self.nargs(e, args, 1, 'eprint')

        def use(c, t, p):
            if t != STR:
                err(e.line, f'eprint() takes a string; to show a {tn(t)} x, write eprint("{{x}}")')
            return f'vu_eprint(({c}).data, ({c}).len)', VOID
        return self.with_borrow(args[0], use)

    def b_swap(self, e, args, expect):
        """swap(&a, &b): exchange two values of the same type. Both need write access, and they must be
        different variables (two parts of one variable could overlap)."""
        self.nargs(e, args, 2, 'swap')
        places = []
        for a in args:
            if a.k != 'ref':
                err(a.line, "swap() changes both values, so mark each argument with '&': swap(&a, &b)")
            p = self.place(a.e)
            if p is None:
                err(a.line, "'&' needs a variable, field, or list element")
            self.write_check(p, a.line)
            places.append(p)
        pa, pb = places
        if pa.root is pb.root or getattr(pa.root, 'base', pa.root) is getattr(pb.root, 'base', pb.root):
            err(e.line, f"swap() needs two different variables; both of these are part of '{pa.root.name}'")
        if pa.ty != pb.ty:
            err(e.line, f"swap() needs two values of the same type, not {tn(pa.ty)} and {tn(pb.ty)}")
        x, y, tv = self.tmp(), self.tmp(), self.tmp()
        ty = self.ct(pa.ty)
        return f'({{ {ty} *{x} = &{pa.code}; {ty} *{y} = &{pb.code}; {ty} {tv} = *{x}; *{x} = *{y}; *{y} = {tv}; }})', VOID

    def b_args(self, e, args, expect):
        self.nargs(e, args, 0, 'args')
        lt = self.reg(('list', STR))
        tv = self.tmp()
        return (f'({{ L_Str {tv} = {{0}}; for (int i = 0; i < vu_argc; i++) vu_push_L_Str(&{tv}, '
                f'vu_str_from_c(vu_argv[i])); {tv}; }})', lt)

    def b_sqrt(self, e, args, expect):
        self.nargs(e, args, 1, 'sqrt')
        c, _ = self.value(args[0], FLOAT)
        return f'sqrt({c})', FLOAT

    def b_float(self, e, args, expect):
        self.nargs(e, args, 1, 'float')
        if self.parse_call(e):
            err(e.line, 'float(s) reads a number from text, which can fail, so handle its error: float(s)? passes it '
                        'on, float(s) else <default> replaces it, or match float(s): with ok(v) and err(e) arms')
        c, t = self.value(args[0])
        if t not in INTEGERS:
            err(e.line, f'float() converts an Int or Byte, not a {tn(t)}')
        return f'((double)({c}))', FLOAT

    def b_int(self, e, args, expect):
        self.nargs(e, args, 1, 'int')
        if self.parse_call(e):
            err(e.line, 'int(s) reads a number from text, which can fail, so handle its error: int(s)? passes it '
                        'on, int(s) else <default> replaces it, or match int(s): with ok(v) and err(e) arms')
        c, t = self.value(args[0])
        if t == FLOAT:
            return f'vu_ftoi({c}, {e.line})', INT
        if t not in INTEGERS:
            err(e.line, f'int() converts a Float or Byte, not a {tn(t)}')
        return f'((int64_t)({c}))', INT

    def b_abs(self, e, args, expect):
        self.nargs(e, args, 1, 'abs')
        c, t = self.value(args[0])
        if t not in (INT, FLOAT):
            err(e.line, f'abs() needs an Int or Float, not {tn(t)}')
        return (f'vu_iabs({c}, {e.line})' if t == INT else f'fabs({c})'), t

    def minmax(self, e, args, which):
        if len(args) == 1:
            return self.minmax_list(e, args[0], which)
        if len(args) > 2:
            # min(a, b, c, ...) is min(min(a, b), c)...: left to right, like Python
            inner = Node('call', e.line, fn=e.fn, args=[(None, args[0]), (None, args[1])])
            self.keep.append(inner)   # types are cached by id(node): keep it alive so no id is reused
            for a in args[2:-1]:
                inner = Node('call', e.line, fn=e.fn, args=[(None, inner), (None, a)])
                self.keep.append(inner)
            return self.minmax(e, [inner, args[-1]], which)
        if not args:
            err(e.line, f'{which}() takes two or more numbers, or one list')
        l, lt, r, rt = self.operands(args[0], args[1])
        if lt != rt or lt not in (INT, FLOAT, BYTE):
            err(e.line, f'{which}() needs two numbers of the same type')
        pre = []
        if self.effects(args[0]) or self.effects(args[1]):
            a, b = self.tmp(), self.tmp()
            pre = [f'{self.ct(lt)} {a} = {l};', f'{self.ct(lt)} {b} = {r};']
            l, r = a, b
        call = f'vu_{"f" if lt == FLOAT else "i"}{which}({l}, {r})'
        return self.wrap(pre, f'((uint8_t){call})' if lt == BYTE else call, [], lt)

    def minmax_list(self, e, arg, which):
        """min(xs) / max(xs): the smallest (largest) element; an empty list stops the program."""
        def use(c, t, _p):
            if t[0] != 'list' or t[1] not in SORT_FN or t[1] == BOOL:
                err(e.line, f'{which}() takes two or more numbers, or one list of Int, Float, Byte or Str; '
                            f'not {tn(t)}')
            pick = f'vu_pick_{SORT_FN[t[1]]}(({c}).data, ({c}).len, {int(which == "max")}, {e.line})'
            if t[1] == STR:
                return f'vu_str_dup(&({c}).data[{pick}])', STR
            return f'({c}).data[{pick}]', t[1]
        return self.with_borrow(arg, use)

    def b_min(self, e, args, expect):
        return self.minmax(e, args, 'min')

    def b_max(self, e, args, expect):
        return self.minmax(e, args, 'max')

    def b_arg(self, e, args, expect):
        self.nargs(e, args, 2, 'arg')
        i, _ = self.value(args[0], INT)
        if self.probe_type(args[1]) == STR:
            d, _ = self.value(args[1], STR)
            return f'vu_arg_str({i}, {d})', STR
        d, _ = self.value(args[1], INT)
        return f'vu_arg({i}, {d}, {e.line})', INT

    # ---- statements (each returns True if control never falls through)
    def block(self, stmts, loop=False, setup=None):
        self.scopes.append(Scope(loop))
        if setup:
            setup()
        div = self.stmts(stmts)
        if not div:
            self.emit_drops([self.scopes[-1]])
        sc = self.scopes.pop()
        for v in reversed(sc.unfreeze):
            v.frozen.pop()
        return div

    def stmts(self, stmts):
        div = False
        self.rest.append([stmts, 0, None])
        for i, st in enumerate(stmts):
            if div:
                err(st.line, 'unreachable code (the code before it always returns, breaks, or continues)')
            self.rest[-1][1] = i
            # VU_AT records the line for panic backtraces (quick builds only; nothing in optimized
            # builds). A par loop body runs on several threads at once, so it doesn't write the frame.
            outer = self.src_line
            self.src_line = st.line
            if not self.par:
                self.emit(f'VU_AT({st.line});')
            self.hoist_tries(st)
            div = getattr(self, 's_' + st.k)(st)
            self.src_line = outer
        self.rest.pop()
        return div

    def last_use(self, e):
        """Is e a Str variable owned by this block and never mentioned again in it? Then it can be moved
        instead of copied. If this is ever wrong, the variable is marked moved, so a later use is a
        compile error, never a memory error."""
        if e.k != 'name' or not self.rest:
            return None
        v = self.lookup(e.name)
        if (v is None or v.kind != 'local' or v.ty != STR or v.state != 'no' or v.frozen
                or self.scopes[-1].vars.get(v.name) is not v):
            return None
        block = self.rest[-1]
        if block[2] is None:
            # One pass over the block: the last statement each name appears in. (Rescanning the rest of
            # the block at every insert made compile time quadratic.)
            last = {}
            for i, st in enumerate(block[0]):
                for x in self.walk(st):
                    if x.k == 'name':
                        last[x.name] = i
            block[2] = last
        if block[2].get(v.name, -1) > block[1]:
            return None
        return v

    def hoist_tries(self, st):
        """`?` inside an expression (items.push(value(&p)?)): each one becomes a hidden `let` just before
        the statement, in the order they're written, and the expression uses that variable. Nothing the
        statement evaluates before a ? may change anything, or moving the ? first would reorder it."""
        found, effect = [], [False]

        def refuse(e, where):
            for x in self.walk(e):
                if x.k == 'try':
                    err(x.line, f"'?' can't be used {where}")

        def walk(e, top=False):
            if not isinstance(e, Node):
                if isinstance(e, (list, tuple)):
                    for x in e:
                        walk(x)
                return
            if e.k == 'lambda':
                return   # its ? run when it's called, inside its own function
            if e.k == 'try':
                # what its call evaluates first: the receiver and the arguments (not the call itself)
                if e.e.k == 'call':
                    walk(e.e.fn)
                    for _, a in e.e.args:
                        walk(a)
                else:
                    walk(e.e)
                if top:
                    return
                if effect[0]:
                    err(e.line, "this '?' is inside an expression that already did something before it (a call "
                                "to its left); move that part to its own statement first")
                found.append(e)   # (all of them are moved first, in order, so they don't block each other)
                return
            if e.k == 'bin' and e.op in ('and', 'or'):
                walk(e.l)
                refuse(e.r, f"on the right of '{e.op}' (it would run even when '{e.op}' skips that side); "
                            f"use an if instead")
                return
            if e.k == 'orelse':
                walk(e.e, top)
                if e.d is not None:
                    refuse(e.d, "in an 'else' fallback (it would run even when the fallback isn't needed)")
                elif e.jump.k in ('return', 'fail') and e.jump.expr is not None:
                    refuse(e.jump.expr, f"in an 'else {e.jump.k}' value (it would run even when the call succeeds)")
                return
            if e.k == 'call':
                walk(e.fn)
                for _, a in e.args:
                    walk(a)
                if not (e.fn.k == 'name' and e.fn.name in PURE_BUILTINS):
                    effect[0] = True
                return
            for v in list(e.__dict__.values()):
                walk(v)

        k = st.k
        if k in ('let', 'exprstmt', 'return', 'fail', 'spawn'):
            walk(st.expr, True)
        elif k == 'assign':
            walk(st.expr, True)   # the value is computed before the target's index
            walk(st.target)
        elif k == 'if':
            walk(st.cond)
        elif k == 'while':
            refuse(st.cond, "in a while condition, which runs again on every pass; write 'while true:', then "
                            "'let c = ...?' and 'if not c: break' inside")
        elif k == 'range':
            walk(st.start)
            walk(st.end)
            walk(st.step)
        elif k == 'each':
            walk(st.seq)
        elif k == 'match':
            walk(st.subj)
        # Inner ones come first (an outer ?'s call then reads the inner one's variable).
        for t in found:
            self.ntry += 1
            name = f'$t{self.ntry}'
            h = Node('let', t.line, name=name, mut=False, ty=None, expr=t)
            self.keep.append(h)
            self.s_let(h)
            self.hoisted[id(t)] = name

    def statement_mentions(self, name):
        """How many times the statement being generated mentions name."""
        block = self.rest[-1]
        return sum(1 for x in self.walk(block[0][block[1]]) if x.k == 'name' and x.name == name)

    def stmt_value(self, e, expect=None):
        """The value of a whole statement right-hand side. Handles f(x)?: if the call fails, every live
        value is freed and the error is returned to this function's caller."""
        if e.k != 'try':
            return self.value(e, expect)
        call = e.e
        if not self.throwing_call(call):
            err(e.line, "'?' passes on the error of a call to a function marked throws, and this isn't one")
        if not self.throws:
            err(e.line, "'?' can only be used inside a function marked throws; here, handle the error with "
                        "'else' or with match ... ok(v): / err(e):")
        if self.par:
            err(e.line, f"'?' would leave the par loop on line {ln(self.par['line'])} early; handle the error with "
                        f"'else' or match instead")
        code, rt = self.throw_code(call, expect)
        mine = self.rett[2] if len(self.rett) == 3 else None
        theirs = rt[2] if len(rt) == 3 else None
        if mine is not None and theirs != mine:
            what = f'{tn(theirs)} values' if theirs else 'a message'
            err(e.line, f"this call fails with {what}, but this function fails with {tn(mine)} values; handle "
                        f"its error with else or match (and fail with a {tn(mine)})")
        rv = self.tmp()
        self.emit(f'{self.ct(rt)} {rv} = {code};')
        self.open(f'if ({rv}.bad) {{')
        self.emit_drops(self.scopes)
        if mine is not None:
            self.emit(f'return ({self.ct(self.rett)}){{.bad = 1, .err = {rv}.err, .eval = {rv}.eval}};')
        else:
            if theirs is not None and not self.is_copy(theirs):
                self.emit(self.drop(theirs, f'{rv}.eval'))   # passed on as its message only
            self.emit(f'return ({self.ct(self.rett)}){{.bad = 1, .err = {rv}.err}};')
        self.close()
        if rt[1] == VOID:
            return None, VOID
        return self.coerce(f'{rv}.val', rt[1], expect, e.line)

    def s_fail(self, n):
        if not self.throws:
            err(n.line, "only a function marked throws can fail; mark it (fn f() -> T throws:) or use panic(...)")
        if self.par:
            err(n.line, f"'fail' can't leave the par loop on line {ln(self.par['line'])} early")
        if len(self.rett) == 3:
            et = self.rett[2]
            if self.probe_type(n.expr) == STR:
                err(n.line, f"this function fails with {tn(et)} values (throws {tn(et)}), so fail with one, "
                            f"like: fail {self.enums[et[1]].variants[0][0]}" + ('(...)' if self.enums[et[1]].variants[0][1] else ''))
            c, _ = self.value(n.expr, et)
            ev = self.tmp()
            self.open('{')
            self.emit(f'{self.ct(et)} {ev} = {c};')
            self.emit_drops(self.scopes)
            self.emit(f'return ({self.ct(self.rett)}){{.bad = 1, .err = vu_etext_{et[1]}(&{ev}), .eval = {ev}}};')
            self.close()
            return True
        if (self.probe_type(n.expr) or ('',))[0] == 'enum':
            et = self.probe_type(n.expr)
            err(n.line, f"to fail with {tn(et)} values, declare the function 'throws {tn(et)}'; "
                        f"a plain 'throws' fails with a message (Str)")
        c, _ = self.value(n.expr, STR)
        ev = self.tmp()
        self.open('{')
        self.emit(f'vu_str {ev} = {c};')
        self.emit_drops(self.scopes)
        self.emit(f'return ({self.ct(self.rett)}){{.bad = 1, .err = {ev}}};')
        self.close()
        return True

    def s_match(self, n):
        if self.throwing_call(n.subj):
            return self.match_result(n)
        self.open('{')
        self.scopes.append(Scope())
        code, t, p = self.gen(n.subj)
        if t[0] != 'enum':
            err(n.line, f"match works on enum values and on calls that can fail, not on {tn(t)}")
        info = self.enums[t[1]]
        sp = self.tmp()
        if p is None:
            hv = Var('$', t, self.tmp(), 'local', False, False, n.line)
            self.emit(f'{self.ct(t)} {hv.cname} = {code};')
            self.scopes[-1].order.append(hv)
            self.emit(f'{self.ct(t)} *{sp} = &{hv.cname};')
        else:
            if n.mut:
                self.write_check(p, n.line)
            self.emit(f'{self.ct(t)} *{sp} = &{p.code};')
        # An arm names a variant of the matched enum, so in another module's enum (geo__Shape) the arm
        # Circle means geo__Circle.
        # A qualified arm (geo.Circle) names the module itself.
        prefix = module_prefix(self.template_of(t[1]))
        n_arms = [(pn if pn == '_' else pn.replace('.', '__') if '.' in pn else prefix + pn, b, bd, l, pn)
                  for pn, b, bd, l in n.arms]
        seen, default = {}, None
        for pname, binds, body, line, written in n_arms:
            if pname == '_':
                if binds is not None:
                    err(line, "'_' matches anything and takes no names")
                if default:
                    err(line, f"'_' is already used on line {ln(default[1])}")
                default = (body, line)
                continue
            if self.variants.get(pname) != self.template_of(t[1]):
                names = ', '.join(v[len(prefix):] for v, _ in info.variants)
                err(line, f"{written} is not a variant of {disp(t[1])} (its variants are: {names})")
            if pname in seen:
                err(line, f"{written} is matched twice (also on line {ln(seen[pname])})")
            seen[pname] = line
            fields = info.fields_of(pname)
            if binds is not None and len(binds) != len(fields):
                err(line, f"{written} holds {len(fields)} value(s), so write {written}(...) "
                          f"with {len(fields)} name(s) "
                          f"(use _ for one you don't need)")
        missing = [v[len(prefix):] for v, _ in info.variants if v not in seen]
        if missing and not default:
            err(n.line, f"match doesn't handle {', '.join(missing)}; add an arm for each, or a '_' arm")
        if default and not missing:
            err(default[1], "every variant already has an arm, so '_' would never run")
        if p is not None:
            p.root.frozen.append(('lock' if n.mut else 'read', n.line))
        snap, ends = self.snapshot(), []
        arms = [a for a in n_arms if a[0] != '_']
        for idx, (pname, binds, body, line, _) in enumerate(arms):
            k = info.index(pname)
            last = idx == len(arms) - 1 and not default
            if idx == 0:
                self.open('{' if last else f'if ({sp}->tag == {k}) {{')
            else:
                self.open('else {' if last else f'else if ({sp}->tag == {k}) {{')

            def setup(binds=binds, k=k, line=line, fields=info.fields_of(pname)):
                for b, (fname, ftype) in zip(binds or [], fields):
                    if b == '_':
                        continue
                    v = Var(b, ftype, self.var_cname(b), 'ref', n.mut, True, line)
                    self.declare(v)
                    self.emit(f'{self.ct(ftype)} *{v.cname} = &{self.payload(t[1], k, sp)}{cf(fname)};')
            if not self.block(body, setup=setup):
                ends.append(self.snapshot())
            self.restore(snap)
            self.close()
        if default:
            self.open('else {' if arms else '{')
            if not self.block(default[0]):
                ends.append(self.snapshot())
            self.restore(snap)
            self.close()
        if p is not None:
            p.root.frozen.pop()
        sc = self.scopes.pop()
        self.emit_drops([sc])
        self.close()
        if not ends:
            return True
        self.merge(ends)
        return False

    def match_result(self, n):
        """match f(x): with ok(v) and err(e) arms, for a call to a function that can fail."""
        call = n.subj
        self.open('{')
        self.scopes.append(Scope())
        code, rt = self.throw_code(call)
        hv = Var('$', rt, self.tmp(), 'local', False, False, n.line)
        self.emit(f'{self.ct(rt)} {hv.cname} = {code};')
        self.scopes[-1].order.append(hv)
        t = rt[1]
        arms = {}
        for pname, binds, body, line in n.arms:
            if pname not in ('ok', 'err', '_'):
                err(line, f"a call that can fail is matched with ok(value) and err(message) arms, not {pname}")
            if pname in arms:
                err(line, f"'{pname}' is matched twice")
            want = 0 if (pname == '_' or (pname == 'ok' and t == VOID)) else 1
            if len(binds or []) > want:
                err(line, f"'{pname}' takes {want} name(s)")
            arms[pname] = (binds or [], body, line)
        if '_' in arms and 'ok' in arms and 'err' in arms:
            err(arms['_'][2], "ok and err are both handled, so '_' would never run")
        if '_' not in arms and not ('ok' in arms and 'err' in arms):
            err(n.line, "handle both ok(value) and err(message), or add a '_' arm")
        snap, ends = self.snapshot(), []
        for which, cond in (('ok', f'!{hv.cname}.bad'), ('err', f'{hv.cname}.bad')):
            binds, body, line = arms.get(which) or arms['_']
            self.open(f'if ({cond}) {{' if which == 'ok' else 'else {')

            def setup(binds=binds, which=which, line=line):
                for b in binds:
                    if b == '_':
                        continue
                    if which == 'ok':
                        ty, field = t, 'val'
                    elif len(rt) == 3:
                        ty, field = rt[2], 'eval'   # throws E: the error value itself
                    else:
                        ty, field = STR, 'err'
                    v = Var(b, ty, self.var_cname(b), 'ref', False, True, line)
                    self.declare(v)
                    self.emit(f'{self.ct(ty)} *{v.cname} = &{hv.cname}.{field};')
            if not self.block(body, setup=setup):
                ends.append(self.snapshot())
            self.restore(snap)
            self.close()
        sc = self.scopes.pop()
        self.emit_drops([sc])
        self.close()
        if not ends:
            return True
        self.merge(ends)
        return False

    def s_let(self, n):
        ty = self.resolve(n.ty, n.line) if n.ty else None
        if n.expr.k == 'lambda':
            code, t = self.g_lambda(n.expr, ty)
            if t[0] == 'lfn':
                if n.mut:
                    err(n.line, "a closure that borrows local variables can't be a 'var' (it would be stored); use "
                                "let, or 'own fn' to give it its own copies of them")
                if ty is not None and ty != ('fn',) + t[1:]:
                    err(n.line, f'expected {tn(ty)}, found {tn(t)}')
            else:
                code, t = self.coerce(code, t, ty, n.line)
            v = Var(n.name, t, self.var_cname(n.name), 'local', n.mut, False, n.line)
            self.declare(v)
            self.emit(f'vu_fn {v.cname} = {code};')
            self.freeze_caps(n.expr, n.line)
            return False
        if not n.mut and n.expr.k in ('name', 'field', 'index'):
            code, t, p = self.gen(n.expr, ty)
            if (p is not None and not self.is_copy(t) and t != STR
                    and (not p.is_name or p.root.kind != 'local' or p.root.frozen)):
                # The value can't be moved (it's part of something, or borrowed), so `let` names it
                # instead: a read-only view. What it's part of is frozen for reading until the view's
                # block ends, so the view can never dangle.
                if ty is not None and ty != t:
                    err(n.line, f'expected {tn(ty)}, found {tn(t)}')
                v = Var(n.name, t, self.var_cname(n.name), 'view', False, True, n.line)
                self.declare(v)
                self.emit(f'{self.ct(t)} *{v.cname} = &{p.code};')
                p.root.frozen.append(('read', n.line))
                self.scopes[-1].unfreeze.append(p.root)
                return False
            if p is not None and not self.is_copy(t):
                code = self.move(p, n.expr.line)
            code, t = self.coerce(code, t, ty, n.expr.line)
        else:
            code, t = self.stmt_value(n.expr, ty)
        if t == VOID:
            err(n.line, "this call doesn't produce a value")
        if t == NIL:
            err(n.line, f"can't tell the type of nil; write: let {n.name}: Type? = nil")
        if t[0] == 'lfn' and n.mut:
            err(n.line, "a closure that borrows local variables can't be a 'var' (it would be stored); use "
                        "let, or 'own fn' to give it its own copies of them")
        v = Var(n.name, t, self.var_cname(n.name), 'local', n.mut, False, n.line)
        self.declare(v)
        self.emit(f'{self.ct(t)} {v.cname} = {code};')
        return False

    def s_spawn(self, n):
        """spawn f(args): run f as a new task. The arguments move into it, so every parameter that
        isn't plain data or a capability is 'own'; f can't fail and returns nothing."""
        e = n.expr
        if e.k == 'call' and e.fn.k == 'name':
            self.not_shadowed(e)
        gen_name = None
        if e.k == 'call' and e.fn.k == 'name' and e.fn.name in self.gfns and not self.lookup(e.fn.name):
            gen_name = self.gcall(e, None)
        if gen_name is None and (e.k != 'call' or e.fn.k != 'name' or e.fn.name not in self.fns):
            err(n.line, "spawn runs a function call as a new task, like: spawn handle(net, conn)")
        name = gen_name or e.fn.name
        params, ret, node = self.fns[name]
        d = disp(name)
        if name == 'main':
            err(n.line, "main can't be spawned")
        if node.body is None:
            err(n.line, f"{d}() is C code; spawn runs a Vu function")
        if node.throws:
            err(n.line, f"spawn {d}(): a task's function can't fail, since no caller receives its error; "
                        f"handle errors inside it (or send them on a channel)")
        if ret != VOID:
            err(n.line, f"spawn {d}(): a task's function returns nothing, since no caller receives its result; "
                        f"send results on a channel")
        for pn, pt, pv, pl, po in params:
            if pv:
                err(n.line, f"spawn {d}(): parameter '{pn}' is 'var', but a task can't change its spawner's variables")
            if not po and pt not in SCALARS and pt[0] != 'cap':
                err(n.line, f"spawn {d}(): the task takes its arguments with it, so parameter '{pn}' must be "
                            f"'own' (own {pn}: {tn(pt)})")
        if self.par is not None:
            err(n.line, "spawn can't be used inside a par loop")
        self.uses_tasks = True
        if name not in self.spawned:
            self.spawned.append(name)
        code, _ = self.call_user(e, name, spawn_line=n.line)
        self.emit(code + ';')
        return False

    def s_exprstmt(self, n):
        e = n.expr
        if e.k not in ('call', 'try', 'orelse'):
            err(n.line, "this line computes a value but does nothing with it; assign it with 'let x = ...'")
        if e.k == 'try':
            code, t = self.stmt_value(e)
            if t == VOID:
                return False
        else:
            code, t, _ = self.gen(e)
        if t == VOID:
            self.emit(code + ';')
        elif self.is_copy(t):
            self.emit(f'(void){code};')
        else:
            tv = self.tmp()
            self.emit(f'{{ {self.ct(t)} {tv} = {code}; {self.drop(t, tv)} }}')
        return e.k == 'call' and e.fn.k == 'name' and e.fn.name in ('panic', 'exit')

    def s_assign(self, n):
        if n.target.k not in ('name', 'field', 'index'):
            err(n.line, 'can only assign to a variable, field, or list element')
        if n.target.k == 'index' and n.op == '=':
            mt = self.probe_type(n.target.e)
            if mt is not None and mt[0] == 'map':
                return self.map_insert(n, mt)
        p = self.place(n.target)
        if p is None:
            if n.target.k == 'index' and self.probe_type(n.target.e) == STR:
                err(n.line, "strings can't be changed in place; build a new one, or use a [Byte] list")
            if self.computed_key(n.target):
                err(n.line, "to change part of a map value, put the key in a variable first: let k = ...; m[k].x = ...")
            err(n.line, "can't assign to this (constants can't change)")
        self.write_check(p, n.line, whole_ok=(n.op == '='))
        ty = self.ct(p.ty)
        tv, pp = self.tmp(), self.tmp()
        if n.op == '=':
            c, _ = self.stmt_value(n.expr, p.ty)
            if not p.is_name:
                self.read_check(p, n.line)
            if not self.is_copy(p.ty):
                self.emit(f'{{ {ty} {tv} = {c}; {ty} *{pp} = &{p.code}; drop_{self.mg(p.ty)}({pp}); *{pp} = {tv}; }}')
            elif p.is_name or not self.effects(n.expr):
                self.emit(f'{p.code} = {c};')
            else:
                self.emit(f'{{ {ty} {tv} = {c}; {p.code} = {tv}; }}')
            if p.is_name:
                p.root.state, p.root.moved_line = 'no', None
            return False
        if p.ty == STR:
            if n.op != '+=':
                err(n.line, f"strings support '+=' (append), not '{n.op}'")
            if n.expr.k == 'slice' and self.probe_type(n.expr.e) == STR:
                sl = n.expr

                def use_s(c, t, _p):
                    self.pure_index(sl.lo, sl.hi)
                    lo, _ = self.value(sl.lo, INT)
                    hi, _ = self.value(sl.hi, INT)
                    return f'vu_str_cat_slice(&{p.code}, &{c}, {lo}, {hi}, {n.line})', VOID
                code, _ = self.with_borrow(sl.e, use_s)
                self.emit(code + ';')
                return False

            def use(c, t, _p):
                if t != STR:
                    err(n.line, f'can only append a Str to a string; to add a {tn(t)} x, write s += "{{x}}"')
                return f'vu_str_cat(&{p.code}, &{c})', VOID
            code, _ = self.with_borrow(n.expr, use)
            self.emit(code + ';')
            return False
        if p.ty not in (INT, FLOAT, BYTE):
            err(n.line, f"'{n.op}' needs a number on the left, not {tn(p.ty)}")
        c, _ = self.stmt_value(n.expr, p.ty)
        op = n.op[0]
        if p.ty == FLOAT and op in '%&|^':
            err(n.line, f"'{n.op}' needs an Int or Byte")
        fn = (INT_OPS if p.ty == INT else BYTE_OPS if p.ty == BYTE else {}).get(op)
        if fn:
            self.emit(f'{{ {ty} {tv} = {c}; {ty} *{pp} = &{p.code}; *{pp} = {fn}(*{pp}, {tv}, {n.line}); }}')
        elif self.effects(n.expr):
            self.emit(f'{{ {ty} {tv} = {c}; {p.code} {n.op} {tv}; }}')
        else:
            self.emit(f'{p.code} {n.op} {c};')
        return False

    def map_insert(self, n, mt):
        """m[k] = v: insert or replace. The map keeps its own copy of the key."""
        mp = self.place(n.target.e)
        if mp is None:
            err(n.line, 'can only insert into a map stored in a variable')
        self.write_check(mp, n.line)
        c, _ = self.stmt_value(n.expr, mt[2])
        self.read_check(mp, n.line)
        self.pure_index(n.target.i)
        tv = self.tmp()
        ke = n.target.i
        if mt[1] == STR and self.place(ke) is None and not (ke.k == 'str' and all(isinstance(x, str) for x in ke.parts)):
            # A computed Str key (m["k{i}"] = v): build it in a temporary and hand it to the map.
            kc, _ = self.value(ke, STR)
            kv = self.tmp()
            self.emit(f'{{ {self.ct(mt[2])} {tv} = {c}; vu_str {kv} = {kc}; '
                      f'vu_mtake_{self.mg(mt)}(&{mp.code}, &{kv}, {tv}, {n.line}); }}')
            return False
        if mt[1] == STR:
            kvar = self.last_use(ke)
            if kvar is not None:
                # The key variable isn't used again: move it into the map instead of copying it.
                kc = self.move(self.place(ke), n.line)
                kv = self.tmp()
                self.emit(f'{{ {self.ct(mt[2])} {tv} = {c}; vu_str {kv} = {kc}; '
                          f'vu_mtake_{self.mg(mt)}(&{mp.code}, &{kv}, {tv}, {n.line}); }}')
                return False
        kr = self.key_ref(ke, mt[1], n.line)
        self.emit(f'{{ {self.ct(mt[2])} {tv} = {c}; vu_mset_{self.mg(mt)}(&{mp.code}, {kr}, {tv}, {n.line}); }}')
        return False

    def s_return(self, n):
        if self.par:
            err(n.line, f"'return' can't leave the par loop on line {ln(self.par['line'])} early; every iteration runs")
        if n.expr is None:
            if self.ret != VOID:
                err(n.line, f'this function must return a {tn(self.ret)}')
            self.emit_drops(self.scopes)
            if self.throws:
                self.emit(f'return ({self.ct(self.rett)}){{0}};')
            else:
                self.emit('return 0;' if self.is_main else 'return;')
            return True
        if self.ret == VOID:
            err(n.line, "this function doesn't return a value (add '-> Type' to its signature)")
        c, _ = self.stmt_value(n.expr, self.ret)
        rv = self.tmp()
        self.open('{')
        self.emit(f'{self.ct(self.ret)} {rv} = {c};')
        self.emit_drops(self.scopes)
        self.emit(f'return ({self.ct(self.rett)}){{.bad = 0, .val = {rv}}};' if self.throws else f'return {rv};')
        self.close()
        return True

    def loop_exit(self, n, word):
        if not self.loops:
            err(n.line, f"'{word}' outside a loop")
        if word == 'break' and self.loops[-1][2]:
            err(n.line, "'break' can't stop a par loop early; every iteration runs (use 'continue' to skip one)")
        self.loops[-1][0 if word == 'break' else 1].append(self.snapshot())
        idx = max(i for i, sc in enumerate(self.scopes) if sc.loop)
        self.emit_drops(self.scopes[idx:])
        self.emit(word + ';')
        return True

    def s_break(self, n):
        return self.loop_exit(n, 'break')

    def s_continue(self, n):
        return self.loop_exit(n, 'continue')

    def s_if(self, n):
        ends = []
        self.if_chain(n, ends)
        if not ends:
            return True
        self.merge(ends)
        return False

    def if_chain(self, n, ends):
        if n.bind is None:
            c, _ = self.value(n.cond, BOOL)
            snap = self.snapshot()
            self.open(f'if ({c}) {{')
            div = self.block(n.body)
            if not div:
                ends.append(self.snapshot())
            self.restore(snap)
            self.close()
            self.else_part(n, ends)
            return
        self.open('{')
        self.scopes.append(Scope())
        code, t, p = self.gen(n.cond)
        if t[0] != 'opt':
            err(n.line, f"'if {n.bind} = ...' needs an optional value (T?), but this is {tn(t)}")
        if p is None:
            hv = Var('$', t, self.tmp(), 'local', False, False, n.line)
            self.emit(f'{self.ct(t)} {hv.cname} = {code};')
            self.scopes[-1].order.append(hv)
            subj = hv.cname
        else:
            if n.mut:
                self.write_check(p, n.line)
            subj = self.tmp()   # evaluate the subject once
            self.emit(f'{self.ct(t)} {subj} = {p.code};')
        bt = t[1]
        snap = self.snapshot()
        self.open(f'if ({subj}) {{')
        if p is not None:
            p.root.frozen.append(('lock' if n.mut else 'read', n.line))

        def setup():
            v = Var(n.bind, bt, self.var_cname(n.bind), 'ref', n.mut, True, n.line)
            self.declare(v)
            self.emit(f'{self.ct(bt)} *{v.cname} = {subj};')
        div = self.block(n.body, setup=setup)
        if p is not None:
            p.root.frozen.pop()
        if not div:
            ends.append(self.snapshot())
        self.restore(snap)
        self.close()
        self.else_part(n, ends)
        sc = self.scopes.pop()
        self.emit_drops([sc])
        self.close()

    def else_part(self, n, ends):
        if n.els is None:
            ends.append(self.snapshot())
            return
        self.open('else {')
        # An elif whose condition has a ? is an if statement in an else block, so the ? is moved to just
        # before it, inside the else (it runs only when the earlier conditions were false).
        if len(n.els) == 1 and n.els[0].is_elif and not any(x.k == 'try' for x in self.walk(n.els[0].cond)):
            self.if_chain(n.els[0], ends)
        else:
            div = self.block(n.els)
            if not div:
                ends.append(self.snapshot())
        self.close()

    def loop_check(self, before, ends):
        for v, (st, _) in before.items():
            if st != 'no':
                continue
            for sn in ends:
                if v in sn and sn[v][0] != 'no':
                    err(sn[v][1], f"'{v.name}' is moved inside a loop, so the next pass would use a moved value; "
                                  f"move it after the loop, or give it a new value before the loop repeats")

    def run_loop(self, before, body, line, setup=None, par=False):
        self.loops.append(([], [], par))
        div = self.block(body, loop=True, setup=setup)
        brk, cont, _ = self.loops.pop()
        return div, brk, cont

    def s_while(self, n):
        before = self.snapshot()
        forever = n.cond.k == 'bool' and n.cond.v
        c, _ = self.value(n.cond, BOOL)
        self.open(f'while ({c}) {{')
        div, brk, cont = self.run_loop(before, n.body, n.line)
        self.close()
        self.loop_check(before, ([] if div else [self.snapshot()]) + cont)
        if forever and not brk:
            return True
        self.merge(([] if forever else [before]) + brk)
        return False

    def s_range(self, n):
        a, _ = self.value(n.start, INT)
        b, _ = self.value(n.end, INT)
        self.open('{')
        ta, tb = self.tmp(), self.tmp()
        self.emit(f'int64_t {ta} = {a}; int64_t {tb} = {b};')
        step = '1'
        if n.step is not None:
            sc, _ = self.value(n.step, INT)
            if self.is_lit(n.step):
                val = n.step.v if n.step.k == 'int' else -n.step.e.v
                if val <= 0:
                    err(n.line, "the 'by' step must be positive")
                step = str(val)
            else:
                step = self.tmp()
                self.emit(f'int64_t {step} = {sc};')
                self.emit(f'if ({step} <= 0) vu_fail({n.line}, "loop step must be positive, got %lld", '
                          f'(long long){step});')
        cn = self.var_cname(n.name)
        before = self.snapshot()
        frozen = []
        if n.par:
            if self.par:
                err(n.line, f"par loops can't be nested (the outer one is on line {ln(self.par['line'])})")
            # Lists indexed by the loop counter are split between threads: iteration i owns xs[i].
            # Everything else from outside the loop is read-only inside it, so threads can't race.
            split = {x.e.name for x in self.walk(n.body)
                     if x.k == 'index' and x.e.k == 'name' and x.i.k == 'name' and x.i.name == n.name
                     and self.lookup(x.e.name) is not None and self.lookup(x.e.name).ty[0] == 'list'}
            for sc in self.scopes:
                for v in sc.order:
                    v.frozen.append(('part' if v.name in split else 'par', n.line))
                    frozen.append(v)
            self.par = {'var': n.name, 'line': n.line, 'elems': {}}
            self.uses_par = True
        decl_in_body = False
        if n.par:
            # Count the iterations up front, in unsigned arithmetic, so the counter can never overflow.
            cnt, k = self.tmp(), self.tmp()
            self.emit(f'uint64_t {cnt} = {ta} {">" if n.incl else ">="} {tb} ? 0 : '
                      f'((uint64_t){tb} - (uint64_t){ta} - {0 if n.incl else 1}) / (uint64_t){step} + 1;')
            if n.incl:
                self.emit(f'if ({cnt} == 0 && {ta} <= {tb}) {cnt} = UINT64_MAX;  /* the full Int range */')
            # Each thread sets up its stack-overflow guard once, outside the loop body, and links its
            # backtrace to the frame of the function running the loop.
            top = self.tmp()
            self.emit(f'VU_PAR_TOP({top});')
            self.emit('#pragma omp parallel')
            self.open('{')
            self.emit('vu_thread_guard();')
            self.emit(f'VU_PAR_JOIN({top});')
            self.emit('#pragma omp for schedule(dynamic)')
            self.open(f'for (uint64_t {k} = 0; {k} < {cnt}; {k}++) {{')
            decl_in_body = f'int64_t {cn} = (int64_t)((uint64_t){ta} + {k} * (uint64_t){step});'
        elif not n.incl and step == '1':
            # i < end with step 1: i + 1 can't overflow.
            self.open(f'for (int64_t {cn} = {ta}; {cn} < {tb}; {cn}++) {{')
        else:
            # Stop instead of wrapping when the next step would pass the largest Int.
            ok = self.tmp()
            self.open(f'for (int64_t {cn} = {ta}, {ok} = 1; {ok} && {cn} {"<=" if n.incl else "<"} {tb}; '
                      f'{ok} = !__builtin_add_overflow({cn}, {step}, &{cn})) {{')

        def setup():
            self.declare(Var(n.name, INT, cn, 'loop', False, False, n.line))
            if decl_in_body:
                self.emit(decl_in_body)
        div, brk, cont = self.run_loop(before, n.body, n.line, setup=setup, par=n.par)
        for v in frozen:
            v.frozen.pop()
        if n.par:
            self.par = None
        self.close()
        if n.par:
            self.close()   # the parallel region
        self.close()
        self.loop_check(before, ([] if div else [self.snapshot()]) + cont)
        self.merge([before] + brk)
        return False

    def s_each(self, n):
        code, t, p = self.gen(n.seq)
        if t[0] not in ('list', 'map'):
            err(n.line, f"'for {n.name} in ...' needs a list, a map or a range like 0..n, but this is {tn(t)}")
        if n.name2 and t[0] != 'map':
            err(n.line, f"'for {n.name}, {n.name2} in ...' goes through a map's keys and values; this is {tn(t)}")
        if t[0] == 'map' and n.mut and not n.name2:
            err(n.line, "map keys can't be changed in a loop; to change the values write: for k, var v in m")
        self.open('{')
        self.scopes.append(Scope())
        root = None
        if p is None:
            hv = Var('$', t, self.tmp(), 'local', True, False, n.line)
            self.emit(f'{self.ct(t)} {hv.cname} = {code};')
            self.scopes[-1].order.append(hv)
            lst = hv.cname
        else:
            if n.mut:
                self.write_check(p, n.line)
            lst, root = p.code, p.root
        lp, ln, ix = self.tmp(), self.tmp(), self.tmp()
        is_map = t[0] == 'map'
        self.emit(f'{self.ct(t)} *{lp} = &{lst}; int64_t {ln} = {lp}->{"nents" if is_map else "len"};')
        before = self.snapshot()
        self.open(f'for (int64_t {ix} = 0; {ix} < {ln}; {ix}++) {{')
        if is_map:
            self.emit(f'if (!{lp}->ents[{ix}].live) continue;   /* removed entry */')
        if root:
            root.frozen.append(('lock' if n.mut else 'read', n.line))
        et = t[1]

        def setup():
            if n.name2:
                # Keys stay read-only; the value is writable with 'var'. The map is locked (or frozen for
                # reading) for the whole loop, so entries can't move while these point at them.
                k = Var(n.name, et, self.var_cname(n.name), 'ref', False, True, n.line)
                self.declare(k)
                self.emit(f'{self.ct(et)} *{k.cname} = &{lp}->ents[{ix}].key;')
                v = Var(n.name2, t[2], self.var_cname(n.name2), 'ref', n.mut, True, n.line)
                self.declare(v)
                self.emit(f'{self.ct(t[2])} *{v.cname} = &{lp}->ents[{ix}].val;')
                return
            v = Var(n.name, et, self.var_cname(n.name), 'ref', n.mut, True, n.line)
            self.declare(v)
            self.emit(f'{self.ct(et)} *{v.cname} = &{lp}->{"ents" if is_map else "data"}[{ix}]{".key" if is_map else ""};')
        div, brk, cont = self.run_loop(before, n.body, n.line, setup=setup)
        if root:
            root.frozen.pop()
        self.close()
        sc = self.scopes.pop()
        self.emit_drops([sc])
        self.close()
        self.loop_check(before, ([] if div else [self.snapshot()]) + cont)
        self.merge([before] + brk)
        return False

    # ---- functions and program
    def ffi_ct(self, t, param):
        if t == STR:
            return 'const vu_str *' if param else 'vu_str'
        return 'void *' if t[0] == 'ext' else self.ct(t)

    def extern_proto(self, params, ret, node):
        ps = [self.ffi_ct(pt, True) for _, pt, _, _, _ in params[1:]]
        if node.throws:
            if ret != VOID:
                ps.append(self.ffi_ct(ret, False) + ' *out')
            ps.append('vu_str *err')
            r = 'bool'
        else:
            r = self.ffi_ct(ret, False)
        return f'static {r} {node.cname}({", ".join(ps) or "void"});'

    def gen_extern(self, name):
        """The C function behind an extern declaration, wrapped in Vu's calling convention: the Ffi
        argument is dropped, a borrowed Str is passed as const vu_str *, a borrowed handle as its
        pointer, and a failing call reports through (args..., T *out, vu_str *err) -> bool."""
        params, ret, node = self.fns[name]
        cn = node.cname
        cps, args = [], []
        for pn, pt, pv, pl, po in params:
            v = 'v_' + pn
            if pt[0] == 'cap':
                cps.append(f'vu_cap {v}')
            elif po or pt in SCALARS:
                cps.append(f'{self.ct(pt)} {v}')
                args.append(v)
            elif pt == STR:
                cps.append(f'vu_str *restrict {v}')
                args.append(v)
            else:
                cps.append(f'void **restrict {v}')
                args.append(f'*{v}')
        rett = ('res', ret) if node.throws else ret
        sig = f'static {self.ct(rett)} fn_{name}({", ".join(cps)})'
        where = f'{cstr(cn)}, {node.line}'
        lines = [f'    vu_ffi_here({where});']
        if node.throws:
            outs = [] if ret == VOID else ['&r.val']
            lines.append(f'    {self.ct(rett)} r = {{0}};')
            lines.append(f'    r.bad = !{cn}({", ".join(args + outs + ["&r.err"])});')
            lines.append(f'    if (r.bad && !r.err.len) {{ drop_Str(&r.err); r.err = vu_errf("%s failed", {cstr(cn)}); }}')
            if ret[0] == 'ext':
                lines.append(f'    if (!r.bad && !r.val) vu_ffi_null({where});')
            lines.append('    return r;')
        elif ret == VOID:
            lines.append(f'    {cn}({", ".join(args)});')
        else:
            lines.append(f'    {self.ct(ret)} r = {cn}({", ".join(args)});')
            if ret[0] == 'ext':
                lines.append(f'    if (!r) vu_ffi_null({where});')
            lines.append('    return r;')
        return sig, lines

    def gen_fn(self, name):
        params, ret, node = self.fns[name]
        if node.body is None:
            return self.gen_extern(name)
        self.lines, self.ind = [], 1
        self.src_line = node.line   # the function's own setup and cleanup belong to its 'fn' line
        # its module's prefix (geo__ for geo__area): a local named like one of the module's types is rejected
        self.prefix = module_prefix(name)
        self.scopes, self.loops, self.par = [Scope()], [], None
        self.rest = []
        self.throws = node.throws
        self.ret, self.is_main = ret, name == 'main' and not node.throws
        self.rett = self.res_of(name, ret) if node.throws else ret
        cps = []
        for pn, pt, pv, pl, po in params:
            cn = 'v_' + pn
            if po:
                # owned: a local the function may change, move or return, freed at its end
                cps.append(f'{self.ct(pt)} {cn}')
                self.declare(Var(pn, pt, cn, 'local', True, False, pl))
                continue
            if pv:
                cps.append(f'{self.ct(pt)} *restrict {cn}')
                ptr = True
            elif self.by_value(pt):
                cps.append(f'{self.ct(pt)} {cn}')
                ptr = False
            else:
                cps.append(f'{self.ct(pt)} *restrict {cn}')
                ptr = True
            self.declare(Var(pn, pt, cn, 'param', pv, ptr, pl))
        if self.is_main:
            sig = 'static int vu_main(void)'

            for pn, _, _, _, _ in params:
                self.emit(f'vu_cap v_{pn} = {{0}};')
        else:
            sig = f'static {self.ct(self.rett)} fn_{name}({", ".join(cps) or "void"})'
        self.emit(f'VU_ENTER({cstr(disp(name))});')
        div = self.stmts(node.body)
        if not div:
            if ret != VOID:
                err(node.line, f"function '{disp(name)}' must end with a return (it returns {tn(ret)})")
            self.emit_drops(self.scopes)
            if self.is_main:
                self.emit('return 0;')
            elif self.throws:
                self.emit(f'return ({self.ct(self.rett)}){{0}};')
        self.src_line = 0
        return sig, self.lines

    def gen_consts(self):
        out = []
        self.scopes, self.loops, self.lines, self.ind = [Scope()], [], [], 0
        self.throws, self.par, self.rest = False, None, []

        def has_call(e):
            if e.k in ('call', 'list', 'str'):
                return True
            return any(has_call(c) for c in (getattr(e, 'e', None), getattr(e, 'l', None), getattr(e, 'r', None))
                       if c is not None)
        consts = [it for it in self.items if it.k == 'const']
        by_name = {it.name: it for it in consts}
        order, state = [], {}

        def visit(it):
            # A constant comes after the constants it uses, wherever (and in whichever module) they are.
            if state.get(it.name) == 2:
                return
            if state.get(it.name) == 1:
                err(it.line, f"constant '{disp(it.name)}' depends on itself")
            state[it.name] = 1
            for x in self.walk(it.expr):
                if x.k == 'name' and x.name in by_name:
                    visit(by_name[x.name])
            state[it.name] = 2
            order.append(it)
        for it in consts:
            visit(it)
        for it in order:
            if has_call(it.expr):
                err(it.line, 'a const must be a number, true/false, or arithmetic on other consts')
            c, t = self.value(it.expr)
            self.consts[it.name] = t
            out.append(f'#define C_{it.name} ({c})')
        return out

    def build(self):
        consts = self.gen_consts()
        fns, i = [], 0
        while i < len(self.fn_queue):   # registers types as it goes, and generic instances as they're used
            n = self.fn_queue[i]
            i += 1
            if n not in self.inst_env:
                fns.append(self.gen_fn(n))
                continue
            saved, self.tenv = self.tenv, self.inst_env[n]
            try:
                fns.append(self.gen_fn(n))
            except VuError as ex:
                d = disp(n)
                ex.msg += f" (in {d if len(d) <= 120 else d[:120] + '...'}, used on line {ln(self.inst_line[n])})"
                raise
            self.tenv = saved
        out = [RUNTIME]
        if self.uses_float_parse:
            out += [POW10_TABLE, FLOAT_RT]
        if self.uses_tls:
            out.append('#define VU_TLS 1')
            self.links += [l for l in ('ssl', 'crypto') if l not in self.links]
        if self.uses_tasks:
            out.append(TASK_RT)
        if self.jtypes:
            out.append(JSON_RT)
        if self.externs:
            out.append(FFI_RT)
            # The C signatures the glue must have, declared before it: a definition that doesn't match
            # is a C compile error, instead of a call through the wrong types.
            for n, it in self.exttypes.items():
                out.append(f'static void {it.drop}(void *p);')
            for n, (params, ret, node) in self.fns.items():
                if node.body is None:
                    out.append(self.extern_proto(params, ret, node))
            seen = []
            for it in self.externs:
                if it.path not in seen:
                    seen.append(it.path)
                    out.append(f'#include {cstr(it.path)}')
            for n, it in self.exttypes.items():
                out.append(f'static void drop_X_{n}(void **p) {{ if (*p) {{ {it.drop}(*p); *p = NULL; }} }}')
        out += consts
        out += [f'typedef struct T_{n} T_{n};' for n in self.struct_order]
        # Boxed variant payloads are named T_<k>_<Enum>: user type names can't start with a digit.
        out += [f'typedef struct T_{k}_{n} T_{k}_{n};' for n, k in sorted(self.boxed)]
        for t in self.types:
            if t[0] == 'list':
                out.append(f'typedef struct {{ {self.ct(t[1])} *data; int64_t len, cap; }} {self.ct(t)};')
            elif t[0] == 'map':
                m = self.mg(t)
                out.append(f'typedef struct ME_{m} ME_{m}; typedef struct {{ ME_{m} *ents; int64_t nents, cap, live; '
                           f'int64_t *idx; int64_t nidx; }} {m};')
        for n in self.struct_order:
            if n in self.structs:
                fields = ' '.join(f'{self.ct(ft)} {cf(f)};' for f, ft in self.structs[n].fields)
                out.append(f'struct T_{n} {{ {fields} }};')
            else:
                info = self.enums[n]
                for k, (_, fs) in enumerate(info.variants):
                    if (n, k) in self.boxed:
                        out.append(f'struct T_{k}_{n} {{ ' + ' '.join(f'{self.ct(ft)} {cf(f)};' for f, ft in fs) + ' };')
                parts = ' '.join((f'T_{k}_{n} *b{k};' if (n, k) in self.boxed else
                                  f'struct {{ ' + ' '.join(f'{self.ct(ft)} {cf(f)};' for f, ft in fs) + f' }} v{k};')
                                 for k, (_, fs) in enumerate(info.variants) if fs)
                out.append(f'struct T_{n} {{ int32_t tag; ' + (f'union {{ {parts} }} u; ' if parts else '') + '};')
        for t in self.types:
            if t[0] == 'res':
                val = '' if t[1] == VOID else f' {self.ct(t[1])} val;'
                ev = f' {self.ct(t[2])} eval;' if len(t) == 3 else ''
                out.append(f'typedef struct {{ bool bad; vu_str err;{val}{ev} }} {self.ct(t)};')
        owned = [n for n in self.struct_order if n in self.structs and not self.structs[n].copy]
        owned_enums = [n for n in self.struct_order if n in self.enums and not self.enums[n].copy]
        out += [f'static void drop_S_{n}(T_{n} *p);' for n in owned]
        out += [f'static void drop_E_{n}(T_{n} *p);' for n in owned_enums]
        out += [f'static void drop_{self.mg(t)}({self.ct(t)} *p);' for t in self.types]
        for t in self.types:
            if t[0] == 'fn':
                # a call through a function value of this type: the C function cast back to its real type
                r = self.ct(('res', t[2]) if t[3] else t[2])
                ps = ''.join(', ' + self.pdecl(pt, '') .rstrip() for pt in t[1])
                decl = ''.join(', ' + self.pdecl(pt, f'a{i}') for i, pt in enumerate(t[1]))
                call = f'(({r} (*)(void *{ps}))f.fn)(f.env{"".join(f", a{i}" for i in range(len(t[1])))})'
                out.append(f'static inline {r} vu_call_{self.mg(t)}(vu_fn f{decl}) {{ '
                           f'{"" if r == "void" else "return "}{call}; }}')
        nums = sorted(self.lam_fns)
        out += [self.lam_envs[k] for k in nums if self.lam_envs.get(k)]
        out += [self.lam_drops[k] for k in nums if k in self.lam_drops]
        out += [sig + ';' for sig, _ in fns if sig.startswith('static') and sig != 'static int vu_main(void)']
        out += [self.lam_fns[k][0] + ';' for k in nums]
        for name in self.thunks:
            params, ret, node = self.fns[name]
            r = self.ct(self.res_of(name, ret) if node.throws else ret)
            decl = ''.join(', ' + self.pdecl(pt, f'a{i}') for i, (_, pt, _, _, _) in enumerate(params))
            call = f'fn_{name}({", ".join(f"a{i}" for i in range(len(params)))})'
            out.append(f'static {r} vu_th_{name}(void *e{decl}) {{ (void)e; {"" if r == "void" else "return "}{call}; }}')
        out.append('static int vu_main(void);')
        for name in self.spawned:
            # spawn name(...): the arguments travel to the new task in a block it frees
            ps = self.fns[name][0]
            fields = ' '.join(f'{self.ct(pt)} a{i};' for i, (_, pt, _, _, _) in enumerate(ps)) or 'char unused;'
            out.append(f'typedef struct {{ {fields} }} vu_sa_{name};')
            call = ', '.join(f'a.a{i}' for i in range(len(ps)))
            out.append(f'static void vu_se_{name}(void *p) {{ vu_sa_{name} a = *(vu_sa_{name} *)p; free(p); '
                       f'(void)a; fn_{name}({call}); }}')
            decl = ''.join(f', {self.ct(pt)} a{i}' for i, (_, pt, _, _, _) in enumerate(ps))
            sets = ' '.join(f'p->a{i} = a{i};' for i in range(len(ps)))
            out.append(f'static void vu_spawn_{name}(int line{decl}) {{ vu_sa_{name} *p = (vu_sa_{name} *)'
                       f'vu_malloc(sizeof *p); {sets} vu_task_spawn(vu_se_{name}, p, line); }}')
        out += [box_code(f'{k}_{n}') for n, k in sorted(self.boxed)]
        for t in self.types:
            if t[0] == 'opt':
                out.append(box_code(self.box_name(t[1]), self.ct(t[1])))
            elif t[0] == 'list':
                out.append(list_code(self.mg(t), self.ct(t), self.ct(t[1])))
            elif t[0] == 'map':
                out.append(self.map_c(t))
        for n in owned:
            body = ' '.join(self.drop(ft, f'p->{cf(f)}') for f, ft in self.structs[n].fields if not self.is_copy(ft))
            out.append(f'static void drop_S_{n}(T_{n} *p) {{ {body} }}')
        for n in owned_enums:
            def case(k, fs, n=n):
                body = ' '.join(self.drop(ft, self.payload(n, k, 'p') + cf(f)) for f, ft in fs if not self.is_copy(ft))
                if (n, k) in self.boxed:
                    # A moved-from value is all zeros, so its box pointer can be NULL.
                    return f'case {k}: if (p->u.b{k}) {{ {body} vu_release_{k}_{n}(p->u.b{k}); }} break;'
                return f'case {k}: {body} break;'
            cases = ' '.join(case(k, fs) for k, (_, fs) in enumerate(self.enums[n].variants)
                             if (n, k) in self.boxed or any(not self.is_copy(ft) for _, ft in fs))
            out.append(f'static void drop_E_{n}(T_{n} *p) {{ switch (p->tag) {{ {cases} default: break; }} }}')
        for t in self.types:
            m = self.mg(t)
            if t[0] == 'res':
                val = '' if t[1] == VOID or self.is_copy(t[1]) else f' else {{ {self.drop(t[1], "p->val")} }}'
                out.append(f'static void drop_{m}({m} *p) {{ if (p->bad) {{ {self.drop_err(t, "(*p)")} }}{val} }}')
                continue
            if t[0] == 'map':
                continue   # map_c defines it
            if t[0] == 'fn':
                out.append(f'static void drop_{m}(vu_fn *p) {{ vu_fn_drop(p); }}')
                continue
            if t[0] == 'chan':
                if not self.is_copy(t[1]):
                    out.append(f'static void vu_cdrop_{m}(void *e) {{ {self.drop(t[1], f"*({self.ct(t[1])} *)e")} }}')
                out.append(f'static void drop_{m}(vu_chan **p) {{ vu_chan_release(p); }}')
                continue
            if t[0] == 'opt':
                x, tx = self.box_name(t[1]), self.ct(t[1])
                inner = '' if self.is_copy(t[1]) else f'drop_{self.mg(t[1])}(q); '
                out.append(f'static void vu_freenode_{m}(void *v, int64_t n) {{ (void)n; {tx} *q = ({tx} *)v; '
                           f'{inner}vu_release_{x}(q); }}')
                out.append(f'static void drop_{m}({tx} **p) {{ {tx} *q = *p; if (!q) return; '
                           f'if (__builtin_expect(vu_drop_depth < VU_MAX_DROP_DEPTH, 1)) {{ vu_drop_depth++; {inner}vu_release_{x}(q); '
                           f'vu_drop_depth--; }} else vu_defer(vu_freenode_{m}, q, 0); }}')
            else:
                et = t[1]
                if self.is_copy(et):
                    out.append(f'static void drop_{m}({self.ct(t)} *p) {{ free(p->data); }}')
                    continue
                e = self.ct(et)
                out.append(f'static void vu_freeitems_{m}(void *v, int64_t n) {{ {e} *d = ({e} *)v; '
                           f'for (int64_t i = 0; i < n; i++) {self.drop(et, "d[i]")} free(d); }}')
                out.append(f'static void drop_{m}({self.ct(t)} *p) {{ if (!p->data) return; '
                           f'if (__builtin_expect(vu_drop_depth < VU_MAX_DROP_DEPTH, 1)) {{ vu_drop_depth++; vu_freeitems_{m}(p->data, p->len); '
                           f'vu_drop_depth--; }} else vu_defer(vu_freeitems_{m}, p->data, p->len); }}')
        for n in self.err_enums:
            out.append(self.etext(n))
        out += self.json_code()
        # Everything after this point is user code under #line directives, so the program's entry
        # points come first.
        out.append(f'static const char *const vu_file_names[] = {{{", ".join(self.cpaths)}}};')
        if self.fns['main'][2].throws:
            caps = [pn for pn, _, _, _, _ in self.fns['main'][0]]
            decl = ' '.join(f'vu_cap v_{pn} = {{0}};' for pn in caps)
            out.append('static int vu_main(void) {\n'
                       f'    {decl}\n'
                       f'    {self.ct(self.res_of("main", VOID))} r = fn_main({", ".join("v_" + pn for pn in caps)});\n'
                       '    if (r.bad) {\n'
                       '        int rc = vu_uncaught((const char *)r.err.data, (size_t)(r.err.len > 1000000 ? 1000000 : r.err.len));\n'
                       f'        {self.drop_err(self.res_of("main", VOID), "r")}\n'
                       '        return rc;\n'
                       '    }\n'
                       '    return 0;\n}')
        out.append('int main(int argc, char **argv) { return vu_start(argc, argv, vu_main, vu_file_names); }')
        for sig, lines in fns + [self.lam_fns[k] for k in nums]:
            out.append(sig + ' {')
            out += lines
            out.append('}')
        return '\n'.join(out) + '\n'

    def map_c(self, t):
        """An insertion-ordered hash map: entries in an array (so iteration follows insertion order) plus
        an open-addressing index into it. Removed entries stay as tombstones until the next rebuild."""
        key, val = t[1], t[2]
        m, kc, vc = self.mg(t), self.ct(key), self.ct(val)
        if key == STR:
            hsh, eq, cpy, kdrop = 'vu_siphash(k->data, (size_t)k->len)', 'vu_str_eq(&en->key, k)', 'vu_str_dup(k)', 'drop_Str(&en->key);'
            ktdrop = 'drop_Str(k);'
        else:
            hsh, eq, cpy, kdrop = 'vu_hash_int((int64_t)*k)', 'en->key == *k', '*k', ''
            ktdrop = ''
        vdrop = '' if self.is_copy(val) else self.drop(val, 'en->val')
        getor = (f'static {vc} vu_mgetor_{m}(const {m} *m, const {kc} *k, {vc} d) {{\n'
                 f'    int64_t e = vu_mfind_{m}(m, k);\n    return e < 0 ? d : m->ents[e].val;\n}}\n'
                 if self.is_copy(val) else '')
        return f'''struct ME_{m} {{ {kc} key; {vc} val; uint64_t hash; bool live; }};
/* Small maps (up to VU_SMALL_MAP entries) have no index: a scan comparing keys beats hashing them.
   Bigger maps hash with SipHash and probe an index into the entries. */
static int64_t vu_mfind_{m}(const {m} *m, const {kc} *k) {{
    if (!m->nidx) {{
        for (int64_t i = 0; i < m->nents; i++) {{
            const ME_{m} *en = &m->ents[i];
            if (en->live && ({eq})) return i;
        }}
        return -1;
    }}
    uint64_t h = {hsh};
    uint64_t mask = (uint64_t)m->nidx - 1;
    for (uint64_t i = h & mask;; i = (i + 1) & mask) {{
        int64_t e = m->idx[i];
        if (e == 0) return -1;
        const ME_{m} *en = &m->ents[e - 1];
        if (en->live && en->hash == h && ({eq})) return e - 1;
    }}
}}
static void vu_mindex_{m}({m} *m, int64_t want) {{
    int64_t j = 0;
    for (int64_t i = 0; i < m->nents; i++) if (m->ents[i].live) m->ents[j++] = m->ents[i];
    m->nents = j;
    int64_t n = 8;
    while (n < want) {{ if (n > INT64_MAX / 4) vu_oom(); n *= 2; }}
    free(m->idx);
    m->idx = (int64_t *)calloc((size_t)n, sizeof(int64_t));
    if (!m->idx) vu_oom();
    m->nidx = n;
    for (int64_t i = 0; i < m->nents; i++) {{
        uint64_t s = m->ents[i].hash & ((uint64_t)n - 1);
        while (m->idx[s]) s = (s + 1) & ((uint64_t)n - 1);
        m->idx[s] = i + 1;
    }}
}}
static void vu_mbig_{m}({m} *m) {{
    for (int64_t i = 0; i < m->nents; i++) {{
        ME_{m} *en = &m->ents[i];
        if (!en->live) continue;
        const {kc} *k = &en->key;
        en->hash = {hsh};
    }}
    vu_mindex_{m}(m, (m->live + 1) * 2);
}}
static void vu_mput_{m}({m} *m, {kc} *k, {vc} v, bool take) {{
    int64_t e = vu_mfind_{m}(m, k);
    if (e >= 0) {{ ME_{m} *en = &m->ents[e]; {vdrop} en->val = v; if (take) {{ {ktdrop} }} return; }}
    if (!m->nidx) {{
        if (m->nents >= VU_SMALL_MAP) vu_mbig_{m}(m);
    }} else if ((m->nents + 1) * 4 > m->nidx * 3) vu_mindex_{m}(m, (m->live + 1) * 2);
    uint64_t h = m->nidx ? {hsh} : 0;
    if (m->nents == m->cap) {{
        if (m->cap > (int64_t)(PTRDIFF_MAX / sizeof(ME_{m}) / 2)) vu_oom();
        /* 4 entries first (most objects are small), then 12, so a typical record grows once; then 1.5x. */
        int64_t c = m->cap == 0 ? 4 : m->cap == 4 ? 12 : m->cap + m->cap / 2;
        ME_{m} *d = (ME_{m} *)realloc(m->ents, (size_t)c * sizeof(ME_{m}));
        if (!d) vu_oom();
        m->ents = d;
        m->cap = c;
    }}
    ME_{m} *en = &m->ents[m->nents];
    en->key = take ? *k : {cpy}; en->val = v; en->hash = h; en->live = true;
    m->nents++;
    m->live++;
    if (m->nidx) {{
        uint64_t mask = (uint64_t)m->nidx - 1, s = h & mask;
        while (m->idx[s]) s = (s + 1) & mask;
        m->idx[s] = m->nents;
    }}
}}
static void vu_mset_{m}({m} *m, const {kc} *k, {vc} v, int line) {{ (void)line; vu_mput_{m}(m, ({kc} *)k, v, false); }}
/* Takes ownership of *k: the map keeps it, or frees it if the key was already there. */
static void vu_mtake_{m}({m} *m, {kc} *k, {vc} v, int line) {{ (void)line; vu_mput_{m}(m, k, v, true); }}
static {vc} *vu_mget_{m}({m} *m, const {kc} *k, int line) {{
    int64_t e = vu_mfind_{m}(m, k);
    if (e < 0) vu_fail(line, "key not found in map");
    return &m->ents[e].val;
}}
static bool vu_mhas_{m}(const {m} *m, const {kc} *k) {{ return vu_mfind_{m}(m, k) >= 0; }}
static bool vu_mremove_{m}({m} *m, const {kc} *k) {{
    int64_t e = vu_mfind_{m}(m, k);
    if (e < 0) return false;
    ME_{m} *en = &m->ents[e];
    {kdrop} {vdrop}
    en->live = false;
    m->live--;
    return true;
}}
{getor}static void vu_freeents_{m}(void *v, int64_t n) {{
    ME_{m} *ents = (ME_{m} *)v;
    for (int64_t i = 0; i < n; i++) {{ ME_{m} *en = &ents[i]; if (!en->live) continue; {kdrop} {vdrop} }}
    free(ents);
}}
static void drop_{m}({m} *p) {{
    free(p->idx);
    if (!p->ents) return;
    if (__builtin_expect(vu_drop_depth < VU_MAX_DROP_DEPTH, 1)) {{ vu_drop_depth++; vu_freeents_{m}(p->ents, p->nents); vu_drop_depth--; }}
    else vu_defer(vu_freeents_{m}, p->ents, p->nents);
}}'''


# ----------------------------------------------------------------------------- driver

# ----------------------------------------------------------------------------- modules
# A line number also says which file it is in: (file index << LINE_BITS) | line, the main file being
# index 0. The C runtime gets these numbers too, so a panic names the right file.
SOURCES = []   # (path, text) of each file being compiled, by index, for error reports
LINE_BITS = 24
LINE_MASK = (1 << LINE_BITS) - 1
MAX_MODULES = 127   # the file index must fit in the top bits of a 32-bit C int


def ln(line):
    """The line number within its file."""
    return line & LINE_MASK


def module_prefix(name):
    """geo__ for geo__area (a name from module geo), '' for a name from the main file."""
    i = name.find('__')
    if i > 0 and 'a' <= name[0].lower() <= 'z' and inst_disp(name, i) is None:
        return name[:i + 2]
    return ''


def demangle(m):
    """A type's name in C identifiers (see Gen.mg) back as it's written: L_Int is [Int]."""
    if m in ('Int', 'Float', 'Bool', 'Byte', 'Str'):
        return m
    if m.startswith('L_'):
        d = demangle(m[2:])
        return None if d is None else f'[{d}]'
    if m.startswith('O_'):
        d = demangle(m[2:])
        return None if d is None else f'{d}?'
    if m.startswith('C_'):
        d = demangle(m[2:])
        return None if d is None else f'Chan[{d}]'
    if m[:2] in ('S_', 'E_', 'X_') and len(m) > 2:
        return disp(m[2:])
    if m.startswith('M'):
        j = 1
        while j < len(m) and m[j].isdigit():
            j += 1
        if j > 1 and j < len(m) and m[j] == '_':
            n = int(m[1:j])
            a, b = demangle(m[j + 1:j + 1 + n]), demangle(m[j + 1 + n:])
            if a is not None and b is not None and n > 0:
                return '{' + a + ': ' + b + '}'
    return None


def inst_disp(name, i):
    """Pair[Int, Str] for the generic instance Pair__G3_Int3_Str (its '__' at i), or None if it isn't one."""
    rest = name[i + 2:]
    if not rest.startswith('G'):
        return None
    j, args = 1, []
    while j < len(rest):
        k = j
        while k < len(rest) and rest[k].isdigit():
            k += 1
        if k == j or k >= len(rest) or rest[k] != '_':
            return None
        n = int(rest[j:k])
        m = rest[k + 1:k + 1 + n]
        if len(m) != n or n == 0:
            return None
        d = demangle(m)
        if d is None:
            return None
        args.append(d)
        j = k + 1 + n
    if not args:
        return None
    return disp(name[:i]) + '[' + ', '.join(args) + ']'


def disp(name):
    """A name as it's written in the program: geo__area is geo.area. Only names from modules start
    with a letter and contain '__', and the first '__' ends the module's name (geo.__helper)."""
    i = name.find('__')
    if i > 0 and 'a' <= name[0].lower() <= 'z':
        inst = inst_disp(name, i)
        return inst if inst is not None else name[:i] + '.' + disp(name[i + 2:])
    return name


def jname(name):
    """A variant's name in JSON: without its module (geo__B is B)."""
    return disp(name).split('.', 1)[-1]


def decode_source(data):
    """Source bytes -> (text, None), or (None, (line, byte)) when they aren't UTF-8. Windows line endings
    count as one newline; a byte-order mark at the start is skipped."""
    try:
        src = data.decode('utf-8').replace('\r\n', '\n')
    except UnicodeDecodeError as ex:
        return None, (data[:ex.start].count(b'\n') + 1, data[ex.start])
    return (src[1:] if src.startswith('﻿') else src), None


def too_many_lines(src):
    # (a final newline doesn't start another line)
    return src.count('\n') + (0 if src.endswith('\n') or not src else 1) > MAX_LINES


def std_dir():
    """Where `import http` looks when there is no http.vu next to the importing file: $VU_STD, or the
    std folder next to this compiler."""
    return os.environ.get('VU_STD') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'std')


def load_program(path, src):
    """Parse the main file and every module it imports, directly or not (each once; cycles are fine).
    -> (all items, with module names resolved, and the path of each file by index).
    `import geo` reads geo.vu next to the importing file. A name defined in module geo becomes
    geo__name everywhere, so the rest of the compiler sees one program with no clashes."""
    files, items, mod_names, index = [(path, src)], [Parser(lex(src)).program()], [None], {}
    main_name = os.path.splitext(os.path.basename(path))[0]
    i = 0
    while i < len(files):
        for imp in items[i]:
            if imp.k != 'import' or imp.name in index:
                continue
            if not ('a' <= imp.name[0].lower() <= 'z'):
                err(imp.line, f"a module's name starts with a letter, so '{imp.name}' can't be imported")
            if imp.name == main_name:
                err(imp.line, f"'{imp.name}' is the main file, which other files can't import")
            k = len(files)
            if k > MAX_MODULES:
                err(imp.line, f'a program can have at most {MAX_MODULES} modules')
            d = os.path.dirname(files[i][0])
            mpath = os.path.join(d, imp.name + '.vu') if d else imp.name + '.vu'
            try:
                with open(mpath, 'rb') as f:
                    data = f.read()
            except OSError as ex:
                # not next to the importing file: the standard library (std/ next to the compiler)
                spath = os.path.join(std_dir(), imp.name + '.vu')
                try:
                    with open(spath, 'rb') as f:
                        data = f.read()
                    mpath = spath
                except OSError:
                    err(imp.line, f"module '{imp.name}': can't read '{mpath[:1000]}': "
                                  f"{os.strerror(ex.errno) if ex.errno else ex}")
            msrc, bad = decode_source(data)
            if bad:
                err(imp.line, f"module '{imp.name}' ({mpath}) isn't valid UTF-8 text (byte 0x{bad[1]:02x} on line "
                              f"{bad[0]}); save it as UTF-8")
            if too_many_lines(msrc):
                err(imp.line, f"module '{imp.name}' has more than {MAX_LINES:,} lines")
            index[imp.name] = k
            files.append((mpath, msrc))
            SOURCES.append((mpath, msrc))
            mod_names.append(imp.name)
            items.append(Parser(lex(msrc, base=k << LINE_BITS)).program())
        i += 1
    own = []   # per file: each name it defines -> the name the compiler uses
    for k, its in enumerate(items):
        prefix = '' if k == 0 else mod_names[k] + '__'
        table = {}
        for it in its:
            if it.k in ('fn', 'type', 'enum', 'const', 'exttype'):
                table.setdefault(it.name, prefix + it.name)
            if it.k == 'extern':
                # the C file is next to the Vu file that names it
                d = os.path.dirname(files[k][0])
                it.path = os.path.join(d, it.path) if d and not it.path.startswith('/') else it.path
                try:
                    with open(it.path, 'rb'):
                        pass
                except OSError as ex:
                    err(it.line, f"extern: can't read '{it.path[:1000]}': {os.strerror(ex.errno) if ex.errno else ex}")
            if it.k == 'enum':
                for vn, _, _ in it.variants:
                    table.setdefault(vn, prefix + vn)
        own.append(table)
    for k, its in enumerate(items):
        alias, frm = {}, {}
        for imp in its:
            if imp.k != 'import':
                continue
            m = index[imp.name] if imp.name in index else k
            if imp.names is None:
                if imp.name in own[k]:
                    err(imp.line, f"'{imp.name}' is both an imported module and a name defined in this file")
                alias[imp.name] = m
                continue
            for a in imp.names:
                if a not in own[m]:
                    err(imp.line, f"module '{imp.name}' has no '{a}'")
                if a in own[k]:
                    err(imp.line, f"'{a}' is already defined in this file")
                if a in frm and frm[a] != own[m][a]:
                    err(imp.line, f"'{a}' is imported from two modules")
                frm[a] = own[m][a]
        Resolver(own[k], alias, frm, own, index).items(its)
        if k:
            for it in its:
                if it.k in ('fn', 'type', 'enum', 'const', 'exttype'):
                    it.name = own[k][it.name]
                if it.k == 'enum':
                    it.variants = [(own[k][vn], fs, vl) for vn, fs, vl in it.variants]
    # Each file after the files it imports (depth first from the main file), so a constant or type from
    # a module is known by the time the code importing it is checked.
    order, seen = [], set()

    def visit(k):
        if k in seen:
            return
        seen.add(k)
        for imp in items[k]:
            if imp.k == 'import':
                visit(index.get(imp.name, k))
        order.append(k)
    visit(0)
    return [it for k in order for it in items[k] if it.k != 'import'], [p for p, _ in files], files


class Resolver:
    """Renames what one file refers to: its own top-level names, names it imports with from, and
    module.name. Local variables keep their names (it tracks scopes the way the checker does)."""
    def __init__(self, own, alias, frm, all_own, modules):
        self.own, self.alias, self.frm, self.all_own = own, alias, frm, all_own
        self.modules = modules   # every module in the program, imported here or not
        self.scopes = []
        self.tps = set()   # the type parameters of the item being resolved

    def local(self, name):
        return any(name in s for s in self.scopes)

    def key(self, name):
        return self.own.get(name) or self.frm.get(name)

    def ty(self, t):
        if not isinstance(t, tuple):
            return t
        if t[0] == 'gapp':
            r = self.ty(('named', t[1], t[3]))
            return ('gapp', r[1], [self.ty(a) for a in t[2]], t[3])
        if t[0] == 'named' and t[1] in self.tps:
            return t   # a type parameter of the item being resolved
        if t[0] == 'named':
            n = t[1]
            if '.' in n:
                mod, nm = n.split('.', 1)
                if mod not in self.alias:
                    err(t[2], f"unknown module '{mod}' (write 'import {mod}' at the top of the file)")
                k = self.all_own[self.alias[mod]].get(nm)
                if k is None:
                    err(t[2], f"module '{mod}' has no '{nm}'")
                return ('named', k, t[2])
            k = self.key(n)
            return ('named', k, t[2]) if k else t
        if t[0] in ('list', 'opt', 'chan'):
            return (t[0], self.ty(t[1]))
        if t[0] == 'map':
            return ('map', self.ty(t[1]), self.ty(t[2]))
        if t[0] == 'fnty':
            return ('fnty', [self.ty(a) for a in t[1]], self.ty(t[2]), t[3], t[4])
        return t

    def declare(self, name, line):
        if name in self.alias:
            err(line, f"'{name}' is the name of an imported module; use a different name")
        self.scopes[-1].add(name)

    def items(self, its):
        for it in its:
            self.tps = set(getattr(it, 'tparams', None) or [])
            if it.k == 'fn':
                it.params = [(pn, self.ty(pt), pv, pl, po) for pn, pt, pv, pl, po in it.params]
                it.ret = self.ty(it.ret)
                if it.err_ty is not None:
                    it.err_ty = self.ty(it.err_ty)
                if it.body is None:
                    continue   # an extern function: its body is C
                self.scopes = [set()]
                for pn, _, _, pl, _ in it.params:
                    self.declare(pn, pl)
                self.block(it.body)
                self.scopes = []
            elif it.k == 'type':
                it.fields = [(f, self.ty(ft), v, l) for f, ft, v, l in it.fields]
            elif it.k == 'enum':
                it.variants = [(vn, [(f, self.ty(ft), v, l) for f, ft, v, l in fs], vl) for vn, fs, vl in it.variants]
            elif it.k == 'const':
                self.expr(it.expr)

    def block(self, stmts):
        self.scopes.append(set())
        for st in stmts:
            self.stmt(st)
        self.scopes.pop()

    def stmt(self, st):
        k = st.k
        if k == 'let':
            st.ty = self.ty(st.ty)
            self.expr(st.expr)
            self.declare(st.name, st.line)
        elif k in ('exprstmt', 'return', 'fail', 'spawn'):
            self.expr(st.expr)
        elif k == 'fnstmt':
            self.expr(st.lam)
            self.declare(st.lam.name, st.line)
        elif k == 'assign':
            self.expr(st.target)
            self.expr(st.expr)
        elif k == 'if':
            self.expr(st.cond)
            self.scopes.append(set())
            if st.bind:
                self.declare(st.bind, st.line)
            self.block(st.body)
            self.scopes.pop()
            if st.els is not None:
                self.block(st.els)
        elif k == 'while':
            self.expr(st.cond)
            self.block(st.body)
        elif k == 'range':
            self.expr(st.start)
            self.expr(st.end)
            self.expr(st.step)
            self.scopes.append(set())
            self.declare(st.name, st.line)
            self.block(st.body)
            self.scopes.pop()
        elif k == 'each':
            self.expr(st.seq)
            self.scopes.append(set())
            self.declare(st.name, st.line)
            if st.name2:
                self.declare(st.name2, st.line)
            self.block(st.body)
            self.scopes.pop()
        elif k == 'match':
            self.expr(st.subj)
            for _, binds, body, line in st.arms:
                self.scopes.append(set())
                for b in binds or []:
                    self.declare(b, line)
                self.block(body)
                self.scopes.pop()

    def expr(self, e):
        if isinstance(e, (list, tuple)):
            for x in e:
                self.expr(x)
            return
        if not isinstance(e, Node):
            return
        if e.k == 'name':
            if not self.local(e.name):
                e.name = self.key(e.name) or e.name
            return
        if e.k == 'typearg':
            e.t = self.ty(e.t)
            return
        if e.k == 'lambda':
            e.params = [(pn, self.ty(pt), pl) for pn, pt, pl in e.params]
            e.ret = self.ty(e.ret)
            self.scopes.append(set())
            for pn, _, pl in e.params:
                self.declare(pn, pl)
            if e.block is not None:
                self.block(e.block)
            else:
                self.expr(e.body)
            self.scopes.pop()
            return
        if e.k == 'field' and e.e.k == 'name' and e.e.name in self.alias and not self.local(e.e.name):
            k = self.all_own[self.alias[e.e.name]].get(e.name)
            if k is None:
                err(e.line, f"module '{e.e.name}' has no '{e.name}'")
            e.k, e.name = 'name', k
            del e.e
            return
        if (e.k == 'field' and e.e.k == 'name' and e.e.name in self.modules and not self.local(e.e.name)
                and not self.key(e.e.name)):
            err(e.line, f"module '{e.e.name}' isn't imported in this file; add 'import {e.e.name}' at the top")
        for v in list(e.__dict__.values()):
            self.expr(v)


def compile_source(src, path='main.vu'):
    """-> (C source, whether it needs OpenMP for par loops). The compiler recurses over the program's
    structure, so it runs on a thread with a large stack: long expressions compile, and only absurdly
    deep nesting is reported as an error (RecursionError) instead of crashing Python."""
    import threading
    result = {}

    def work():
        try:
            SOURCES[:] = [(path, src)]
            if too_many_lines(src):
                # Panic locations pack the line into 24 bits (the file into the rest).
                err(MAX_LINES + 1, f'a source file can have at most {MAX_LINES:,} lines')
            items, paths, _ = load_program(path, src)
            g = Gen(items, paths)
            result['ok'] = (g.build(), g.uses_par, g.links, bool(g.externs))
        except BaseException as ex:
            result['err'] = ex
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(1000000)
    threading.stack_size(1 << 30)
    t = threading.Thread(target=work)
    t.start()
    t.join()
    threading.stack_size(0)
    sys.setrecursionlimit(old)
    if 'err' in result:
        raise result['err']
    return result['ok']


def json_str(text):
    """A JSON string: quotes, backslashes and control characters escaped, everything else as is."""
    out = ['"']
    for ch in text:
        if ch in '"\\':
            out.append('\\' + ch)
        elif ord(ch) < 0x20:
            out.append(f'\\u{ord(ch):04x}')
        else:
            out.append(ch)
    return ''.join(out) + '"'


def report(path, src, e, as_json=False):
    k = e.line >> LINE_BITS
    if 0 < k < len(SOURCES):
        path, src = SOURCES[k]   # the error is in a module
    e.line = ln(e.line)
    lines = src.split('\n')
    if as_json:
        source = lines[e.line - 1].rstrip(WS) if 1 <= e.line <= len(lines) else ''
        print(f'{{"type": "error", "file": {json_str(path)}, "line": {e.line}, "message": {json_str(e.msg)}, '
              f'"source": {json_str(source)}}}', file=sys.stderr)
        return
    print(f'{path}:{e.line}: error: {e.msg}', file=sys.stderr)
    if 1 <= e.line <= len(lines):
        print(f'  {e.line} | {lines[e.line - 1].rstrip(WS)}', file=sys.stderr)


def main(argv):
    if not argv or argv[0] in ('-h', '--help') or argv[0] not in ('build', 'run', 'check'):
        print(__doc__.strip())
        return 0 if argv and argv[0] in ('-h', '--help') else 2
    cmd, rest = argv[0], argv[1:]
    opts = {'o': None, 'debug': False, 'release': False, 'json': False, 'malloc': False, 'san': False, 'san_pool': False, 'tsan': False, 'time': False,
            'emit_c': None}
    path, prog_args, i = None, [], 0
    while i < len(rest):
        a = rest[i]
        if cmd == 'run' and path:
            prog_args = rest[i:]
            break
        if a in ('-o', '--emit-c'):
            opts['o' if a == '-o' else 'emit_c'] = rest[i + 1]
            i += 2
        elif a in ('--debug', '--release', '--json', '--malloc', '--san', '--san-pool', '--tsan', '--time'):
            opts[a[2:].replace('-', '_')] = True
            i += 1
        elif a.startswith('-'):
            print(f'vu: unknown option {a}', file=sys.stderr)
            return 2
        else:
            path = a
            i += 1
    if not path:
        print('vu: no input file', file=sys.stderr)
        return 2
    def fail_early(line, msg):
        """An error found before compiling: reported like any other, but without a source line."""
        if opts['json']:
            print(f'{{"type": "error", "file": {json_str(path)}, "line": {line}, "message": {json_str(msg)}, '
                  f'"source": ""}}', file=sys.stderr)
        elif line:
            print(f'{path}:{line}: error: {msg}', file=sys.stderr)
        else:
            print(f'vu: {msg}', file=sys.stderr)
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except OSError as ex:
        fail_early(0, f"can't read '{path[:1000]}': {os.strerror(ex.errno) if ex.errno else ex}")
        return 2
    try:
        # Windows line endings: \r\n ends a line like \n. A lone \r is an ordinary character.
        src = data.decode('utf-8').replace('\r\n', '\n')
        if src.startswith('\ufeff'):
            src = src[1:]   # a byte-order mark some editors put at the start
    except UnicodeDecodeError as ex:
        fail_early(data[:ex.start].count(b'\n') + 1,
                   f"this file isn't valid UTF-8 text (byte 0x{data[ex.start]:02x}); save it as UTF-8")
        return 1
    t0 = time.perf_counter()
    try:
        csrc, uses_par, links, has_ext = compile_source(src, path)
    except VuError as e:
        report(path, src, e, opts['json'])
        return 1
    except RecursionError:
        msg = 'the program is nested too deeply to compile (simplify the deepest expression or block)'
        if opts['json']:
            print(f'{{"type": "error", "file": {json_str(path)}, "line": 0, "message": {json_str(msg)}, '
                  f'"source": ""}}', file=sys.stderr)
        else:
            print(f'{path}: error: {msg}', file=sys.stderr)
        return 1
    t1 = time.perf_counter()
    if cmd == 'check':
        # Every error comes from the front end, so stopping here gives the full answer without gcc.
        if opts['time']:
            print(f'vu: front end {1000 * (t1 - t0):.1f} ms', file=sys.stderr)
        return 0
    if opts['tsan']:
        # With dynamic scheduling, threads hand out chunks through an atomic counter, which ThreadSanitizer
        # sees as synchronization and which can hide real races. A static split has no such hand-off.
        csrc = csrc.replace('schedule(dynamic)', 'schedule(static)')
    work = tempfile.mkdtemp(prefix='vu-')
    cfile = opts['emit_c'] or os.path.join(work, 'out.c')
    with open(cfile, 'w') as f:
        f.write(csrc)
    out = opts['o'] or (os.path.splitext(path)[0] if cmd == 'build' else os.path.join(work, 'prog'))
    # Vu semantics: overflow is checked in the generated code (-fwrapv only covers loop counters),
    # sqrt never sets errno, floating point raises no traps,
    # and is never fused (a*b+c rounds twice), so results are identical on every machine
    flags = ['-std=gnu11', '-fwrapv', '-fno-math-errno', '-fno-trapping-math', '-ffp-contract=off', '-w']
    # `run` is the edit-and-test loop, so it builds unoptimized (several times faster to compile)
    # unless asked for --release; `build` makes the optimized binary unless asked for --debug.
    quick = opts['debug'] or (cmd == 'run' and not opts['release'])
    # Quick builds also keep the shadow call stack that gives panics a backtrace.
    flags += ['-O0', '-g', '-DVU_TRACE'] if quick else ['-O3', '-march=native']
    if opts['json']:
        flags.append('-DVU_JSON_PANIC')
    if uses_par:
        flags.append('-fopenmp')
    if has_ext:
        flags += ['-iquote', '.']   # extern C files are named relative to the current directory
    if opts['malloc'] or opts['san']:
        flags.append('-DVU_MALLOC')
    if opts['san'] or opts['san_pool']:
        # --san uses malloc/free (so LeakSanitizer sees every node); --san-pool keeps Vu's node allocator,
        # with freed nodes poisoned so any use after free is still reported
        flags += ['-fsanitize=address,undefined', '-fno-sanitize-recover=undefined', '-fno-omit-frame-pointer', '-g']
    if opts['tsan']:
        # ThreadSanitizer. Use CC=clang and run with OMP_TOOL_LIBRARIES=<llvm>/lib/libarcher.so so that
        # OpenMP's own synchronization is understood and only real data races are reported.
        flags += ['-fsanitize=thread', '-g']
    r = subprocess.run([os.environ.get('CC', 'cc'), *flags, cfile, '-o', out, '-lm'] + ['-l' + l for l in links])
    t2 = time.perf_counter()
    if r.returncode:
        if has_ext:
            print('vu: the C compiler rejected the program; errors in an extern C file are shown above',
                  file=sys.stderr)
            return 1
        print('vu: internal error: the C compiler rejected the generated code', file=sys.stderr)
        return 3
    if opts['time']:
        print(f'vu: front end {1000 * (t1 - t0):.1f} ms, C compiler {1000 * (t2 - t1):.1f} ms', file=sys.stderr)
    if cmd == 'run':
        sys.stdout.flush()
        os.execv(out, [out] + prog_args)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
