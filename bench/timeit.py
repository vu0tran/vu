import os, resource, subprocess, sys, time, statistics
name, cmd = sys.argv[1], sys.argv[2:]
env = dict(os.environ)
env.setdefault("GOMAXPROCS", "1")  # single-threaded unless the caller sets it
ts, mems = [], []
for _ in range(5):
    t = time.perf_counter()
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, env=env)
    _, _, ru = os.wait4(p.pid, 0)
    ts.append(time.perf_counter() - t); mems.append(ru.ru_maxrss / 1024)
print(f"{name:<8} {statistics.median(ts):6.2f}s  {max(mems):7.1f} MB")
