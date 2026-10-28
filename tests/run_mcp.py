#!/usr/bin/env python3
"""The MCP filesystem server (mcp/filesystem) against the reference server it stands in for
(@modelcontextprotocol/server-filesystem 2.0.1, Node): the same requests to both, each on its own copy
of a fixture tree, and every answer compared as JSON (paths shown relative to the tree).

  tests/run_mcp.py VU_SERVER REF_SERVER_JS [--seed N] [--rounds N]

Then random cases: edit_file (the diff text must be identical), list_directory_with_sizes on random
names (ICU order), search_files and directory_tree with random globs, head and tail."""
import json, os, random, shutil, subprocess, sys, tempfile

def die(msg):
    print("FAIL: " + msg)
    sys.exit(1)

META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "run_mcp", "version": "1"}}
INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "run_mcp", "version": "1"}}}

class Server:
    def __init__(self, cmd):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=dict(os.environ, TZ="UTC"))
        self.n = 1000
    def ask(self, msg):
        self.p.stdin.write((json.dumps(msg) + "\n").encode())
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line: die("server closed its output: " + self.p.stderr.read().decode()[:2000])
        return json.loads(line)
    def tell(self, msg):
        self.p.stdin.write((json.dumps(msg) + "\n").encode())
        self.p.stdin.flush()
    def call(self, name, args, modern=False):
        self.n += 1
        params = {"name": name, "arguments": args}
        if modern: params["_meta"] = META
        return self.ask({"jsonrpc": "2.0", "id": self.n, "method": "tools/call", "params": params})
    def close(self):
        self.p.stdin.close()
        self.p.wait(10)
        return self.p.returncode

def start(cmd):
    s = Server(cmd)
    r = s.ask(INIT)
    if "result" not in r: die("initialize: %r" % r)
    s.tell({"jsonrpc": "2.0", "method": "notifications/initialized"})
    return s

FILES = {
    "a.txt": "hello\nworld\n", "b.md": "# Title\n\nSome text\r\nwith CRLF\r\nlines\r\n", "empty.txt": "",
    "no_newline.txt": "one\ntwo\nthree", "sub/c.txt": "c\n", "sub/deeper/d.json": '{"k": 1}\n',
    ".hidden/x.txt": "hidden\n", "sub/.dot": "dot\n", "Upper.TXT": "U\n", "image.png": "PNG fake",
    "song.mp3": "ID3 fake", "data.bin": "\x00\x01\x02binary", "spaces in name.txt": "s\n",
    "unicode-\u00e9.txt": "\u00e9\n", "big.txt": "".join("line %d\n" % i for i in range(3000)),
    "indent.py": "def f():\n    if x:\n        return 1\n    return 2\n",
    "tabs.go": "func f() {\n\tif x {\n\t\treturn 1\n\t}\n}\n", "_under": "u\n", "-dash": "d\n", "10.txt": "10\n", "9.txt": "9\n",
}

def fixture(root):
    for rel, text in FILES.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", newline="") as f: f.write(text)
    os.makedirs(os.path.join(root, "emptydir"))
    if sys.platform.startswith("linux"):   # elsewhere the server refuses symlinks on a path (documented)
        os.symlink("sub", os.path.join(root, "link_to_sub"))
        os.symlink("a.txt", os.path.join(root, "link_to_a"))
    os.chmod(os.path.join(root, "a.txt"), 0o640)

def norm(x, roots):
    s = json.dumps(x, sort_keys=True)
    for r in roots: s = s.replace(r, "<ROOT>")
    # a file's access time moves when the other server reads it, a second apart at most: not compared
    import re
    s = re.sub(r"accessed: [^\\]*", "accessed: <TIME>", s)
    return json.loads(s)

checks = 0
def same(rv, rr, roots, what):
    global checks
    checks += 1
    a, b = norm(rv, roots), norm(rr, roots)
    if a != b:
        die("%s differs:\n  vu:  %s\n  ref: %s" % (what, json.dumps(a)[:1500], json.dumps(b)[:1500]))

