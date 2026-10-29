#!/usr/bin/env python3
"""The library tests/lib/words.vu, called through ctypes as a Python program would, against the
same functions written in Python: random strings (with zero bytes and UTF-8), byte strings and lists
of numbers, the failing functions' messages, and every result freed.
  tests/lib/model.py LIBRARY [--seed N] [--rounds N]"""
import ctypes as C, random, sys

a = sys.argv[1:]
L = C.CDLL(a[0])
seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
rounds = int(a[a.index("--rounds") + 1]) if "--rounds" in a else 2000
libc = C.CDLL(None)
libc.free.argtypes = [C.c_void_p]
I, D, P, N = C.c_int64, C.c_double, C.c_void_p, C.POINTER(C.c_int64)
E = C.POINTER(C.c_char_p)
def sig(f, res, *args): fn = getattr(L, f); fn.restype = res; fn.argtypes = list(args); return fn
count_words = sig("count_words", I, C.c_char_p, I)
exclaim = sig("exclaim", P, C.c_char_p, I, N)
reverse_bytes = sig("reverse_bytes", P, C.c_char_p, I, N)
squares = sig("squares", P, I, N)
scaled = sig("scaled", P, C.POINTER(D), I, D, N)
total = sig("total", I, C.POINTER(I), I)
mean = sig("mean", D, C.POINTER(D), I, C.POINTER(P))
greet = sig("greet", P, C.c_char_p, I, I, N, C.POINTER(P))
evens = sig("evens", P, C.POINTER(I), I, N, C.POINTER(P))
psum = sig("psum", I, I)

def take(p, n, ctype):
    v = C.cast(p, C.POINTER(ctype))
    out = v[:n] if ctype is not C.c_char else C.string_at(p, n)
    libc.free(p)
    return out
def message(e):
    t = C.string_at(e.value)
    libc.free(e.value)
    return t

WS = b" \t\n\r\x0b\x0c"
def fsum_left(xs):   # (Python's sum() of floats compensates; Vu's loop adds left to right)
    t = 0.0
    for x in xs: t += x
    return t
r = random.Random(seed)
pieces = [b"a", b"B", b" ", b"  ", b"\t", b"\n", b"\x00", "é".encode(), "日本".encode(), b"\xff", b"word", b"x y"]
n = 0
for _ in range(rounds):
    s = b"".join(r.choice(pieces) for _ in range(r.randrange(0, 12)))
    xs = [r.choice([0, 1, -1, 7, 2**62, -2**62, r.randrange(-1000, 1000)]) for _ in range(r.randrange(0, 8))]
    fs = [r.choice([0.0, -0.0, 1.5, 1e300, -2.25, r.random()]) for _ in range(r.randrange(0, 8))]
    k = r.choice([0.0, 2.0, -0.5, 3.0])
    ln = C.c_int64(-7)
    err = C.c_void_p()
    def same(what, got, want):
        global n
        n += 1
        if got != want: sys.exit("FAIL %s on %r %r %r: got %r, want %r" % (what, s, xs, fs, got, want))
    same("count_words", count_words(s, len(s)), len(s.split()))
    p = exclaim(s, len(s), C.byref(ln)); same("exclaim", take(p, ln.value, C.c_char), s + b"!")
    p = reverse_bytes(s, len(s), C.byref(ln)); same("reverse_bytes", take(p, ln.value, C.c_char), s[::-1])
    m = r.randrange(0, 20)
    p = squares(m, C.byref(ln)); same("squares", take(p, ln.value, I), [i * i for i in range(m)])
    fa = (D * max(1, len(fs)))(*fs)
    p = scaled(fa, len(fs), k, C.byref(ln)); same("scaled", take(p, ln.value, D), [x * k for x in fs])
    xa = (I * max(1, len(xs)))(*xs)
    prefix = [sum(xs[:i + 1]) for i in range(len(xs))]
    if all(-2**63 <= t < 2**63 for t in prefix): same("total", total(xa, len(xs)), sum(xs))   # (else Vu stops: overflow)
    got = mean(fa, len(fs), C.byref(err))
    if fs: same("mean", (got, err.value), (fsum_left(fs) / len(fs), None))
    else: same("mean error", (got, message(err)), (0.0, b"mean of no numbers"))
    times = r.randrange(-2, 4)
    p = greet(s, len(s), times, C.byref(ln), C.byref(err))
    if times < 0: same("greet error", (p, ln.value, message(err)), (None, 0, b"times is negative: %d" % times))
    else: same("greet", take(p, ln.value, C.c_char), b" ".join([b"hi " + s + b"."] * times).strip(WS))
    p = evens(xa, len(xs), C.byref(ln), C.byref(err))
    neg = [x for x in xs if x < 0]
    if neg: same("evens error", (p, message(err)), (None, b"negative: %d" % neg[0]))
    else: same("evens", take(p, ln.value, I), [x for x in xs if x % 2 == 0])
same_n = psum(500)
if same_n != 249500: sys.exit("FAIL psum: %d" % same_n)
print("model.py: %d answers the same as Python's (seed %d)" % (n + 1, seed))
