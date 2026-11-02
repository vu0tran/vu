import json
def pkg(name="app", deps=None, dev=None, scripts=None, extra=None, peer=None, opt=None):
    m={"name":name,"version":"1.0.0"}
    if deps: m["dependencies"]={d:"1" for d in deps}
    if dev: m["devDependencies"]={d:"1" for d in dev}
    if peer: m["peerDependencies"]={d:"1" for d in peer}
    if opt: m["optionalDependencies"]={d:"1" for d in opt}
    if scripts: m["scripts"]=scripts
    if extra: m.update(extra)
    return json.dumps(m, indent=2)+"\n"
CASES={}
CASES["c2_default_reexports"]={
 "package.json":pkg(),
 "src/index.ts":"export { default } from './a';\nexport { default as Bee, b2 } from './b';\nimport type * as T from './types';\nexport type X = T.One;\nexport type { Two } from './types';\nimport { ns } from './nsre';\nconsole.log(ns.k1);\n",
 "src/a.ts":"export default 1;\nexport const a1 = 1;\n",
 "src/b.ts":"const v = 2;\nexport { v as default };\nexport const b2 = 2;\nexport const b3 = 3;\n",
 "src/types.ts":"export type One = 1;\nexport type Two = 2;\nexport type Three = 3;\n",
 "src/nsre.ts":"export * as ns from './k';\n",
 "src/k.ts":"export const k1 = 1;\nexport const k2 = 2;\n",
}
CASES["c2_enum_enumerated"]={
 "package.json":pkg(),
 "src/index.ts":"import { E1, E2, E3 } from './e';\nimport cfg from './cfg';\nconsole.log(Object.values(E1), E2['A'], E3[0 as any], cfg.alpha);\n",
 "src/e.ts":"export enum E1 { A, B }\nexport enum E2 { A, B }\nexport enum E3 { A, B }\n",
 "src/cfg.ts":"export default { alpha: 1, beta: 2 };\nexport const unusedCfg = 1;\n",
}
CASES["c2_cjs_more"]={
 "package.json":pkg(deps=["dotenv"]),
 "index.cjs":"module.exports = require('./lib.cjs');\n",
 "lib.cjs":"const { x } = require('./x.cjs');\nmodule.exports.alpha = 1;\nmodule.exports['beta'] = 2;\nexports.gamma = 3;\nmodule.exports.delta = require('./x.cjs').y;\n",
 "x.cjs":"exports.x = 1;\nexports.y = 2;\nexports.z = 3;\n",
}
CASES["c2_var_reexport"]={
 "package.json":pkg(),
 "src/index.ts":"import { alias, spread } from './mid';\nimport { fn } from './gen';\nconsole.log(alias, spread);\nexport const out = fn();\n",
 "src/mid.ts":"import { orig, other } from './orig';\nimport * as all from './orig';\nexport const alias = orig;\nexport const spread = { ...all };\nexport const unusedMid = other;\n",
 "src/orig.ts":"export const orig = 1;\nexport const other = 2;\nexport const third = 3;\n",
 "src/gen.ts":"export interface Shape { a: number }\nexport interface Unrelated { b: number }\nexport function fn(): Shape { return { a: 1 }; }\n",
}
CASES["c2_jsx_ns"]={
 "package.json":pkg(dev=["react","@types/react"]),
 "src/index.tsx":"import * as UI from './ui';\nimport React from 'react';\nexport const App = () => <UI.Button><UI.Icon /></UI.Button>;\n",
 "src/ui.tsx":"export const Button = (p: any) => <button {...p} />;\nexport const Icon = () => <i />;\nexport const Unused = () => null;\n",
}
CASES["c2_url_worker"]={
 "package.json":pkg(),
 "src/index.ts":"const w = new Worker(new URL('./worker.ts', import.meta.url));\nconst u = new URL('./asset.ts', import.meta.url);\nexport {};\n",
 "src/worker.ts":"export const work = 1;\n",
 "src/asset.ts":"export const asset = 1;\n",
}
CASES["c2_augment"]={
 "package.json":pkg(dev=["typescript"]),
 "src/index.ts":"import './types';\nexport {};\n",
 "src/types.ts":"import type { Base } from './base';\ndeclare module './base' {\n  interface Base { extra: Opt }\n}\nexport interface Opt { x: 1 }\n",
 "src/base.ts":"export interface Base { a: number }\nexport interface Lonely { b: number }\n",
}
CASES["c2_imports_field"]={
 "package.json":pkg(extra={"imports":{"#internal/*":"./src/internal/*.ts","#cfg":"./src/config.ts"}}),
 "src/index.ts":"import { i1 } from '#internal/one';\nimport { c } from '#cfg';\nconsole.log(i1, c);\n",
 "src/internal/one.ts":"export const i1 = 1;\nexport const i2 = 2;\n",
 "src/internal/two.ts":"export const t = 1;\n",
 "src/config.ts":"export const c = 1;\n",
}
CASES["c2_deps_types"]={
 "package.json":pkg(deps=["react","lodash","shared"],dev=["@types/react","@types/lodash","@types/express","@types/unrelated","react"],peer=["peer-used","peer-unused"],opt=["opt-used","opt-unused"]),
 "src/index.ts":"import React from 'react';\nimport type { Request } from 'express';\nimport p from 'peer-used';\nimport o from 'opt-used';\nimport pj from 'lodash/package.json';\nconsole.log(React, p, o, pj);\nexport type R = Request;\n",
}
CASES["c2_scripts2"]={
 "package.json":pkg(dev=["concurrently","dotenv","ts-node","vite","husky"],scripts={
   "a":"npm run build -- --watch",
   "b":"yarn test",
   "c":"pnpm --filter web build",
   "d":"node -r dotenv/config ./src/server.js",
   "e":"NODE_OPTIONS='--require ./setup.cjs' node src/other.js",
   "f":"concurrently \"npm:watch-*\" \"vite\"",
   "g":"bash ./scripts/build.sh && ./node_modules/.bin/husky install",
   "h":"ts-node --transpile-only src/tool.ts",
   "build":"vite build",
   "test":"echo ok",
   "watch-a":"tsc -w",
 }),
 "src/server.js":"export const s = 1;\n",
 "src/other.js":"export const o = 1;\n",
 "setup.cjs":"module.exports = {};\n",
 "src/tool.ts":"export const t = 1;\n",
 "scripts/build.sh":"echo hi\n",
 "src/orphan.ts":"export const z = 1;\n",
}
CASES["c2_query_specs"]={
 "package.json":pkg(),
 "src/index.ts":"import raw from './file.txt?raw';\nimport svg from './icon.svg';\nimport w from './w.ts?worker';\nconst name = 'x';\nimport('./' + name);\nconsole.log(raw, svg, w);\n",
 "src/w.ts":"export const w = 1;\n",
}
CASES["c2_tsconfig_files"]={
 "package.json":pkg(dev=["typescript"]),
 "tsconfig.json":"{ \"compilerOptions\": {}, \"files\": [\"src/env.d.ts\", \"src/index.ts\"] }\n",
 "src/index.ts":"export const i = 1;\n",
 "src/env.d.ts":"export interface Env { a: string }\n",
 "src/other.d.ts":"export interface Other { a: string }\n",
}
CASES["c2_destructure_ns"]={
 "package.json":pkg(),
 "src/index.ts":"import * as ns from './n';\nimport def from './d';\nconst { a, ...rest } = ns;\nconst { inner: { deep } } = def;\nconst { x } = def.obj;\nconsole.log(a, rest, deep, x);\n",
 "src/n.ts":"export const a = 1;\nexport const b = 2;\n",
 "src/d.ts":"export default { inner: { deep: 1 }, obj: { x: 1 } };\nexport const dd = 1;\n",
}
CASES["c2_class_static"]={
 "package.json":pkg(),
 "src/index.ts":"import { Svc } from './svc';\nSvc.create();\nexport {};\n",
 "src/svc.ts":"export class Svc { static create() { return new Svc(); } private x = 1; }\nexport abstract class Base {}\nexport type Ctor = typeof Svc;\n",
}
CASES["c2_alias_import"]={
 "package.json":pkg(),
 "src/index.ts":"import { thing as t, Enm as E } from './m';\nimport * as M from './m';\nconst alias = M;\nconsole.log(t, E.X, alias.viaAlias);\n",
 "src/m.ts":"export const thing = 1;\nexport enum Enm { X, Y }\nexport const viaAlias = 1;\nexport const nope = 1;\n",
}
CASES["c2_lazy_fn"]={
 "package.json":pkg(),
 "src/index.ts":"const routes = [() => import('./pageA'), async () => import('./pageB')];\nexport default routes;\n",
 "src/pageA.ts":"export default function A() {}\nexport const metaA = 1;\n",
 "src/pageB.ts":"export const onlyNamed = 1;\n",
}
CASES["c2_optional_peer"]={
 "package.json":json.dumps({"name":"op","version":"1.0.0","peerDependencies":{"opt-peer":"1","opt-peer2":"1","req-peer":"1"},"peerDependenciesMeta":{"opt-peer":{"optional":True},"opt-peer2":{"optional":True}}},indent=2)+"\n",
 "src/index.ts":"import a from 'opt-peer';\nimport b from 'req-peer';\nconsole.log(a, b);\n",
}
