# Catalogs, compilers and more workspace layouts.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases3 import pkg, mod

CASES = {}

def case(name, files, args=None, links=None):
    files = dict(files)
    if args: files["__args__"] = args
    if links: files["__links__"] = links
    CASES[name] = files

case("cat_pnpm", {
    "pnpm-workspace.yaml": "packages:\n  - packages/*\ncatalog:\n  used-a: ^1.0.0\n  unused-b: ^2.0.0\ncatalogs:\n  react18:\n    react: ^18\n    react-dom: ^18\n",
    "package.json": pkg("root", dev=[]), "packages/p/package.json": json.dumps({"name": "p", "dependencies": {"used-a": "catalog:", "react": "catalog:react18", "missing-c": "catalog:nope"}}, indent=2),
    "packages/p/index.js": "require('used-a'); require('react'); require('missing-c');\n", **mod("used-a"), **mod("react"), **mod("missing-c"),
}, args=[[], ["--reporter", "json"], ["--include", "catalog"], ["--production"]])
case("cat_pkg_json", {
    "package.json": json.dumps({"name": "root", "workspaces": {"packages": ["packages/*"], "catalog": {"x-dep": "1", "y-dep": "1"}}}, indent=2),
    "packages/p/package.json": json.dumps({"name": "p", "dependencies": {"x-dep": "catalog:"}}, indent=2), "packages/p/index.js": "require('x-dep');\n", **mod("x-dep"),
})
case("compilers", {
    "package.json": pkg(deps=["vue", "svelte"], dev=["sass", "@mdx-js/mdx", "tailwindcss"]), **mod("vue"), **mod("svelte"), **mod("sass"), **mod("@mdx-js/mdx"), **mod("tailwindcss"),
    "src/index.ts": "import App from './App.vue';\nimport S from './S.svelte';\nimport './styles.css';\nconsole.log(App, S);\n",
    "src/App.vue": "<template><div/></template>\n<script setup lang=\"ts\">\nimport { h } from './helper';\nimport Child from './Child.vue';\n</script>\n<style lang=\"scss\">@use './vars';</style>\n",
    "src/Child.vue": "<template><p/></template>\n", "src/Unused.vue": "<template><p/></template>\n", "src/_vars.scss": "$x: 1;\n", "src/other.scss": "a{}\n",
    "src/helper.ts": "export const h = 1;\nexport const unusedH = 2;\n",
    "src/S.svelte": "<script>\nimport { s } from './s';\n</script>\n<p>{s}</p>\n", "src/s.ts": "export const s = 1;\n",
    "src/styles.css": "@import 'tailwindcss';\n@import './base.css';\n", "src/base.css": "a{}\n", "src/stray.css": "a{}\n",
    "docs/a.mdx": "import { h } from '../src/helper';\n\n# Hi\n",
})
case("ws_yarn_nested_globs", {
    "package.json": pkg("root", extra={"workspaces": {"packages": ["apps/**", "!apps/legacy"]}}),
    "apps/a/package.json": pkg("a"), "apps/a/index.js": "", "apps/group/b/package.json": pkg("b", deps=["unused-x"]), "apps/group/b/index.js": "", **mod("unused-x"),
    "apps/legacy/package.json": pkg("legacy"), "apps/legacy/index.js": "", "apps/legacy/x.js": "",
}, args=[[], ["--workspace", "apps/group/b"], ["--workspace", "legacy"]])
case("ignore_ws_config", {
    "package.json": pkg("root", extra={"workspaces": ["packages/*"]}), "knip.json": json.dumps({"ignoreWorkspaces": ["packages/skip"], "workspaces": {"packages/*": {"entry": ["lib/*.js"]}}}),
    "packages/use/package.json": pkg("use"), "packages/use/lib/a.js": "require('../x');\n", "packages/use/x.js": "", "packages/use/y.js": "",
    "packages/skip/package.json": pkg("skip"), "packages/skip/z.js": "",
})
case("tags", {
    "package.json": pkg(), "index.ts": "import { used, usedIgnored, E } from './lib';\nconsole.log(used, usedIgnored, E.A, E.C);\n",
    "lib.ts": "export const used = 1;\n/** @lintignore */\nexport const usedIgnored = 2;\n/** @lintignore */\nexport const unusedIgnored = 3;\n/** @custom */\nexport const unusedCustom = 4;\nexport const plain = 5;\nexport enum E { A, /** @lintignore */ B, /** @lintignore */ C, D }\n",
    "knip.json": json.dumps({"tags": ["-lintignore"]}),
}, args=[[], ["--tags", "custom"], ["--tags=-lintignore,-custom"], ["--treat-tag-hints-as-errors"], ["--no-tag-hints"]])
