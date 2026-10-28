"""The eval's tasks. Each is a program that reads standard input and writes standard output, so one set
of tests judges every language. A task has a prompt (what the program must do), gen(rng) making a
random input, and ref(text) giving the right output (in Python: the reference). cases() turns a task
into tests: its edge inputs plus random ones, each with the reference's output."""
import collections, heapq, itertools, json, math, random, re, sys, zlib
sys.set_int_max_str_digits(0)

TASKS = []

def add(name, prompt, gen, ref, edges=()):
    TASKS.append({"name": name, "prompt": " ".join(prompt.split()), "gen": gen, "ref": ref, "edges": list(edges)})

def cases(t, n=6, seed=0):
    rng = random.Random(zlib.crc32(t["name"].encode()) + seed)
    ins = list(t["edges"]) + [t["gen"](rng) for _ in range(n)]
    return [{"stdin": i, "stdout": t["ref"](i)} for i in ins]

def words(r, n, alpha="abcde", lo=1, hi=6):
    return ["".join(r.choice(alpha) for _ in range(r.randint(lo, hi))) for _ in range(n)]

def lines_of(t):
    """The lines of t as a line reader gives them: split at "\\n", a last line without one included."""
    if t == "": return []
    ls = t.split("\n")
    if t.endswith("\n"): ls.pop()
    return ls

def out(ls):
    return "".join(str(l) + "\n" for l in ls)

# ================================================================ text

def g(r): return "\n".join(" ".join(words(r, r.randint(0, 8), "aAbBc")) for _ in range(r.randint(1, 6))) + "\n"
def f(t): return out(f"{c} {w}" for w, c in sorted(collections.Counter(t.lower().split()).items(), key=lambda x: (-x[1], x[0])))
add("word_count", """Read all of standard input. Split it into words at runs of whitespace (spaces, tabs, newlines),
lowercase each word (ASCII), and count them. Print one line per distinct word, "COUNT WORD", most frequent first;
words with the same count in byte order.""", g, f, ["", "\n\n", "A a A\n"])

def g(r): return "".join(w + "\n" for w in words(r, r.randint(0, 6)))
def f(t): return out(reversed(lines_of(t)))
add("reverse_lines", """Print the lines of standard input in reverse order, each followed by "\\n". Text after the last
newline, if any, is a line too.""", g, f, ["", "one\n", "a\nb", "\n\n"])

def g(r): return f"{r.randint(-60, 60)}\n" + " ".join(words(r, 5, "abXYz,.")) + "\n"
def f(t):
    k, rest = t.split("\n", 1)
    k = int(k)
    def sh(c):
        if "a" <= c <= "z": return chr((ord(c) - 97 + k) % 26 + 97)
        if "A" <= c <= "Z": return chr((ord(c) - 65 + k) % 26 + 65)
        return c
    return "".join(sh(c) for c in rest)
add("caesar", """The first line of standard input is an integer K (it may be negative). Shift every ASCII letter in the
rest of the input by K places in the alphabet, wrapping around and keeping its case; leave every other byte as it is.
Print the rest of the input, shifted, exactly (with its newlines).""", g, f, ["0\nHello\n", "-1\nabc XYZ!\n", "27\nZz\n"])

def g(r): return out(r.choice(["abba", "Ab,c Ba", "racecar", "abc", "12 21", "x", ""]) for _ in range(6))
def f(t):
    def pal(l):
        s = [c.lower() for c in l if c.isascii() and c.isalnum()]
        return s == s[::-1]
    return out("yes" if pal(l) else "no" for l in lines_of(t))
add("palindromes", """For each line of standard input print "yes" if the line reads the same backwards when only its ASCII
letters and digits are kept, compared without case, and "no" otherwise. A line with no letters or digits is a
palindrome.""", g, f, ["A man, a plan, a canal: Panama\nhello\n\n"])

def g(r): return out("".join(r.choice("aab") * r.randint(1, 4) for _ in range(r.randint(0, 5))) for _ in range(4))
def f(t): return out("".join(f"{len(list(gr))}{k}" for k, gr in itertools.groupby(l)) for l in lines_of(t))
add("run_length", """Each line of standard input holds text with no digits. Print its run-length encoding: each run of
the same byte as the run's length then the byte, so "aaab" becomes "3a1b". An empty line prints an empty line.""",
    g, f, ["aaab\n\nz\n"])

def g(r): return out(words(r, r.randint(1, 10), "abc", 1, 4))
def f(t):
    groups = collections.defaultdict(list)
    for w in t.split(): groups["".join(sorted(w))].append(w)
    return out(" ".join(gr) for gr in sorted(sorted(v) for v in groups.values()))
add("anagram_groups", """Each line of standard input is one lowercase word. Group the words that are anagrams of each other.
Print each group on one line, its words sorted (byte order) and separated by single spaces, the groups ordered by
their sorted word lists (compare first words, then second words, and so on, a shorter list first when it is a
prefix). A word given twice appears twice.""", g, f, ["listen\nsilent\nenlist\ngoogle\n"])

def g(r): return out(" ".join(words(r, r.randint(1, 4), "aBcD")) for _ in range(3))
def f(t): return out(" ".join(w[:1].upper() + w[1:].lower() for w in l.split(" ")) for l in lines_of(t))
add("title_case", """For each line of standard input, words are separated by single spaces. Make the first byte of each
word uppercase and its other bytes lowercase (ASCII letters only; other bytes stay). Print the lines.""",
    g, f, ["hello WORLD\n", "\n"])

def g(r): return out(words(r, r.randint(1, 8)))
def f(t):
    ls = lines_of(t)
    if not ls: return "0: \n"
    best = max(ls, key=len)
    return f"{len(best)}: {best}\n"
add("longest_line", """Print the longest line of standard input (its length in bytes, without the newline) as
"LENGTH: LINE". If several are longest print the first. If there are no lines print "0: ".""",
    g, f, ["", "a\nbb\ncc\n"])

def g(r): return " ".join(words(r, 12, "aeiouxyzAE")) + "\n"
def f(t): return out([f"{v} {t.lower().count(v)}" for v in "aeiou"] + [f"total {sum(t.lower().count(v) for v in 'aeiou')}"])
add("vowel_stats", """Count the vowels a, e, i, o and u (either case) in standard input. Print five lines "a N", "e N",
"i N", "o N", "u N", then "total N".""", g, f, ["", "AEIOUaeiou\n"])

def g(r): return f"{r.randint(1, 15)}\n" + " ".join(words(r, r.randint(0, 15))) + "\n"
def f(t):
    w, rest = t.split("\n", 1)
    w = int(w)
    lines = []
    for x in rest.split():
        if lines and len(lines[-1]) + 1 + len(x) <= w: lines[-1] += " " + x
        else: lines.append(x)
    return out(lines)
add("wrap_text", """The first line of standard input is a width W (at least 1); the rest is text. Split the text into words
at whitespace and print them in lines of at most W bytes, words separated by one space, filling each line greedily
(a word goes on the current line if it fits, else it starts a new one). A word longer than W stands on a line of its
own.""", g, f, ["5\nhello world\n", "3\nabcdef a b\n", "10\n\n"])

def g(r): return out(r.choice(["ab", "ba", "abc", "cab", "zz", "a"]) + " " + r.choice(["ba", "ab", "acb", "bca", "z", "a"]) for _ in range(5))
def f(t): return out("yes" if sorted(a) == sorted(b) else "no" for a, b in (l.split() for l in lines_of(t)))
add("is_anagram", """Each line of standard input holds two words separated by one space. Print "yes" if they are
anagrams (the same bytes in some order) and "no" otherwise.""", g, f, ["abc cab\nab abc\n"])

def g(r): return " ".join(words(r, r.randint(1, 10), "ab")) + "\n"
def f(t):
    ws = t.split()
    seen, outl = set(), []
    for w in ws:
        if w not in seen:
            seen.add(w)
            outl.append(w)
    return " ".join(outl) + "\n"
add("dedupe_words", """Standard input holds words separated by whitespace. Print each distinct word once, in the order
it first appears, separated by single spaces, then a newline.""", g, f, ["a b a c b\n"])

def g(r): return "".join(r.choice("()[]{}ab") for _ in range(r.randint(0, 14))) + "\n"
def f(t):
    s = t.rstrip("\n")
    st, pairs = [], {")": "(", "]": "[", "}": "{"}
    for c in s:
        if c in "([{": st.append(c)
        elif c in pairs:
            if not st or st[-1] != pairs[c]: return "unbalanced\n"
            st.pop()
    return "balanced\n" if not st else "unbalanced\n"
