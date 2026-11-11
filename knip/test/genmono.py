# genmono.py DIR NPKG NFILES [SLOW_MS]: a synthetic pnpm monorepo (no node_modules): NPKG packages of
# NFILES TypeScript files each, packages depending on earlier ones, some unused files and exports.
# With SLOW_MS, JavaScript configs too (loaded with Node.js, as real ones are): a vitest.config.ts in
# every package, a playwright.config.ts in every fifth, and in the first a vite config that takes
# SLOW_MS to load (as a large one importing its plugins does); none imports anything.
import os, sys, json, random
d, npkg, nf = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
slow = int(sys.argv[4]) if len(sys.argv) > 4 else -1

random.seed(7)
def w(p, t):
    p = os.path.join(d, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(t)
# (with SLOW_MS: 400 packages in node_modules, with exports maps, that the files import, as a real
# monorepo's do: resolving them is much of the work)
NEXT = 400 if slow >= 0 else 0
for e in range(NEXT):
    name = f"@x/e{e}" if e % 3 == 0 else f"ext{e}"
    w(f'node_modules/{name}/package.json', json.dumps({"name": name, "version": "1.0.0", "type": "module",
        "exports": {".": {"types": "./dist/index.d.ts", "import": "./dist/index.js"}, "./sub/*": "./dist/sub/*.js", "./package.json": "./package.json"}}))
    w(f'node_modules/{name}/dist/index.js', "export const v = 1;\n")
    w(f'node_modules/{name}/dist/index.d.ts', "export declare const v: number;\n")
    for q in range(3): w(f'node_modules/{name}/dist/sub/s{q}.js', "export const s = 1;\n")
def ext_name(e): return f"@x/e{e}" if e % 3 == 0 else f"ext{e}"
w('package.json', json.dumps({"name": "mono", "private": True, "devDependencies": {"typescript": "5.0.0"}}, indent=2))
w('pnpm-workspace.yaml', "packages:\n  - packages/*\n")
w('tsconfig.json', json.dumps({"compilerOptions": {"strict": True, "module": "esnext", "moduleResolution": "bundler"}}))
for i in range(npkg):
    deps = {f"@m/p{j}": "workspace:*" for j in random.sample(range(i), min(i, 3))}
    w(f'packages/p{i}/package.json', json.dumps({"name": f"@m/p{i}", "version": "1.0.0", "type": "module", "main": "src/index.ts",
        "exports": {".": "./src/index.ts"}, "dependencies": deps, "scripts": {"build": "tsc -p .", "test": "vitest run"}}, indent=2))
    w(f'packages/p{i}/tsconfig.json', json.dumps({"extends": "../../tsconfig.json", "include": ["src"]}))
    # (with SLOW_MS, ten files a folder, two levels down, as real sources are spread)
    def mpath(k): return f"f{k // 100}/g{k // 10}/m{k}" if NEXT else f"m{k}"
    imports = '\n'.join(f"import {{ f{k} }} from './{mpath(k)}';" for k in range(nf - 2))
    depimp = '\n'.join(f"import {{ api as a{j} }} from '{n}';" for j, n in enumerate(deps))
    w(f'packages/p{i}/src/index.ts', f"{imports}\n{depimp}\nexport const api = () => [{', '.join(f'f{k}()' for k in range(nf - 2))}{''.join(f', a{j}()' for j in range(len(deps)))}];\n")
    exts = random.sample(range(NEXT), min(NEXT, 40)) if NEXT else []
    for k in range(nf - 2):
        if NEXT:
            # (a few of the package's dependencies, some by subpath; the functions not exported)
            use = random.sample(exts, 4)
            eimp = '\n'.join((f"import {{ s as s{z} }} from '{ext_name(e)}/sub/s{z % 3}';" if z % 2 else f"import {{ v as v{z} }} from '{ext_name(e)}';") for z, e in enumerate(use))
            body = '\n'.join(f"function g{k}_{q}(x: number): number {{ return x * {q} + {k}; }}" for q in range(8))
            uses = ' + '.join((f"s{z}" if z % 2 else f"v{z}") for z in range(len(use)))
            w(f'packages/p{i}/src/{mpath(k)}.ts', f"{eimp}\n{body}\nexport const f{k} = (): number => g{k}_0(1) + g{k}_7({uses});\n")
        else:
            body = '\n'.join(f"export function g{k}_{q}(x: number): number {{ return x * {q} + {k}; }}" for q in range(8))
            w(f'packages/p{i}/src/m{k}.ts', f"{body}\nexport interface T{k} {{ a: number; b: string }}\nexport const f{k} = (): number => g{k}_0(1);\n")
    w(f'packages/p{i}/src/unused.ts', "export const nobody = 1;\n")
    if slow >= 0:
        pj = json.loads(open(os.path.join(d, f'packages/p{i}/package.json')).read())
        pj["devDependencies"] = {"vitest": "3.0.0"}
        pj["dependencies"].update({ext_name(e): "1.0.0" for e in exts})
        w(f'packages/p{i}/vitest.config.ts', "export default { test: { include: ['src/**/*.test.ts'] } };\n")
        w(f'packages/p{i}/src/m0.test.ts', f"import {{ f0 }} from './{mpath(0)}';\nf0();\n")
        if i % 5 == 0:
            pj["devDependencies"]["@playwright/test"] = "1.0.0"
            w(f'packages/p{i}/playwright.config.ts', "export default { testDir: 'e2e' };\n")
            w(f'packages/p{i}/e2e/a.spec.ts', "export const a = 1;\n")
        if i == 0:
            pj["devDependencies"]["vite"] = "6.0.0"
            w('packages/p0/vite.config.ts', f"const t = Date.now(); while (Date.now() - t < {slow}) {{}}\nexport default {{ build: {{ outDir: 'dist' }} }};\n")
        w(f'packages/p{i}/package.json', json.dumps(pj, indent=2))
    w(f'packages/p{i}/src/also-unused.ts', "import { readFileSync } from 'node:fs';\nexport const x = readFileSync;\n")
