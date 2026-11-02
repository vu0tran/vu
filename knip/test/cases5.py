# --fix: the files knip leaves after fixing (compared file by file), on fresh copies.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases3 import pkg, mod

CASES = {}
FIX_ARGS = [["--fix"], ["--fix-type", "exports"], ["--fix-type", "types"], ["--fix-type", "dependencies"], ["--fix", "--allow-remove-files"], ["--fix-type", "files", "--allow-remove-files"], ["--fix", "--reporter", "json"]]

def case(name, files, args=FIX_ARGS):
    files = dict(files); files["__args__"] = args; files["__fresh__"] = True
    CASES[name] = files

case("fix_exports", {
    "package.json": pkg(deps=["used-dep", "unused-dep"], dev=["unused-dev"]) ,
    **mod("used-dep"), **mod("unused-dep"), **mod("unused-dev"),
    "src/index.ts": "import { a, T } from './lib';\nimport { s1 } from './specs';\nimport d from './def';\nimport 'used-dep';\nconst x: T = a + s1;\nconsole.log(x, d);\n",
    "src/lib.ts": "export const a = 1;\nexport const b = 2;\nexport function f() {}\nexport class C {}\nexport type T = number;\nexport type U = string;\nexport interface I { x: 1 }\nexport enum E { A }\nexport let m = 1, n = 2;\n",
    "src/specs.ts": "const s1 = 1, s2 = 2, s3 = 3;\ntype Q = 1;\nexport { s1, s2, s3 };\nexport { type Q };\nexport {\n  s3 as s4,\n};\n",
    "src/def.ts": "export default function named() {}\nexport const extra = 1;\n",
    "src/defexpr.ts": "export const only = 1;\n",
    "src/reexp.ts": "export { a as ra } from './lib';\nexport { b, f } from './lib';\n",
    "src/orphan.ts": "export const o = 1;\n",
    "src/usesall.ts": "import './reexp';\nimport './defexpr';\n",
    "src/main.ts": "import './usesall';\n",
    "knip.json": json.dumps({"entry": ["src/index.ts", "src/main.ts"]}),
})
case("fix_deps_indent", {
    "package.json": '{\n\t"name": "x",\n\t"dependencies": {\n\t\t"a-dep": "1",\n\t\t"b-dep": "1"\n\t},\n\t"devDependencies": {\n\t\t"c-dev": "1"\n\t}\n}\n',
    **mod("a-dep"), **mod("b-dep"), **mod("c-dev"), "index.js": "require('a-dep');\n",
})
case("fix_default_expr", {
    "package.json": pkg(), "index.ts": "import { k } from './m';\nconsole.log(k);\n",
    "m.ts": "export const k = 1;\nexport default { a: 1 };\n", "n.ts": "export const z = 1;\n",
})
