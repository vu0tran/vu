#!/usr/bin/env python3
"""split_state.py: the mutable state a split build would give each part its own copy of.

A split build (vu build of a big program) compiles the program's functions as several C files. Each
includes the same header: the runtime, the templates, and the extern blocks' glue headers ("x.h").
State in that header must be one for the program (VU_G: defined in part 0, extern in the others). A
`static` variable there, at file scope or inside a function, is each part's own: a value one part
stores is never seen by another (ts/ctab.h's ct_slack_n was 0 for every reader that way).

This lists every static variable that isn't const in that header, as clang parses it for a part
(-DVU_PART), in files that aren't system headers, and fails for any not in ALLOWED below (each
with the reason a copy per part is fine).

  tests/split_state.py PROG.vu [-I DIR]...   (emits the program's C; DIR for its glue headers,
                                               default the program's folder)
  tests/split_state.py --c FILE.c [-I DIR]... (a C file vu emitted)
  -v: list the allowed ones too
Needs clang. Exit 0: nothing new; 1: a static not allowed; 2: couldn't run.
"""
import os, re, subprocess, sys, tempfile

# name -> why a copy in each part is fine. A name is the variable's, or FUNCTION.NAME for a
# static inside a function.
ALLOWED = {
    # the runtime (compiler/rt)
    **{"vu_m_" + f: "libm's function behind a volatile pointer (so the C compiler can't fold the call): never written, the same in every part"
       for f in "sin cos tan asin acos atan sinh cosh tanh exp expm1 log log1p log2 log10 floor ceil trunc atan2 pow hypot fmod copysign".split()},
    "vu_guard_init.altstack": "the main thread's signal stack: vu_guard_init runs once, from vu_start in part 0",
    # ts/ctab.h
    "ct_res_nz": "VTSC_MEM's report: set and read in one call of cs_report (static inline: within one part)",
    "ct_res_nzb": "VTSC_MEM's report: summed and read in one call of cs_report",
}

SYSTEM = ("/usr/", "/Library/", "/Applications/", "/opt/homebrew/", "/nix/", "/System/")
LOC = re.compile(r"(?<![\w/.])((?:/|\.{0,2}/?)[^\s<>,:'\"()]+\.[A-Za-z]+):(\d+):(\d+)")
VAR = re.compile(r"^((?:[| `]*)[|`]-)VarDecl 0x[0-9a-f]+ .*? (?:used |referenced )?(\w+) '([^']*)'(?::'[^']*')? (.*)$")
FUN = re.compile(r"^((?:[| `]*)[|`]-)FunctionDecl 0x[0-9a-f]+ .*? (?:used |referenced )?(\w+) '")


def is_const(ty):
    # const at the top: "T *const", "const int[4]" (an array of const), "const int"
    t = ty.strip()
    while re.search(r"\[\d*\]$", t): t = re.sub(r"\[\d*\]$", "", t).strip()   # an array: its elements
    if t.endswith("const") or t.endswith("const volatile") or t.endswith("volatile const"): return True
    if "*" not in t and "(" not in t and re.match(r"^(const|static const)\b", t): return True
    return False


def scan(cfile, incs):
    head = open(cfile, encoding="utf-8", errors="replace").read()
    at = head.find("\n/* vu-parts */\n")
    if at < 0:
        print("split_state: no /* vu-parts */ line in " + cfile)
        sys.exit(2)
    d = tempfile.mkdtemp(prefix="split_state")
    hp = os.path.join(d, "head.c")
    # (split_build moves the tried copies of functions, VU_FNI, into the header: every part has them)
    fni = [f for f in head[at + 15:].split("\n/* vu-part */\n") if f.startswith("VU_FNI ")]
    with open(hp, "w") as f:
        f.write(head[:at + 1] + "\n".join(fni) + "\n")
    cmd = ["clang", "-fsyntax-only", "-w", "-DVU_PART", "-Xclang", "-ast-dump", "-fno-color-diagnostics"]
    for i in incs: cmd += ["-I", i]
    for extra in ("/opt/homebrew/include", "/opt/homebrew/opt/openssl@3/include"):
        if os.path.isdir(extra): cmd += ["-I", extra]
    cmd.append(hp)
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    except FileNotFoundError:
        print("split_state: clang not found")
        sys.exit(2)
    if p.returncode != 0:
        print("split_state: clang failed:\n" + p.stderr[-3000:])
        sys.exit(2)
    found = []
    cur = hp
    fns = []   # (depth, name): the function a static local is in
    for ln in p.stdout.split("\n"):
        mv = VAR.match(ln)
        mf = FUN.match(ln)
        m0 = mv or mf
        if m0:
            depth = len(m0.group(1))
            while fns and fns[-1][0] >= depth: fns.pop()
        # the file: the dumper names it in a location only when it changes, in the order printed
        for m in LOC.finditer(ln):
            if m.group(1) not in ("line", "col"): cur = m.group(1)
        if mf:
            fns.append((len(mf.group(1)), mf.group(2)))
            continue
        if not mv: continue
        rest = mv.group(4).split()
        if "static" not in rest: continue
        if any(cur.startswith(s) for s in SYSTEM) or cur.startswith("<"): continue
        name, ty = mv.group(2), mv.group(3)
        if is_const(ty): continue
        depth = len(mv.group(1))
        inside = [f for f in fns if f[0] < depth]
        full = (inside[-1][1] + "." + name) if inside else name
        where = "header" if cur == hp else os.path.basename(cur)
        found.append((full, ty, where, "tls" in rest))
    os.remove(hp)
    os.rmdir(d)
    return found


def main():
    args = sys.argv[1:]
    verbose = "-v" in args
    args = [a for a in args if a != "-v"]
    incs = []
    cfile = None
    prog = None
    i = 0
    while i < len(args):
        if args[i] == "-I": incs.append(args[i + 1]); i += 2
        elif args[i] == "--c": cfile = args[i + 1]; i += 2
        else: prog = args[i]; i += 1
    tmp = None
    if prog:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not incs: incs = [os.path.dirname(os.path.abspath(prog))]
        tmp = tempfile.mkdtemp(prefix="split_state")
        cfile = os.path.join(tmp, "prog.c")
        # (CC=true: the C is all that's wanted, not a build)
        env = dict(os.environ, CC="true")
        r = subprocess.run([os.path.join(root, "vu"), "build", os.path.basename(prog), "--emit-c", cfile, "-o", os.path.join(tmp, "prog")],
                           cwd=os.path.dirname(os.path.abspath(prog)), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode != 0 or not os.path.exists(cfile):
            print("split_state: vu build failed:\n" + r.stdout[-3000:])
            sys.exit(2)
    if not cfile:
        print(__doc__)
        sys.exit(2)
    found = scan(cfile, incs)
    if tmp:
        for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    bad = 0
    for full, ty, where, tls in found:
        ok = full in ALLOWED
        if not ok: bad += 1
        if not ok or verbose:
            print("%s %s '%s'%s in %s%s" % ("allowed" if ok else "STATIC", full, ty, " (thread-local)" if tls else "", where,
                                            (": " + ALLOWED[full]) if ok else ""))
    print("split_state: %d static variables in the parts' header, %d not allowed" % (len(found), bad))
    sys.exit(1 if bad else 0)


main()
