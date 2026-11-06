# genmono.py DIR NPKG NFILES: a synthetic pnpm monorepo (no node_modules): NPKG packages of NFILES
# TypeScript files each, packages depending on earlier ones, some unused files and exports
import os, sys, json, random
d, npkg, nf = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
random.seed(7)
def w(p, t):
    p = os.path.join(d, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(t)
w('package.json', json.dumps({"name": "mono", "private": True, "devDependencies": {"typescript": "5.0.0"}}, indent=2))
w('pnpm-workspace.yaml', "packages:\n  - packages/*\n")
w('tsconfig.json', json.dumps({"compilerOptions": {"strict": True, "module": "esnext", "moduleResolution": "bundler"}}))
for i in range(npkg):
    deps = {f"@m/p{j}": "workspace:*" for j in random.sample(range(i), min(i, 3))}
    w(f'packages/p{i}/package.json', json.dumps({"name": f"@m/p{i}", "version": "1.0.0", "type": "module", "main": "src/index.ts",
        "exports": {".": "./src/index.ts"}, "dependencies": deps, "scripts": {"build": "tsc -p .", "test": "vitest run"}}, indent=2))
    w(f'packages/p{i}/tsconfig.json', json.dumps({"extends": "../../tsconfig.json", "include": ["src"]}))
    imports = '\n'.join(f"import {{ f{k} }} from './m{k}';" for k in range(nf - 2))
    depimp = '\n'.join(f"import {{ api as a{j} }} from '{n}';" for j, n in enumerate(deps))
    w(f'packages/p{i}/src/index.ts', f"{imports}\n{depimp}\nexport const api = () => [{', '.join(f'f{k}()' for k in range(nf - 2))}{''.join(f', a{j}()' for j in range(len(deps)))}];\n")
    for k in range(nf - 2):
        body = '\n'.join(f"export function g{k}_{q}(x: number): number {{ return x * {q} + {k}; }}" for q in range(8))
        w(f'packages/p{i}/src/m{k}.ts', f"{body}\nexport interface T{k} {{ a: number; b: string }}\nexport const f{k} = (): number => g{k}_0(1);\n")
    w(f'packages/p{i}/src/unused.ts', "export const nobody = 1;\n")
    w(f'packages/p{i}/src/also-unused.ts', "import { readFileSync } from 'node:fs';\nexport const x = readFileSync;\n")
