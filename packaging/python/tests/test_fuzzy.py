"""fuzzy (Vu, through ctypes) against tests/pure.py on random strings: ASCII, accents, CJK, emoji,
empty ones. python tests/test_fuzzy.py [rounds]"""
import os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
import fuzzy
import pure

r = random.Random(1)
alphabet = "abcde" + "éü" + "日本" + "\U0001F600" + " "
def word(): return "".join(r.choice(alphabet) for _ in range(r.randrange(0, 12)))
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
for _ in range(rounds):
    a, b = word(), word()
    assert fuzzy.distance(a, b) == pure.distance(a, b), (a, b)
    ws = [word() for _ in range(r.randrange(0, 6))]
    assert fuzzy.closest(a, ws) == pure.closest(a, ws), (a, ws)
assert fuzzy.distance("kitten", "sitting") == 3
try:
    fuzzy.closest("a", ["b\nc"]); raise SystemExit("FAIL: a word with a line break was accepted")
except ValueError: pass
print("test_fuzzy: %d answers the same as pure Python's" % (2 * rounds + 1))
