"""Tasks for the experiment: each reads standard input and writes standard output. ref() is the
reference (Python); gen() makes test inputs (edge cases first)."""
import random, heapq
from collections import Counter, OrderedDict, defaultdict, deque

TASKS = []

def task(name, prompt):
    def deco(cls):
        cls.name, cls.prompt = name, prompt
        TASKS.append(cls)
        return cls
    return deco

@task("wordfreq", """Read all of standard input. Split it into words: maximal runs of ASCII letters (a-z, A-Z); everything else separates words. Lowercase them. Print the 10 most frequent words, one per line as `WORD COUNT`, most frequent first; ties broken alphabetically. Fewer than 10 distinct words: print them all. No words: print nothing.""")
class WordFreq:
    @staticmethod
    def ref(s):
        import re
        c = Counter(w.lower() for w in re.findall(r'[A-Za-z]+', s))
        return ''.join(f'{w} {n}\n' for w, n in sorted(c.items(), key=lambda x: (-x[1], x[0]))[:10])
    @staticmethod
    def gen(r):
        words = ['the', 'a', 'Vu', 'rust', 'Go', 'zeta', 'alpha', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'it']
        out = ['', '!!! 123 ---\n', 'Hello hello HELLO world\n']
        for _ in range(4):
            out.append(''.join(r.choice(words) + r.choice([' ', ', ', '\n', '--', '3', "'s "]) for _ in range(r.randint(5, 400))))
        return out

@task("brackets", """Each line of standard input is a string of characters. For each line print `ok` if its brackets ()[]{} are balanced and properly nested (other characters are ignored), otherwise print `error at N`, where N is the 1-based position (in bytes) of the first character that makes it unbalanced: a closing bracket that doesn't match the innermost open one or has nothing to close; or, if the line ends with brackets still open, N is the line's length plus 1. Lines are separated by `\\n`; a final newline doesn't start another line.""")
class Brackets:
    @staticmethod
    def ref(s):
        out = []
        for line in s.split('\n')[:-1] if s.endswith('\n') else s.split('\n') if s else []:
            st, res = [], None
            for i, ch in enumerate(line.encode()):
                ch = chr(ch)
                if ch in '([{': st.append(ch)
                elif ch in ')]}':
                    if not st or '([{'[')]}'.index(ch)] != st[-1]:
                        res = f'error at {i + 1}'; break
                    st.pop()
            if res is None: res = 'ok' if not st else f'error at {len(line.encode()) + 1}'
            out.append(res + '\n')
        return ''.join(out)
    @staticmethod
    def gen(r):
        out = ['', '\n', '()\n(]\n)(\n((\n{[()()]}x\n']
        for _ in range(4):
            out.append(''.join(''.join(r.choice('()[]{}ab ') for _ in range(r.randint(0, 30))) + '\n' for _ in range(50)))
        return out

@task("dijkstra", """Standard input: a first line `N M S` (nodes 0..N-1, M edges, source S), then M lines `U V W`: a directed edge from U to V with weight W (0 <= W <= 1000). Print N lines: the shortest distance from S to node i, or `unreachable`. 1 <= N <= 2000, 0 <= M <= 20000.""")
class Dijkstra:
    @staticmethod
    def ref(s):
        it = iter(s.split())
        n, m, src = int(next(it)), int(next(it)), int(next(it))
        adj = [[] for _ in range(n)]
        for _ in range(m):
            u, v, w = int(next(it)), int(next(it)), int(next(it)); adj[u].append((v, w))
        d = [None] * n; d[src] = 0; pq = [(0, src)]
        while pq:
            du, u = heapq.heappop(pq)
            if du > d[u]: continue
            for v, w in adj[u]:
                if d[v] is None or du + w < d[v]: d[v] = du + w; heapq.heappush(pq, (d[v], v))
        return ''.join(('unreachable' if x is None else str(x)) + '\n' for x in d)
    @staticmethod
    def gen(r):
        out = ['1 0 0\n', '3 2 0\n0 1 5\n1 0 1\n']
        for n, m in [(10, 30), (200, 1000), (2000, 20000)]:
            es = [f'{r.randrange(n)} {r.randrange(n)} {r.randint(0, 1000)}' for _ in range(m)]
            out.append(f'{n} {m} {r.randrange(n)}\n' + '\n'.join(es) + '\n')
        return out

