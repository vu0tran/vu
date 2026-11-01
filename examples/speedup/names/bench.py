"""Times the pure-Python functions, their Vu ports (after vu speedup) and, when jellyfish is installed,
jellyfish's own Rust extension, on name pairs and on a list of names. python3 bench.py"""
import random, sys, time
sys.path.insert(0, ".")
import names
from _vu_names import speedup
try:
    import jellyfish
except ImportError:
    jellyfish = None

rng = random.Random(3)
first = ["james", "mary", "robert", "patricia", "john", "jennifer", "michael", "linda", "william", "elizabeth",
         "josé", "zoë", "françois", "björn", "siobhán", "aleksandr", "mohammed", "ngọc", "søren", "łukasz"]
def name():
    w = list(rng.choice(first))
    for _ in range(rng.randint(0, 2)):   # a typo or two
        i = rng.randrange(len(w))
        w[i] = rng.choice("abcdefghijklmnopqrstuvwxyz")
    return "".join(w).title()
pairs = [(name(), name()) for _ in range(20000)]
people = [name() for _ in range(5000)]

def per_call(f, args_list):
    best = float("inf")
    for _ in range(3):
        t = time.perf_counter()
        for a in args_list: f(*a)
        best = min(best, time.perf_counter() - t)
    return best / len(args_list) * 1e6

def row(label, py, vu, rust=None):
    s = f"{label:<34} Python {py:8.2f} us   Vu {vu:7.2f} us ({py / vu:4.1f}x)"
    if rust is not None: s += f"   jellyfish's Rust {rust:6.2f} us ({py / rust:4.1f}x)"
    print(s)

for fname, rname in [("jaro_winkler_similarity", "jaro_winkler_similarity"), ("damerau_levenshtein_distance", "damerau_levenshtein_distance")]:
    py = getattr(names, fname)
    vu = speedup(py)
    for a, b in pairs[:2000]: assert vu(a, b) == py(a, b)
    rust = getattr(jellyfish, rname) if jellyfish else None
    row(fname + " (a pair)", per_call(py, pairs), per_call(vu, pairs), per_call(rust, pairs) if rust else None)

vu = speedup(names.closest_names)
queries = [(name(), people) for _ in range(20)]
for q in queries[:5]: assert vu(*q) == names.closest_names(*q)
row("closest_names (among 5,000)", per_call(names.closest_names, queries) / 1000, per_call(vu, queries) / 1000)
print("(closest_names in ms per call; answers checked identical)")
