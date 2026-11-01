"""Times track_km and nearest in Python and as Vu on realistic GPS data. python3 bench.py (after vu speedup)."""
import random, sys, time
sys.path.insert(0, ".")
import geo
from _vu_geo import speedup

rng = random.Random(5)
def walk(n):   # a GPS track: small steps from a start near Paris
    lat, lon, lats, lons = 48.85, 2.35, [], []
    for _ in range(n):
        lat += rng.uniform(-0.0005, 0.0005); lon += rng.uniform(-0.0005, 0.0005)
        lats.append(lat); lons.append(lon)
    return lats, lons

def best(f, *a):
    t = float("inf")
    for _ in range(3):
        s = time.perf_counter(); f(*a); t = min(t, time.perf_counter() - s)
    return t

tk, nr = speedup(geo.track_km), speedup(geo.nearest)
lats, lons = walk(100_000)
assert tk(lats, lons) == geo.track_km(lats, lons)
py, vu = best(geo.track_km, lats, lons), best(tk, lats, lons)
print(f"track_km, 100,000 points:            Python {py * 1e3:7.1f} ms, Vu {vu * 1e3:6.2f} ms: {py / vu:5.1f}x")
lats, lons = walk(5_000)
qlats, qlons = walk(200)
assert nr(lats, lons, qlats, qlons) == geo.nearest(lats, lons, qlats, qlons)
py, vu = best(geo.nearest, lats, lons, qlats, qlons), best(nr, lats, lons, qlats, qlons)
print(f"nearest, 200 queries among 5,000:    Python {py * 1e3:7.1f} ms, Vu {vu * 1e3:6.2f} ms: {py / vu:5.1f}x")
print("(answers checked identical, to the last bit)")