@task("lru", """Simulate an LRU cache. The first line of standard input is the capacity C (1 <= C <= 1000). Each following line is `get K` or `put K V` (K and V are integers). `get K` prints the value for K, or -1 if absent, and marks K as most recently used. `put K V` sets K to V and marks it most recently used; if that makes the cache hold more than C keys, the least recently used key is evicted (print nothing). Up to 100000 operations.""")
class Lru:
    @staticmethod
    def ref(s):
        lines = s.split('\n'); c = int(lines[0]); od = OrderedDict(); out = []
        for l in lines[1:]:
            p = l.split()
            if not p: continue
            if p[0] == 'get':
                k = int(p[1])
                if k in od: od.move_to_end(k); out.append(f'{od[k]}\n')
                else: out.append('-1\n')
            else:
                k, v = int(p[1]), int(p[2]); od[k] = v; od.move_to_end(k)
                if len(od) > c: od.popitem(last=False)
        return ''.join(out)
    @staticmethod
    def gen(r):
        out = ['1\nget 1\nput 1 5\nget 1\nput 2 6\nget 1\nget 2\n']
        for c, n, keys in [(2, 50, 4), (10, 2000, 30), (1000, 100000, 3000)]:
            ops = [f'get {r.randrange(keys)}' if r.random() < 0.5 else f'put {r.randrange(keys)} {r.randint(-10**9, 10**9)}' for _ in range(n)]
            out.append(f'{c}\n' + '\n'.join(ops) + '\n')
        return out

@task("calc", """Each line of standard input is an arithmetic expression over 64-bit signed integers with + - * / (integer division truncating toward zero), unary minus, and parentheses; spaces may appear anywhere. * and / bind tighter than + and -; operators of equal precedence group left to right. For each non-empty line print its value, or `error` if the expression is malformed (anything but digits, spaces, + - * / and parentheses is malformed too) or divides by zero; empty lines are skipped. Every intermediate value fits in 64 bits.""")
class Calc:
    @staticmethod
    def ref(s):
        out = []
        for line in s.split('\n'):
            if line == '' : continue
            out.append(Calc.ev(line) + '\n')
        return ''.join(out)
    @staticmethod
    def ev(line):
        toks, i = [], 0
        while i < len(line):
            c = line[i]
            if c == ' ': i += 1
            elif c.isdigit():
                j = i
                while j < len(line) and line[j].isdigit(): j += 1
                toks.append(int(line[i:j])); i = j
            elif c in '+-*/()': toks.append(c); i += 1
            else: return 'error'
        pos = [0]
        class E(Exception): pass
        def peek(): return toks[pos[0]] if pos[0] < len(toks) else None
        def take(): t = peek(); pos[0] += 1; return t
        def expr():
            v = term()
            while peek() in ('+', '-'):
                op = take(); w = term(); v = v + w if op == '+' else v - w
            return v
        def term():
            v = unary()
            while peek() in ('*', '/'):
                op = take(); w = unary()
                if op == '*': v = v * w
                else:
                    if w == 0: raise E()
                    q = abs(v) // abs(w); v = q if (v >= 0) == (w >= 0) else -q
            return v
        def unary():
            if peek() == '-': take(); return -unary()
            return prim()
        def prim():
            t = take()
            if isinstance(t, int): return t
            if t == '(':
                v = expr()
                if take() != ')': raise E()
                return v
            raise E()
        try:
            v = expr()
            if pos[0] != len(toks): return 'error'
            return str(v)
        except E: return 'error'
    @staticmethod
    def gen(r):
        out = ['1+2*3\n(1+2)*3\n-7/2\n7/-2\n- -3\n2*(3\n1/0\n\n  42  \n1 2\n()\n--1\n']
        def e(d):
            if d == 0 or r.random() < 0.3: return str(r.randint(0, 9))
            k = r.random()
            if k < 0.15: return '-' + e(d - 1)
            if k < 0.3: return '(' + e(d - 1) + ')'
            return e(d - 1) + r.choice([' + ', '-', '*', ' / ']) + e(d - 1)
        for _ in range(3): out.append(''.join(e(4) + '\n' for _ in range(100)))
        return out

