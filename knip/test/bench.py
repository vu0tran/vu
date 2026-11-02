# CPU time (user+sys) and wall time of knip and vknip on projects, best of N runs each.
#   python3 bench.py VKNIP KNIP_JS N DIR...
import os, sys, time, subprocess
def run(cmd, cwd):
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _, status, ru = os.wait4(p.pid, 0)
    return ru.ru_utime + ru.ru_stime, time.time() - t0
def best(cmd, cwd, n):
    cpu = []; wall = []
    for _ in range(n):
        c, w = run(cmd, cwd); cpu.append(c); wall.append(w)
    return min(cpu), min(wall)
vk, kn, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
print("| project | files | knip CPU s | vknip CPU s | CPU ratio | knip wall s | vknip wall s |")
print("|---|---:|---:|---:|---:|---:|---:|")
for d in sys.argv[4:]:
    nfiles = 0
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in ("node_modules", ".git")]
        nfiles += sum(1 for f in files if f.endswith((".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts", ".cts")))
    kc, kw = best(["node", kn], d, n)
    vc, vw = best([vk], d, n)
    print(f"| {os.path.basename(d)} | {nfiles} | {kc:.2f} | {vc:.3f} | {kc / max(vc, 1e-3):.0f}x | {kw:.2f} | {vw:.3f} |", flush=True)
