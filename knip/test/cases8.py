# Generated projects for the plugins' visitors (registerVisitors): jest/vitest/rstest mocks,
# execa/zx/nano-spawn scripts, import.meta.glob, require.context, fs/promises glob, pino transports,
# knex clients.
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

case("v8_jest_mock", {
    "package.json": pkg(dev=["jest", "mocked-dep", "virtual-dep", "actual-dep"]), **mods("jest", "mocked-dep", "actual-dep"),
    "src/a.test.js": "jest.mock('../lib/mocked');\njest.mock('mocked-dep');\njest.mock('virtual-dep', () => ({}), { virtual: true });\nconst a = jest.requireActual('actual-dep');\njest.doMock('./side');\n",
    "src/side.js": "export const s = 1;\n", "lib/mocked.js": "export const m = 1;\nexport const n = 2;\n", "lib/orphan.js": "export {};\n",
})
case("v8_jest_globals", {
    "package.json": pkg(dev=["jest", "@jest/globals"]), **mods("jest", "@jest/globals"),
    "src/b.test.ts": "import { jest as j } from '@jest/globals';\nj.mock('./c');\nj.createMockFromModule('./d');\n",
    "src/c.ts": "export const c = 1;\n", "src/d.ts": "export const d = 1;\n",
})
case("v8_vitest_mock", {
    "package.json": pkg(dev=["vitest"]), **mods("vitest"),
    "src/x.test.ts": "import { vi } from 'vitest';\nvi.mock(import('./dep'), () => ({ a: 1 }));\nvi.mock(import('./dep2'), async () => ({ b: 1 }));\nvi.mock('./dep3');\n",
    "src/dep.ts": "export const a = 1;\nexport const z = 2;\n", "src/dep2.ts": "export const b = 1;\nexport const y = 2;\n", "src/dep3.ts": "export const c = 1;\n",
})
case("v8_execa", {
    "package.json": pkg(deps=["execa"], dev=["tsx", "cowsay"]), **mods("execa", "tsx", "cowsay"),
    "src/index.ts": "import { execa, $, execaNode } from 'execa';\nawait execa('tsx', ['scripts/a.ts']);\nawait $`cowsay hi`;\nawait execaNode('scripts/b.js');\n",
    "scripts/a.ts": "export {};\n", "scripts/b.js": "", "scripts/c.ts": "export {};\n",
})
case("v8_zx_nano", {
    "package.json": pkg(deps=["zx", "nano-spawn"], dev=["tsx"]), **mods("zx", "nano-spawn", "tsx"),
    "scripts/run.mjs": "#!/usr/bin/env zx\nawait $`tsx scripts/a.ts`;\n", "index.js": "import spawn from 'nano-spawn';\nawait spawn('node', ['scripts/b.js']);\n",
    "scripts/a.ts": "export {};\n", "scripts/b.js": "", "scripts/c.js": "",
}, [["--include", "files,dependencies,devDependencies,unlisted,binaries"]])
case("v8_vite_glob", {
    "package.json": pkg(dev=["vite"]), **mods("vite"),
    "index.html": "<script type=\"module\" src=\"/src/main.ts\"></script>\n",
    "src/main.ts": "const mods = import.meta.glob('./pages/*.ts');\nconst raw = import.meta.glob(['./raw/*.ts', '!./raw/skip.ts'], { query: '?raw' });\nconst abs = import.meta.glob('/lib/**/*.ts', { eager: true });\nconsole.log(mods, raw, abs);\n",
    "src/pages/a.ts": "export const a = 1;\n", "src/pages/b.ts": "export const b = 1;\n", "src/raw/r.ts": "export const r = 1;\n", "src/raw/skip.ts": "export {};\n",
    "lib/x/y.ts": "export const y = 1;\n", "src/other.ts": "export {};\n",
})
case("v8_require_context", {
    "package.json": pkg(dev=["webpack"]), **mods("webpack"),
    "src/index.js": "const ctx = require.context('./icons', false, /\\.svg\\.js$/);\nconst all = require.context('./parts');\n",
    "src/icons/a.svg.js": "", "src/icons/b.js": "", "src/icons/sub/c.svg.js": "", "src/parts/p.js": "", "src/parts/q/r.js": "", "src/orphan.js": "",
})
case("v8_fs_glob", {
    "package.json": pkg(), "index.js": "import { glob } from 'node:fs/promises';\nfor await (const f of glob('plugins/*.js')) await import(f);\nimport * as fsp from 'fs/promises';\nfsp.glob(['tasks/*.js'], { cwd: 'src' });\n",
    "plugins/a.js": "", "plugins/b.js": "", "src/tasks/t.js": "", "src/other.js": "",
})
case("v8_pino_knex", {
    "package.json": pkg(deps=["pino", "pino-pretty", "knex", "pg", "mysql2", "sqlite3"]), **mods("pino", "pino-pretty", "knex", "pg", "mysql2", "sqlite3"),
    "index.js": "import pino from 'pino';\nimport knex from 'knex';\nconst l = pino({ transport: { targets: [{ target: 'pino-pretty' }, { target: './transport.js' }] } });\nconst db = knex({ client: 'postgres' });\nconsole.log(l, db);\n",
    "transport.js": "export default () => {};\n", "other.js": "",
})
