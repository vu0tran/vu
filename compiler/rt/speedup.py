#!/usr/bin/env python3
"""vu speedup: a slow Python function, ported to Vu, checked, and swapped in.

    vu speedup FILE.py:FUNC [options]

1. Reads FUNC: its source, its type hints (int, float, bool, str, bytes, list[...], dict[str, ...],
   tuple[X, ...], X | None), and the module globals it uses.
2. Makes inputs: generated from the hints (edge cases, Unicode, sizes), plus real calls recorded from
   a script (--record) or given in a file (--inputs-file). Runs the original on each and keeps what it
   returns or raises. A function that changes its arguments is refused.
3. Gets a port: a Vu file given with --port (written by you or a coding agent), or one a model writes
   (ANTHROPIC_API_KEY or OPENAI_API_KEY set) in a loop that feeds back the compiler's errors and every
   answer that differs. With neither, it writes the prompt for an agent and stops.
4. Builds the port as a library and runs it on every input in a separate process: each answer must be
   the same as the original's (same types; same exception type where it raises).
5. Measures both, writes a loader next to the module, and adds two lines after FUNC so the Vu version
   runs instead. Anything the Vu version can't take (an int too big for 64 bits, a string Python can't
   encode, an argument of another type, a panic) runs the original instead, so the swap never changes
   what the program does.
"""
import argparse, ast, copy, ctypes, ctypes.util, importlib.util, inspect, json, math, os, random
import re, shutil, signal, subprocess, sys, tempfile, textwrap, time, typing, types, urllib.error, urllib.request

VERSION = 1

# ---------------------------------------------------------------- types
# A type is a tuple: ("int",) ("float",) ("bool",) ("str",) ("bytes",) ("none",)
# ("list", T) ("dict", T) (keys are str) ("opt", T) ("tuple", T) (a tuple of any length, all T)

class Unsupported(Exception):
    pass

def hint_type(h, where):
    if h is int: return ("int",)
    if h is float: return ("float",)
    if h is bool: return ("bool",)
    if h is str: return ("str",)
    if h is bytes: return ("bytes",)
    if h is None or h is type(None): return ("none",)
    origin, args = typing.get_origin(h), typing.get_args(h)
    if origin in (list, typing.List) and len(args) == 1:
        return ("list", hint_type(args[0], where))
    if origin in (dict, typing.Dict) and len(args) == 2:
        if args[0] is not str: raise Unsupported(f"{where}: dict keys must be str (JSON's), not {args[0]!r}")
        return ("dict", hint_type(args[1], where))
    if origin in (tuple, typing.Tuple) and len(args) == 2 and args[1] is Ellipsis:
        return ("tuple", hint_type(args[0], where))
    if origin is typing.Union or (hasattr(types, "UnionType") and origin is types.UnionType):
        rest = [a for a in args if a is not type(None)]
        if len(rest) == 1 and len(args) == 2: return ("opt", hint_type(rest[0], where))
    if h is list or h is dict or h is tuple:
        raise Unsupported(f"{where}: say what's in it ({h.__name__}[...])")
    raise Unsupported(f"{where}: {h!r} isn't a type vu speedup handles yet "
                      "(int, float, bool, str, bytes, list[T], dict[str, T], tuple[T, ...], T | None)")

def vu_type(t):
    k = t[0]
    if k == "int": return "Int"
    if k == "float": return "Float"
    if k == "bool": return "Bool"
    if k == "str": return "Str"
    if k == "bytes": return "[Byte]"
    if k in ("list", "tuple"): return "[" + vu_type(t[1]) + "]"
    if k == "dict": return "{Str: " + vu_type(t[1]) + "}"
    if k == "opt": return vu_type(t[1]) + "?"
    raise Unsupported(f"no Vu type for {t}")

def show_type(t):
    k = t[0]
    if k in ("list", "tuple", "opt", "dict"):
        inner = show_type(t[1])
        return {"list": f"list[{inner}]", "tuple": f"tuple[{inner}, ...]", "opt": f"{inner} | None",
                "dict": f"dict[str, {inner}]"}[k]
    return k if k != "none" else "None"

def has_bytes(t):
    return t[0] == "bytes" or (len(t) > 1 and has_bytes(t[1]))

# Passed directly (no JSON): numbers, Bool, str and bytes, lists of numbers, and lists of str (one
# UTF-8 buffer of the strings joined by NUL, and their count: a string holding a NUL goes as JSON).
NATIVE = {("int",), ("float",), ("bool",), ("str",), ("bytes",), ("list", ("int",)), ("list", ("float",)),
          ("list", ("str",))}

def native_ok(params, ret):
    return all(t in NATIVE for _, t, _ in params) and (ret in NATIVE or ret == ("none",))

# ---------------------------------------------------------------- reading the function

class Target:
    pass

def load_target(spec):
    if ":" not in spec: raise SystemExit("vu speedup: name the function as FILE.py:FUNC")
    path, name = spec.rsplit(":", 1)
    path = os.path.abspath(path)
    if not os.path.isfile(path): raise SystemExit(f"vu speedup: no file {path}")
    t = Target()
    t.path, t.name = path, name
    t.dir = os.path.dirname(path)
    t.modname = os.path.splitext(os.path.basename(path))[0]
    t.package = os.path.exists(os.path.join(t.dir, "__init__.py"))
    t.module = import_path(path, t.modname)
    f = getattr(t.module, name, None)
    if f is None: raise SystemExit(f"vu speedup: {os.path.basename(path)} has no {name}")
    f = getattr(f, "__vu_original__", f)
    if not isinstance(f, types.FunctionType): raise SystemExit(f"vu speedup: {name} isn't a plain function")
    t.func = f
    sig = inspect.signature(f)
    try:
        hints = typing.get_type_hints(f)
    except Exception as e:
        raise SystemExit(f"vu speedup: can't read {name}'s type hints: {e}")
    t.params = []   # (name, type, default or inspect._empty)
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            raise SystemExit(f"vu speedup: {name} takes *{p.name}; only plain parameters are handled")
        if p.kind == p.KEYWORD_ONLY:
            raise SystemExit(f"vu speedup: {name}'s keyword-only parameter {p.name} isn't handled yet")
        if p.name not in hints: raise SystemExit(f"vu speedup: {name}'s parameter {p.name} has no type hint")
        try:
            t.params.append((p.name, hint_type(hints[p.name], f"parameter {p.name}"), p.default))
        except Unsupported as e:
            raise SystemExit(f"vu speedup: {name}: {e}")
    if "return" not in hints: raise SystemExit(f"vu speedup: {name} has no return type hint")
    try:
        t.ret = hint_type(hints["return"], "the result")
    except Unsupported as e:
        raise SystemExit(f"vu speedup: {name}: {e}")
    if any(has_bytes(ty) and ty != ("bytes",) for _, ty, _ in t.params) or (has_bytes(t.ret) and t.ret != ("bytes",)):
        raise SystemExit(f"vu speedup: {name}: bytes inside lists or dicts aren't handled yet")
    t.native = native_ok(t.params, t.ret)
    if not t.native and (any(ty == ("bytes",) for _, ty, _ in t.params) or t.ret == ("bytes",)):
        raise SystemExit(f"vu speedup: {name}: bytes work only with ints, floats, bools, str and lists of numbers")
    t.source = textwrap.dedent(inspect.getsource(f))
    with open(path, encoding="utf-8") as fh:
        t.file_source = fh.read()
    t.context = context_of(t)
    return t

def import_path(path, modname):
    d = os.path.dirname(path)
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[modname] = m
    spec.loader.exec_module(m)
    return m