add("brackets", """Standard input is one line. Print "balanced" if its brackets (), [] and {} are properly nested and
closed, ignoring every other byte, and "unbalanced" otherwise.""", g, f, ["\n", "([]{})\n", "(]\n", "((\n"])

def g(r): return out(r.choice(["2026-10-28", "1999-12-31", "2000-02-29", "1900-02-29", "2023-02-29", "2024-13-01", "2024-04-31", "abc", "2024-1-1"]) for _ in range(5))
def f(t):
    def ok(s):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
        if not m: return False
        y, mo, d = map(int, m.groups())
        if not 1 <= mo <= 12: return False
        leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
        days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1]
        return 1 <= d <= days
    return out("valid" if ok(l) else "invalid" for l in lines_of(t))
add("valid_dates", """Each line of standard input should be a date YYYY-MM-DD (exactly four, two and two digits). Print
"valid" if it is a real date in the Gregorian calendar (leap years: divisible by 4, except centuries not divisible by
400) and "invalid" otherwise.""", g, f, ["2000-02-29\n1900-02-29\n"])

def g(r): return out(r.choice(["hello world", "a", "", "abc def ghi"]) for _ in range(4))
def f(t): return out(" ".join(w[::-1] for w in l.split(" ")) for l in lines_of(t))
add("reverse_words_letters", """For each line of standard input (words separated by single spaces), reverse the bytes
of each word but keep the words in order. Print the lines.""", g, f, ["ab cd\n"])

