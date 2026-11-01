"""Times close_matches in Python and as Vu on realistic calls: a misspelled word against a list of
words, as a CLI's "did you mean?" or a search box does. python3 bench.py (after vu speedup)."""
import importlib, random, statistics, sys, time
sys.path.insert(0, ".")
import suggest
from _vu_suggest import speedup

rng = random.Random(7)
letters = "abcdefghijklmnopqrstuvwxyz"
def word():
    return "".join(rng.choice(letters) for _ in range(rng.randint(4, 12)))
def typo(w):
    i = rng.randrange(len(w))
    return w[:i] + rng.choice(letters) + w[i + 1:]

fast = speedup(suggest.close_matches)
for size in (50, 1000, 10000):
    words = [word() for _ in range(size)]
    queries = [typo(rng.choice(words)) for _ in range(200 if size < 10000 else 30)]
    for q in queries:
        assert fast(q, words) == suggest.close_matches(q, words), q
    def run(f):
        best = float("inf")
        for _ in range(3):
            t = time.perf_counter()
            for q in queries: f(q, words)
            best = min(best, time.perf_counter() - t)
        return best / len(queries)
    py, vu = run(suggest.close_matches), run(fast)
    print(f"{size:>6} words: Python {py * 1e3:8.3f} ms per call, Vu {vu * 1e3:7.3f} ms: {py / vu:5.1f}x  (answers identical)")
