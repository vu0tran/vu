"""vu test (on tests/tools/*_test.vu) and vu lsp (spoken to over a pipe, as an editor would): what each
reports, and that neither leaves files behind."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VU = os.environ.get('VU', f'{HERE}/../vu').split()
counts = {'passed': 0, 'failed': 0}


def check(name, ok, detail=''):
    counts['passed' if ok else 'failed'] += 1
    print(f'ok    {name}' if ok else f'FAIL  {name}\n      {str(detail)[:700]}')


work = tempfile.mkdtemp()
shutil.copytree(os.path.join(HERE, 'tools'), os.path.join(work, 'tools'))
T = os.path.join(work, 'tools')
tmp = os.path.join(work, 'tmp')
os.makedirs(tmp)
env = dict(os.environ, TMPDIR=tmp)


def vu(*args, cwd=T, inp=None):
    return subprocess.run(VU + list(args), cwd=cwd, capture_output=True, text=True, env=env, input=inp, timeout=300)


# ---- vu test
r = vu('test', 'calc_test.vu')
lines = r.stdout.splitlines()
status = {l.split()[1]: l.split()[0] for l in lines if l.startswith(('ok ', 'FAIL '))}
check('vu test: passing tests', [status.get(t) for t in ('test_add', 'test_parse', 'test_files')] == ['ok', 'ok', 'ok'], r.stdout)
check('vu test: a failed assert, an error and a panic fail only their tests',
      [status.get(t) for t in ('test_add_wrong', 'test_parse_bad', 'test_panics')] == ['FAIL', 'FAIL', 'FAIL'], r.stdout)
check('vu test: the summary and exit status', lines[-1] == '3 passed, 3 failed' and r.returncode == 1, (lines[-1:], r.returncode))
check("vu test: an assert's message and a panic's line are shown",
      "2 + 2 isn't 5" in r.stderr and 'calc_test.vu:19' in r.stderr and "not an Int: 'x'" in r.stderr, r.stderr)
r = vu('test', 'broken_test.vu')
check("vu test: a test file that doesn't compile", "doesn't compile" in r.stderr and 'expected Int, found Str' in r.stderr and
      r.returncode == 1, r.stderr)
r = vu('test', 'none_test.vu')
check('vu test: a file with no tests', 'no tests in' in r.stderr and r.returncode == 1, r.stderr)
open(os.path.join(T, 'ok_test.vu'), 'w').write('fn test_one():\n  assert(1 + 1 == 2)\n')
r = vu('test', 'ok_test.vu')
check('vu test: all passing exits 0', r.returncode == 0 and r.stdout.endswith('1 passed, 0 failed\n'), r.stdout)
r = vu('test')
check('vu test: no files is a usage error', r.returncode == 2, r.returncode)
left = sorted(f for f in os.listdir(T) if f.startswith('vutest_'))
check('vu test: its generated file is gone', left == [], left)
# (the only folder left in TMPDIR is the one test_files made for itself)
left = [d for d in os.listdir(tmp) if not os.listdir(os.path.join(tmp, d)) == ['a.txt']]
check('vu test and vu build leave nothing in TMPDIR', left == [], left)


# ---- vu lsp
def lsp(messages):
    """Sends LSP messages (dicts) to one vu lsp; returns the messages it sent back and its exit status."""
    data = ''.join(f'Content-Length: {len(b)}\r\n\r\n{b}' for b in (json.dumps(m) for m in messages))
    p = subprocess.run(VU + ['lsp'], cwd=T, input=data.encode(), capture_output=True, env=env, timeout=120)
    out, msgs = p.stdout, []
    while out:
        head, _, rest = out.partition(b'\r\n\r\n')
        n = int(head.split(b':')[1])
        msgs.append(json.loads(rest[:n]))
        out = rest[n:]
    return msgs, p.returncode, p.stderr.decode()


uri = 'file://' + os.path.join(T, 'edit.vu')
bad = 'fn main():\n  let x = 1\n  print(y)\n'
good = 'fn main():\n  let x = 1\n  print("{x}")\n'
messy = 'fn main( ):\n    let x=1+2\n    print( "{x}" )\n'
msgs, code, err = lsp([
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
    {'jsonrpc': '2.0', 'method': 'initialized', 'params': {}},
    {'jsonrpc': '2.0', 'method': 'textDocument/didOpen', 'params': {'textDocument': {'uri': uri, 'languageId': 'vu', 'version': 1, 'text': bad}}},
    {'jsonrpc': '2.0', 'method': 'textDocument/didChange', 'params': {'textDocument': {'uri': uri, 'version': 2}, 'contentChanges': [{'text': good}]}},
    {'jsonrpc': '2.0', 'method': 'textDocument/didChange', 'params': {'textDocument': {'uri': uri, 'version': 3}, 'contentChanges': [{'text': messy}]}},
    {'jsonrpc': '2.0', 'id': 2, 'method': 'textDocument/formatting', 'params': {'textDocument': {'uri': uri}, 'options': {'tabSize': 2, 'insertSpaces': True}}},
    {'jsonrpc': '2.0', 'id': 3, 'method': 'textDocument/hover', 'params': {}},
    {'jsonrpc': '2.0', 'id': 'str', 'method': 'textDocument/hover', 'params': {}},
    {'jsonrpc': '2.0', 'method': 'textDocument/didClose', 'params': {'textDocument': {'uri': uri}}},
    {'jsonrpc': '2.0', 'id': 4, 'method': 'shutdown'},
    {'jsonrpc': '2.0', 'method': 'exit'},
])
by_id = {m.get('id'): m for m in msgs if 'id' in m}
diags = [m['params']['diagnostics'] for m in msgs if m.get('method') == 'textDocument/publishDiagnostics']
caps = by_id.get(1, {}).get('result', {}).get('capabilities', {})
check('lsp: initialize offers full sync and formatting', caps.get('textDocumentSync') == 1 and caps.get('documentFormattingProvider'), by_id.get(1))
check('lsp: an error on open, at its line', len(diags) >= 1 and len(diags[0]) == 1 and diags[0][0]['range']['start']['line'] == 2 and
      "'y'" in diags[0][0]['message'], diags[:1])
check('lsp: fixed after a change', len(diags) >= 2 and diags[1] == [], diags[1:2])
edits = by_id.get(2, {}).get('result')
check('lsp: formatting returns the formatted text', edits and edits[0]['newText'] == 'fn main():\n  let x = 1 + 2\n  print("{x}")\n', edits)
check('lsp: an unsupported request gets -32601', by_id.get(3, {}).get('error', {}).get('code') == -32601, by_id.get(3))
check('lsp: a string id gets an error, not silence', by_id.get('str', {}).get('error', {}).get('code') == -32600, by_id.get('str'))
check('lsp: closing a document clears its diagnostics', diags and diags[-1] == [], diags[-1:])
check('lsp: shutdown answered, exit ends it with status 0', 4 in by_id and code == 0, (by_id.get(4), code, err[-300:]))
left = sorted(f for f in os.listdir(T) if f.startswith('.vulsp_'))
check('lsp: its temporary copies are gone', left == [], left)

# an error in a module the open file imports is reported at the top of the file
open(os.path.join(T, 'helper.vu'), 'w').write('fn h() -> Int:\n  return "x"\n')
msgs, code, err = lsp([
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
    {'jsonrpc': '2.0', 'method': 'textDocument/didOpen', 'params': {'textDocument': {'uri': uri, 'languageId': 'vu', 'version': 1,
                                                                                    'text': 'import helper\nfn main():\n  print(helper.h())\n'}}},
    {'jsonrpc': '2.0', 'method': 'exit'},
])
diags = [m['params']['diagnostics'] for m in msgs if m.get('method') == 'textDocument/publishDiagnostics']
check("lsp: an error in an imported module names that file", diags and diags[0] and 'helper.vu' in diags[0][0]['message'], diags)
# a body cut short, and garbage: the server ends without hanging
p = subprocess.run(VU + ['lsp'], cwd=T, input=b'Content-Length: 500\r\n\r\n{"jsonrpc"', capture_output=True, env=env, timeout=30)
check('lsp: input that ends mid-message ends the server', p.returncode in (0, 1), p.returncode)
p = subprocess.run(VU + ['lsp'], cwd=T, input=b'Content-Length: 9\r\n\r\nnot json!' + b'Content-Length: 40\r\n\r\n{"jsonrpc":"2.0","method":"exit"}' + b' ' * 7,
                   capture_output=True, env=env, timeout=30)
check('lsp: a body that isn\'t JSON is skipped', p.returncode == 0, (p.returncode, p.stdout[:200]))

shutil.rmtree(work)
print(f'{counts["passed"]} passed, {counts["failed"]} failed')
sys.exit(1 if counts['failed'] else 0)