def g(r): return "".join(r.choice(["ab", "abab", "aa", "abc", "x"]) for _ in range(2)) + "\n"
def f(t):
    s = t.rstrip("\n")
    for k in range(1, len(s) + 1):
        if len(s) % k == 0 and s[:k] * (len(s) // k) == s: return f"{k}\n"
    return "0\n"
add("smallest_period", """Standard input is one line S. Print the length of the shortest string P such that S is P
repeated a whole number of times (S itself when nothing shorter works). Print 0 for an empty line.""",
    g, f, ["\n", "abab\n", "abc\n", "aaaa\n"])

def g(r): return " ".join(words(r, r.randint(1, 6), "abc", 1, 5)) + "\n"
def f(t):
    ws = t.split()
    if not ws: return "\n"
    p = ws[0]
    for w in ws[1:]:
        while not w.startswith(p): p = p[:-1]
    return p + "\n"
add("common_prefix", """Standard input holds words separated by whitespace. Print their longest common prefix (an empty
line if there is none or there are no words).""", g, f, ["\n", "flower flow flight\n"])

def g(r): return " ".join(r.choice(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero"]) for _ in range(r.randint(1, 6))) + "\n"
def f(t):
    d = "zero one two three four five six seven eight nine".split()
    return "".join(str(d.index(w)) for w in t.split()) + "\n"
add("digit_words", """Standard input holds English digit words (zero to nine) separated by whitespace. Print the digits
they spell as one number, with no separators ("one zero" prints 10).""", g, f, ["zero\n"])

# ================================================================ numbers

def g(r): return " ".join(str(r.randint(-10**12, 10**12)) for _ in range(r.randint(1, 30))) + "\n"
def f(t): return f"{sum(int(x) for x in t.split())}\n"
add("sum_ints", """Standard input holds integers separated by whitespace (each, and their sum, fits in a signed
64-bit integer). Print their sum (0 when there are none).""", g, f, ["", "-5\n", "9223372036854775806 1\n"])

def g(r): return " ".join(str(r.randint(-1000, 1000)) for _ in range(r.randint(1, 20))) + "\n"
def f(t):
    xs = sorted(int(x) for x in t.split())
    n = len(xs)
    med = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
    return f"{xs[0]}\n{xs[-1]}\n{sum(xs) / n:.2f}\n{med:.2f}\n"
add("stats", """Standard input holds at least one integer, separated by whitespace. Print four lines: the minimum,
the maximum, the mean with exactly 2 digits after the decimal point, and the median with 2 digits (for an even count,
the mean of the two middle values). Round as C's printf("%.2f") does.""", g, f, ["5\n", "1 2 3 4\n"])

def g(r): return f"{r.randint(0, 200000)}\n"
def f(t):
    n = int(t)
    s = bytearray([1]) * (n + 1)
    s[0:2] = b"\x00\x00"[:min(2, n + 1)]
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]: s[i * i::i] = bytearray(len(range(i * i, n + 1, i)))
    ps = [i for i in range(n + 1) if s[i]]
    return f"{len(ps)}\n{' '.join(map(str, ps[-10:]))}\n"
add("primes_upto", """Standard input holds one integer N (0 <= N <= 1000000). Print how many primes are <= N on the
first line, then the last (largest) up to 10 of them in increasing order on the second line, separated by spaces (an
empty second line if there are none).""", g, f, ["0\n", "1\n", "2\n", "10\n", "1000000\n"])

def g(r): return f"{r.randint(0, 100)}\n"
def f(t): return out("FizzBuzz" if i % 15 == 0 else "Fizz" if i % 3 == 0 else "Buzz" if i % 5 == 0 else i for i in range(1, int(t) + 1))
add("fizzbuzz", """Standard input holds an integer N (0 <= N <= 100000). Print 1 to N, one per line, but "Fizz" for
multiples of 3, "Buzz" for multiples of 5 and "FizzBuzz" for multiples of both.""", g, f, ["0\n", "15\n"])

def g(r): return out(f"{r.randint(1, 10**9)} {r.randint(1, 10**9)}" for _ in range(5))
def f(t): return out(f"{math.gcd(a, b)} {a * b // math.gcd(a, b)}" for a, b in (map(int, l.split()) for l in lines_of(t)))
add("gcd_lcm", """Each line of standard input holds two positive integers A and B (each at most 10^9). Print "GCD LCM"
for each line.""", g, f, ["12 18\n1 1\n"])

def g(r): return out(f"{r.randint(0, 2**62 - 1)} {r.randint(2, 36)}" for _ in range(5))
def f(t):
    def conv(n, b):
        if n == 0: return "0"
        s = ""
        while n: n, d = divmod(n, b); s = "0123456789abcdefghijklmnopqrstuvwxyz"[d] + s
        return s
    return out(conv(*map(int, l.split())) for l in lines_of(t))
add("base_convert", """Each line of standard input holds a non-negative integer N (below 2^62) and a base B from 2 to 36.
Print N written in base B, with the digits 0-9 then lowercase a-z.""", g, f, ["0 2\n255 16\n35 36\n"])

def g(r): return f"{r.randint(1, 30000)}\n"
def f(t):
    n = int(t)
    steps = [0] * (n + 1)
    best, bs = 1, 0
    for s in range(2, n + 1):
        x, c = s, 0
        while x >= s: x = x // 2 if x % 2 == 0 else 3 * x + 1; c += 1
        steps[s] = c + steps[x]
        if steps[s] > bs: best, bs = s, steps[s]
    return f"{best} {bs}\n"
add("collatz", """Standard input holds an integer N (1 <= N <= 1000000). Among the starting values 1 to N, find the one
whose Collatz sequence (n becomes n/2 if even, 3n+1 if odd, until it reaches 1) takes the most steps. Print
"START STEPS"; on a tie, the smallest start.""", g, f, ["1\n", "10\n", "1000000\n"])

def g(r):
    n, m, p = r.randint(1, 5), r.randint(1, 5), r.randint(1, 5)
    a = out(" ".join(str(r.randint(-50, 50)) for _ in range(m)) for _ in range(n))
    b = out(" ".join(str(r.randint(-50, 50)) for _ in range(p)) for _ in range(m))
    return f"{n} {m} {p}\n" + a + b
def f(t):
    v = [int(x) for x in t.split()]
    n, m, p, rest = v[0], v[1], v[2], v[3:]
    A = [rest[i * m:(i + 1) * m] for i in range(n)]
    B = [rest[n * m + k * p:n * m + (k + 1) * p] for k in range(m)]
    return out(" ".join(str(sum(A[i][k] * B[k][j] for k in range(m))) for j in range(p)) for i in range(n))
add("matrix_multiply", """Standard input: a line "N M P", then N lines of M integers (matrix A), then M lines of P
integers (matrix B). Print the product A times B as N lines of P integers separated by single spaces.""",
    g, f, ["1 1 1\n2\n3\n"])

def g(r): return out(r.randint(1, 3999) for _ in range(6))
def f(t):
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    def rom(n):
        s = ""
        for v, sym in vals:
            while n >= v: s += sym; n -= v
        return s
    return out(rom(int(l)) for l in lines_of(t))
add("to_roman", """Each line of standard input is an integer from 1 to 3999. Print it as a Roman numeral in standard
subtractive form (IV, IX, XL, XC, CD, CM).""", g, f, ["1\n4\n3999\n1994\n"])

def g(r): return out(r.choice(["MCMXCIV", "IV", "MMMCMXCIX", "LVIII", "IX", "XLII"]) for _ in range(5))
def f(t):
    v = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    def num(s):
        total = 0
        for i, c in enumerate(s):
            if i + 1 < len(s) and v[c] < v[s[i + 1]]: total -= v[c]
            else: total += v[c]
        return total
    return out(num(l) for l in lines_of(t))
add("from_roman", """Each line of standard input is a valid Roman numeral (standard form, 1 to 3999). Print its value.""",
    g, f, ["MCMXCIV\n"])

def g(r): return f"{r.randint(0, 90)}\n"
def f(t):
    n = int(t)
    a, b = 0, 1
    for _ in range(n): a, b = b, a + b
    return f"{a}\n"
add("fibonacci", """Standard input holds N (0 <= N <= 90). Print the Nth Fibonacci number, with F(0) = 0 and F(1) = 1.""",
    g, f, ["0\n", "1\n", "90\n"])

def g(r): return out(r.randint(1, 10**12) for _ in range(4))
def f(t):
    def fac(n):
        fs, d = [], 2
        while d * d <= n:
            while n % d == 0: fs.append(d); n //= d
            d += 1
        if n > 1: fs.append(n)
        return fs
    return out(" ".join(map(str, fac(int(l)))) for l in lines_of(t))
add("factorize", """Each line of standard input is an integer N (2 <= N <= 10^12). Print its prime factors in increasing
order, with repeats, separated by single spaces.""", g, f, ["2\n12\n999999999989\n"])

def g(r): return out(f"{r.randint(0, 10**6)} {r.randint(0, 10**6)} {r.randint(1, 10**9)}" for _ in range(4))
def f(t): return out(pow(*map(int, l.split())) for l in lines_of(t))
add("modpow", """Each line of standard input holds B, E and M (0 <= B, E <= 10^6, 1 <= M <= 10^9). Print B to the power
E modulo M (with 0^0 = 1, then taken modulo M).""", g, f, ["2 10 1000\n0 0 1\n5 0 7\n"])

def g(r): return " ".join(str(r.randint(-20, 20)) for _ in range(r.randint(1, 15))) + "\n"
def f(t):
    xs = [int(x) for x in t.split()]
    best, cur = xs[0], 0
    for x in xs:
        cur = max(x, cur + x)
        best = max(best, cur)
    return f"{best}\n"
add("max_subarray", """Standard input holds at least one integer, separated by whitespace. Print the largest sum of a
non-empty run of consecutive integers.""", g, f, ["-3 -1 -2\n", "5\n"])

def g(r): return f"{r.randint(0, 20)}\n"
def f(t): return f"{math.comb(2 * int(t), int(t)) // (int(t) + 1)}\n"
add("catalan", """Standard input holds N (0 <= N <= 30). Print the Nth Catalan number.""", g, f, ["0\n", "30\n"])

def g(r): return f"{r.randint(1, 40)}\n"
def f(t):
    n = int(t)
    rows = [[1]]
    for i in range(1, n): rows.append([1] + [rows[-1][j] + rows[-1][j + 1] for j in range(i - 1)] + [1])
    return out(" ".join(map(str, r)) for r in rows)
add("pascal", """Standard input holds N (1 <= N <= 40). Print the first N rows of Pascal's triangle, the numbers of each
row separated by single spaces.""", g, f, ["1\n", "5\n"])

def g(r): return out(f"{r.randint(-100, 100)} {r.randint(-100, 100)}" for _ in range(r.randint(3, 12)))
def f(t):
    pts = sorted(set(tuple(map(int, l.split())) for l in lines_of(t)))
    if len(pts) < 3: return out(f"{x} {y}" for x, y in pts)
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    return out(f"{x} {y}" for x, y in lower[:-1] + upper[:-1])
add("convex_hull", """Each line of standard input holds a point "X Y" (integers). Print the convex hull's vertices, one
"X Y" per line, counterclockwise, starting from the lowest X (lowest Y among those), without points that lie on an edge.
Duplicate points count once; with fewer than 3 distinct points print them all sorted by X then Y.""",
    g, f, ["0 0\n1 1\n2 2\n", "0 0\n2 0\n1 1\n2 2\n0 2\n"])

def g(r): return out(r.choice(["3 + 4 * 2", "(1 + 2) * 3", "10 / 3", "2 - 5 - 1", "-(4 - 6) * 3", "7 % 4 + 1", "((2))"]) for _ in range(5))
def f(t):
    def ev(s):
        toks = re.findall(r"\d+|[-+*/%()]", s)
        pos = [0]
        def peek(): return toks[pos[0]] if pos[0] < len(toks) else None
        def nxt(): pos[0] += 1; return toks[pos[0] - 1]
        def atom():
            if peek() == "-": nxt(); return -atom()
            if peek() == "(":
                nxt(); v = expr(); nxt(); return v
            return int(nxt())
        def term():
            v = atom()
            while peek() in ("*", "/", "%"):
                op = nxt(); w = atom()
                if op == "*": v *= w
                elif op == "/": v = int(v / w)
                else: v = v - int(v / w) * w
            return v
        def expr():
            v = term()
            while peek() in ("+", "-"):
                op = nxt(); w = term()
                v = v + w if op == "+" else v - w
            return v
        return expr()
    return out(ev(l) for l in lines_of(t))
add("calculator", """Each line of standard input is an arithmetic expression on non-negative integers with + - * / %,
unary minus and parentheses, and spaces anywhere. * / % bind tighter than + and -, all left to right; / truncates toward
zero and % takes the sign of the dividend (as in C). No division by zero occurs. Print each expression's value.""",
    g, f, ["1+2*3\n", "-(2)\n"])

# ================================================================ data

def g(r): return json.dumps([{"name": w, "age": r.randint(1, 90)} for w in words(r, r.randint(0, 6))]) + "\n"
def f(t):
    people = json.loads(t)
    if not people: return "none\n"
    old = max(people, key=lambda p: p["age"])
    return f"{len(people)} people, average age {sum(p['age'] for p in people) / len(people):.1f}, oldest {old['name']}\n"
add("json_people", """Standard input is a JSON array of objects, each with "name" (a string) and "age" (an integer).
Print "N people, average age A, oldest NAME", with A rounded to 1 decimal (as printf("%.1f")); the oldest is the first
with the highest age. For an empty array print "none".""", g, f, ["[]\n", '[{"name": "a", "age": 5}]\n'])

def g(r):
    rows = [["id", "name", "score"]] + [[str(i), r.choice(["ann", "bob", "cy"]), str(r.randint(0, 100))] for i in range(r.randint(1, 8))]
    return out(",".join(x) for x in rows)
def f(t):
    rows = [l.split(",") for l in lines_of(t)][1:]
    tot = collections.defaultdict(int)
    for _, name, score in rows: tot[name] += int(score)
    return out(f"{n} {s}" for n, s in sorted(tot.items(), key=lambda x: (-x[1], x[0])))
add("csv_totals", """Standard input is CSV with a header line "id,name,score" and then rows (no quoting, no commas
inside fields). Print each name's total score as "NAME TOTAL", highest total first, ties by name.""",
    g, f, ["id,name,score\n"])

def g(r): return out(f"{r.choice(['push', 'push', 'pop', 'peek'])} {r.randint(1, 9)}" for _ in range(8))
def f(t):
    st, res = [], []
    for l in lines_of(t):
        op, v = l.split()
        if op == "push": st.append(int(v))
        elif op == "pop": res.append(str(st.pop()) if st else "empty")
        else: res.append(str(st[-1]) if st else "empty")
    return out(res)
add("stack_ops", """Each line of standard input is "push N", "pop X" or "peek X" (X is ignored). Run them on a stack of
integers. For each pop print the value removed and for each peek the top value, or "empty" when the stack is empty.""",
    g, f, ["pop 0\n"])

def g(r): return out(f"{r.choice(['a', 'b', 'c', 'd'])} {r.choice(['a', 'b', 'c', 'd'])}" for _ in range(r.randint(1, 6)))
def f(t):
    adj = collections.defaultdict(set)
    nodes = set()
    for l in lines_of(t):
        a, b = l.split(); adj[a].add(b); adj[b].add(a); nodes |= {a, b}
    seen, comps = set(), []
    for n in sorted(nodes):
        if n in seen: continue
        comp, q = [], [n]
        seen.add(n)
        while q:
            x = q.pop(); comp.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); q.append(y)
        comps.append(sorted(comp))
    return out(" ".join(c) for c in comps)
add("components", """Each line of standard input is an edge "A B" of an undirected graph (names of lowercase letters).
Print the connected components, one per line, each as its node names sorted and separated by spaces, the lines
ordered by their first name.""", g, f, ["a a\n"])

def g(r):
    n = r.randint(2, 7)
    edges = [(r.randint(1, n), r.randint(1, n), r.randint(1, 20)) for _ in range(r.randint(1, 12))]
    return f"{n} {len(edges)}\n" + out(f"{a} {b} {w}" for a, b, w in edges)
def f(t):
    v = list(map(int, t.split()))
    n, m = v[0], v[1]
    adj = collections.defaultdict(list)
    for i in range(m):
        a, b, w = v[2 + 3 * i:5 + 3 * i]
        adj[a].append((b, w)); adj[b].append((a, w))
    dist = {1: 0}
    pq = [(0, 1)]
    while pq:
        d, x = heapq.heappop(pq)
        if d > dist.get(x, 1 << 62): continue
        for y, w in adj[x]:
            if d + w < dist.get(y, 1 << 62): dist[y] = d + w; heapq.heappush(pq, (d + w, y))
    return out(dist.get(i, -1) for i in range(1, n + 1))
add("dijkstra", """Standard input: "N M", then M lines "A B W": an undirected edge between nodes A and B (1..N) with
weight W >= 1. Print N lines: the shortest distance from node 1 to each node 1..N, or -1 if it can't be reached.""",
    g, f, ["1 0\n", "3 1\n1 2 5\n"])

def g(r):
    n = r.randint(1, 6)
    deps = [(r.randint(1, n), r.randint(1, n)) for _ in range(r.randint(0, 6))]
    return f"{n}\n" + out(f"{a} {b}" for a, b in deps if a != b)
def f(t):
    ls = lines_of(t)
    n = int(ls[0])
    indeg = [0] * (n + 1); adj = collections.defaultdict(list)
    for l in ls[1:]:
        a, b = map(int, l.split()); adj[a].append(b); indeg[b] += 1
    pq = [i for i in range(1, n + 1) if indeg[i] == 0]
    heapq.heapify(pq)
    order = []
    while pq:
        x = heapq.heappop(pq); order.append(x)
        for y in adj[x]:
            indeg[y] -= 1
            if indeg[y] == 0: heapq.heappush(pq, y)
    return " ".join(map(str, order)) + "\n" if len(order) == n else "cycle\n"
add("topo_sort", """Standard input: N on the first line (tasks 1..N), then lines "A B" meaning A must come before B.
Print an order of all N tasks, separated by spaces, choosing the smallest available number each time; or "cycle" if no
order exists.""", g, f, ["3\n", "2\n1 2\n2 1\n"])

def g(r):
    h, w = r.randint(1, 6), r.randint(1, 8)
    return out("".join(r.choice("..#") for _ in range(w)) for _ in range(h))
def f(t):
    grid = lines_of(t)
    h, w = len(grid), len(grid[0])
    if grid[0][0] == "#" or grid[h - 1][w - 1] == "#": return "-1\n"
    dist = {(0, 0): 0}
    q = collections.deque([(0, 0)])
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == "." and (ny, nx) not in dist:
                dist[(ny, nx)] = dist[(y, x)] + 1; q.append((ny, nx))
    return f"{dist.get((h - 1, w - 1), -1)}\n"
add("maze_bfs", """Standard input is a grid of equal-length lines of "." (open) and "#" (wall). Print the fewest steps
(up, down, left, right) from the top-left cell to the bottom-right one through open cells, or -1 if there is no path
or either corner is a wall.""", g, f, [".\n", "..\n#.\n", ".#\n#.\n"])

def g(r): return out(r.choice(["set a 1", "set b 2", "get a", "get c", "del a", "count"]) for _ in range(8))
def f(t):
    d, res = {}, []
    for l in lines_of(t):
        p = l.split()
        if p[0] == "set": d[p[1]] = p[2]
        elif p[0] == "get": res.append(d.get(p[1], "NULL"))
        elif p[0] == "del": d.pop(p[1], None)
        else: res.append(str(len(d)))
    return out(res)
add("kv_store", """Each line of standard input is a command: "set K V", "get K", "del K" or "count". Keep a map from
string keys to string values. For get print the value or "NULL"; for count print how many keys there are.""",
    g, f, ["get x\ncount\n"])

def g(r): return out(f"{r.choice(['in', 'out'])} {r.choice(['ann', 'bob'])} {h:02d}:{m:02d}" for h, m in sorted((r.randint(0, 23), r.randint(0, 59)) for _ in range(6)))
def f(t):
    since, tot = {}, collections.defaultdict(int)
    for l in lines_of(t):
        kind, who, hm = l.split()
        mins = int(hm[:2]) * 60 + int(hm[3:])
        if kind == "in":
            if who not in since: since[who] = mins
        elif who in since: tot[who] += mins - since.pop(who);
    return out(f"{w} {m}" for w, m in sorted(tot.items()))
add("timesheet", """Each line of standard input is "in NAME HH:MM" or "out NAME HH:MM", in time order within one day.
An "in" for someone already in, or an "out" for someone not in, is ignored. Print each person who completed at least one
in/out pair and their total minutes, "NAME MINUTES", sorted by name.""", g, f, ["out x 01:00\n"])

def g(r): return out(r.randint(-50, 50) for _ in range(r.randint(1, 10)))
def f(t):
    xs = [int(l) for l in lines_of(t)]
    res, h = [], []
    for i, x in enumerate(xs):
        heapq.heappush(h, -x) if len(h) < 3 else heapq.heappushpop(h, -x) if False else None
    top = sorted(xs, reverse=True)[:3]
    return out(top)
add("top_three", """Each line of standard input holds an integer. Print the three largest values (fewer if there are
fewer lines), largest first, one per line; equal values each count.""", g, f, ["5\n", "1\n1\n1\n1\n"])

def g(r): return " ".join(str(r.randint(1, 30)) for _ in range(r.randint(1, 10))) + "\n" + f"{r.randint(1, 60)}\n"
def f(t):
    ls = lines_of(t)
    xs, target = list(map(int, ls[0].split())), int(ls[1])
    seen = {}
    for i, x in enumerate(xs):
        if target - x in seen: return f"{seen[target - x]} {i}\n"
        seen.setdefault(x, i)
    return "none\n"
add("two_sum", """Standard input: a line of integers, then a line with a target T. Print "I J" (0-based, I < J) for the
first pair whose values add up to T, where "first" means the smallest J, and for that J the smallest I. Print "none" if
no pair does.""", g, f, ["1 2\n5\n", "3 3\n6\n"])

def g(r): return out(f"{r.randint(0, 100)} {r.randint(0, 100)}" for _ in range(r.randint(1, 8)))
def f(t):
    iv = sorted(tuple(sorted(map(int, l.split()))) for l in lines_of(t))
    res = []
    for a, b in iv:
        if res and a <= res[-1][1]: res[-1][1] = max(res[-1][1], b)
        else: res.append([a, b])
    return out(f"{a} {b}" for a, b in res)
add("merge_intervals", """Each line of standard input holds two integers, the ends of a closed interval (in either
order). Merge overlapping or touching intervals (sharing an end counts) and print the results sorted, one "A B" per
line, A <= B.""", g, f, ["5 1\n", "1 2\n2 3\n"])

def g(r): return f"{r.randint(1, 8)}\n"
def f(t):
    n = int(t)
    res = []
    def go(row, cols, d1, d2, cur):
        if row == n: res.append(cur[:]); return
        for c in range(n):
            if c in cols or row - c in d1 or row + c in d2: continue
            cur.append(c); go(row + 1, cols | {c}, d1 | {row - c}, d2 | {row + c}, cur); cur.pop()
    go(0, set(), set(), set(), [])
    first = " ".join(str(c + 1) for c in res[0]) if res else "none"
    return f"{len(res)}\n{first}\n"
add("n_queens", """Standard input holds N (1 <= N <= 10). Print the number of ways to place N queens on an N x N board
so that none attack each other, then the lexicographically first solution as the queens' columns (1-based) for rows 1
to N, separated by spaces, or "none".""", g, f, ["1\n", "2\n", "8\n"])

def g(r): return "".join(r.choice("abc") for _ in range(r.randint(0, 8))) + "\n" + "".join(r.choice("abc") for _ in range(r.randint(0, 8))) + "\n"
def f(t):
    a, b = lines_of(t)[0], lines_of(t)[1]
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return f"{prev[-1]}\n"
add("edit_distance", """Standard input holds two lines. Print the Levenshtein distance between them: the fewest
single-byte insertions, deletions and substitutions that turn the first into the second.""",
    g, f, ["\n\n", "kitten\nsitting\n"])

def g(r): return out(f"{r.randint(1, 10)} {r.randint(1, 30)}" for _ in range(r.randint(1, 8))) + "CAP " + str(r.randint(1, 40)) + "\n"
def f(t):
    ls = lines_of(t)
    cap = int(ls[-1].split()[1])
    items = [tuple(map(int, l.split())) for l in ls[:-1]]
    best = [0] * (cap + 1)
    for w, v in items:
        for c in range(cap, w - 1, -1): best[c] = max(best[c], best[c - w] + v)
    return f"{best[cap]}\n"
add("knapsack", """Each line of standard input but the last is an item "WEIGHT VALUE" (positive integers); the last
line is "CAP C". Print the largest total value of items (each used at most once) whose weights add up to at most C.""",
    g, f, ["CAP 5\n"])

def g(r): return " ".join(str(r.randint(1, 20)) for _ in range(r.randint(1, 12))) + "\n"
def f(t):
    xs = list(map(int, t.split()))
    tails = []
    import bisect
    for x in xs:
        i = bisect.bisect_left(tails, x)
        if i == len(tails): tails.append(x)
        else: tails[i] = x
    return f"{len(tails)}\n"
add("lis", """Standard input holds integers separated by whitespace (at least one). Print the length of the longest
strictly increasing subsequence.""", g, f, ["5\n", "3 3 3\n"])

def g(r):
    w = r.randint(1, 5)
    rows = [" ".join(str(r.randint(0, 9)) for _ in range(w)) for _ in range(r.randint(1, 5))]
    return out(rows)
def f(t):
    m = [l.split() for l in lines_of(t)]
    return out(" ".join(m[r][c] for r in range(len(m))) for c in range(len(m[0])))
add("transpose", """Standard input is a matrix: lines of the same number of values separated by single spaces. Print its
transpose in the same format.""", g, f, ["1\n", "1 2 3\n"])

def g(r):
    cells = [[r.random() < 0.4 for _ in range(6)] for _ in range(5)]
    return f"{r.randint(0, 4)}\n" + out("".join("#" if c else "." for c in row) for row in cells)
def f(t):
    ls = lines_of(t)
    gens, g0 = int(ls[0]), [list(l) for l in ls[1:]]
    h, w = len(g0), len(g0[0])
    for _ in range(gens):
        nxt = [["."] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                n = sum(g0[y + dy][x + dx] == "#" for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and 0 <= y + dy < h and 0 <= x + dx < w)
                if n == 3 or (n == 2 and g0[y][x] == "#"): nxt[y][x] = "#"
        g0 = nxt
    return out("".join(r) for r in g0)
add("game_of_life", """Standard input: a number of generations G, then a grid of equal-length lines of "#" (alive) and
"." (dead). Run Conway's Game of Life for G generations (cells outside the grid are dead and stay dead) and print the
grid.""", g, f, ["0\n#\n", "1\n...\n###\n...\n"])

def g(r): return " ".join(str(r.randint(-100, 100)) for _ in range(r.randint(0, 20))) + "\n"
def f(t):
    xs = list(map(int, t.split()))
    return " ".join(map(str, sorted(xs))) + "\n"
add("sort_ints", """Standard input holds integers separated by whitespace. Print them sorted in increasing order on one
line, separated by single spaces (an empty line when there are none).""", g, f, ["\n", "3 -1 2\n"])

def g(r): return " ".join(str(r.randint(1, 5)) for _ in range(r.randint(1, 15))) + "\n"
def f(t):
    xs = t.split()
    c = collections.Counter(xs)
    top = max(c.values())
    return " ".join(sorted((x for x in c if c[x] == top), key=int)) + "\n"
add("modes", """Standard input holds integers separated by whitespace (at least one). Print the value(s) that occur most
often, in increasing order, separated by single spaces.""", g, f, ["7\n", "1 2 2 1\n"])

def g(r): return out(f"{r.randint(0, 2**31)}" for _ in range(4))
def f(t): return out(bin(int(l)).count("1") for l in lines_of(t))
add("popcount", """Each line of standard input is a non-negative integer below 2^62. Print how many 1 bits it has in
binary.""", g, f, ["0\n", "4611686018427387903\n"])

def g(r): return "".join(r.choice("01") for _ in range(r.randint(1, 40))) + "\n"
def f(t):
    s = t.strip()
    return f"{int(s, 2)}\n"
add("binary_to_decimal", """Standard input is one line of 0s and 1s (at most 62 of them). Print the number it is in
binary, in decimal.""", g, f, ["0\n", "1\n"])

def g(r): return f"{r.randint(1, 3000)}\n"
def f(t): return f"{sum(int(c) for c in str(math.factorial(int(t))))}\n"
add("factorial_digits", """Standard input holds N (1 <= N <= 3000). Print the sum of the decimal digits of N factorial
(N! has thousands of digits: it needs arithmetic on big numbers).""", g, f, ["1\n", "10\n", "3000\n"])

def g(r): return f"{r.randint(1, 500)} {r.randint(1, 500)}\n"
def f(t):
    a, b = t.split()
    return f"{int(a) ** int(b)}\n"
add("big_power", """Standard input holds two integers A and B (1 <= A, B <= 500). Print A to the power B exactly (it can
have more than a thousand digits).""", g, f, ["2 100\n", "500 500\n"])

# ================================================================ formats

def g(r): return out(r.choice(["192.168.1.1", "256.1.1.1", "1.2.3", "01.2.3.4", "0.0.0.0", "a.b.c.d", "1.2.3.4.5", "255.255.255.255"]) for _ in range(5))
def f(t):
    def ok(s):
        p = s.split(".")
        return len(p) == 4 and all(x.isdigit() and x.isascii() and (x == "0" or not x.startswith("0")) and int(x) <= 255 for x in p)
    return out("valid" if ok(l) else "invalid" for l in lines_of(t))
add("ipv4", """Each line of standard input should be an IPv4 address: four decimal numbers 0-255 separated by dots, with
no leading zeros (except "0" itself) and nothing else. Print "valid" or "invalid" for each line.""",
    g, f, ["1.1.1.01\n"])

def g(r): return out(r.choice(["%41%42", "a+b", "100%25", "%zz", "x%2Fy", "plain"]) for _ in range(5))
def f(t):
    def dec(s):
        out_b, i = bytearray(), 0
        b = s.encode()
        while i < len(b):
            if b[i:i + 1] == b"+": out_b += b" "; i += 1
            elif b[i:i + 1] == b"%" and i + 2 < len(b) + 0 and re.fullmatch(rb"[0-9A-Fa-f]{2}", b[i + 1:i + 3] or b""): out_b.append(int(b[i + 1:i + 3], 16)); i += 3
            else: out_b += b[i:i + 1]; i += 1
        return out_b.decode("latin-1")
    return out(dec(l) for l in lines_of(t))
add("url_decode", """Each line of standard input is URL-encoded text. Decode it: "+" becomes a space and "%XX" (two hex
digits, either case) becomes that byte; a "%" not followed by two hex digits stays as it is. Print each decoded line.
(The decoded bytes are ASCII.)""", g, f, ["%\n"])

def g(r): return "".join(r.choice(["Hello, World", "abc", "", "Man"]) for _ in range(1)) + "\n"
def f(t):
    import base64
    return base64.b64encode(t.rstrip("\n").encode()).decode() + "\n"
add("base64_encode", """Standard input is one line. Print its bytes (without the newline) in standard base64 with "="
padding.""", g, f, ["\n", "M\n", "Ma\n"])

def g(r):
    d = {w: r.randint(0, 9) for w in words(r, r.randint(1, 4), "abc")}
    return json.dumps(d) + "\n"
def f(t):
    d = json.loads(t)
    return out(f"{k}={v}" for k, v in sorted(d.items()))
add("json_flat", """Standard input is a JSON object whose values are integers. Print "KEY=VALUE" for each key, sorted by
key (byte order). If a key appears twice, the last value counts.""", g, f, ["{}\n", '{"b": 1, "a": 2, "b": 3}\n'])

def g(r): return out(r.choice(["# Title", "## Sub", "text", "### Deep", "#notheading", ""]) for _ in range(6))
def f(t):
    res = []
    for l in lines_of(t):
        m = re.match(r"(#{1,6}) (.*)", l)
        if m: res.append("  " * (len(m.group(1)) - 1) + m.group(2))
    return out(res)
add("markdown_toc", """Standard input is Markdown. A heading is a line starting with 1 to 6 "#" then a space. Print each
heading's text (after the "# "), indented by two spaces for each level below 1, one per line, in order.""",
    g, f, ["####### seven\n"])

def g(r): return out(f"{r.choice(['GET', 'POST'])} /{r.choice(['a', 'b', 'c'])} {r.choice([200, 404, 500])} {r.randint(1, 900)}" for _ in range(r.randint(1, 10)))
def f(t):
    rows = [l.split() for l in lines_of(t)]
    errs = sum(1 for r in rows if int(r[2]) >= 500)
    by = collections.defaultdict(list)
    for r in rows: by[r[1]].append(int(r[3]))
    res = [f"requests {len(rows)}", f"errors {errs}"]
    res += [f"{p} {len(v)} {max(v)}" for p, v in sorted(by.items())]
    return out(res)
add("access_log", """Each line of standard input is a log entry "METHOD PATH STATUS MILLISECONDS". Print "requests N"
(the number of entries), "errors N" (entries with status 500 or more), then for each path in byte order "PATH COUNT
SLOWEST" (its number of entries and its largest milliseconds).""", g, f, [])

def g(r): return out(r.choice(["key = value", "# comment", "  name=  vu  ", "", "[section]", "bad line", "x=1"]) for _ in range(6))
def f(t):
    sec, res = "", []
    for l in lines_of(t):
        s = l.strip()
        if not s or s.startswith("#"): continue
        if s.startswith("[") and s.endswith("]"): sec = s[1:-1].strip(); continue
        if "=" not in s: res.append(f"error: {s}"); continue
        k, v = s.split("=", 1)
        res.append(f"{sec + '.' if sec else ''}{k.strip()}={v.strip()}")
    return out(res)
add("ini_parse", """Standard input is an INI file. Ignore blank lines and lines starting with "#" (after leading spaces).
"[NAME]" starts a section. "KEY = VALUE" (spaces around both trimmed, split at the first "=") prints "SECTION.KEY=VALUE",
or "KEY=VALUE" before any section. Any other line prints "error: LINE" (trimmed). Print in input order.""",
    g, f, ["a=b=c\n"])

def g(r): return out(f"{r.randint(0, 23):02d}:{r.randint(0, 59):02d} {r.randint(-300, 300)}" for _ in range(4))
def f(t):
    res = []
    for l in lines_of(t):
        hm, d = l.split()
        m = (int(hm[:2]) * 60 + int(hm[3:]) + int(d)) % 1440
        res.append(f"{m // 60:02d}:{m % 60:02d}")
    return out(res)
add("clock_add", """Each line of standard input is "HH:MM D": a 24-hour time and a number of minutes D (may be negative).
Print the time D minutes later on a 24-hour clock, wrapping around midnight, as HH:MM.""", g, f, ["23:59 1\n00:00 -1\n"])

def g(r): return f"{r.randint(1900, 2100)}\n"
def f(t):
    import calendar
    y = int(t)
    return out(sum(1 for m in range(1, 13) if calendar.weekday(y, m, 13) == 4) for _ in [0])
add("friday_13", """Standard input holds a year Y (1900 to 2100). Print how many Friday-the-13ths that year has (in the
Gregorian calendar).""", g, f, ["2026\n"])

def g(r): return out(f"{r.randint(1, 3000)}-{r.randint(1, 12):02d}-{r.randint(1, 28):02d} {r.randint(1, 3000)}-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}" for _ in range(3))
def f(t):
    import datetime
    res = []
    for l in lines_of(t):
        a, b = (datetime.date(*map(int, x.split("-"))) for x in l.split())
        res.append(abs((b - a).days))
    return out(res)
add("days_between", """Each line of standard input holds two dates YYYY-MM-DD (years 1 to 3000, Gregorian calendar).
Print the number of days between them (never negative).""", g, f, ["2026-01-01 2026-01-01\n"])

# ================================================================ simulation

def g(r): return "".join(r.choice("NESWLRF") for _ in range(r.randint(0, 20))) + "\n"
def f(t):
    x = y = 0; d = 0
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for c in t.strip():
        if c == "L": d = (d + 3) % 4
        elif c == "R": d = (d + 1) % 4
        elif c == "F": x += dirs[d][0]; y += dirs[d][1]
        else: dx, dy = dirs["NESW".index(c)]; x += dx; y += dy
    return f"{x} {y} {'NESW'[d]}\n"
add("robot", """Standard input is one line of commands for a robot at (0, 0) facing north: N, E, S, W move one step in
that direction without turning; L and R turn 90 degrees left or right; F moves one step in the facing direction. North
is +Y and east is +X. Print the final "X Y D" where D is the facing letter.""", g, f, ["\n", "RFFLF\n"])

def g(r): return f"{r.randint(1, 30)} {r.randint(1, 6)}\n"
def f(t):
    n, k = map(int, t.split())
    people, i, order = list(range(1, n + 1)), 0, []
    while people:
        i = (i + k - 1) % len(people)
        order.append(people.pop(i))
    return " ".join(map(str, order)) + "\n"
add("josephus", """Standard input holds N and K (1 <= N, K). N people stand in a circle, numbered 1 to N. Starting from
person 1, count K people (person 1 is the first counted) and remove the Kth; continue counting from the next person.
Print the order in which people are removed, separated by spaces.""", g, f, ["1 1\n", "7 3\n"])

def g(r): return out(f"{r.choice(['deposit', 'withdraw', 'balance'])} {r.choice(['a', 'b'])} {r.randint(1, 100)}" for _ in range(8))
def f(t):
    bal, res = collections.defaultdict(int), []
    for l in lines_of(t):
        op, who, amt = l.split(); amt = int(amt)
        if op == "deposit": bal[who] += amt
        elif op == "withdraw":
            if bal[who] >= amt: bal[who] -= amt
            else: res.append(f"insufficient {who}")
        else: res.append(f"{who} {bal[who]}")
    return out(res)
add("bank", """Each line of standard input is "deposit NAME AMOUNT", "withdraw NAME AMOUNT" or "balance NAME X" (X is
ignored). Accounts start at 0. A withdrawal larger than the balance is refused and prints "insufficient NAME"; balance
prints "NAME AMOUNT".""", g, f, ["balance z 0\n"])

def g(r): return out(r.choice(["LRU 2", ""]) for _ in range(0)) + "3\n" + out(f"{r.choice(['get', 'put'])} {r.randint(1, 5)}" for _ in range(10))
def f(t):
    ls = lines_of(t)
    cap = int(ls[0])
    cache, res = collections.OrderedDict(), []
    for l in ls[1:]:
        op, k = l.split()
        if op == "get":
            if k in cache: cache.move_to_end(k); res.append("hit")
            else: res.append("miss")
        else:
            cache[k] = 1; cache.move_to_end(k)
            if len(cache) > cap: res.append(f"evict {cache.popitem(last=False)[0]}")
    return out(res)
add("lru_cache", """Standard input: a capacity C (at least 1), then lines "get K" or "put K". Keep an LRU cache of up to C
keys. get prints "hit" (and marks K most recently used) or "miss". put adds K (or marks it most recently used); if that
makes more than C keys, remove the least recently used and print "evict KEY".""", g, f, ["1\nput a\nput b\nget a\n"])

def g(r): return f"{r.randint(1, 20)}\n"
def f(t):
    n = int(t)
    moves = []
    def hanoi(k, a, b, c):
        if k == 0: return
        hanoi(k - 1, a, c, b); moves.append(f"{a} {c}"); hanoi(k - 1, b, a, c)
    if n <= 10:
        hanoi(n, "A", "B", "C")
        return f"{2 ** n - 1}\n" + out(moves)
    return f"{2 ** n - 1}\n"
add("hanoi", """Standard input holds N (1 <= N <= 20) disks on peg A. Print the fewest moves to move them all to peg C
(using B), and then, only if N <= 10, each move as "FROM TO" in order (the usual recursive solution: move N-1 to B, the
biggest to C, then N-1 onto it).""", g, f, ["1\n", "3\n", "20\n"])

def g(r):
    n = r.randint(1, 5)
    return f"{n}\n" + out(" ".join(str(r.randint(0, 9)) for _ in range(n)) for _ in range(n))
def f(t):
    v = list(map(int, t.split()))
    n = v[0]; m = [v[1 + i * n:1 + (i + 1) * n] for i in range(n)]
    best = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            best[i][j] = m[i][j] + max(best[i - 1][j] if i else 0, best[i][j - 1] if j else 0) if (i or j) else m[0][0]
    return f"{best[n - 1][n - 1]}\n"
add("grid_path_max", """Standard input: N, then an N x N grid of digits separated by spaces. Moving only right or down
from the top-left to the bottom-right cell, print the largest possible sum of the cells visited (both corners included).""",
    g, f, ["1\n7\n"])

def g(r): return "".join(r.choice("abc") for _ in range(r.randint(1, 12))) + "\n"
def f(t):
    s = t.strip()
    best = ""
    for i in range(len(s)):
        for j in range(i, len(s)):
            sub = s[i:j + 1]
            if sub == sub[::-1] and len(sub) > len(best): best = sub
    return best + "\n"
add("longest_palindrome", """Standard input is one line of lowercase letters. Print its longest substring that reads the
same backwards; if several are longest, the leftmost.""", g, f, ["a\n", "abacdfgdcaba\n"])

def g(r): return " ".join(str(r.randint(0, 9)) for _ in range(r.randint(1, 12))) + "\n"
def f(t):
    h = list(map(int, t.split()))
    l, r_, lm, rm, w = 0, len(h) - 1, 0, 0, 0
    while l < r_:
        if h[l] < h[r_]:
            lm = max(lm, h[l]); w += lm - h[l]; l += 1
        else:
            rm = max(rm, h[r_]); w += rm - h[r_]; r_ -= 1
    return f"{w}\n"
add("trapping_rain", """Standard input holds non-negative bar heights separated by spaces. Print how many units of water
the bars trap after rain (water above a bar is bounded by the lower of the tallest bars to its left and right).""",
    g, f, ["0 1 0 2 1 0 1 3 2 1 2 1\n"])

def g(r): return out(r.choice(["(define x 1)", "x", "(+ 1 2)", "(* (+ 1 2) 4)", "(- 10 3 2)", "(define y (+ x 5))", "y"]) for _ in range(6))
def f(t):
    env, res = {}, []
    def toks(s): return s.replace("(", " ( ").replace(")", " ) ").split()
    def parse(ts):
        x = ts.pop(0)
        if x == "(":
            l = []
            while ts[0] != ")": l.append(parse(ts))
            ts.pop(0); return l
        return int(x) if re.fullmatch(r"-?\d+", x) else x
    def ev(e):
        if isinstance(e, int): return e
        if isinstance(e, str): return env.get(e)
        if e[0] == "define":
            v = ev(e[2]); env[e[1]] = v; return None
        args = [ev(a) for a in e[1:]]
        if None in args: return None
        if e[0] == "+": return sum(args)
        if e[0] == "*": return math.prod(args)
        if e[0] == "-": return args[0] - sum(args[1:]) if len(args) > 1 else -args[0]
    for l in lines_of(t):
        v = ev(parse(toks(l)))
        if not (isinstance(parse(toks(l)), list) and parse(toks(l))[0] == "define"): res.append("undefined" if v is None else v)
    return out(res)
add("mini_lisp", """Each line of standard input is one expression in a tiny Lisp: an integer, a name, (define NAME EXPR),
or (OP EXPR ...) with OP one of + (sum), * (product) and - (the first minus the rest; one argument negates). For each
line that isn't a define, print its value, or "undefined" if it uses a name not yet defined. A define prints nothing.""",
    g, f, ["(+ 1 (* 2 3))\nz\n"])

def g(r): return out(f"{r.randint(1, 5)} {r.randint(1, 5)}" for _ in range(r.randint(1, 8)))
def f(t):
    parent = {}
    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    res = []
    for l in lines_of(t):
        a, b = l.split()
        ra, rb = find(a), find(b)
        if ra == rb: res.append("cycle")
        else: parent[ra] = rb; res.append("ok")
    return out(res)
add("union_find", """Each line of standard input adds an undirected edge "A B" to a graph that starts empty. Print "cycle"
if A and B were already connected before this edge (so it closes a cycle), else "ok".""", g, f, ["1 1\n"])

# ================================================================ more

def g(r): return out(" ".join(str(r.randint(0, 9)) for _ in range(9)) for _ in range(9)) if False else sudoku_input(r)
SUDOKU = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
def sudoku_input(r):
    s = list(SUDOKU)
    sol = sudoku_solve(SUDOKU)
    for _ in range(r.randint(0, 20)):
        i = r.randrange(81)
        s[i] = sol[i]
    return "".join(s) + "\n"
def sudoku_solve(p):
    g_ = [int(c) for c in p.strip()]
    def ok(i, v):
        r_, c = divmod(i, 9)
        for k in range(9):
            if g_[r_ * 9 + k] == v or g_[k * 9 + c] == v: return False
        br, bc = r_ // 3 * 3, c // 3 * 3
        return all(g_[(br + a) * 9 + bc + b] != v for a in range(3) for b in range(3))
    def go(i):
        while i < 81 and g_[i]: i += 1
        if i == 81: return True
        for v in range(1, 10):
            if ok(i, v):
                g_[i] = v
                if go(i + 1): return True
        g_[i] = 0
        return False
    go(0)
    return "".join(map(str, g_))
def f(t): return sudoku_solve(t) + "\n"
add("sudoku", """Standard input is a Sudoku as one line of 81 digits, row by row, 0 for an empty cell. It has exactly one
solution. Print the solved grid the same way: one line of 81 digits.""", g, f, [SUDOKU + "\n"])

def g(r): return out(r.choice(["hello world", "aaaa", "abcabc", "zz top"]) for _ in range(3))
def f(t):
    res = []
    for l in lines_of(t):
        c = collections.Counter(l.replace(" ", ""))
        res.append(" ".join(f"{k}:{v}" for k, v in sorted(c.items())))
    return out(res)
add("char_histogram", """For each line of standard input, count each byte other than spaces. Print "B:N" for each byte
B that occurs, in byte order, separated by single spaces (an empty line if there are none).""", g, f, [" \n"])

def g(r): return " ".join(str(r.randint(1, 50)) for _ in range(r.randint(2, 10))) + "\n"
def f(t):
    xs = list(map(int, t.split()))
    best = 0
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)): best = max(best, min(xs[i], xs[j]) * (j - i))
    return f"{best}\n"