def main():
    args = sys.argv[1:]
    seed, rounds = 1, 200
    if "--seed" in args: seed = int(args[args.index("--seed") + 1])
    if "--rounds" in args: rounds = int(args[args.index("--rounds") + 1])
    vu, ref = args[0], args[1]
    rnd = random.Random(seed)
    base = tempfile.mkdtemp(prefix="vu-mcp-")
    rv, rr = os.path.join(base, "v"), os.path.join(base, "r")
    fixture(rv)
    fixture(rr)
    sv, sr = start([vu, rv]), start(["node", ref, rr])
    roots = [rv, rr]
    def both(name, a, modern=False, what=None):
        same(sv.call(name, a, modern), sr.call(name, a, modern), roots, what or "%s %s" % (name, json.dumps(a)))
    # protocol
    for m in [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, {"jsonrpc": "2.0", "id": 2, "method": "ping"},
              {"jsonrpc": "2.0", "id": 3, "method": "nope"},
              {"jsonrpc": "2.0", "id": "s", "method": "tools/call", "params": {"name": "bogus", "arguments": {}}}]:
        same(sv.ask(m), sr.ask(m), roots, "protocol %s" % json.dumps(m))
    # a 2026-07-28 client (no initialize: the version is in each request). The reference picks the
    # era from a connection's first message, so these go to connections of their own.
    mv, mr = Server([vu, rv]), Server(["node", ref, rr])
    for m in [{"jsonrpc": "2.0", "id": 5, "method": "server/discover", "params": {"_meta": META}},
              {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {"_meta": META}},
              {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "read_text_file", "arguments": {"path": "a.txt"}, "_meta": META}},
              {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "list_allowed_directories", "arguments": {}, "_meta": META}},
              {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "read_text_file", "arguments": {"path": "nope"}, "_meta": META}},
              {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "bogus", "arguments": {}, "_meta": META}}]:
        same(mv.ask(m), mr.ask(m), roots, "modern %s" % json.dumps(m)[:200])
    mv.close(); mr.close()
    # every tool, the plain cases and the errors
    # without openat2 (macOS) the server refuses every symlink on a path: a documented difference
    links = ["link_to_a", "link_to_sub/c.txt"] if sys.platform.startswith("linux") else []
    for p in ["a.txt", "b.md", "empty.txt", "no_newline.txt", "sub/c.txt"] + links + [
              "unicode-\u00e9.txt", "spaces in name.txt", "nope.txt", "sub", "/etc/hostname", rv + "/a.txt"]:
        a = {"path": p}
        if p.startswith(rv):
            same(sv.call("read_text_file", {"path": p}), sr.call("read_text_file", {"path": p.replace(rv, rr)}), roots, "read abs")
            continue
        both("read_text_file", a)
        both("read_file", a)
        both("get_file_info", a)
    for n in [1, 2, 5, 0, 2.5, -1, 100]:
        for f in ["big.txt", "no_newline.txt", "b.md", "a.txt", "empty.txt"]:
            both("read_text_file", {"path": f, "head": n})
            both("read_text_file", {"path": f, "tail": n})
    both("read_text_file", {"path": "a.txt", "head": 1, "tail": 1})
    for f in ["image.png", "song.mp3", "data.bin", "spaces in name.txt"]:
        both("read_media_file", {"path": f})
    both("read_multiple_files", {"paths": ["a.txt", "nope", "sub/c.txt"]})
    for d in [".", "sub", "emptydir", "a.txt", "nope"] + (["link_to_sub"] if links else []):
        both("list_directory", {"path": d})
        both("list_directory_with_sizes", {"path": d})
        both("list_directory_with_sizes", {"path": d, "sortBy": "size"})
        both("directory_tree", {"path": d})
    both("directory_tree", {"path": ".", "excludePatterns": ["sub", "*.txt"]})
    for pat in ["*.txt", "**/*.txt", "**/*", "sub/**", "*", "**/.*", "{a,b}.*", "[ab].*", "nothing"]:
        both("search_files", {"path": ".", "pattern": pat})
        both("search_files", {"path": ".", "pattern": pat, "excludePatterns": ["sub"]})
    both("list_allowed_directories", {})
    # validation
    for name, a in [("read_text_file", {}), ("read_text_file", {"path": 5}), ("read_multiple_files", {"paths": []}),
                    ("edit_file", {"path": "a.txt", "edits": [{"oldText": 1}]}), ("move_file", {}),
                    ("list_directory_with_sizes", {"path": ".", "sortBy": "date"}), ("directory_tree", {"path": ".", "excludePatterns": "x"})]:
        both(name, a)
    # writes, on each server's own copy
    both("write_file", {"path": "new.txt", "content": "made\n"})
    both("read_text_file", {"path": "new.txt"})
    both("write_file", {"path": "a.txt", "content": "replaced\n"})
    both("create_directory", {"path": "x/y/z"})
    both("create_directory", {"path": "x/y"})
    both("move_file", {"source": "new.txt", "destination": "x/moved.txt"})
    both("move_file", {"source": "b.md", "destination": "x/moved.txt"})
    both("edit_file", {"path": "indent.py", "edits": [{"oldText": "if x:\n    return 1", "newText": "if y:\n    return 3"}]})
    both("edit_file", {"path": "tabs.go", "edits": [{"oldText": "if x {", "newText": "if y {"}], "dryRun": True})
    both("edit_file", {"path": "b.md", "edits": [{"oldText": "with CRLF", "newText": "still CRLF"}]})
    both("edit_file", {"path": "a.txt", "edits": [{"oldText": "missing", "newText": "x"}]})
    both("read_text_file", {"path": "b.md"})
    # random edit_file: the diffs must be the same text
    words = ["alpha", "beta", "gamma", "", "  indented", "\tTab", "x = 1", "}"]
    for i in range(rounds):
        lines = [rnd.choice(words) for _ in range(rnd.randint(0, 30))]
        text = "\n".join(lines) + rnd.choice(["", "\n"])
        name = "rand%d.txt" % (i % 5)
        for root in (rv, rr):
            with open(os.path.join(root, name), "w") as f: f.write(text)
        edits = []
        for _ in range(rnd.randint(1, 3)):
            if lines and rnd.random() < 0.8:
                a = rnd.randrange(len(lines)); b = min(len(lines), a + rnd.randint(1, 4))
                old = "\n".join(lines[a:b])
            else:
                old = rnd.choice(words)
            new = "\n".join(rnd.choice(words) for _ in range(rnd.randint(0, 4)))
            edits.append({"oldText": old, "newText": new})
        both("edit_file", {"path": name, "edits": edits, "dryRun": rnd.random() < 0.5}, what="random edit %d" % i)
        both("read_text_file", {"path": name}, what="after random edit %d" % i)
    # random names: the ICU order of list_directory_with_sizes, and globs
    alphabet = "aAbBzZ09_-. ~"
    for i in range(max(1, rounds // 20)):
        d = "names%d" % i
        names = set()
        for _ in range(rnd.randint(1, 15)):
            names.add("".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 6))).strip(". ") or "n")
        sizes = {n: rnd.randint(0, 3000) for n in sorted(names)}
        for root in (rv, rr):
            os.makedirs(os.path.join(root, d))
            for n in names:
                with open(os.path.join(root, d, n), "w") as f: f.write("x" * sizes[n])
        both("list_directory_with_sizes", {"path": d})
        both("list_directory_with_sizes", {"path": d, "sortBy": "size"})
        for pat in ["*", "a*", "*[0-9]*", "{a,b}*", "?", "**/*Z*"]:
            both("search_files", {"path": d, "pattern": pat})
            both("directory_tree", {"path": d, "excludePatterns": [pat]})
    sv.close(); sr.close()
    shutil.rmtree(base)
    print("run_mcp: %d answers the same as the reference server (seed %d)" % (checks, seed))

main()
