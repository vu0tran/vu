#!/usr/bin/env python3
"""The MCP git server (mcp/git) against the reference (mcp-server-git, Python, through GitPython), each
on its own copy of the same repository: random sessions of file edits (made the same in both copies by
the test) and tool calls (status, the diffs, add with good and bad paths, commit, log with counts and
dates, branches made from names, tags and shas, checkout, show of commits, trees, blobs and revision
expressions, reset), arguments of the wrong type or missing, and, with --repository, paths that try
to leave it. The commit dates are fixed, so both write the same commits. Every answer is compared as
JSON, each copy's path written as REPO.
  tests/run_mcp_git.py VU_SERVER PYTHON_WITH_MCP_SERVER_GIT [--seed N] [--rounds N]"""
import json, os, random, shutil, subprocess, sys, tempfile

INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}

class S:
    def __init__(self, cmd, env, repo):
        # (run in the repository, so a repo_path of "." is the same text for both)
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, cwd=repo)
        self.repo = repo
        self.n = 0
        self.init = self.ask(INIT)
        self.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    def ask(self, m):
        self.p.stdin.write((json.dumps(m) + "\n").encode()); self.p.stdin.flush()
        l = self.p.stdout.readline()
        if not l: sys.exit("FAIL: a server closed its output after " + json.dumps(m)[:500])
        return json.loads(l)
    def call(self, name, args):
        self.n += 1
        a = json.loads(json.dumps(args).replace("@REPO@", self.repo))
        x = self.ask({"jsonrpc": "2.0", "id": self.n, "method": "tools/call", "params": {"name": name, "arguments": a}})
        x["id"] = 0
        return json.loads(json.dumps(x).replace(self.repo, "@REPO@").replace(os.path.dirname(self.repo), "@PARENT@"))

def sh(cwd, *a, env=None):
    subprocess.run(list(a), cwd=cwd, check=True, capture_output=True, env=env)

NAMES = ["a.txt", "b.md", "d/c.txt", "d/e/f.txt", "space name.txt", "\u00e9t\u00e9.txt", "-dash.txt", "x.bin"]
TEXTS = ["hello\n", "hello\nworld\n", "", "no newline", "caf\xe9\n", "line\n" * 30, "\U0001F600\n", "tab\there\n"]

def make_repo(path, env):
    os.makedirs(path)
    sh(path, "git", "init", "-q", "-b", "main", env=env)
    sh(path, "git", "config", "user.name", "Ada Lovelace", env=env)
    sh(path, "git", "config", "user.email", "ada@example.org", env=env)
    with open(os.path.join(path, "a.txt"), "w") as f: f.write("first\n")
    sh(path, "git", "add", ".", env=env)
    sh(path, "git", "commit", "-q", "-m", "first commit\n\nwith a body", env=env)
    sh(path, "git", "tag", "v1", env=env)
    sh(path, "git", "tag", "-a", "v1a", "-m", "annotated", env=env)
    with open(os.path.join(path, "b.md"), "w") as f: f.write("# b\n")
    os.makedirs(os.path.join(path, "d"))
    with open(os.path.join(path, "d", "c.txt"), "w") as f: f.write("c\n")
    sh(path, "git", "add", ".", env=env)
    sh(path, "git", "commit", "-q", "-m", "second", env=env)
    sh(path, "git", "branch", "side", "HEAD~1", env=env)