def context_of(t):
    """The module globals the function uses: their source (functions, classes) or value (constants)."""
    out, seen = [], set()
    def visit(f):
        for n in f.__code__.co_names:
            if n in seen or n == t.name: continue
            seen.add(n)
            if not hasattr(t.module, n): continue
            v = getattr(t.module, n)
            if isinstance(v, types.ModuleType):
                out.append(f"import {v.__name__}" + (f" as {n}" if v.__name__ != n else ""))
                # the module's Python functions and classes the function names (module.name): their
                # source, so a model sees what the call does (difflib.get_close_matches, say)
                for attr in f.__code__.co_names:
                    w = getattr(v, attr, None)
                    if isinstance(w, (types.FunctionType, type)) and attr not in seen:
                        try:
                            src = textwrap.dedent(inspect.getsource(w))
                        except (OSError, TypeError):
                            continue
                        seen.add(attr)
                        out.append(f"# {v.__name__}.{attr}:\n" + src[:20000])
                        if isinstance(w, types.FunctionType):
                            for g2 in w.__code__.co_names:
                                u = w.__globals__.get(g2)
                                if isinstance(u, (types.FunctionType, type)) and g2 not in seen and getattr(u, "__module__", "") == v.__name__:
                                    try:
                                        out.append(f"# {v.__name__}.{g2}:\n" + textwrap.dedent(inspect.getsource(u))[:20000])
                                        seen.add(g2)
                                    except (OSError, TypeError):
                                        pass
            elif isinstance(v, (types.FunctionType, type)) and getattr(v, "__module__", None) == t.module.__name__:
                try:
                    out.append(textwrap.dedent(inspect.getsource(v)))
                except OSError:
                    pass
                if isinstance(v, types.FunctionType): visit(v)
            elif isinstance(v, (int, float, str, bool, bytes, tuple, list, dict, frozenset, set)) or v is None:
                r = repr(v)
                out.append(f"{n} = {r if len(r) < 4000 else r[:4000] + ' ...'}")
        for c in f.__code__.co_consts:
            if isinstance(c, types.CodeType):
                visit(types.FunctionType(c, f.__globals__))
    visit(t.func)
    return "\n\n".join(out)

# ---------------------------------------------------------------- inputs

ALPHABETS = [
    "abcdefghijklmnopqrstuvwxyz",
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:-_'\"!?()/\\",
    "aeiouéèêëàâäîïôöùûüçñßÉÀÖÜ漢字かなカナ한국어ΩλσςΣΑΒΓ😀👍🏽🇫🇷éﬁİıẞǅ",
    " \t\n\r  abc",
]

class Gen:
    def __init__(self, seed, big=False):
        self.big = big   # lists and dicts of 500 to 2,000 (for timing)
        self.length = None   # a length every top-level list of a call shares (when set)
        self.rng = random.Random(seed)
        self.pool = [self.fresh_str() for _ in range(40)]

    def fresh_str(self):
        r = self.rng
        n = r.choices([0, 1, 2, 3, 4, 6, 9, 14, 30, 80], [3, 6, 8, 10, 12, 14, 14, 12, 6, 3])[0]
        a = r.choices(ALPHABETS, [40, 25, 25, 10])[0]
        return "".join(r.choice(a) for _ in range(n))

    def string(self):
        r = self.rng
        x = r.random()
        if x < 0.45:
            s = r.choice(self.pool)
            if r.random() < 0.5 and s:   # a near copy: one character changed, added or removed
                i = r.randrange(len(s) + 1)
                op = r.randrange(3)
                c = r.choice(r.choice(ALPHABETS))
                s = s[:i] + c + s[i + 1:] if op == 0 else s[:i] + c + s[i:] if op == 1 else s[:i] + s[i + 1:]
            return s
        return self.fresh_str()

    def value(self, t, depth=0):
        r = self.rng
        k = t[0]
        if k == "int":
            b = r.random()
            if b < 0.45: return r.randint(-10, 10)
            if b < 0.75: return r.randint(-1000, 1000)
            if b < 0.95: return r.randint(-2**31, 2**31)
            return r.choice([2**62, -2**62, 2**63 - 1, -2**63, 2**64, 10**30, -(10**30)])
        if k == "float":
            b = r.random()
            if b < 0.4: return round(r.uniform(-10, 10), r.randint(0, 6))
            if b < 0.7: return r.uniform(-1e6, 1e6)
            if b < 0.85: return float(r.randint(-100, 100))
            return r.choice([0.0, -0.0, 1e-300, -1e300, 1e300, 0.1, 1 / 3, 2.5, float("inf"), float("-inf"), float("nan")])
        if k == "bool": return r.random() < 0.5
        if k == "str": return self.string()
        if k == "bytes": return bytes(r.randrange(256) for _ in range(r.choice([0, 1, 3, 8, 30, 100])))
        if k in ("list", "tuple") and depth == 0 and self.length is not None:
            xs = [self.value(t[1], depth + 1) for _ in range(self.length)]
            return tuple(xs) if k == "tuple" else xs
        if k in ("list", "tuple") and self.big and depth == 0:
            xs = [self.value(t[1], depth + 1) for _ in range(r.randint(500, 2000))]
            return tuple(xs) if k == "tuple" else xs
        if k == "dict" and self.big and depth == 0:
            return {self.string(): self.value(t[1], depth + 1) for _ in range(r.randint(500, 2000))}
        if k in ("list", "tuple"):
            n = r.choices([0, 1, 2, 3, 5, 8, 15, 40, 120], [5, 10, 12, 14, 16, 15, 13, 10, 5])[0] if depth < 2 else r.randint(0, 4)
            xs = [self.value(t[1], depth + 1) for _ in range(n)]
            return tuple(xs) if k == "tuple" else xs
        if k == "dict":
            n = r.choices([0, 1, 2, 4, 8, 20], [8, 15, 20, 25, 20, 12])[0] if depth < 2 else r.randint(0, 3)
            return {self.string(): self.value(t[1], depth + 1) for _ in range(n)}
        if k == "opt":
            return None if r.random() < 0.2 else self.value(t[1], depth)
        raise Unsupported(str(t))

def near_default(g, ty, d):
    """A value like a parameter's default (most calls use such values; random ones are mostly invalid)."""
    r = g.rng
    if ty == ("int",) and type(d) is int:
        return r.randint(min(0, d), max(1, abs(d) * 3 + 3))
    if ty == ("float",) and type(d) is float:
        if 0.0 <= d <= 1.0: return r.choice([0.0, 1.0, d, r.random(), round(r.random(), 2)])
        return r.uniform(min(0.0, d * 3), max(1.0, d * 3))
    return d if r.random() < 0.3 else g.value(ty)

def generate(t, n, seed, big=False):
    g = Gen(seed, big)
    calls = []
    nreq = sum(1 for _, _, d in t.params if d is inspect._empty)
    lists = sum(1 for _, ty, _ in t.params if ty[0] in ("list", "tuple"))
    for _ in range(n):
        # functions given several lists mostly want them the same length (pairs, columns): most calls
        # give them one
        g.length = None
        if lists > 1 and g.rng.random() < 0.75:
            g.length = g.rng.randint(500, 2000) if big else g.rng.choices([0, 1, 2, 3, 5, 8, 15, 40, 120], [4, 8, 10, 12, 16, 16, 14, 12, 8])[0]
        args = [near_default(g, ty, d) if d is not inspect._empty and g.rng.random() < 0.8 else g.value(ty)
                for _, ty, d in t.params]
        # sometimes leave out the parameters that have defaults, to use them
        if len(args) > nreq and g.rng.random() < 0.3:
            args = args[:g.rng.randint(nreq, len(args) - 1)]
        calls.append(args)
    return calls

def record_calls(t, argv, limit):
    """Runs a script (or -m module) and keeps the arguments of each call to the function."""
    calls = []
    code = t.func.__code__
    def prof(frame, event, arg):
        if event == "call" and frame.f_code is code and len(calls) < limit:
            loc = frame.f_locals
            calls.append([copy.deepcopy(loc[p]) for p, _, _ in t.params])
    import runpy
    old = sys.argv
    sys.argv = argv[:]
    sys.setprofile(prof)
    try:
        if argv[0] == "-m": runpy.run_module(argv[1], run_name="__main__", alter_sys=True)
        else: runpy.run_path(argv[0], run_name="__main__")
    except SystemExit:
        pass
    finally:
        sys.setprofile(None)
        sys.argv = old
    return calls

