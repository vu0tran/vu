"""Random Vu programs for run_loops.sh: loops the compiler versions (hoisted index checks, tried
copies with deferred checks; see "loop versioning" in compiler/c4_stmt.vu), with integer arithmetic
that may overflow, list reads and writes at offsets that may be out of range, division by values that
may be zero, shifts, calls to small functions, nested loops, break and continue.
  python3 loops_gen.py A B DIR    writes DIR/pA.vu .. DIR/p(B-1).vu"""
import random, sys

def lit(r):
    return str(r.choice([0, 1, 2, 3, 7, 31, 1000, 65536, 3000000000, 1 << 40, 99, 5, 12, 4611686018427387904 if r.random() < 0.2 else 4]))

def iexpr(r, names, d=0, fn=False):
    if d > 2 or r.random() < 0.3:
        return r.choice(names + [lit(r)])
    k = r.random()
    if fn and k >= 0.86: k = r.random() * 0.86
    a = iexpr(r, names, d + 1, fn); b = iexpr(r, names, d + 1, fn)
    if k < 0.25: return f"({a} + {b})"
    if k < 0.45: return f"({a} - {b})"
    if k < 0.65: return f"({a} * {b})"
    if k < 0.72: return f"({a} / {b})"
    if k < 0.78: return f"({a} % {b})"
    if k < 0.82: return f"({a} << {r.choice(['1', '3', '63', '64', names[0]])})"
    if k < 0.86: return f"({a} >> {r.choice(['1', '2', names[0]])})"
    if k < 0.90: return f"f{r.randrange(3)}({a})"
    if k < 0.95: return f"xs[{r.choice(names)}{r.choice([' + 0', ' + 1', ' - 1', ' + 2', '', '', ' * 2'])}]"
    return f"abs({a})"

def fexpr(r, names):
    a = iexpr(r, names, 1)
    return r.choice([f"float({a}) * 0.5", f"sqrt(float({a}))", f"ys[{names[-1]}] * 1.5", f"fma(ys[{names[-1]}], 2.0, float({a}))"])

def body(r, names, depth, ind):
    out = []
    for _ in range(r.randint(1, 3)):
        k = r.random()
        if k < 0.45:
            out.append(f"{ind}s{r.randrange(2)} += {iexpr(r, names)}")
        elif k < 0.55:
            out.append(f"{ind}fl += {fexpr(r, names)}")
        elif k < 0.65:
            out.append(f"{ind}if {iexpr(r, names)} > {lit(r)}: {r.choice(['break', 'continue', 's0 += 1'])}")
        elif k < 0.70:
            out.append(f"{ind}zs[{r.choice(names)}{r.choice([' + 1', ' - 1', '', ''])}] = {iexpr(r, names)}")
        elif k < 0.75:
            out.append(f"{ind}let t{depth}{len(out)} = {iexpr(r, names)}")
            names = names + [f"t{depth}{len(out) - 1}"]
        elif k < 0.86 and depth < 3:
            # two indexes walking toward each other (hoisted when each moves by one, at most once a pass)
            lo, hi = f"lo{depth}{len(out)}", f"hi{depth}{len(out)}"
            out.append(f"{ind}var {lo} = {r.choice(['0', '1', '-1', names[0]])}")
            out.append(f"{ind}var {hi} = {r.choice(['n - 1', 'n', 'n + 1', names[0], '2'])}")
            out.append(f"{ind}while {lo} < {hi}:")
            inner = ind + "  "
            steps = []
            for _ in range(r.randint(1, 3)):
                q = r.random()
                if q < 0.3: steps.append(f"{inner}s0 += xs[{lo}] - zs[{hi}]")
                elif q < 0.5: steps.append(f"{inner}zs[{r.choice([lo, hi])}] = {iexpr(r, names + [lo, hi])}")
                elif q < 0.6: steps.append(f"{inner}if xs[{lo}] > {r.randint(0, 8)}: {lo} += 1")
                elif q < 0.7: steps.append(f"{inner}s1 += zs[{r.choice(['0', '2', 'n'])}]")
                elif q < 0.8: steps.append(f"{inner}if {iexpr(r, names + [lo])} > 5: break")
                else: steps.append(f"{inner}{r.choice([lo + ' += 2', hi + ' -= 1', lo + ' += 1'])}")
            r.shuffle(steps)
            out.extend(steps)
            out.append(f"{inner}{lo} += 1")
            if r.random() < 0.5: out.append(f"{inner}s0 += xs[{lo}]")
            out.append(f"{inner}{hi} -= 1")
            if r.random() < 0.5: out.append(f"{inner}s1 += zs[{hi}] + xs[{lo}]")
        elif depth < 3:
            v = f"i{depth + 1}"
            lo = r.choice(["0", "1", names[0], "-1"])
            hi = r.choice(["n", "n - 1", "n + 1", "3", names[0]])
            out.append(f"{ind}for {v} in {lo}..{hi}:")
            out.extend(body(r, [v] + names, depth + 1, ind + "  "))
        else:
            out.append(f"{ind}s1 -= {iexpr(r, names)}")
    return out

def program(seed):
    r = random.Random(seed)
    fs = []
    for k in range(3):
        e = iexpr(r, ["x"], 1, True)
        fs.append(f"fn f{k}(x: Int) -> Int:\n  return {e}\n")
    n = r.choice([3, 5, 8])
    lines = [f"  let n = {n}", f"  let xs = [{', '.join(str(r.randint(-5, 9)) for _ in range(n))}]",
             f"  let ys = [{', '.join(str(r.randint(-5, 9)) + '.25' for _ in range(n))}]",
             f"  var zs = [0] * {n + 1}", "  var s0 = 0", "  var s1 = 0", "  var fl = 0.0"]
    for _ in range(r.randint(1, 3)):
        lines.append(f"  for i0 in {r.choice(['0', '1'])}..{r.choice(['n', 'n - 1', 'n + 1'])}:")
        lines.extend(body(r, ["i0"], 0, "    "))
        lines.append('  print("{s0} {s1} {fl} {zs[0]} {zs[1]}")')
    return "\n".join(fs) + "\nfn main():\n" + "\n".join(lines) + "\n"

if __name__ == "__main__":
    a, b, d = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    for s in range(a, b):
        open(f"{d}/p{s}.vu", "w").write(program(s))
