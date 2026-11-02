#!/usr/bin/env python3
# golangci-lint (own/REPO.out, default flags, the repo's own config) vs vgolint run, as printed:
# issue blocks (header, source line, caret) of the linters vgolint implements, in order.
import subprocess, sys, re, os
S = "/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad"
W = S + "/golint-work"
VG = os.environ.get("VG", W + "/vgolint")
IMPL = set("errcheck govet ineffassign staticcheck unused nolintlint asciicheck copyloopvar dogsled gocyclo misspell nakedret predeclared unconvert whitespace".split())
hdr = re.compile(r"^(.+?):(\d+)(?::(\d+))?: (.*) \(([\w-]+)\)$")
def blocks(text):
    out = []; lines = text.split("\n"); i = 0
    while i < len(lines):
        m = hdr.match(lines[i])
        if m and not lines[i].startswith("* "):
            b = [lines[i]]; j = i + 1
            while j < len(lines) and not hdr.match(lines[j]) and not re.match(r"^\d+ issues:$|^\* \S+: \d+$|^0 issues\.$", lines[j]):
                b.append(lines[j]); j += 1
            out.append((m.group(5), "\n".join(b))); i = j
        else: i += 1
    return out
tot = same = 0
for r in sys.argv[1:] or sorted(os.listdir(S + "/gocorpus")):
    if not os.path.exists(f"{W}/own/{r}.out"): continue
    want_rc = open(f"{W}/own/{r}.rc").read().strip()
    want = open(f"{W}/own/{r}.out").read()
    p = subprocess.run([VG, "run", "--no-cache"], cwd=f"{S}/gocorpus/{r}", capture_output=True, text=True, env=dict(os.environ, VGOLINT_QUIET="1"))
    wb = [b for k, b in blocks(want) if k in IMPL]
    gb = [b for k, b in blocks(p.stdout) if k in IMPL]
    tot += len(wb)
    ok = wb == gb
    if want_rc == "3" or p.returncode == 3:
        werr = open(f"{W}/own/{r}.err").read().strip()
        ok = werr == p.stderr.strip() and str(p.returncode) == want_rc
        print(f"{r:12} config error: {'same' if ok else 'DIFF'}")
        if not ok: print("   want:", werr[:300]); print("   got: ", p.stderr.strip()[:300], p.returncode)
        continue
    if ok: same += len(wb)
    print(f"{r:12} want {len(wb):4} got {len(gb):4} {'same' if ok else 'DIFF'}  rc {want_rc}/{p.returncode}")
    if not ok:
        import difflib
        for l in list(difflib.unified_diff(wb, gb, lineterm="", n=0))[2:14]: print("   ", l.replace("\n", " | ")[:250])
print("TOTAL blocks", tot, "identical-repo blocks", same)
