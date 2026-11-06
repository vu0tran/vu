#!/usr/bin/env python3
# Generates React components that call hooks with random callbacks and dependency arrays, for
# differential tests of react-hooks(exhaustive-deps) against oxlint:
#   gen_hooks.py OUTDIR [N] [SEED]
import random, sys, os

out = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
os.makedirs(out, exist_ok=True)

HOOKS = ["useEffect", "useLayoutEffect", "useCallback", "useMemo", "React.useEffect", "React.useCallback",
         "useImperativeHandle", "useInsertionEffect", "useCustomEffect"]

def gen_file(i):
    R = random.Random(SEED * 100003 + i)
    ext = R.choice(["jsx", "tsx"])
    names = []          # (name, kind)
    lines = []
    lines.append("import React, { useEffect, useLayoutEffect, useCallback, useMemo, useRef, useState, useReducer, useImperativeHandle, useEffectEvent, useTransition } from 'react';")
    outer = []
    for k in range(R.randint(0, 3)):
        nm = R.choice(["OUTER", "config", "helper", "API", "count0"]) + str(k)
        outer.append(nm)
        if R.random() < 0.5: lines.append(f"const {nm} = {R.choice(['1', '{}', '[]', 'fetchIt()', '() => 1'])};")
        else: lines.append(f"function {nm}() {{ return 1; }}")
    style = R.choice(["fn", "arrow", "memo"])
    params = R.choice(["props", "{ a, b, onChange, items }", "{ a, ...rest }", "props, ref"])
    body = []
    pnames = []
    if params.startswith("props"): pnames = ["props"]
    elif "rest" in params: pnames = ["a", "rest"]
    else: pnames = ["a", "b", "onChange", "items"]
    if "ref" in params: pnames.append("ref")
    locals_ = list(pnames)
    decls = []
    for k in range(R.randint(1, 7)):
        t = R.choice(["state", "ref", "const", "let", "obj", "fn", "fnstable", "reducer", "memo", "destr", "transition", "event", "literal"])
        nm = f"v{k}"
        if t == "state":
            decls.append(f"const [{nm}, set{nm.upper()}] = useState(0);"); locals_ += [nm, "set" + nm.upper()]
        elif t == "ref":
            decls.append(f"const {nm} = useRef(null);"); locals_.append(nm)
        elif t == "const":
            decls.append(f"const {nm} = {R.choice(pnames)}{R.choice(['', '.x', '.y.z', '?.w'])};"); locals_.append(nm)
        elif t == "let":
            decls.append(f"let {nm} = 1;"); locals_.append(nm)
        elif t == "obj":
            decls.append(f"const {nm} = {R.choice(['{}', '[]', 'new Map()', '/x/', '<div />', 'cond ? {} : null', 'x || []', 'function () {}', 'class {}'])};"); locals_.append(nm)
        elif t == "fn":
            decls.append(f"function {nm}() {{ return {R.choice(locals_)}; }}"); locals_.append(nm)
        elif t == "fnstable":
            decls.append(f"const {nm} = () => {R.choice(outer + ['1', 'Math.random()'])};"); locals_.append(nm)
        elif t == "reducer":
            decls.append(f"const [{nm}, dispatch{k}] = useReducer(r, 0);"); locals_ += [nm, f"dispatch{k}"]
        elif t == "memo":
            decls.append(f"const {nm} = useMemo(() => {R.choice(locals_)}, [{R.choice(locals_)}]);"); locals_.append(nm)
        elif t == "destr":
            decls.append(f"const {{ {nm}, q{k} }} = {R.choice(pnames)};"); locals_ += [nm, f"q{k}"]
        elif t == "transition":
            decls.append(f"const [{nm}, start{k}] = useTransition();"); locals_ += [nm, f"start{k}"]
        elif t == "event":
            decls.append(f"const {nm} = useEffectEvent(() => {R.choice(locals_)});"); locals_.append(nm)
        elif t == "literal":
            decls.append(f"const {nm} = {R.choice(['1', '\"s\"', 'null', 'true', '-1', '`t`', '1n'])};"); locals_.append(nm)
    body += decls
    allv = locals_ + outer + ["window", "console", "undefined"]
    def expr(d=0):
        c = R.random()
        v = R.choice(allv)
        if c < 0.3: return v
        if c < 0.5: return f"{v}.{R.choice(['x', 'current', 'foo', 'bar'])}{R.choice(['', '.y', '.current', '?.z'])}"
        if c < 0.6: return f"{v}.{R.choice(['call', 'map', 'current.focus'])}({R.choice(allv)})"
        if c < 0.7: return f"{v}({R.choice(allv)})"
        if c < 0.75: return f"{v}?.{R.choice(['a', 'b'])}"
        if c < 0.8: return f"({v} as any).p" if R.random() < 0.3 and ext == "tsx" else f"{v}[0]"
        if c < 0.85 and d < 2: return f"(() => {expr(d + 1)})()"
        if c < 0.9 and d < 2: return f"{expr(d + 1)} + {expr(d + 1)}"
        if c < 0.95: return f"`${{{v}}}`"
        return f"{v}!" if ext == "tsx" else f"!{v}"
    for k in range(R.randint(1, 4)):
        hook = R.choice(HOOKS)
        stmts = []
        for z in range(R.randint(0, 4)):
            c = R.random()
            if c < 0.6: stmts.append(f"{expr()};")
            elif c < 0.7: stmts.append(f"{R.choice(locals_)} = {expr()};")
            elif c < 0.8: stmts.append(f"if ({expr()}) {{ {expr()}; }}")
            elif c < 0.9: stmts.append(f"return () => {{ {expr()}; }};")
            else: stmts.append(f"const t{z} = {expr()}; t{z};")
        asy = "async " if R.random() < 0.1 else ""
        cb = R.choice([f"{asy}() => {{ {' '.join(stmts)} }}", f"{asy}function () {{ {' '.join(stmts)} }}", f"() => {expr()}",
                       R.choice(locals_ + outer), "...args"])
        dc = R.random()
        if dc < 0.15: deps = None
        elif dc < 0.2: deps = R.choice(["deps", "undefined", "[...deps]", "...rest"])
        else:
            items = []
            for z in range(R.randint(0, 5)):
                cc = R.random()
                if cc < 0.6: items.append(R.choice(allv))
                elif cc < 0.8: items.append(f"{R.choice(allv)}.{R.choice(['x', 'current', 'foo'])}")
                elif cc < 0.85: items.append(R.choice(["1", "'s'", "null", "/re/"]))
                elif cc < 0.9: items.append(f"{R.choice(allv)}()")
                elif cc < 0.95: items.append(f"{R.choice(allv)}?.x")
                else: items.append(f"...{R.choice(allv)}")
            deps = "[" + ", ".join(items) + "]"
        args = [cb] if deps is None else [cb, deps]
        if hook == "useImperativeHandle": args = ["ref"] + args
        if R.random() < 0.05: args = []
        body.append(f"{hook}({', '.join(args)});")
    body.append("return <div />;")
    inner = "\n  ".join(body)
    if style == "fn": comp = f"export function Comp{i}({params}) {{\n  {inner}\n}}"
    elif style == "arrow": comp = f"export const Comp{i} = ({params}) => {{\n  {inner}\n}};"
    else: comp = f"export const Comp{i} = React.memo(function Comp({params}) {{\n  {inner}\n}});"
    lines.append(comp)
    open(os.path.join(out, f"h{i}.{ext}"), "w").write("\n".join(lines) + "\n")

for i in range(n): gen_file(i)
