#!/usr/bin/env python3
"""Do models write correct Vu? The same tasks (eval/tasks.py) in Vu, Rust, Go and Python, across models.

  eval/run.py --model anthropic:claude-sonnet-5-5 --model openai:gpt-5 [--lang vu --lang rust ...]
              [--tasks word_count,caesar] [--attempts 3] [--jobs 4] [--out eval/results]
  eval/run.py --self-test          # the harness end to end, with the Python reference as the "model"
  eval/report.py eval/results      # the table

Keys come from ANTHROPIC_API_KEY and OPENAI_API_KEY. Each task is asked for once per model and
language. The program is built (vu build, rustc -O, go build, python3) and run on every test case;
if it doesn't build or a case fails, the model is shown the compiler's errors or the first failing
case and asked again, up to --attempts in all. For Vu the system prompt holds llms.txt (the
language in brief): models haven't seen much Vu, and a user would hand them the same page. The other
languages get no documentation. Every request, reply, build and run is kept in the results, so any
number in the report can be traced back."""
import argparse, concurrent.futures, json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import tasks as T

LANGS = {
    "vu": {"name": "Vu", "ext": "vu", "fence": "vu"},
    "rust": {"name": "Rust", "ext": "rs", "fence": "rust"},
    "go": {"name": "Go", "ext": "go", "fence": "go"},
    "python": {"name": "Python 3", "ext": "py", "fence": "python"},
}

def system_prompt(lang):
    base = ("You write complete, correct {name} programs. Reply with exactly one fenced code block holding the "
            "whole program, and nothing else. Use only the standard library. The program reads standard input and "
            "writes standard output exactly as specified: no prompts, no extra spaces or lines.").format(**LANGS[lang])
    if lang == "vu":
        with open(os.path.join(ROOT, "llms.txt")) as f:
            base += "\n\nVu is a new language; here is its reference:\n\n" + f.read()
    return base

# ---------------------------------------------------------------- models

def post(url, headers, body, tries=6):
    data = json.dumps(body).encode()
    for k in range(tries):
        req = urllib.request.Request(url, data=data, headers=dict(headers, **{"content-type": "application/json"}))
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and k + 1 < tries:
                time.sleep(2 ** k * 5)
                continue
            raise RuntimeError("HTTP %d: %s" % (e.code, e.read()[:500]))
        except (urllib.error.URLError, TimeoutError):
            if k + 1 < tries:
                time.sleep(2 ** k * 5)
                continue
            raise

