# Generated projects for the knip5 round: tsconfig references (the referenced tsconfig that includes
# a file gives its paths and rootDirs, as oxc-resolver's references: 'auto'), --strict without
# type-only imports, Vite inline module scripts, Vitest workspace entries, webpack rules that are
# functions, scripts a source file runs (the manifest's folder), gitignored tsconfig references.
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

TS = mods("typescript")
def js(o): return json.dumps(o, indent=2) + "\n"

# a solution tsconfig: files [] and two references with different paths for the same alias
case("v9_refs_solution", {
    "package.json": pkg(dev=["typescript"], extra={"main": "src/index.ts"}), **TS,
    "tsconfig.json": js({"files": [], "references": [{"path": "./tsconfig.app.json"}, {"path": "./tsconfig.node.json"}]}),
    "tsconfig.app.json": js({"include": ["src"], "compilerOptions": {"paths": {"@x/*": ["./lib-a/*"], "~/*": ["./src/*"]}}}),
    "tsconfig.node.json": js({"include": ["scripts/**/*.ts", "src/**/*"], "compilerOptions": {"paths": {"@x/*": ["./lib-b/*"], "@n/*": ["./lib-b/*"]}}}),
    "src/index.ts": "import { a } from '@x/m';\nimport { u } from '~/util';\nimport { n } from '@n/m';\nconsole.log(a, u, n);\n",
    "src/util.ts": "export const u = 1;\nexport const v = 2;\n",
    "lib-a/m.ts": "export const a = 1;\nexport const n = 3;\n", "lib-b/m.ts": "export const a = 2;\nexport const n = 4;\n",
    "scripts/build.ts": "import { a } from '@x/m';\nconsole.log(a);\n",
})
# references: one folder reference, extends in the reference, exclude, a file outside every reference
case("v9_refs_dir_extends", {
    "package.json": pkg(dev=["typescript"], extra={"main": "src/index.ts"}), **TS,
    "tsconfig.json": js({"references": [{"path": "./config"}], "compilerOptions": {"paths": {"@r/*": ["./root-lib/*"]}}}),
    "config/tsconfig.json": js({"extends": "./base.json", "include": ["../src/**/*"], "exclude": ["../src/legacy.ts"]}),
    "config/base.json": js({"compilerOptions": {"paths": {"@x/*": ["../lib/*"]}}}),
    "src/index.ts": "import { a } from '@x/m';\nimport './legacy';\nimport '../other/o';\nconsole.log(a);\n",
    "src/legacy.ts": "import { b } from '@r/m';\nconsole.log(b);\n",
    "other/o.ts": "import { c } from '@r/m';\nimport { d } from '@x/m';\nconsole.log(c, d);\n",
    "lib/m.ts": "export const a = 1;\nexport const d = 2;\nexport const z = 3;\n",
    "root-lib/m.ts": "export const b = 1;\nexport const c = 2;\nexport const y = 3;\n",
})
# rootDirs in a referenced tsconfig (React Router's ./+types), the generated folder gitignored
case("v9_refs_rootdirs", {
    "package.json": pkg(dev=["typescript"], extra={"main": "app/root.tsx"}), **TS,
    ".gitignore": ".gen/\n",
    "tsconfig.json": js({"files": [], "references": [{"path": "./tsconfig.vite.json"}]}),
    "tsconfig.vite.json": js({"include": [".gen/types/**/*", "app/**/*"], "compilerOptions": {"rootDirs": [".", "./.gen/types"], "jsx": "react-jsx"}}),
    "app/root.tsx": "import type { Route } from './+types/root';\nimport { h } from './routes/home';\nexport const x: Route = h;\n",
    "app/routes/home.tsx": "import type { Route } from './+types/home';\nexport const h = 1;\nexport const unused = 2;\n",
    ".gen/types/app/+types/root.ts": "export type Route = number;\n",
    ".gen/types/app/routes/+types/home.ts": "export type Route = number;\n",
})
# a tsconfig whose references are gitignored (Nuxt's .nuxt): their types and jsxImportSource aren't read
case("v9_refs_gitignored", {
    "package.json": pkg(dev=["typescript"], extra={"main": "index.ts"}), **TS,
    ".gitignore": ".cache/\n",
    "tsconfig.json": js({"files": [], "references": [{"path": "./.cache/tsconfig.app.json"}, {"path": "./tsconfig.local.json"}]}),
    ".cache/tsconfig.app.json": js({"compilerOptions": {"jsxImportSource": "vue", "types": ["some-types"]}}),
    "tsconfig.local.json": js({"extends": "./.cache/tsconfig.app.json", "compilerOptions": {"types": ["local-types"]}}),
    "index.ts": "export {};\n",
})
# --strict: type-only imports of packages and unresolved type-only imports aren't counted
case("v9_strict_type_only", {
    "package.json": pkg(deps=["runtime-dep"], dev=["types-dep", "typescript"], extra={"main": "index.ts"}), **mods("runtime-dep", "types-dep", "typescript"),
    "index.ts": "import type { T } from 'types-dep';\nimport { r } from 'runtime-dep';\nimport type { U } from 'unlisted-types';\nimport type { G } from './gone';\n/** @type {import('./also-gone').X} */\nexport const v: T | U | G = r;\n",
}, [[], ["--strict"], ["--production"]])
# Vite's inline module scripts: comments, import.meta strings, dynamic imports, from-clauses
case("v9_vite_inline", {
    "package.json": pkg(dev=["vite"], scripts={"dev": "vite"}), **mods("vite"),
    "index.html": "<!doctype html>\n<script type=\"module\">\n  // import '/src/commented.ts'\n  /* import '/src/block.ts' */\n  import '/src/main.ts'\n  import { x } from './src/named.ts'\n  const m = import('/src/lazy.ts')\n  console.log(import.meta.url, '/src/decoy.ts', x, m)\n  importx('/src/notimport.ts')\n</script>\n<script type=\"module\" src=\"/src/src-attr.ts\"></script>\n<script src=\"/src/classic.ts\"></script>\n",
    "src/main.ts": "", "src/named.ts": "export const x = 1;\n", "src/lazy.ts": "", "src/commented.ts": "", "src/block.ts": "",
    "src/decoy.ts": "", "src/notimport.ts": "", "src/src-attr.ts": "", "src/classic.ts": "",
})
# Vitest: workspace entries (objects with test.setupFiles), vi shadowed by a parameter
case("v9_vitest_workspace", {
    "package.json": pkg(dev=["vitest"]), **mods("vitest"),
    "vitest.config.ts": "import { defineConfig } from 'vitest/config';\nexport default defineConfig({ test: { workspace: ['packages/*', { test: { name: 'a', setupFiles: './setup-a.ts' } }, { test: { globalSetup: ['./global-b.ts'], environment: 'happy-dom' } }] } });\n",
    "setup-a.ts": "", "global-b.ts": "",
    "src/x.test.ts": "import { vi, test } from 'vitest';\nvi.mock(import('./dep'), () => ({ a: 1 }));\nfunction f(vi: any) { vi.mock(import('./dep2'), () => ({ b: 1 })); }\ntest('t', () => f(1));\n",
    "src/dep.ts": "export const a = 1;\nexport const z = 2;\n", "src/dep2.ts": "export const b = 1;\nexport const y = 2;\n",
})
# webpack: a rule that is a function (called with the rule info), returning a loader
case("v9_webpack_fn_rule", {
    "package.json": pkg(dev=["webpack", "webpack-cli", "svgo-loader", "css-loader"], scripts={"build": "webpack"}), **mods("webpack", "webpack-cli", "css-loader"),
    "webpack.config.js": "module.exports = { entry: './src/index.js', module: { rules: [ info => ({ loader: 'svgo-loader', options: {} }), () => 'raw-loader', { test: /\\.css$/, use: ['css-loader'] } ] } };\n",
    "src/index.js": "",
})
# a source file's scripts: expanded package scripts run in the manifest's folder
case("v9_script_manifest_dir", {
    "package.json": pkg(extra={"workspaces": ["packages/*"]}, scripts={"build": "node scripts/build.mjs"}),
    "packages/app/package.json": pkg("app", scripts={"pack": "node tasks/pack.mjs"}),
    "packages/app/dev/dev.mjs": "import { spawnSync } from 'node:child_process';\nspawnSync('npm', ['run', 'pack', '--', '--watch']);\nspawnSync('yarn', ['run', 'pack', '--fast']);\n",
    "packages/app/tasks/pack.mjs": "", "scripts/build.mjs": "",
    "scripts/dev/dev.mjs": "import { execSync } from 'node:child_process';\nexecSync('npm run build -- --verbose');\n",
    "knip.json": js({"workspaces": {".": {"entry": ["scripts/dev/*.mjs"]}, "packages/app": {"entry": ["dev/*.mjs"]}}}),
})