@task("life", """Conway's Game of Life on a torus. Standard input: a first line `H W T`, then H lines of W characters each, `#` (alive) or `.` (dead). Run T generations (0 <= T <= 1000) where the grid wraps around at the edges (row -1 is row H-1, etc.), then print the grid in the same format. A live cell with 2 or 3 live neighbours stays alive; a dead cell with exactly 3 becomes alive; every other cell is dead. 1 <= H, W <= 100.""")
class Life:
    @staticmethod
    def ref(s):
        lines = s.split('\n'); h, w, t = map(int, lines[0].split())
        g = [list(lines[1 + i]) for i in range(h)]
        for _ in range(t):
            ng = [['.'] * w for _ in range(h)]
            for y in range(h):
                for x in range(w):
                    n = sum(g[(y + dy) % h][(x + dx) % w] == '#' for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
                    ng[y][x] = '#' if (n == 3 or (n == 2 and g[y][x] == '#')) else '.'
            g = ng
        return ''.join(''.join(row) + '\n' for row in g)
    @staticmethod
    def gen(r):
        out = ['1 1 3\n#\n', '3 3 1\n.#.\n.#.\n.#.\n']
        for h, w, t in [(5, 7, 10), (40, 30, 50), (100, 100, 20)]:
            out.append(f'{h} {w} {t}\n' + ''.join(''.join(r.choice('#..') for _ in range(w)) + '\n' for _ in range(h)))
        return out

@task("bst", """Standard input is a sequence of commands, one per line: `insert X` adds integer X to a binary search tree (ignored if X is already there), `delete X` removes X if present, `inorder` prints the keys in increasing order separated by single spaces (an empty line if the tree is empty), `height` prints the tree's height (0 for an empty tree, 1 for a single node). Implement it as an actual (unbalanced) binary search tree of nodes; deleting a node with two children replaces its key with the smallest key of its right subtree and deletes that key from the right subtree. Up to 50000 commands; keys inserted in random order.""")
class Bst:
    @staticmethod
    def ref(s):
        root = None
        def ins(n, x):
            if n is None: return [x, None, None]
            if x < n[0]: n[1] = ins(n[1], x)
            elif x > n[0]: n[2] = ins(n[2], x)
            return n
        def dele(n, x):
            if n is None: return None
            if x < n[0]: n[1] = dele(n[1], x)
            elif x > n[0]: n[2] = dele(n[2], x)
            else:
                if n[1] is None: return n[2]
                if n[2] is None: return n[1]
                m = n[2]
                while m[1] is not None: m = m[1]
                n[0] = m[0]; n[2] = dele(n[2], m[0])
            return n
        def ino(n, acc):
            st = []; cur = n
            while st or cur:
                while cur: st.append(cur); cur = cur[1]
                cur = st.pop(); acc.append(str(cur[0])); cur = cur[2]
        def hei(n):
            if n is None: return 0
            best, st = 0, [(n, 1)]
            while st:
                x, d = st.pop(); best = max(best, d)
                if x[1]: st.append((x[1], d + 1))
                if x[2]: st.append((x[2], d + 1))
            return best
        out = []
        for l in s.split('\n'):
            p = l.split()
            if not p: continue
            if p[0] == 'insert': root = ins(root, int(p[1]))
            elif p[0] == 'delete': root = dele(root, int(p[1]))
            elif p[0] == 'inorder': a = []; ino(root, a); out.append(' '.join(a) + '\n')
            else: out.append(f'{hei(root)}\n')
        return ''.join(out)
    @staticmethod
    def gen(r):
        out = ['inorder\nheight\ninsert 5\ninsert 3\ninsert 8\ninsert 3\ninorder\nheight\ndelete 5\ninorder\ndelete 9\ndelete 3\ndelete 8\ninorder\nheight\n']
        for n, keys in [(100, 30), (5000, 2000), (50000, 100000)]:
            cmds = []
            for _ in range(n):
                k = r.random()
                if k < 0.6: cmds.append(f'insert {r.randint(-keys, keys)}')
                elif k < 0.9: cmds.append(f'delete {r.randint(-keys, keys)}')
                elif k < 0.95: cmds.append('height')
                else: cmds.append('inorder' if n < 10000 or r.random() < 0.02 else 'height')
            out.append('\n'.join(cmds) + '\n')
        return out

@task("topo", """Standard input: a first line `N M`, then M lines `A B` meaning task A must come before task B (tasks are 0..N-1). Print a single line with an ordering of all N tasks that respects every constraint, separated by spaces, choosing the smallest-numbered available task at each step; if the constraints have a cycle, print `cycle`. 1 <= N <= 100000, 0 <= M <= 200000.""")
class Topo:
    @staticmethod
    def ref(s):
        it = iter(s.split()); n, m = int(next(it)), int(next(it))
        adj = [[] for _ in range(n)]; indeg = [0] * n
        for _ in range(m):
            a, b = int(next(it)), int(next(it)); adj[a].append(b); indeg[b] += 1
        pq = [i for i in range(n) if indeg[i] == 0]; heapq.heapify(pq); out = []
        while pq:
            u = heapq.heappop(pq); out.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0: heapq.heappush(pq, v)
        return ('cycle' if len(out) < n else ' '.join(map(str, out))) + '\n'
    @staticmethod
    def gen(r):
        out = ['1 0\n', '2 2\n0 1\n1 0\n', '3 1\n2 0\n']
        for n, m in [(50, 100), (100000, 200000)]:
            perm = list(range(n)); r.shuffle(perm)
            es = []
            for _ in range(m):
                i, j = sorted(r.sample(range(n), 2)); es.append(f'{perm[i]} {perm[j]}')
            out.append(f'{n} {m}\n' + '\n'.join(es) + '\n')
        n = 1000; es = [f'{i} {i + 1}' for i in range(n - 1)] + ['999 500']
        out.append(f'{n} {len(es)}\n' + '\n'.join(es) + '\n')
        return out

@task("roman", """Each non-empty line of standard input is a decimal integer, a Roman numeral, or something else (empty lines are skipped). For a number print its Roman numeral (standard form: I V X L C D M with subtractive pairs IV IX XL XC CD CM); for a Roman numeral in standard form print its value; for anything else (including non-standard numerals such as IIII or VX, lowercase letters, numbers with leading zeros or a sign, and numbers outside 1..3999) print `invalid`. Print one line per input line.""")
class Roman:
    VALS = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    @staticmethod
    def to_r(n):
        o = ''
        for v, sy in Roman.VALS:
            while n >= v: o += sy; n -= v
        return o
    @staticmethod
    def ref(s):
        table = {Roman.to_r(i): i for i in range(1, 4000)}
        out = []
        for l in s.split('\n'):
            if l == '': continue
            if l.isdigit() and l.isascii():
                n = int(l); out.append(Roman.to_r(n) if 1 <= n <= 3999 and not (len(l) > 1 and l[0] == '0') else 'invalid')
            else: out.append(str(table[l]) if l in table else 'invalid')
        return ''.join(x + '\n' for x in out)
    @staticmethod
    def gen(r):
        out = ['1\n3999\n4000\n0\nIV\nIIII\nVX\nMMMCMXCIX\nmcm\n-5\nIM\n007\n']
        for _ in range(3):
            ls = []
            for _ in range(300):
                k = r.random()
                if k < 0.4: ls.append(str(r.randint(1, 3999)))
                elif k < 0.8: ls.append(Roman.to_r(r.randint(1, 3999)))
                else: ls.append(''.join(r.choice('IVXLCDM') for _ in range(r.randint(1, 6))))
            out.append('\n'.join(ls) + '\n')
        return out

@task("csvsum", """Standard input is CSV with a header line. Columns are separated by commas; a field may be quoted with double quotes, in which case it can contain commas, and a doubled quote `""` inside it stands for one quote. The header names the columns; one of them is named `region` and another `amount` (in any position). `amount` is a decimal number with at most 2 digits after the point (it may be negative). Print, for each distinct region in order of first appearance, a line `REGION TOTAL` where TOTAL is the sum of its amounts printed with exactly 2 digits after the point (e.g. `-3.50`). Lines end with `\\n`; there are no line breaks inside fields.""")
class CsvSum:
    @staticmethod
    def ref(s):
        import csv, io
        from decimal import Decimal
        rows = list(csv.reader(io.StringIO(s)))
        h = rows[0]; ri, ai = h.index('region'), h.index('amount')
        tot = {}
        for row in rows[1:]:
            if not row: continue
            tot.setdefault(row[ri], Decimal(0)); tot[row[ri]] += Decimal(row[ai])
        return ''.join(f'{k} {v:.2f}\n' for k, v in tot.items())
    @staticmethod
    def gen(r):
        out = ['region,amount\n', 'id,amount,region\n1,5,west\n2,-3.5,"west"\n3,0.25,"north, far"\n4,1.00,"say ""hi"""\n']
        regs = ['east', 'west', '"north, far"', '"a ""b"""', 'x']
        for n in [10, 1000, 20000]:
            ls = ['note,region,amount']
            for i in range(n):
                amt = f'{r.randint(-100000, 100000) / 100:.2f}'.rstrip('0').rstrip('.') if r.random() < 0.5 else f'{r.randint(-100000, 100000) / 100:.2f}'
                ls.append(f'"n{i}, ok",{r.choice(regs)},{amt}')
            out.append('\n'.join(ls) + '\n')
        return out
