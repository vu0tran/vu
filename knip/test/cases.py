# Hand-written feature projects for the differential test: each is {path: content}.
import json
def pkg(name="app", deps=None, dev=None, scripts=None, extra=None):
    m={"name":name,"version":"1.0.0"}
    if deps: m["dependencies"]={d:"1" for d in deps}
    if dev: m["devDependencies"]={d:"1" for d in dev}
    if scripts: m["scripts"]=scripts
    if extra: m.update(extra)
    return json.dumps(m, indent=2)+"\n"

CASES = {}
CASES["reexport_chain"] = {
 "package.json": pkg(),
 "src/index.ts": "export { a, b as bee } from './mid';\nexport * from './star';\nexport * as ns from './nsmod';\nimport { c } from './mid';\nconsole.log(c);\n",
 "src/mid.ts": "export { a, b, c, d } from './leaf';\nexport const own = 1;\n",
 "src/leaf.ts": "export const a = 1;\nexport const b = 2;\nexport const c = 3;\nexport const d = 4;\nexport type T = string;\n",
 "src/star.ts": "export const s1 = 1;\nexport function s2() {}\nexport default 5;\n",
 "src/nsmod.ts": "export const n1 = 1;\nexport const n2 = 2;\n",
 "src/unused.ts": "export const z = 1;\n",
}
CASES["namespace_usage"] = {
 "package.json": pkg(),
 "src/index.ts": "import * as m from './m';\nimport * as all from './all';\nimport * as passed from './passed';\nconsole.log(m.used, m.deep.x);\nfoo(passed);\nconst k = Object.keys(all);\nfunction foo(x: unknown) {}\nexport type Q = m.TypeA;\n",
 "src/m.ts": "export const used = 1;\nexport const unused = 2;\nexport const deep = { x: 1 };\nexport type TypeA = number;\nexport type TypeB = number;\n",
 "src/all.ts": "export const p = 1;\nexport const q = 2;\n",
 "src/passed.ts": "export const r = 1;\nexport interface I { a: 1 }\n",
}
CASES["enums_members"] = {
 "package.json": pkg(),
 "src/index.ts": "import { Color, Size, Dir } from './e';\nimport * as E from './e';\nconsole.log(Color.Red, E.Size.S);\nfor (const k in Dir) {}\nexport { };\n",
 "src/e.ts": "export enum Color { Red, Green, Blue }\nexport enum Size { S = 's', M = 'm', L = 'l' }\nexport enum Dir { Up, Down }\nexport const enum Unused { A, B }\nexport namespace NS { export const a = 1; export function b() {} export type C = number }\n",
}
CASES["types_only"] = {
 "package.json": pkg(),
 "src/index.ts": "import type { A } from './t';\nimport { type B, C } from './t';\nexport function f(x: A): B { return x as any; }\nconsole.log(C);\n",
 "src/t.ts": "export type A = number;\nexport type B = string;\nexport interface Unused1 { x: number }\nexport type Unused2 = A | B;\nexport const C = 1;\nexport class K {}\nexport type InSig = { a: 1 };\nexport function g(): InSig { return { a: 1 }; }\n",
}
CASES["entry_exports_used_in_sig"] = {
 "package.json": pkg(extra={"main":"src/lib.ts"}),
 "src/lib.ts": "import { make, type Opts } from './make';\nexport { make };\nexport type { Opts };\n",
 "src/make.ts": "export interface Opts { a: number }\nexport interface Ret { b: number }\nexport interface Nope { c: number }\nexport function make(o: Opts): Ret { return { b: o.a }; }\n",
}
CASES["cjs"] = {
 "package.json": pkg(deps=["lodash","chalk"]),
 "index.js": "const a = require('./a');\nconst { b1 } = require('./b');\nrequire('./side');\nconst chalk = require('chalk');\nconst x = require('express');\nmodule.exports = { a, b1 };\n",
 "a.js": "module.exports = function a() {};\n",
 "b.js": "exports.b1 = 1;\nexports.b2 = 2;\nmodule.exports.b3 = 3;\n",
 "side.js": "console.log('side');\n",
 "orphan.js": "module.exports = { o: 1 };\n",
}
CASES["dynamic_imports"] = {
 "package.json": pkg(),
 "src/index.ts": "async function main() {\n  const m = await import('./lazy');\n  console.log(m.used);\n  const { picked } = await import('./picked');\n  import('./opaque').then(x => x.y);\n  import('./side');\n  const lz = () => import('./loader');\n  const p = require.resolve('./resolved');\n}\nmain();\n",
 "src/lazy.ts": "export const used = 1;\nexport const notUsed = 2;\n",
 "src/picked.ts": "export const picked = 1;\nexport const other = 2;\n",
 "src/opaque.ts": "export const y = 1;\nexport const w = 2;\n",
 "src/side.ts": "export const s = 1;\n",
 "src/loader.ts": "export default function L() {}\nexport const extra = 1;\n",
 "src/resolved.ts": "export const r = 1;\n",
}
CASES["unresolved_unlisted"] = {
 "package.json": pkg(deps=["used-dep","unused-dep"], dev=["@types/node","@types/used-dep","dev-unused","typescript"]),
 "src/index.ts": "import a from './missing';\nimport b from '../nope/x.js';\nimport 'used-dep';\nimport c from 'not-listed';\nimport d from '@scope/not-listed/sub';\nimport fs from 'fs';\nimport p from 'node:path';\nimport css from './style.css';\nimport data from './data.json';\nimport { z } from 'used-dep/sub';\nconsole.log(a, b, c, d, fs, p, css, data, z);\n",
 "src/data.json": "{}\n",
}
CASES["scripts_bins"] = {
 "package.json": pkg(dev=["eslint","vitest","tsx","cross-env","rimraf","prettier","c8"], scripts={
   "lint": "eslint . && prettier --check .",
   "test": "cross-env NODE_ENV=test c8 vitest run",
   "dev": "tsx watch src/dev.ts",
   "clean": "rimraf dist && unknown-bin --flag",
   "start": "node ./server/main.js",
   "build": "npm run clean && tsc -p tsconfig.build.json",
   "x": "npx some-tool@1 arg && pnpm exec other-tool",
 }),
 "src/dev.ts": "export const dev = 1;\n",
 "server/main.js": "require('./util');\n",
 "server/util.js": "module.exports = 1;\n",
 "src/a.test.ts": "import { x } from './x';\nconsole.log(x);\n",
 "src/x.ts": "export const x = 1;\nexport const y = 2;\n",
 "tsconfig.build.json": "{ \"extends\": \"@tsconfig/node20/tsconfig.json\" }\n",
}
CASES["tsconfig_paths"] = {
 "package.json": pkg(dev=["typescript"]),
 "tsconfig.json": "{\n  // comment\n  \"compilerOptions\": { \"baseUrl\": \".\", \"paths\": { \"@/*\": [\"src/*\"], \"~lib\": [\"lib/index.ts\"] }, \"types\": [\"vitest/globals\"], },\n  \"include\": [\"src\", \"types\"]\n}\n",
 "src/index.ts": "import { a } from '@/a';\nimport { l } from '~lib';\nimport { b } from 'src/b';\nconsole.log(a, l, b);\n",
 "src/a.ts": "export const a = 1;\nexport const a2 = 2;\n",
 "src/b.ts": "export const b = 1;\n",
 "lib/index.ts": "export const l = 1;\n",
 "types/global.d.ts": "declare global { var X: number }\nexport {};\n",
 "types/ambient.d.ts": "declare module 'foo' { export const x: number }\n",
 "types/withexport.d.ts": "export interface Shape { x: number }\n",
}
CASES["index_and_ext"] = {
 "package.json": pkg(extra={"type":"module"}),
 "src/index.ts": "import { a } from './dir';\nimport { b } from './b.js';\nimport { c } from './c.mjs';\nimport { d } from './d';\nconsole.log(a, b, c, d);\n",
 "src/dir/index.ts": "export const a = 1;\nexport const unusedA = 1;\n",
 "src/b.ts": "export const b = 1;\n",
 "src/c.mts": "export const c = 1;\n",
 "src/d.tsx": "export const d = 1;\nexport function Comp() { return <div/>; }\n",
}
CASES["defaults_dups"] = {
 "package.json": pkg(),
 "src/index.ts": "import def, { named } from './d';\nimport other from './other';\nconsole.log(def, named, other);\n",
 "src/d.ts": "export function named() {}\nexport const alias = named;\nexport default named;\n",
 "src/other.ts": "const x = 1;\nexport { x as y, x as z };\nexport default class Foo {}\n",
 "src/third.ts": "export default function () {}\n",
}
CASES["jsdoc_tags"] = {
 "package.json": pkg(),
 "src/index.ts": "import './lib';\n",
 "src/lib.ts": "/** @public */\nexport const pub = 1;\n/**\n * Doc\n * @internal\n */\nexport const internal = 2;\n/** @beta */\nexport function beta() {}\n// @alias\nexport const al = 3;\nexport const plain = 4;\n/** @deprecated */\nexport type Old = 1;\n",
}
CASES["export_assign"] = {
 "package.json": pkg(),
 "src/index.ts": "import x = require('./ea');\nimport * as ns from './nsx';\nimport y = ns.inner;\nconsole.log(x, y);\n",
 "src/ea.ts": "const v = 1;\nexport = v;\n",
 "src/nsx.ts": "export const inner = 1;\nexport const outer = 2;\n",
}
CASES["class_and_destructure"] = {
 "package.json": pkg(),
 "src/index.ts": "import { Svc, cfg } from './svc';\nnew Svc();\nconst { port } = cfg;\nconsole.log(port);\n",
 "src/svc.ts": "export class Svc { method() {} }\nexport const cfg = { port: 1, host: 'x' };\nexport const { a1, b1 } = { a1: 1, b1: 2 };\nexport const [ar1, ar2] = [1, 2];\n",
}
CASES["vitest_jest_tests"] = {
 "package.json": pkg(dev=["vitest","jest"]),
 "src/index.ts": "export const main = 1;\n",
 "src/util.ts": "export const u = 1;\nexport const v = 2;\n",
 "src/util.test.ts": "import { u } from './util';\nimport { helper } from '../test/helper';\nconsole.log(u, helper);\n",
 "src/__tests__/x.js": "require('../util');\n",
 "src/__mocks__/m.ts": "export const m = 1;\n",
 "test/helper.ts": "export const helper = 1;\nexport const nohelp = 2;\n",
 "test/spec.spec.ts": "import '../src/util';\n",
}
CASES["gitignore"] = {
 "package.json": pkg(),
 ".gitignore": "dist\n*.gen.ts\n!keep.gen.ts\nbuild/\n/rootonly.ts\n",
 "src/index.ts": "import './a.gen';\nexport {};\n",
 "src/a.gen.ts": "export const g = 1;\n",
 "src/b.gen.ts": "export const g = 1;\n",
 "src/keep.gen.ts": "export const k = 1;\n",
 "dist/out.js": "x\n",
 "build/x.ts": "export const b = 1;\n",
 "rootonly.ts": "export const r = 1;\n",
 "sub/rootonly.ts": "export const r = 1;\n",
 "sub/.gitignore": "ignored-in-sub.ts\n",
 "sub/ignored-in-sub.ts": "export const i = 1;\n",
}
CASES["package_entries"] = {
 "package.json": pkg(extra={"main":"./lib/main.js","bin":{"tool":"./bin/tool.js"},"exports":{".":{"import":"./lib/main.js","types":"./lib/main.d.ts"},"./feature":"./lib/feature.js","./utils/*":"./lib/utils/*.js"}}),
 "lib/main.js": "export const m = 1;\n",
 "lib/feature.js": "export const f = 1;\n",
 "lib/utils/one.js": "export const one = 1;\n",
 "lib/utils/two.js": "export const two = 1;\n",
 "lib/internal.js": "export const i = 1;\n",
 "bin/tool.js": "#!/usr/bin/env node\nimport '../lib/internal.js';\n",
}
CASES["outdir_mapping"] = {
 "package.json": pkg(dev=["typescript"], extra={"main":"dist/index.js","types":"dist/index.d.ts"}),
 "tsconfig.json": "{ \"compilerOptions\": { \"outDir\": \"dist\", \"rootDir\": \"src\" } }\n",
 "src/index.ts": "export { helper } from './helper';\n",
 "src/helper.ts": "export const helper = 1;\nexport const hidden = 2;\n",
 "src/stray.ts": "export const s = 1;\n",
}
CASES["self_reference"] = {
 "package.json": pkg(name="selfpkg", extra={"exports":{".":"./src/index.ts","./sub":"./src/sub.ts"}}),
 "src/index.ts": "export const root = 1;\n",
 "src/sub.ts": "export const sub = 1;\nexport const sub2 = 2;\n",
 "test/t.test.js": "import { sub } from 'selfpkg/sub';\nimport x from 'selfpkg';\n",
}
CASES["node_test_runner"] = {
 "package.json": pkg(scripts={"test": "node --test"}),
 "src/index.js": "export const a = 1;\n",
 "test/a.test.js": "import '../src/lib.js';\n",
 "src/lib.js": "export const lib = 1;\nexport const nolib = 2;\n",
 "src/b-test.mjs": "export const z = 1;\n",
}
CASES["comments_imports"] = {
 "package.json": pkg(dev=["@types/node", "preact"]),
 "src/index.ts": "/// <reference types=\"node\" />\n/// <reference path=\"./ref.d.ts\" />\n/** @jsxImportSource preact */\n/** @type {import('./typed').T} */\nconst x = 1;\nexport {};\n",
 "src/ref.d.ts": "declare const R: number;\n",
 "src/typed.ts": "export type T = number;\nexport type U = string;\n",
}
CASES["shadowing"] = {
 "package.json": pkg(),
 "src/index.ts": "import * as ns from './ns';\nimport { obj } from './obj';\nfunction f(ns: any) { return ns.hidden; }\nconsole.log(ns.vis, obj.prop);\n{ const ns = { blk: 1 }; ns.blk; }\nexport {};\n",
 "src/ns.ts": "export const vis = 1;\nexport const hidden = 2;\nexport const blk = 3;\n",
 "src/obj.ts": "export const obj = { prop: 1 };\nexport const other = 1;\n",
}
CASES["reexport_ns_alias"] = {
 "package.json": pkg(),
 "src/index.ts": "import { api } from './barrel';\nimport * as B from './barrel';\nconsole.log(api.one, B.direct);\n",
 "src/barrel.ts": "import * as api from './api';\nexport { api };\nexport { two as direct, three } from './api';\n",
 "src/api.ts": "export const one = 1;\nexport const two = 2;\nexport const three = 3;\nexport const four = 4;\n",
}
CASES["workspace_like_dirs"] = {
 "package.json": pkg(dev=["prettier","eslint"], extra={"prettier":"some-prettier-config","eslintConfig":{"extends":["airbnb","plugin:react/recommended"],"plugins":["import"],"parser":"@typescript-eslint/parser"}}),
 "src/index.js": "export default 1;\n",
}
