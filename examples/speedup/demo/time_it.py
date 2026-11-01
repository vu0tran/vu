import random, time
from typos import did_you_mean
rng = random.Random(7)
words = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(4, 12))) for _ in range(10000)]
best = float("inf")
for _ in range(3):
    t = time.perf_counter()
    for _ in range(10): did_you_mean("pythn", words)
    best = min(best, (time.perf_counter() - t) / 10)
print(f"did_you_mean, 10,000 words: {best * 1000:.1f} ms")
