# Generated projects for YAML configs: ones the yaml package (knip's parser) rejects give knip's
# "Error loading" message, and ones vknip's reader isn't sure about (flow collections and plain
# scalars over several lines, anchors, block scalars, tags) are read by the yaml package as knip does.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases3 import pkg, mod

CASES = {}

def case(name, files, args=None):
    files = dict(files)
    if args: files["__args__"] = args
    CASES[name] = files

def mods(*names):
    out = {}
    for n in names: out.update(mod(n))
    return out

LH = mods("lefthook")

case("y10_lefthook_bad_indent", {
    "package.json": pkg(dev=["lefthook"]), **LH,
    "lefthook.yml": "pre-commit:\n  commands:\n    lint:\n      run: eslint\n bad: [1\n",
})
case("y10_lefthook_duplicate_key", {
    "package.json": pkg(dev=["lefthook", "eslint"]), **mods("lefthook", "eslint"),
    "lefthook.yml": "pre-commit:\n  commands:\n    lint:\n      run: eslint .\npre-commit:\n  commands: {}\n",
})
case("y10_lefthook_tab", {
    "package.json": pkg(dev=["lefthook"]), **LH,
    "lefthook.yml": "pre-commit:\n\tcommands:\n    lint:\n      run: eslint\n",
})
case("y10_lefthook_nested_compact", {
    "package.json": pkg(dev=["lefthook"]), **LH,
    "lefthook.yml": "pre-commit:\n  commands:\n    lint:\n      run: eslint: .\n",
})
case("y10_workflow_bad", {
    "package.json": pkg(),
    ".github/workflows/ci.yml": "on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: node scripts/a.js\n     - run: node scripts/b.js\n",
    "scripts/a.js": "", "scripts/b.js": "",
})
case("y10_workflow_two_docs", {
    "package.json": pkg(),
    ".github/workflows/ci.yml": "on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: node scripts/a.js\n---\nmore: 1\n",
    "scripts/a.js": "",
})
case("y10_workflow_irregular_valid", {
    "package.json": pkg(dev=["tsx"]), **mods("tsx"),
    ".github/workflows/ci.yml": "on:\n  push:\n    paths: &paths\n      - 'src/**'\n  pull_request:\n    paths: *paths\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: >-\n          node\n          scripts/folded.js\n      - name: [\n          \"x\" ]\n        run: node scripts/flow-name.js\n      - name: Multi\n        run: tsx\n          scripts/plain-multi.ts\n      - run: !!str node scripts/tagged.js\n      - run: |\n          node scripts/a.js\n          node scripts/b.js\n",
    "scripts/a.js": "", "scripts/b.js": "", "scripts/folded.js": "", "scripts/plain-multi.ts": "", "scripts/tagged.js": "", "scripts/flow-name.js": "", "scripts/unused.js": "",
})
case("y10_mocharc_bad", {
    "package.json": pkg(dev=["mocha"]), **mods("mocha"),
    ".mocharc.yml": "spec: 'test/**/*.spec.js'\nrequire: [ts-node/register\n",
    "test/a.spec.js": "",
})