def main():
    a = sys.argv[1:]
    vu, py = a[0], a[1]
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    rounds = int(a[a.index("--rounds") + 1]) if "--rounds" in a else 300
    r = random.Random(seed)
    d = tempfile.mkdtemp()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_AUTHOR_DATE": "1705321825 +0200", "GIT_COMMITTER_DATE": "1705321825 +0200", "HOME": d,
                "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C", "TZ": "UTC"})
    base = os.path.join(d, "base")
    make_repo(base, env)
    rv, rr = os.path.join(d, "v", "repo"), os.path.join(d, "r", "repo")
    for p in (rv, rr): shutil.copytree(base, p, symlinks=True)
    confined = "--confined" in a
    extra_v = ["--repository", rv] if confined else []
    extra_r = ["--repository", rr] if confined else []
    sv = S([vu] + extra_v, env, rv)
    sr = S([py, "-m", "mcp_server_git"] + extra_r, env, rr)
    if sv.init != sr.init: sys.exit("FAIL initialize:\n  vu:  %s\n  ref: %s" % (sv.init, sr.init))
    n = 0
    kinds = {}
    def same(name, args):
        nonlocal n
        n += 1
        x, y = sv.call(name, args), sr.call(name, args)
        t = y.get("result", {}).get("content", [{}])[0].get("text", "")
        kind = name + (" error" if y.get("result", {}).get("isError") else " ok")
        if "validation error" in t: kind = "validation error"
        kinds[kind] = kinds.get(kind, 0) + 1
        if x != y: sys.exit("FAIL %s %s:\n  vu:  %s\n  ref: %s" % (name, json.dumps(args)[:600], json.dumps(x)[:2500], json.dumps(y)[:2500]))
    R = "."
    revs = ["HEAD", "HEAD~1", "HEAD~2", "HEAD^", "HEAD^0", "HEAD^2", "HEAD~9", "main", "side", "v1", "v1a", "v1a^{commit}", "v1a^{}", "v1a^{tag}", "v1^{tree}",
            "HEAD:a.txt", "HEAD:d", "HEAD:d/c.txt", "HEAD:nope", "HEAD:d/nope", "HEAD:a.txt/x", ":a.txt", ":nope", "HEAD^{tree}", "HEAD^{blob}", "HEAD^{bogus}",
            "nope", "", "~1", "@", "@~1", "HEAD@{0}", "main@{0}", "HEAD@{1}", "refs/heads/main", "heads/side", "HEAD..side", "-p", "HEAD:", "HEAD^{/first}",
            ":/second", ":/nomatch", "HEAD^{/nomatch}"]
    for _ in range(rounds):
        k = r.random()
        if k < 0.04:
            # a rename, a mode change, a binary file or a deletion, the same in both copies
            op = r.choice(["mv", "chmod", "bin", "rm"])
            for root in (rv, rr):
                if op == "mv" and os.path.exists(os.path.join(root, "b.md")): subprocess.run(["git", "mv", "-f", "b.md", "renamed.md"], cwd=root, capture_output=True, env=env)
                elif op == "mv" and os.path.exists(os.path.join(root, "renamed.md")): subprocess.run(["git", "mv", "-f", "renamed.md", "b.md"], cwd=root, capture_output=True, env=env)
                elif op == "chmod" and os.path.exists(os.path.join(root, "a.txt")): os.chmod(os.path.join(root, "a.txt"), 0o755 if r.random() < 2 else 0o644)
                elif op == "bin":
                    with open(os.path.join(root, "x.bin"), "wb") as f: f.write(bytes(range(256)))
                elif op == "rm" and os.path.exists(os.path.join(root, "d", "c.txt")): subprocess.run(["git", "rm", "-q", "d/c.txt"], cwd=root, capture_output=True, env=env)
        elif k < 0.2:
            # edit files the same way in both copies
            name = r.choice(NAMES)
            text = r.choice(TEXTS)
            for root in (rv, rr):
                p = os.path.join(root, name)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as f: f.write(text.encode("latin-1") if "\xe9" in text and r.random() < 2 else text.encode())
        elif k < 0.35:
            same(r.choice(["git_status", "git_diff_unstaged", "git_diff_staged"]), {"repo_path": R} if r.random() < 0.8 else {"repo_path": R, "context_lines": r.choice([0, 1, 10, "2", 1.0, 1.5, None, -1, True])})
        elif k < 0.45:
            files = r.choice([["."], ["a.txt"], ["d"], ["nope.txt"], ["../x"], ["/etc/passwd"], [], ["a.txt", "b.md"], ["-dash.txt"], ["space name.txt"], [5], "a.txt", ["\u00e9t\u00e9.txt"], ["d/../a.txt"]])
            same("git_add", {"repo_path": R, "files": files})
        elif k < 0.52:
            same("git_commit", {"repo_path": R, "message": r.choice(["msg", "two\nlines", "", "\u00e9 unicode", "trailing\n"])})
        elif k < 0.6:
            args = {"repo_path": R}
            if r.random() < 0.5: args["max_count"] = r.choice([1, 2, 0, 100, -1, "3", "x"])
            if r.random() < 0.2: args["start_timestamp"] = r.choice(["2024-01-01", "2030-01-01", "-x", "yesterday"])
            if r.random() < 0.2: args["end_timestamp"] = r.choice(["2020-01-01", "2030-01-01", None])
            same("git_log", args)
        elif k < 0.68:
            args = {"repo_path": R, "branch_name": r.choice(["feat", "feat", "x%d" % r.randrange(100), "main", "side", "-bad", "a b", "x..y", "x.lock", "@", "ok/name", "x/", "\u00e9"])}
            if r.random() < 0.5: args["base_branch"] = r.choice(["main", "side", "v1", "v1a", "HEAD~1", "nope", "-x", None, "HEAD^{tree}", "refs/heads/side"])
            same("git_create_branch", args)
        elif k < 0.75:
            same("git_checkout", {"repo_path": R, "branch_name": r.choice(["main", "side", "feat", "v1", "HEAD~1", "nope", "-b", "HEAD"])})
        elif k < 0.88:
            same("git_show", {"repo_path": R, "revision": r.choice(revs)})
        elif k < 0.93:
            same(r.choice(["git_diff", "git_branch"]), r.choice([{"repo_path": R, "target": r.choice(revs[:12])}, {"repo_path": R, "branch_type": r.choice(["local", "remote", "all", "bogus"])},
                                                             {"repo_path": R, "branch_type": "local", "contains": r.choice(["HEAD", "nope", "-x", None])}]))
        elif k < 0.96:
            same("git_reset", {"repo_path": R})
        else:
            same(r.choice(["git_status", "git_log", "git_show", "git_add"]), r.choice([{}, {"repo_path": 5}, {"repo_path": "d"}, {"repo_path": "/nonexistent"}, {"repo_path": "/"},
                                                                                     {"repo_path": ".."}, {"repo_path": R, "revision": 5}, {"repo_path": ".git"}, {"repo_path": "@REPO@"}, {"repo_path": "@REPO@/d"}]))
    print("  answers by kind: " + ", ".join("%s %d" % kv for kv in sorted(kinds.items(), key=lambda kv: -kv[1])))
    print("run_mcp_git: %d answers the same as the reference server (seed %d%s)" % (n, seed, ", confined" if confined else ""))

main()
