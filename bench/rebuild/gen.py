#!/usr/bin/env python3
"""The same generated program in Vu and in Rust, of N functions spread over M modules, for timing
builds and rebuilds after a one-line edit (run.sh). Each function does a little arithmetic, string
and list work and calls one function of the module before it (on a path the run never takes), so
nothing is dead code to either compiler.
  gen.py N M OUTDIR"""
import os, sys

n, m, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
per = n // m
vu, rs = os.path.join(out, "vu"), os.path.join(out, "rs")
os.makedirs(vu, exist_ok=True)
os.makedirs(os.path.join(rs, "src"), exist_ok=True)

def vu_fn(k, i):
    call = "" if k == 0 else "\n  if x < 0: t += m%d.f%d_%d(t %% 7, s + \"a\")" % (k - 1, k - 1, i % per)
    return ("fn f%d_%d(x: Int, s: Str) -> Int:\n"
            "  var t = x + %d\n"
            "  var xs: [Int] = []\n"
            "  for i in 0..8:\n"
            "    t = (t * 31 + i) %% 1000003\n"
            "    xs.push(t)\n"
            "  if s.len > 2: t += xs[s.len %% 8]%s\n"
            "  return t + xs.len\n") % (k, i, i, call)

def rs_fn(k, i):
    call = "" if k == 0 else "\n    if x < 0 { t += crate::m%d::f%d_%d(t %% 7, &format!(\"{}a\", s)); }" % (k - 1, k - 1, i % per)
    return ("pub fn f%d_%d(x: i64, s: &str) -> i64 {\n"
            "    let mut t = x + %d;\n"
            "    let mut xs: Vec<i64> = Vec::new();\n"
            "    for i in 0..8 {\n"
            "        t = (t * 31 + i) %% 1000003;\n"
            "        xs.push(t);\n"
            "    }\n"
            "    if s.len() > 2 { t += xs[s.len() %% 8]; }%s\n"
            "    t + xs.len() as i64\n}\n") % (k, i, i, call)

for k in range(m):
    with open(os.path.join(vu, "m%d.vu" % k), "w") as f:
        if k > 0: f.write("import m%d\n\n" % (k - 1))
        f.write("\n".join(vu_fn(k, i) for i in range(per)))
    with open(os.path.join(rs, "src", "m%d.rs" % k), "w") as f:
        f.write("\n".join(rs_fn(k, i) for i in range(per)))
# main sums every function of the last module
with open(os.path.join(vu, "main.vu"), "w") as f:
    f.write("import m%d\n\nfn main():\n  let base = arg(1, 0)\n  var t = 0\n" % (m - 1))
    for i in range(per): f.write("  t += m%d.f%d_%d(base + %d, \"abcd\")\n" % (m - 1, m - 1, i, i))
    f.write("  print(\"{t}\")\n")
with open(os.path.join(rs, "src", "main.rs"), "w") as f:
    for k in range(m): f.write("mod m%d;\n" % k)
    f.write("\nfn main() {\n    let base: i64 = std::env::args().nth(1).and_then(|a| a.parse().ok()).unwrap_or(0);\n    let mut t: i64 = 0;\n")
    for i in range(per): f.write("    t += m%d::f%d_%d(base + %d, \"abcd\");\n" % (m - 1, m - 1, i, i))
    f.write("    println!(\"{}\", t);\n}\n")
with open(os.path.join(rs, "Cargo.toml"), "w") as f:
    f.write('[package]\nname = "gen"\nversion = "0.1.0"\nedition = "2021"\n\n[profile.release]\nincremental = false\n')