def ask(model, system, messages):
    """The model's reply text and its output token count."""
    provider, name = model.split(":", 1)
    if provider == "anthropic":
        r = post("https://api.anthropic.com/v1/messages",
                 {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                 {"model": name, "max_tokens": 8000, "system": system, "messages": messages})
        text = "".join(b.get("text", "") for b in r["content"] if b["type"] == "text")
        return text, r["usage"]["output_tokens"]
    if provider == "openai":
        r = post("https://api.openai.com/v1/chat/completions",
                 {"authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                 {"model": name, "messages": [{"role": "system", "content": system}] + messages})
        return r["choices"][0]["message"]["content"], r["usage"]["completion_tokens"]
    if provider == "reference":
        # --self-test: a Python program that calls the task's reference
        return "```python\nimport sys\nsys.path.insert(0, %r)\nimport tasks\nt = [t for t in tasks.TASKS if t['name'] == %r][0]\nsys.stdout.write(t['ref'](sys.stdin.read()))\n```" % (HERE, name), 0
    raise ValueError("unknown provider " + provider)

def code_of(reply, lang):
    blocks = re.findall(r"```[^\n]*\n(.*?)```", reply, re.S)
    if blocks: return max(blocks, key=len)
    return reply

# ---------------------------------------------------------------- build and run

def build(lang, code, d):
    """The command to run the program, or (None, the errors)."""
    src = os.path.join(d, "main." + LANGS[lang]["ext"])
    with open(src, "w") as f: f.write(code)
    if lang == "python": return [sys.executable, "-I", src], ""
    if lang == "vu": cmd = [os.path.join(ROOT, "vu"), "build", src, "-o", os.path.join(d, "prog")]
    elif lang == "rust": cmd = ["rustc", "-O", "--edition", "2021", src, "-o", os.path.join(d, "prog")]
    else:
        with open(os.path.join(d, "go.mod"), "w") as f: f.write("module prog\n\ngo 1.22\n")
        cmd = ["go", "build", "-o", os.path.join(d, "prog"), "."]
    p = subprocess.run(cmd, cwd=d, capture_output=True, text=True, timeout=300, env=dict(os.environ, GOCACHE=os.path.join(d, ".gocache"), GOFLAGS="-mod=mod"))
    if p.returncode != 0: return None, (p.stdout + p.stderr)[-6000:]
    return [os.path.join(d, "prog")], ""

def run_cases(cmd, cases, d):
    """None when every case passes, else a description of the first that doesn't."""
    for c in cases:
        try:
            p = subprocess.run(cmd, input=c["stdin"].encode(), capture_output=True, timeout=10, cwd=d)
        except subprocess.TimeoutExpired:
            return {"input": c["stdin"], "problem": "timed out after 10 seconds"}
        got = p.stdout.decode("utf-8", "replace")
        if p.returncode != 0:
            return {"input": c["stdin"], "problem": "exited with code %d; stderr: %s" % (p.returncode, p.stderr.decode("utf-8", "replace")[-2000:])}
        if got != c["stdout"]:
            return {"input": c["stdin"], "expected": c["stdout"], "got": got}
    return None

def clip(s, n=1500):
    return s if len(s) <= n else s[:n] + "\n... (%d more bytes)" % (len(s) - n)

def feedback(built_errors, fail):
    if built_errors is not None:
        return "It doesn't compile:\n\n" + built_errors + "\n\nFix it and reply with the whole corrected program."
    msg = "It compiles, but fails a test.\n\nInput:\n" + clip(fail["input"]) + "\n"
    if "problem" in fail: msg += "\nThe program " + fail["problem"] + "\n"
    else: msg += "\nExpected output:\n" + clip(fail["expected"]) + "\n\nYour output:\n" + clip(fail["got"]) + "\n"
    return msg + "\nFix it and reply with the whole corrected program."

def solve(model, lang, t, attempts):
    cases = T.cases(t)
    system = system_prompt(lang)
    messages = [{"role": "user", "content": t["prompt"]}]
    rec = {"model": model, "lang": lang, "task": t["name"], "attempts": []}
    with tempfile.TemporaryDirectory(prefix="vu-eval-") as d:
        for k in range(attempts):
            t0 = time.time()
            try:
                reply, toks = ask(model, system, messages)
            except Exception as e:
                rec["error"] = str(e)[:500]
                break
            code = code_of(reply, lang)
            cmd, errs = build(lang, code, d)
            fail = run_cases(cmd, cases, d) if cmd else None
            ok = cmd is not None and fail is None
            rec["attempts"].append({"code": code, "tokens": toks, "compiled": cmd is not None, "passed": ok,
                                    "errors": errs, "fail": fail, "seconds": round(time.time() - t0, 1)})
            if ok: break
            messages += [{"role": "assistant", "content": reply}, {"role": "user", "content": feedback(errs if cmd is None else None, fail)}]
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append", default=[])
    ap.add_argument("--lang", action="append", default=[])
    ap.add_argument("--tasks", default="")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    langs = a.lang or list(LANGS)
    todo = [t for t in T.TASKS if not a.tasks or t["name"] in a.tasks.split(",")]
    if a.self_test:
        bad = 0
        for t in todo:
            r = solve("reference:" + t["name"], "python", t, 1)
            if not r["attempts"] or not r["attempts"][0]["passed"]:
                bad += 1
                print("FAIL", t["name"], json.dumps(r["attempts"][-1]["fail"] if r["attempts"] else r.get("error"))[:300])
        print("self-test: %d of %d tasks pass with the reference as the program" % (len(todo) - bad, len(todo)))
        sys.exit(1 if bad else 0)
    if not a.model: ap.error("give at least one --model provider:name")
    os.makedirs(a.out, exist_ok=True)
    lock = threading.Lock()
    jobs = [(m, l, t) for m in a.model for l in langs for t in todo]
    done = 0
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
        for rec in ex.map(lambda j: solve(j[0], j[1], j[2], a.attempts), jobs):
            done += 1
            with lock, open(os.path.join(a.out, rec["model"].replace(":", "_").replace("/", "_") + ".jsonl"), "a") as f:
                f.write(json.dumps(rec) + "\n")
            last = rec["attempts"][-1] if rec["attempts"] else {}
            print("%4d/%d %-28s %-6s %-22s %s" % (done, len(jobs), rec["model"], rec["lang"], rec["task"],
                  "pass@%d" % len(rec["attempts"]) if last.get("passed") else "FAIL" + (" (%s)" % rec["error"][:60] if "error" in rec else "")), flush=True)

if __name__ == "__main__":
    main()
