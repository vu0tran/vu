"""Times fuzzy (Vu) against tests/pure.py: distance() on 2,000 pairs of 12-letter words, and
closest() of 20 words among 5,000. Prints the median of 5 runs of each."""
import os, random, statistics, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import fuzzy
import pure

r = random.Random(7)
def word(n=12): return "".join(r.choice("abcdefghij") for _ in range(n))
pairs = [(word(), word()) for _ in range(2000)]
words = [word(r.randrange(4, 14)) for _ in range(5000)]
queries = [word(8) for _ in range(20)]
def median(f):
    ts = []
    for _ in range(5):
        t = time.perf_counter(); f(); ts.append(time.perf_counter() - t)
    return statistics.median(ts)
for name, m in [("distance x 2000", lambda m: [m.distance(a, b) for a, b in pairs]),
                ("closest, 20 in 5000", lambda m: [m.closest(q, words) for q in queries])]:
    assert m(fuzzy) == m(pure)
    tp, tv = median(lambda: m(pure)), median(lambda: m(fuzzy))
    print("%-20s  pure Python %8.1f ms   Vu %7.1f ms   %5.0fx" % (name, tp * 1e3, tv * 1e3, tp / tv))