add("container_water", """Standard input holds at least two positive heights separated by spaces, of lines standing at
x = 0, 1, 2 .... Print the largest area of water two of the lines can hold with the x axis: min(height) times distance.""",
    g, f, ["1 1\n", "1 8 6 2 5 4 8 3 7\n"])

def g(r): return f"{r.randint(0, 10000)}\n"
def f(t):
    n = int(t)
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
    def say(n):
        if n < 20: return ones[n]
        if n < 100: return tens[n // 10] + ("-" + ones[n % 10] if n % 10 else "")
        if n < 1000: return ones[n // 100] + " hundred" + (" and " + say(n % 100) if n % 100 else "")
        return say(n // 1000) + " thousand" + ((" and " if n % 1000 < 100 else " ") + say(n % 1000) if n % 1000 else "")
    return say(n) + "\n"
add("number_words", """Standard input holds N (0 <= N <= 10000). Print it in British English words: "zero" to
"nineteen", tens as "twenty", "thirty"..., joined to units with a hyphen ("forty-two"); hundreds as "three hundred",
followed by " and " and the rest when there is a rest ("three hundred and five"); thousands as "two thousand", followed
by " and " when the rest is under 100, else a space ("two thousand and seven", "two thousand three hundred").""",
    g, f, ["0\n", "105\n", "1000\n", "2042\n", "10000\n"])

def g(r): return out(f"{r.randint(1, 12)} {r.choice(['C', 'F'])} {r.randint(-40, 120)}" for _ in range(0)) + out(f"{r.randint(-40, 120)} {r.choice(['C', 'F'])}" for _ in range(4))
def f(t):
    res = []
    for l in lines_of(t):
        v, u = l.split()
        v = int(v)
        res.append(f"{v * 9 / 5 + 32:.1f} F" if u == "C" else f"{(v - 32) * 5 / 9:.1f} C")
    return out(res)
add("temperature", """Each line of standard input is "N C" or "N F": an integer temperature in Celsius or Fahrenheit.
Print it converted to the other scale with 1 decimal (as printf("%.1f")) and the other unit, e.g. "212.0 F".""",
    g, f, ["100 C\n-40 F\n"])

def g(r): return "".join(r.choice("abcd") for _ in range(r.randint(1, 14))) + "\n"
def f(t):
    s = t.strip()
    best, start, seen = 0, 0, {}
    for i, c in enumerate(s):
        if c in seen and seen[c] >= start: start = seen[c] + 1
        seen[c] = i
        best = max(best, i - start + 1)
    return f"{best}\n"
add("longest_unique_run", """Standard input is one line. Print the length of its longest substring with no repeated
byte.""", g, f, ["\n", "abcabcbb\n", "bbbb\n"])

def g(r): return " ".join(str(r.randint(-10, 10)) for _ in range(r.randint(3, 10))) + "\n"
def f(t):
    xs = sorted(map(int, t.split()))
    res = set()
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            for k in range(j + 1, len(xs)):
                if xs[i] + xs[j] + xs[k] == 0: res.add((xs[i], xs[j], xs[k]))
    return out(" ".join(map(str, x)) for x in sorted(res)) if res else "none\n"
add("three_sum", """Standard input holds integers separated by spaces. Print every distinct triple of values (from three
different positions) that adds up to 0, each as "A B C" with A <= B <= C, the triples sorted; or "none".""",
    g, f, ["1 2 3\n", "0 0 0 0\n"])

def g(r): return out(f"{r.choice(['add', 'add', 'remove', 'min', 'max'])} {r.randint(1, 20)}" for _ in range(10))
def f(t):
    c, res = collections.Counter(), []
    for l in lines_of(t):
        op, v = l.split(); v = int(v)
        if op == "add": c[v] += 1
        elif op == "remove":
            if c[v]: c[v] -= 1
            if not c[v]: del c[v]
        else:
            ks = [k for k in c if c[k]]
            res.append(str((min if op == "min" else max)(ks)) if ks else "empty")
    return out(res)
add("multiset", """Each line of standard input is "add N", "remove N", "min X" or "max X" (X is ignored). Keep a multiset
of integers: add puts one N in, remove takes one N out if there is one. min and max print the smallest or largest value
in it, or "empty".""", g, f, ["min 0\n"])

def g(r): return " ".join(str(r.randint(1, 100)) for _ in range(r.randint(1, 12))) + f"\n{r.randint(1, 5)}\n"
def f(t):
    ls = lines_of(t)
    xs, k = list(map(int, ls[0].split())), int(ls[1])
    return " ".join(str(max(xs[i:i + k])) for i in range(len(xs) - k + 1)) + "\n"
add("sliding_max", """Standard input: a line of integers, then a window size K (at least 1). Print the maximum of every
window of K consecutive values, left to right, separated by spaces (an empty line if K is larger than the count).""",
    g, f, ["1 3 2\n5\n"])

def g(r): return out(r.choice(["4111111111111111", "4111111111111112", "79927398713", "0", "059", "1234-5678"]) for _ in range(4))
def f(t):
    def luhn(s):
        if not s.isdigit() or not s.isascii() or len(s) < 2: return False
        tot = 0
        for i, c in enumerate(reversed(s)):
            d = int(c)
            if i % 2: d = d * 2 - 9 if d * 2 > 9 else d * 2
            tot += d
        return tot % 10 == 0
    return out("valid" if luhn(l) else "invalid" for l in lines_of(t))
add("luhn", """Each line of standard input should be a number to check with the Luhn algorithm. A line with anything but
the digits 0-9, or fewer than 2 of them, is invalid. Print "valid" or "invalid".""", g, f, ["18\n"])

def g(r): return out(f"{r.randint(1, 5)} {r.choice(['apple', 'pear', 'fig'])} {r.randint(1, 500)}" for _ in range(r.randint(1, 6)))
def f(t):
    total = 0
    items = []
    for l in lines_of(t):
        q, name, cents = l.split(); q, cents = int(q), int(cents)
        items.append(f"{name} x{q} {q * cents // 100}.{q * cents % 100:02d}")
        total += q * cents
    return out(items + [f"total {total // 100}.{total % 100:02d}"])
add("receipt", """Each line of standard input is "QUANTITY NAME PRICE", the price in cents. Print each line as
"NAME xQUANTITY D.CC" (that line's total in dollars and cents), then "total D.CC".""", g, f, [])

def g(r): return f"{r.randint(1, 9)} {r.randint(1, 9)}\n"
def f(t):
    h, w = map(int, t.split())
    grid = [[0] * w for _ in range(h)]
    y = x = 0; dy, dx = 0, 1
    for k in range(1, h * w + 1):
        grid[y][x] = k
        ny, nx = y + dy, x + dx
        if not (0 <= ny < h and 0 <= nx < w and not grid[ny][nx]): dy, dx = dx, -dy; ny, nx = y + dy, x + dx
        y, x = ny, nx
    return out(" ".join(map(str, row)) for row in grid)
add("spiral", """Standard input holds H and W. Print an H by W grid holding 1 to H*W in a clockwise spiral starting at the
top-left corner going right, each row's numbers separated by single spaces.""", g, f, ["1 1\n", "3 3\n"])

def g(r): return "".join(r.choice("01") for _ in range(r.randint(1, 20))) + "\n"
def f(t):
    s = t.strip()
    best = cur = 0
    for c in s:
        cur = cur + 1 if c == "1" else 0
        best = max(best, cur)
    return f"{best}\n"
add("longest_ones", """Standard input is one line of 0s and 1s. Print the length of its longest run of 1s.""", g, f, ["0\n"])

def g(r): return out(f"{r.randint(1, 30)}" for _ in range(r.randint(1, 6)))
def f(t):
    res = []
    for l in lines_of(t):
        n = int(l)
        ways = [1] + [0] * n
        for c in (1, 2, 5, 10, 20, 50):
            for v in range(c, n + 1): ways[v] += ways[v - c]
        res.append(ways[n])
    return out(res)
add("coin_ways", """Each line of standard input is an amount N (1 <= N <= 30). Print how many ways there are to make N
from coins of 1, 2, 5, 10, 20 and 50 (order doesn't matter).""", g, f, ["5\n"])

def g(r):
    ws = words(r, r.randint(1, 8), "abc", 1, 3)
    return " ".join(ws) + "\n" + r.choice(ws) + "\n"
def f(t):
    ls = lines_of(t)
    ws, q = ls[0].split(), ls[1]
    idx = [str(i) for i, w in enumerate(ws) if w == q]
    return (" ".join(idx) if idx else "none") + "\n"
add("find_all", """Standard input: a line of words separated by spaces, then a line with one word Q. Print the 0-based
positions of every word equal to Q, separated by spaces, or "none".""", g, f, ["a b\nc\n"])

def g(r): return out(f"{r.randint(1, 100)}" for _ in range(r.randint(1, 8)))
def f(t):
    xs = [int(l) for l in lines_of(t)]
    res, run = [], 0
    for i, x in enumerate(xs): run += x; res.append(f"{run / (i + 1):.2f}")
    return out(res)
add("running_mean", """Each line of standard input is an integer. After each one, print the mean of all values so far
with 2 decimals (as printf("%.2f")).""", g, f, ["1\n2\n"])

def g(r): return out(r.choice(["(a(b)c)", "abc", "((x))", "a(b(c)d)e", "()"]) for _ in range(4))
def f(t):
    res = []
    for l in lines_of(t):
        d = best = 0
        for c in l:
            if c == "(": d += 1; best = max(best, d)
            elif c == ")": d -= 1
        res.append(best)
    return out(res)
add("paren_depth", """Each line of standard input has balanced parentheses (and other text). Print the deepest nesting
of parentheses in it (0 when there are none).""", g, f, ["\n"])

def g(r): return " ".join(str(r.randint(0, 99)) for _ in range(r.randint(1, 15))) + "\n"
def f(t):
    xs = list(map(int, t.split()))
    return f"{sum(xs[::2])} {sum(xs[1::2])}\n"
add("alternate_sums", """Standard input holds integers separated by spaces. Print the sum of those at even positions
(0, 2, 4, ...) and the sum of those at odd positions, separated by a space.""", g, f, ["5\n"])

def g(r): return f"{r.randint(2, 12)}\n"
def f(t):
    n = int(t)
    rows = []
    for i in range(1, n + 1): rows.append(" ".join(str(i * j).rjust(len(str(n * n))) for j in range(1, n + 1)))
    return out(rows)
add("times_table", """Standard input holds N (2 <= N <= 12). Print the N x N multiplication table: row i has i*1 to i*N,
each right-aligned to the width of N*N and separated by single spaces.""", g, f, ["2\n"])

def g(r): return "".join(r.choice("abcdef") for _ in range(r.randint(1, 10))) + "\n" + "".join(r.choice("abcdef") for _ in range(r.randint(1, 10))) + "\n"
def f(t):
    a, b = lines_of(t)[0], lines_of(t)[1]
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i + 1][j + 1] = dp[i][j] + 1 if a[i] == b[j] else max(dp[i][j + 1], dp[i + 1][j])
    return f"{dp[len(a)][len(b)]}\n"
add("lcs_length", """Standard input holds two lines. Print the length of their longest common subsequence (bytes in the
same order, not necessarily next to each other).""", g, f, ["abc\ndef\n", "abcde\nace\n"])