# ---------------------------------------------------------------- running the original

class Timeout(Exception):
    pass

def run_original(f, calls, per_call=5.0):
    """Each call's outcome: ["ok", value] or ["raise", exception type name, message]."""
    out = []
    def on_alarm(sig, frm): raise Timeout()
    old = signal.signal(signal.SIGALRM, on_alarm) if hasattr(signal, "SIGALRM") else None
    try:
        for args in calls:
            before = copy.deepcopy(args)
            try:
                if old is not None: signal.setitimer(signal.ITIMER_REAL, per_call)
                v = f(*args)
                if old is not None: signal.setitimer(signal.ITIMER_REAL, 0)
                res = ["ok", v]
            except Timeout:
                res = ["slow"]
            except RecursionError:
                res = ["slow"]
            except Exception as e:
                if old is not None: signal.setitimer(signal.ITIMER_REAL, 0)
                res = ["raise", type(e).__name__, str(e)]
            if not same_value(before, args):
                raise SystemExit(f"vu speedup: {f.__name__} changes its arguments (called with {short(before)}); "
                                 "only functions that return their result and leave their arguments alone are handled")
            out.append(res)
    finally:
        if old is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)
    return out

def same_value(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, float): return repr(a) == repr(b)
    if isinstance(a, (list, tuple)): return len(a) == len(b) and all(same_value(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return len(a) == len(b) and list(a) == list(b) and all(same_value(a[k], b[k]) for k in a)
    return a == b

def short(v, n=300):
    r = repr(v)
    return r if len(r) <= n else r[:n] + f"... ({len(r)} characters)"

def fits(v, t):
    """Whether a value is what its type says (the original may return something else)."""
    k = t[0]
    if k == "int": return type(v) is int
    if k == "float": return type(v) is float
    if k == "bool": return type(v) is bool
    if k == "str": return type(v) is str
    if k == "bytes": return type(v) is bytes
    if k == "none": return v is None
    if k == "list": return type(v) is list and all(fits(x, t[1]) for x in v)
    if k == "tuple": return type(v) is tuple and all(fits(x, t[1]) for x in v)
    if k == "dict": return type(v) is dict and all(type(a) is str and fits(b, t[1]) for a, b in v.items())
    if k == "opt": return v is None or fits(v, t[1])
    return False

# ---------------------------------------------------------------- the Vu side

def port_signature(t):
    ps = ", ".join(f"{fix_name(p)}: {vu_type(ty)}" for p, ty, _ in t.params)
    ret = "" if t.ret == ("none",) else " -> " + vu_type(t.ret)
    return f"fn {t.name}({ps}){ret}"

VU_WORDS = {"fn", "let", "var", "if", "elif", "else", "for", "in", "while", "return", "match", "type", "enum",
            "import", "export", "const", "and", "or", "not", "true", "false", "nil", "fail", "throws", "own",
            "spawn", "select", "par", "break", "continue", "by", "extern", "interface", "impl", "test", "as"}

def fix_name(n):
    return n + "_" if n in VU_WORDS else n

def shim(t, port):
    """The exported function Python calls, appended to the port (so the port's line numbers stand)."""
    m = re.search(r"^fn\s+" + re.escape(t.name) + r"\s*\(.*$", port, re.M)
    throws = bool(m and re.search(r"\bthrows\b", port[m.start():port.find(":\n", m.start()) + 1 if port.find(":\n", m.start()) >= 0 else len(port)]))
    q = "?" if throws else ""
    names = [f"p{i}" for i in range(len(t.params))]
    lines = ["", "", "# ---- generated by vu speedup: what Python calls"]
    if t.native:
        ps, pre, cargs = [], [], []
        for n, (_, ty, _) in zip(names, t.params):
            if ty == ("list", ("str",)):
                ps += [f"{n}: Str", f"{n}_n: Int"]
                pre += [f"  var {n}_l: [Str] = []", f"  if {n}_n > 0: {n}_l = {n}.split(\"\\0\")"]
                cargs.append(f"{n}_l")
            else:
                ps.append(f"{n}: {vu_type(ty)}")
                cargs.append(n)
        strs = t.ret == ("list", ("str",))
        ret = "" if t.ret == ("none",) else " -> Str" if strs else " -> " + vu_type(t.ret)
        lines.append(f"export fn py_{t.name}({', '.join(ps)}){ret} throws:")
        lines += pre
        call = f"{t.name}({', '.join(cargs)}){q}"
        if t.ret == ("none",): lines.append(f"  {call}")
        elif strs:
            lines += [f"  let r = {call}", "  for x in r:", f"    if \"\\0\" in x: fail \"vu-speedup: result\"",
                      "  return \"{r.len}:\" + \"\\0\".join(r)"]
        else: lines.append(f"  return {call}")
    else:
        lines.append(f"type PyArgs_{t.name}:")
        for n, (_, ty, _) in zip(names, t.params): lines.append(f"  {n}: {vu_type(ty)}")
        if not t.params: lines.append("  unused: Int?")
        lines.append(f"export fn py_{t.name}(args: Str) -> Str throws:")
        lines.append(f"  let a = from_json(args, PyArgs_{t.name}) else fail \"vu-speedup: arguments\"")
        call = f"{t.name}({', '.join('a.' + n for n in names)}){q}"
        if t.ret == ("none",):
            lines.append(f"  {call}")
            lines.append('  return "null"')
        else:
            lines.append(f"  return to_json({call})")
    return port.rstrip() + "\n" + "\n".join(lines) + "\n"

def build(vu, t, port, out_dir):
    """Builds the port as a library; returns (ok, compiler output)."""
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(out_dir, t.name + ".vu")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(shim(t, port))
    lib = os.path.join(out_dir, lib_name(t.name))
    r = subprocess.run([vu, "build", "--lib", src, "-o", lib], capture_output=True, text=True)
    msg = (r.stdout + r.stderr).strip()
    ok = r.returncode == 0 and os.path.exists(lib)
    t.ext = build_ext(t, out_dir) if ok and t.native and not os.environ.get("VU_SPEEDUP_CTYPES") else ""
    return ok, msg

# ---------------------------------------------------------------- the CPython extension (direct calls)
# When Python's headers and a C compiler are there, a small extension module calls the Vu function
# straight from Python's objects (as PyO3 does for Rust), instead of through ctypes: about a tenth of
# the cost of a call. It returns NotImplemented for anything the Vu version can't take, and the
# loader then runs the original.

def ext_source(t):
    n = len(t.params)
    FB = "goto fb;"
    L = ['#define PY_SSIZE_T_CLEAN', '#include <Python.h>', '#include <stdint.h>', '#include <stdbool.h>',
         '#include <stdlib.h>', '#include <string.h>', f'#include "{t.name}.h"', '',
         '/* the Vu function failed: an exception of the type its message names, or NotImplemented (run the',
         '   original) for a panic or what it hands back */',
         'static PyObject *vu_err_to_py(char *m) {',
         '    if (!strncmp(m, "panic: ", 7) || !strcmp(m, "vu-speedup: arguments") || !strcmp(m, "vu-speedup: result") || !strcmp(m, "vu-speedup: fallback")) {',
         '        free(m); Py_RETURN_NOTIMPLEMENTED;', '    }',
         '    const char *sep = strstr(m, ": ");', '    PyObject *exc = PyExc_RuntimeError; const char *text = m;',
         '    if (sep) {', '        PyObject *name = PyUnicode_FromStringAndSize(m, sep - m);',
         '        PyObject *c = name ? PyDict_GetItemWithError(PyEval_GetBuiltins(), name) : NULL;', '        Py_XDECREF(name);',
         '        if (c && PyType_Check(c) && PyType_IsSubtype((PyTypeObject *)c, (PyTypeObject *)PyExc_BaseException)) { exc = c; text = sep + 2; }',
         '        PyErr_Clear();', '    }',
         '    PyErr_SetString(exc, text); free(m); return NULL;', '}', '',
         'static PyObject *vu_call(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {',
         '    PyObject *res = NULL; char *err = NULL; int64_t out_n = 0; (void)out_n; (void)self;']
    tops, body, frees, cargs = [], [], [], []
    for i, (_, ty, _) in enumerate(t.params):
        a = f"args[{i}]"
        if ty == ("int",):
            tops.append(f'    long long v{i} = 0; int o{i} = 0;')
            body += [f'    if (!PyLong_CheckExact({a})) {FB}', f'    v{i} = PyLong_AsLongLongAndOverflow({a}, &o{i});',
                     f'    if (o{i} || (v{i} == -1 && PyErr_Occurred())) {FB}']
            cargs.append(f"(int64_t)v{i}")
        elif ty == ("float",):
            tops.append(f'    double v{i} = 0;')
            body += [f'    if (!PyFloat_CheckExact({a})) {FB}', f'    v{i} = PyFloat_AS_DOUBLE({a});']
            cargs.append(f"v{i}")
        elif ty == ("bool",):
            tops.append(f'    bool v{i} = false;')
            body += [f'    if (!PyBool_Check({a})) {FB}', f'    v{i} = {a} == Py_True;']
            cargs.append(f"v{i}")
        elif ty == ("str",):
            tops.append(f'    const char *v{i} = NULL; Py_ssize_t n{i} = 0;')
            body += [f'    if (!PyUnicode_Check({a})) {FB}', f'    v{i} = PyUnicode_AsUTF8AndSize({a}, &n{i});', f'    if (!v{i}) {FB}']
            cargs += [f"v{i}", f"(int64_t)n{i}"]
        elif ty == ("bytes",):
            tops.append(f'    const char *v{i} = NULL; Py_ssize_t n{i} = 0;')
            body += [f'    if (!PyBytes_CheckExact({a})) {FB}', f'    v{i} = PyBytes_AS_STRING({a}); n{i} = PyBytes_GET_SIZE({a});']
            cargs += [f"(const uint8_t *)v{i}", f"(int64_t)n{i}"]
        elif ty in (("list", ("int",)), ("list", ("float",))):
            ct = "int64_t" if ty[1] == ("int",) else "double"
            tops.append(f'    {ct} *v{i} = NULL; Py_ssize_t n{i} = 0;')
            frees.append(f"v{i}")
            body += [f'    if (!PyList_CheckExact({a})) {FB}', f'    n{i} = PyList_GET_SIZE({a});',
                     f'    v{i} = ({ct} *)malloc(sizeof({ct}) * (size_t)(n{i} ? n{i} : 1));',
                     f'    if (!v{i}) {{ res = PyErr_NoMemory(); goto done; }}',
                     f'    for (Py_ssize_t k = 0; k < n{i}; k++) {{', f'        PyObject *x = PyList_GET_ITEM({a}, k);']
            if ct == "int64_t":
                body += [f'        if (!PyLong_CheckExact(x)) {FB}', '        int o = 0; long long y = PyLong_AsLongLongAndOverflow(x, &o);',
                         f'        if (o || (y == -1 && PyErr_Occurred())) {FB}', f'        v{i}[k] = (int64_t)y;', '    }']
            else:
                body += [f'        if (!PyFloat_CheckExact(x)) {FB}', f'        v{i}[k] = PyFloat_AS_DOUBLE(x);', '    }']
            cargs += [f"v{i}", f"(int64_t)n{i}"]
        elif ty == ("list", ("str",)):
            tops.append(f'    char *v{i} = NULL; Py_ssize_t c{i} = 0, n{i} = 0;')
            frees.append(f"v{i}")
            body += [f'    if (!PyList_CheckExact({a})) {FB}', f'    c{i} = PyList_GET_SIZE({a});',
                     f'    for (Py_ssize_t k = 0; k < c{i}; k++) {{', f'        PyObject *x = PyList_GET_ITEM({a}, k); Py_ssize_t m;',
                     f'        if (!PyUnicode_Check(x)) {FB}', '        const char *u = PyUnicode_AsUTF8AndSize(x, &m);',
                     f'        if (!u || memchr(u, 0, (size_t)m)) {FB}', f'        n{i} += m + (k > 0);', '    }',
                     f'    v{i} = (char *)malloc((size_t)n{i} + 1);', f'    if (!v{i}) {{ res = PyErr_NoMemory(); goto done; }}',
                     f'    {{ char *w = v{i}; for (Py_ssize_t k = 0; k < c{i}; k++) {{ Py_ssize_t m; const char *u = PyUnicode_AsUTF8AndSize(PyList_GET_ITEM({a}, k), &m); if (k) *w++ = 0; memcpy(w, u, (size_t)m); w += m; }} }}']
            cargs += [f"v{i}", f"(int64_t)n{i}", f"(int64_t)c{i}"]
    L += tops
    L += [f'    if (nargs != {n}) {FB}'] + body
    r = t.ret
    big = r[0] in ("str", "bytes", "list")
    if big: cargs.append("&out_n")
    cargs.append("&err")
    call = f"py_{t.name}({', '.join(cargs)})"
    rtype = {("int",): "int64_t", ("float",): "double", ("bool",): "bool", ("str",): "char *", ("list", ("str",)): "char *",
             ("bytes",): "uint8_t *", ("list", ("int",)): "int64_t *", ("list", ("float",)): "double *"}.get(r)
    L += [f'    {call};'] if r == ("none",) else [f'    {rtype} r = {call};']
    L += ['    if (err) { res = vu_err_to_py(err); goto done; }']
    if r == ("none",): L += ['    res = Py_None; Py_INCREF(res);']
    elif r == ("int",): L += ['    res = PyLong_FromLongLong((long long)r);']
    elif r == ("float",): L += ['    res = PyFloat_FromDouble(r);']
    elif r == ("bool",): L += ['    res = PyBool_FromLong(r);']
    elif r == ("str",): L += ['    res = PyUnicode_DecodeUTF8(r, (Py_ssize_t)out_n, "strict"); free(r);']
    elif r == ("bytes",): L += ['    res = PyBytes_FromStringAndSize((const char *)r, (Py_ssize_t)out_n); free(r);']
    elif r in (("list", ("int",)), ("list", ("float",))):
        mk = "PyLong_FromLongLong((long long)r[k])" if r[1] == ("int",) else "PyFloat_FromDouble(r[k])"
        L += ['    res = PyList_New((Py_ssize_t)out_n);',
              f'    for (Py_ssize_t k = 0; res && k < (Py_ssize_t)out_n; k++) {{ PyObject *x = {mk}; if (!x) {{ Py_CLEAR(res); break; }} PyList_SET_ITEM(res, k, x); }}',
              '    free(r);']
    elif r == ("list", ("str",)):
        L += ['    {', '        char *p = r, *end = r + out_n; long long c = strtoll(p, &p, 10); p++;',
              '        res = PyList_New((Py_ssize_t)c);',
              '        for (long long k = 0; res && k < c; k++) {',
              '            char *z = memchr(p, 0, (size_t)(end - p)); if (!z) z = end;',
              '            PyObject *x = PyUnicode_DecodeUTF8(p, z - p, "strict"); if (!x) { Py_CLEAR(res); break; }',
              '            PyList_SET_ITEM(res, (Py_ssize_t)k, x); p = z + 1;', '        }', '        free(r);', '    }']
    L += ['    goto done;', 'fb:', '    PyErr_Clear(); res = Py_NotImplemented; Py_INCREF(res);', 'done:']
    L += [f'    free({f});' for f in frees] + ['    return res;', '}', '',
          'static PyMethodDef vu_methods[] = {{"call", (PyCFunction)(void (*)(void))vu_call, METH_FASTCALL, NULL}, {NULL, NULL, 0, NULL}};',
          f'static struct PyModuleDef vu_module = {{PyModuleDef_HEAD_INIT, "{ext_mod(t.name)}", NULL, -1, vu_methods}};',
          f'PyMODINIT_FUNC PyInit_{ext_mod(t.name)}(void) {{ return PyModule_Create(&vu_module); }}', '']
    return "\n".join(L)

def ext_mod(name):
    return "_vu_ext_" + name

def build_ext(t, out_dir):
    """The extension module next to the library; returns its file name, or "" (then ctypes is used)."""
    import sysconfig
    inc = sysconfig.get_paths().get("include", "")
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    cc = os.environ.get("CC", "cc")
    if not inc or not os.path.exists(os.path.join(inc, "Python.h")) or not shutil.which(cc): return ""
    src = os.path.join(out_dir, ext_mod(t.name) + ".c")
    # pointers freed at done: start them all NULL, so a jump there before one is set frees nothing
    code = ext_source(t)
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(code)
    out = os.path.join(out_dir, ext_mod(t.name) + suffix)
    lib = lib_name(t.name)
    cmd = [cc, "-O2", "-shared", "-fPIC", "-w", "-I", inc, "-I", out_dir, src, "-o", out, "-L", out_dir, "-l:" + lib]
    if sys.platform == "darwin":
        cmd = [cc, "-O2", "-shared", "-fPIC", "-w", "-I", inc, "-I", out_dir, src, "-o", out, os.path.join(out_dir, lib),
               "-undefined", "dynamic_lookup", "-Wl,-rpath,@loader_path"]
    else:
        cmd += ["-Wl,-rpath,$ORIGIN"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.basename(out) if r.returncode == 0 else ""

def lib_name(name):
    return ("lib" + name + (".dylib" if sys.platform == "darwin" else ".so"))

# ---------------------------------------------------------------- the loader (written next to the module)

LOADER = r'''# Written by vu speedup: functions of {module} that run as Vu. Each one's Vu source is in this
# folder; vu speedup builds it. Anything the Vu version can't take (an int over 64 bits, a string
# that isn't encodable, an argument of another type, a panic) runs the original instead.
import array as _array, ctypes as _ct, ctypes.util as _ctu, json as _json, os as _os, builtins as _bi

_here = _os.path.dirname(_os.path.abspath(__file__))
_libc = _ct.CDLL(_ctu.find_library("c") or None)
_libc.free.argtypes = [_ct.c_void_p]
_free = _libc.free
_SPECS = {specs}

def _exc(m, mod=None):
    """The exception "Name: message" names: a built-in one, or a class of the function's module."""
    k, sep, rest = m.partition(": ")
    c = getattr(_bi, k, None)
    if not (isinstance(c, type) and issubclass(c, BaseException)) and mod is not None:
        c = mod.get(k)
    if sep and isinstance(c, type) and issubclass(c, BaseException):
        try:
            return c(rest)
        except Exception:
            pass
    return RuntimeError(m)

def _remap(x, mod):
    """A RuntimeError from the extension whose message names one of the module's exceptions: that one."""
    e = _exc(str(x), mod)
    return x if type(e) is RuntimeError else e

def _fix(v, t):
    k = t[0]
    if k == "float": return float(v)
    if k == "list": return [_fix(x, t[1]) for x in v]
    if k == "tuple": return tuple(_fix(x, t[1]) for x in v)
    if k == "dict": return {{a: _fix(b, t[1]) for a, b in v.items()}}
    if k == "opt": return None if v is None else _fix(v, t[1])
    return v

def _needs_fix(t):
    return t[0] in ("float", "tuple") or (len(t) > 1 and _needs_fix(t[1]))

_CT = {{"int": _ct.c_int64, "float": _ct.c_double, "bool": _ct.c_bool}}

def speedup(original, strict=False):
    """The Vu version of original (a function of this module that vu speedup ported). strict: no
    falling back to the original (vu speedup's check uses it)."""
    name = getattr(original, "__name__", "")
    spec = _SPECS.get(name)
    lib_path = _os.path.join(_here, spec["lib"]) if spec else ""
    if not spec or not _os.path.exists(lib_path):
        if strict: raise ImportError("no Vu version of " + name)
        return original
    lib = _ct.CDLL(lib_path)
    fn = getattr(lib, "py_" + name)
    params, ret = [tuple(_tt(p)) for p in spec["params"]], _tt(spec["ret"])
    names = spec["names"]
    defaults = original.__defaults__ or ()
    nreq = len(names) - len(defaults)
    sig = ", ".join(n if i < nreq else n + "=_D[" + str(i - nreq) + "]" for i, n in enumerate(names))
    args = ", ".join(names)
    g = {{"_fn": fn, "_orig": original, "_D": defaults, "_ct": _ct, "_free": _free, "_exc": _exc, "_array": _array,
         "_fix": _fix, "_ret": ret, "_mod": getattr(original, "__globals__", None), "_remap": _remap, "_dumps": _json.JSONEncoder(ensure_ascii=False, allow_nan=False, check_circular=False).encode,
         "_loads": _json.loads, "_strict": strict}}
    body = []
    fallback = "raise TypeError('vu speedup: the Vu version can not take this call')" if strict else "return _orig(" + args + ")"
    ext_path = _os.path.join(_here, spec["ext"]) if spec.get("ext") else ""
    if ext_path and _os.path.exists(ext_path):
        import importlib.util as _iu
        _s = _iu.spec_from_file_location("_vu_ext_" + name, ext_path)
        _m = _iu.module_from_spec(_s)
        _s.loader.exec_module(_m)
        g["_call"] = _m.call
        body.append("try:")
        body.append("    _r = _call(" + args + ")")
        body.append("except RuntimeError as _x:")
        body.append("    raise _remap(_x, _mod) from None")
        body.append("if _r is NotImplemented:")
        body.append("    " + fallback)
        body.append("return _r")
        src = "def " + name + "(" + sig + "):\n" + "\n".join("    " + l for l in body) + "\n"
        exec(compile(src, "<vu speedup: " + name + ">", "exec"), g)
        fast = g[name]
        fast.__doc__, fast.__wrapped__, fast.__vu_original__ = original.__doc__, original, original
        fast.__module__ = getattr(original, "__module__", None)
        fast.__qualname__ = getattr(original, "__qualname__", name)
        return fast
    if spec["native"]:
        argtypes, conv, cargs = [], [], []
        for i, (n, t) in enumerate(zip(names, params)):
            k = t[0]
            if k in ("int", "float", "bool"):
                cls = {{"int": "int", "float": "float", "bool": "bool"}}[k]
                conv.append("if " + n + ".__class__ is not " + cls + ": " + fallback)
                if k == "int":   # (ctypes wraps an int that doesn't fit in 64 bits instead of refusing it)
                    conv.append("if not -9223372036854775808 <= " + n + " <= 9223372036854775807: " + fallback)
                argtypes.append(_CT[k]); cargs.append(n)
            elif k == "str":
                conv.append("_a" + str(i) + " = " + n + ".encode('utf-8')")
                argtypes += [_ct.c_char_p, _ct.c_int64]; cargs += ["_a" + str(i), "len(_a" + str(i) + ")"]
            elif k == "bytes":
                conv.append("if " + n + ".__class__ is not bytes: " + fallback)
                argtypes += [_ct.c_char_p, _ct.c_int64]; cargs += [n, "len(" + n + ")"]
            elif t[1][0] == "str":
                j = "_j" + str(i)
                conv.append("if " + n + ".__class__ is not list: " + fallback)
                conv.append(j + " = '\\x00'.join(" + n + ")")
                conv.append("if " + n + " and " + j + ".count('\\x00') != len(" + n + ") - 1: " + fallback)
                conv.append("_a" + str(i) + " = " + j + ".encode('utf-8')")
                argtypes += [_ct.c_char_p, _ct.c_int64, _ct.c_int64]
                cargs += ["_a" + str(i), "len(_a" + str(i) + ")", "len(" + n + ")"]
            else:
                code = "q" if t[1][0] == "int" else "d"
                conv.append("if " + n + ".__class__ is not list: " + fallback)
                conv.append("_a" + str(i) + " = _array.array('" + code + "', " + n + ")")
                argtypes += [_ct.c_void_p, _ct.c_int64]
                cargs += ["_a" + str(i) + ".buffer_info()[0]", "len(_a" + str(i) + ")"]
        big = ret[0] in ("str", "bytes", "list")
        strs = ret == ("list", ("str",))
        if big: argtypes.append(_ct.POINTER(_ct.c_int64)); cargs.append("_ct.byref(_n)")
        argtypes.append(_ct.POINTER(_ct.c_void_p)); cargs.append("_ct.byref(_e)")
        fn.argtypes = argtypes
        fn.restype = _ct.c_void_p if big else (_CT[ret[0]] if ret[0] in _CT else None)
        body.append("try:")
        body += ["    " + c for c in conv]
        body.append("except (OverflowError, UnicodeEncodeError, TypeError, ValueError, AttributeError):")
        body.append("    " + fallback)
        if big: body.append("_n = _ct.c_int64()")
        body.append("_e = _ct.c_void_p()")
        body.append("_r = _fn(" + ", ".join(cargs) + ")")
    else:
        fn.argtypes = [_ct.c_char_p, _ct.c_int64, _ct.POINTER(_ct.c_int64), _ct.POINTER(_ct.c_void_p)]
        fn.restype = _ct.c_void_p
        obj = "{{" + ", ".join("'p" + str(i) + "': " + n for i, n in enumerate(names)) + "}}"
        for n, t in zip(names, params):
            if t[0] in ("int", "float", "bool", "str"):
                body.append("if " + n + ".__class__ is not " + t[0] + ": " + fallback)
            elif t[0] == "opt" and t[1][0] in ("int", "float", "bool", "str"):
                body.append("if " + n + " is not None and " + n + ".__class__ is not " + t[1][0] + ": " + fallback)
        body.append("try:")
        body.append("    _s = _dumps(" + obj + ").encode('utf-8')")
        body.append("except (ValueError, TypeError, UnicodeEncodeError, RecursionError, OverflowError):")
        body.append("    " + fallback)
        body.append("_n = _ct.c_int64()")
        body.append("_e = _ct.c_void_p()")
        body.append("_r = _fn(_s, len(_s), _ct.byref(_n), _ct.byref(_e))")
    body.append("if _e.value:")
    body.append("    _m = _ct.string_at(_e.value).decode('utf-8', 'replace'); _free(_e)")
    body.append("    if _m.startswith('panic: ') or _m in ('vu-speedup: arguments', 'vu-speedup: result', 'vu-speedup: fallback'):")
    body.append("        " + ("raise RuntimeError('vu speedup: ' + _m)" if strict else "return _orig(" + args + ")"))
    body.append("    raise _exc(_m, _mod)")
    k = ret[0]
    if spec["native"]:
        if k == "str": body += ["_v = _ct.string_at(_r, _n.value).decode('utf-8'); _free(_r)", "return _v"]
        elif k == "bytes": body += ["_v = _ct.string_at(_r, _n.value); _free(_r)", "return _v"]
        elif strs:
            body += ["_v = _ct.string_at(_r, _n.value).decode('utf-8'); _free(_r)",
                     "_c, _, _v = _v.partition(':')",
                     "return _v.split('\\x00') if _c != '0' else []"]
        elif k == "list":
            code = "q" if ret[1][0] == "int" else "d"
            size = 8
            body += ["_v = _array.array('" + code + "', _ct.string_at(_r, _n.value * " + str(size) + ")).tolist() if _n.value else []",
                     "_free(_r)", "return _v"]
        elif k == "none": body.append("return None")
        else: body.append("return _r")
    else:
        body.append("_v = _loads(_ct.string_at(_r, _n.value).decode('utf-8')); _free(_r)")
        body.append("return _fix(_v, _ret)" if _needs_fix(ret) else "return _v")
    src = "def " + name + "(" + sig + "):\n" + "\n".join("    " + l for l in body) + "\n"
    exec(compile(src, "<vu speedup: " + name + ">", "exec"), g)
    fast = g[name]
    fast.__doc__ = original.__doc__
    fast.__wrapped__ = original
    fast.__vu_original__ = original
    fast.__module__ = getattr(original, "__module__", None)
    fast.__qualname__ = getattr(original, "__qualname__", name)
    return fast

def _tt(x):
    return tuple(_tt(y) if isinstance(y, list) else y for y in x)
'''

def write_loader(t, out_dir, specs):
    with open(os.path.join(out_dir, "__init__.py"), "w", encoding="utf-8") as fh:
        fh.write(LOADER.format(module=t.modname, specs=repr(specs)))

def spec_of(t):
    return {"lib": lib_name(t.name), "names": [p for p, _, _ in t.params], "params": [list_t(ty) for _, ty, _ in t.params],
            "ret": list_t(t.ret), "native": t.native, "ext": getattr(t, "ext", "")}

def list_t(t):
    return [list_t(x) if isinstance(x, tuple) else x for x in t]

def read_specs(out_dir):
    p = os.path.join(out_dir, "__init__.py")
    if not os.path.exists(p): return {}
    m = re.search(r"^_SPECS = (.*)$", open(p, encoding="utf-8").read(), re.M)
    return ast.literal_eval(m.group(1)) if m else {}

# ---------------------------------------------------------------- checking (in a child process)

def check_child(argv):
    """_check TARGET OUT_DIR CASES.json RESULT.json: runs the Vu version on each case, compares."""
    target, out_dir, cases_path, result_path = argv
    t = load_target(target)
    sys.path.insert(0, os.path.dirname(out_dir))
    pkg = importlib.util.spec_from_file_location("_vu_check_loader", os.path.join(out_dir, "__init__.py"))
    loader = importlib.util.module_from_spec(pkg)
    pkg.loader.exec_module(loader)
    fast = loader.speedup(t.func, strict=True)
    with open(cases_path, encoding="utf-8") as fh:
        cases = decode(json.load(fh))
    progress = result_path + ".at"
    res = {"same": 0, "fallback": 0, "differ": [], "fallbacks": []}
    for i, (args, want) in enumerate(cases):
        with open(progress, "w") as fh:
            fh.write(str(i))
        try:
            v = fast(*args)
            got = ["ok", v]
        except TypeError as e:
            if str(e).startswith("vu speedup:"):
                res["fallback"] += 1
                if len(res["fallbacks"]) < 5: res["fallbacks"].append([short(args), "an argument the Vu version can't take"])
                continue
            got = ["raise", "TypeError", str(e)]
        except RuntimeError as e:
            if str(e).startswith("vu speedup: panic: ") or str(e) in ("vu speedup: vu-speedup: arguments", "vu speedup: vu-speedup: result", "vu speedup: vu-speedup: fallback"):
                res["fallback"] += 1
                if len(res["fallbacks"]) < 5: res["fallbacks"].append([short(args), str(e)[12:]])
                continue
            got = ["raise", "RuntimeError", str(e)]
        except Exception as e:
            got = ["raise", type(e).__name__, str(e)]
        if same_outcome(want, got): res["same"] += 1
        else:
            res["differ"].append([i, short(args, 600), show_outcome(want), show_outcome(got)])
    os.unlink(progress)
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh)

def same_outcome(want, got):
    if want[0] == "ok": return got[0] == "ok" and same_value(want[1], got[1])
    if want[0] == "raise": return got[0] == "raise" and want[1] == got[1]
    return True

def show_outcome(o):
    if o[0] == "ok": return "returns " + short(o[1], 600)
    return f"raises {o[1]}: {short(o[2], 300)}"

def encode(v):
    """JSON for any value here: tuples, bytes and non-finite floats tagged."""
    if isinstance(v, tuple): return {"__t": [encode(x) for x in v]}
    if isinstance(v, bytes): return {"__b": v.hex()}
    if isinstance(v, float) and not math.isfinite(v): return {"__f": repr(v)}
    if isinstance(v, list): return [encode(x) for x in v]
    if isinstance(v, dict): return {"__d": [[k, encode(x)] for k, x in v.items()]}
    return v

def decode(v):
    if isinstance(v, list): return [decode(x) for x in v]
    if isinstance(v, dict):
        if "__t" in v: return tuple(decode(x) for x in v["__t"])
        if "__b" in v: return bytes.fromhex(v["__b"])
        if "__f" in v: return float(v["__f"])
        if "__d" in v: return {k: decode(x) for k, x in v["__d"]}
    return v

def check(t, out_dir, cases, tmp):
    """Runs the check in a child process; returns its result, or a crash report."""
    cases_path = os.path.join(tmp, "cases.json")
    result_path = os.path.join(tmp, "result.json")
    with open(cases_path, "w", encoding="utf-8") as fh:
        json.dump(encode(cases), fh)
    if os.path.exists(result_path): os.unlink(result_path)
    r = subprocess.run([sys.executable, __file__, "_check", t.path + ":" + t.name, out_dir, cases_path, result_path],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(result_path):
        at = None
        try:
            at = int(open(result_path + ".at").read())
        except Exception:
            pass
        where = f" on {short(cases[at][0], 600)}" if at is not None else ""
        return {"crash": f"the Vu version stopped the process (exit {r.returncode}){where}:\n{(r.stderr or r.stdout)[-2000:]}"}
    with open(result_path, encoding="utf-8") as fh:
        return json.load(fh)

# ---------------------------------------------------------------- timing

def time_both(t, out_dir, calls, tmp):
    p = os.path.join(tmp, "bench.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(encode(calls), fh)
    r = subprocess.run([sys.executable, __file__, "_time", t.path + ":" + t.name, out_dir, p], capture_output=True, text=True)
    if r.returncode != 0: return None
    return json.loads(r.stdout.strip().splitlines()[-1])

def time_child(argv):
    target, out_dir, path = argv
    t = load_target(target)
    pkg = importlib.util.spec_from_file_location("_vu_time_loader", os.path.join(out_dir, "__init__.py"))
    loader = importlib.util.module_from_spec(pkg)
    pkg.loader.exec_module(loader)
    fast = loader.speedup(t.func)
    calls = decode(json.load(open(path, encoding="utf-8")))
    import gc
    def run(f):
        best = math.inf
        for _ in range(5):
            gc.collect(); gc.disable()
            t0 = time.perf_counter()
            for a in calls:
                try:
                    f(*a)
                except Exception:
                    pass
            best = min(best, time.perf_counter() - t0)
            gc.enable()
        return best
    run(fast)
    orig, vu = run(t.func), run(fast)
    print(json.dumps({"python": orig, "vu": vu, "calls": len(calls)}))

# ---------------------------------------------------------------- the model

PROMPT = """Port this Python function to Vu, a compiled language with Python-like syntax. The Vu
language in brief:

<vu>
{llms}
</vu>

The Python function{context_note}:

```python
{context}{source}
```

Write a Vu file with exactly this function (keep the name and the parameter and result types; add
`throws` after the result type if it can fail; add helper functions and types as you need):

    {signature}

Rules:
- It must give exactly the same results as the Python for every input: same values, same order,
  same float arithmetic (do operations in the same order so floats round the same), the same text.
- Where the Python raises an exception, fail with the exception's type name first:
  `fail "ValueError: <message>"` (the message may differ, the type must not).
- Python str indexing and len() count characters; Vu's `s.len` and `s[i]` are bytes (UTF-8). For
  character positions use `let cs = s.chars()` (a [Str] of characters) and `s.char_count()`.
  `upper()`, `lower()`, `is_alpha()`, `is_digit()`, `is_space()` and friends match Python's.
- Ints are 64-bit; overflow stops the Vu version and the Python one runs instead, so you needn't
  handle numbers over 64 bits.
- Python's math functions are Float methods here, calling the same C functions: `x.sin()`,
  `y.atan2(x)`, `x.pow(y)` (Python's `x ** y` on floats is `x.pow(y)`), `x.floor()`, `sqrt(x)`;
  math.radians(x) is `x * (3.141592653589793 / 180.0)`. (Not math.hypot: Python's is its own
  algorithm, and `x.hypot(y)` is C's, which can differ in the last bit.) Python raises `ValueError: math domain
  error` where C returns NaN for a number that isn't NaN (`sin(inf)`, `sqrt(-1)`), and
  `OverflowError: math range error` where it returns an infinity for a finite number: check and fail
  the same way.
- For a rare case that's hard to get exactly right, `fail "vu-speedup: fallback"` runs the Python
  function for that call instead (for example Python's lower() turns a final capital sigma into
  "ς", which Vu's lower() doesn't: fall back when the text holds "Σ").
- No main, no capabilities (it can't use files, the network or processes), no printing.

Answer with the whole Vu file in one ```vu block.
"""

def make_prompt(t, llms):
    ctx = t.context.strip()
    return PROMPT.format(llms=llms.strip(), context_note=" (and the module code it uses)" if ctx else "",
                         context=(ctx + "\n\n") if ctx else "", source=t.source.strip(), signature=port_signature(t))

def ask_model(model, messages):
    if os.environ.get("ANTHROPIC_API_KEY") and not model.startswith(("gpt", "o1", "o3", "o4")):
        base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        body = {"model": model, "max_tokens": 8000, "messages": messages}
        req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode(), method="POST",
                                     headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    if os.environ.get("OPENAI_API_KEY"):
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        body = {"model": model, "messages": messages}
        req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                                              "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        return d["choices"][0]["message"]["content"] or ""
    raise RuntimeError("no ANTHROPIC_API_KEY or OPENAI_API_KEY")

def code_block(text):
    m = re.findall(r"```(?:vu)?\s*\n(.*?)```", text, re.S)
    return max(m, key=len) if m else text

def feedback(build_msg, result):
    if build_msg is not None:
        return "It doesn't compile:\n\n" + build_msg[-4000:] + "\n\nFix it and answer with the whole file again."
    if "crash" in result: return result["crash"] + "\n\nFix it and answer with the whole file again."
    lines = [f"{len(result['differ'])} of {len(result['differ']) + result['same']} answers differ from the Python. Some:"]
    for i, args, want, got in result["differ"][:6]:
        lines.append(f"- called with {args}: Python {want}; Vu {got}")
    lines.append("\nFix it and answer with the whole file again.")
    return "\n".join(lines)

# ---------------------------------------------------------------- the swap

MARK = "# vu speedup:"

def apply_swap(t, n_checked):
    src = t.file_source
    if re.search(r"^" + re.escape(MARK) + r" " + re.escape(t.name) + r" ", src, re.M):
        return False
    tree = ast.parse(src)
    node = next((n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == t.name), None)
    if node is None: raise SystemExit(f"vu speedup: {t.name} isn't defined at the top level of {t.path}")
    lines = src.splitlines(keepends=True)
    end = node.end_lineno
    imp = f"from ._vu_{t.modname} import speedup as _vu_speedup" if t.package else f"from _vu_{t.modname} import speedup as _vu_speedup"
    block = (f"\n{MARK} {t.name} runs as Vu (checked against this Python on {n_checked} inputs; delete these lines to undo)\n"
             f"try:\n    {imp}\n    {t.name} = _vu_speedup({t.name})\nexcept ImportError:\n    pass\n")
    if end < len(lines) and not lines[end - 1].endswith("\n"): lines[end - 1] += "\n"
    lines.insert(end, block)
    with open(t.path, "w", encoding="utf-8") as fh:
        fh.write("".join(lines))
    return True

# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_check": return check_child(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "_time": return time_child(sys.argv[2:])
    ap = argparse.ArgumentParser(prog="vu speedup", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="FILE.py:FUNC")
    ap.add_argument("--port", help="a Vu file with the port, written by you or an agent")
    ap.add_argument("--model", default=os.environ.get("VU_SPEEDUP_MODEL", "claude-sonnet-5-5"))
    ap.add_argument("--attempts", type=int, default=6)
    ap.add_argument("--inputs", type=int, default=3000, help="generated inputs (default 3000)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--record", nargs=argparse.REMAINDER, help="a script (or -m module) and its arguments: its calls to FUNC are added")
    ap.add_argument("--inputs-file", help="a JSON list of argument lists to add")
    ap.add_argument("--no-apply", action="store_true", help="check and measure, but leave FILE.py as it is")
    ap.add_argument("--prompt", action="store_true", help="print the prompt for a model or agent, and stop")
    ap.add_argument("--force", action="store_true", help="swap the Vu version in even when it isn't faster")
    ap.add_argument("--vu", default=os.environ.get("VU", "vu"))
    ap.add_argument("--llms", default="")
    a = ap.parse_args()

    t = load_target(a.target)
    llms = open(a.llms, encoding="utf-8").read() if a.llms and os.path.exists(a.llms) else ""
    if a.prompt:
        print(make_prompt(t, llms))
        return 0
    out_dir = os.path.join(t.dir, "_vu_" + t.modname)
    say(f"{t.name}({', '.join(p + ': ' + show_type(ty) for p, ty, _ in t.params)}) -> {show_type(t.ret)}"
        f"  [{'direct call' if t.native else 'arguments as JSON'}]")

    calls = []
    if a.record:
        rec = record_calls(t, a.record, 5000)
        say(f"recorded {len(rec)} calls from {' '.join(a.record)}")
        calls += rec
    if a.inputs_file:
        extra = json.load(open(a.inputs_file, encoding="utf-8"))
        calls += [list(x) for x in extra]
    calls += generate(t, a.inputs, a.seed)
    outcomes = run_original(t.func, calls)
    cases = []
    for args, o in zip(calls, outcomes):
        if o[0] == "slow": continue
        if o[0] == "ok" and not fits(o[1], t.ret):
            raise SystemExit(f"vu speedup: {t.name}{short(tuple(args))} returned {short(o[1])}, which isn't {show_type(t.ret)}: fix its hint")
        cases.append([args, o])
    raised = sum(1 for _, o in cases if o[0] == "raise")
    say(f"{len(cases)} inputs; the original raises on {raised}" + (f"; {len(calls) - len(cases)} too slow, left out" if len(cases) < len(calls) else ""))

    tmp = tempfile.mkdtemp(prefix="vu-speedup-")
    try:
        port = None
        if a.port:
            port = open(a.port, encoding="utf-8").read()
            ok, msg = build(a.vu, t, port, out_dir)
            if not ok:
                say("the port doesn't compile:\n" + msg)
                return 1
            specs = read_specs(out_dir); specs[t.name] = spec_of(t)
            write_loader(t, out_dir, specs)
            res = check(t, out_dir, cases, tmp)
            if not report_check(res, len(cases)): return 1
        else:
            if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
                os.makedirs(out_dir, exist_ok=True)
                pp = os.path.join(out_dir, t.name + ".prompt.md")
                with open(pp, "w", encoding="utf-8") as fh:
                    fh.write(make_prompt(t, llms))
                say(f"no ANTHROPIC_API_KEY or OPENAI_API_KEY: the prompt for a model or a coding agent is in {pp}.\n"
                    f"Write the port to a .vu file, then: vu speedup {a.target} --port FILE.vu")
                return 2
            messages = [{"role": "user", "content": make_prompt(t, llms)}]
            res = None
            for attempt in range(1, a.attempts + 1):
                say(f"attempt {attempt}: asking {a.model}")
                try:
                    answer = ask_model(a.model, messages)
                except urllib.error.HTTPError as e:
                    detail = e.read().decode("utf-8", "replace")[:500]
                    sys.exit(f"vu speedup: the model API answered {e.code}: {detail}")
                except (urllib.error.URLError, OSError) as e:
                    sys.exit(f"vu speedup: can't reach the model API: {getattr(e, 'reason', e)}")
                port = code_block(answer)
                messages.append({"role": "assistant", "content": answer})
                ok, msg = build(a.vu, t, port, out_dir)
                if not ok:
                    say("  doesn't compile")
                    messages.append({"role": "user", "content": feedback(msg, None)})
                    continue
                specs = read_specs(out_dir); specs[t.name] = spec_of(t)
                write_loader(t, out_dir, specs)
                res = check(t, out_dir, cases, tmp)
                if "crash" not in res and not res["differ"]: break
                say("  " + (res["crash"].splitlines()[0] if "crash" in res else f"{len(res['differ'])} answers differ"))
                messages.append({"role": "user", "content": feedback(None, res)})
                res = None
            if res is None:
                say(f"no port gave the same answers in {a.attempts} attempts; the last is in {out_dir}/{t.name}.vu")
                return 1
            report_check(res, len(cases))
        timing = time_both(t, out_dir, [c[0] for c in cases], tmp)
        ratio = None
        if timing:
            say(speed_line(f"on the {timing['calls']} test inputs", timing))
            ratio = timing["python"] / timing["vu"] if timing["vu"] > 0 else math.inf
        if any(ty[0] in ("list", "tuple", "dict") for _, ty, _ in t.params):
            bc = generate(t, 40, a.seed + 1, big=True)
            bigcalls = [c for c, o in zip(bc, run_original(t.func, bc)) if o[0] == "ok"]
            if bigcalls:
                timing = time_both(t, out_dir, bigcalls, tmp)
                if timing:
                    say(speed_line(f"on {timing['calls']} bigger inputs (lists of 500 to 2,000)", timing))
                    ratio = timing["python"] / timing["vu"] if timing["vu"] > 0 else math.inf
        if a.no_apply:
            say(f"left {os.path.basename(t.path)} as it is (--no-apply); the Vu version is in {out_dir}")
        elif ratio is not None and ratio < 1.2 and not a.force:
            say(f"left {os.path.basename(t.path)} as it is: the Vu version isn't faster here ({ratio:.1f}x). Most of this "
                "function's time is in Python's own C code, or in passing its arguments; --force swaps it in anyway")
        elif apply_swap(t, len(cases)):
            say(f"{os.path.basename(t.path)}: {t.name} now runs the Vu version (the lines after it say so; delete them to undo)")
        else:
            say(f"{os.path.basename(t.path)} already uses the Vu version of {t.name}; it's rebuilt")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def speed_line(what, timing):
    x = timing["python"] / timing["vu"] if timing["vu"] > 0 else math.inf
    return f"speed {what}: Python {timing['python'] * 1000:.1f} ms, Vu {timing['vu'] * 1000:.1f} ms: {x:.1f}x"

def report_check(res, n):
    if "crash" in res:
        say(res["crash"])
        return False
    if res["differ"]:
        say(f"{len(res['differ'])} of {n} answers differ from the original:")
        for i, args, want, got in res["differ"][:8]:
            say(f"  {args}\n    Python {want}\n    Vu     {got}")
        return False
    fb = res["fallback"]
    say(f"same answers as the original on all {res['same']} inputs" + (f"; {fb} more ran the original (the Vu version can't take them, or hands them back)" if fb else ""))
    for args, why in res["fallbacks"][:3]:
        say(f"  e.g. {args}: {why}")
    return True

def say(s):
    print(s, flush=True)

if __name__ == "__main__":
    sys.exit(main() or 0)
