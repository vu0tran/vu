# cases12.py (gen_cmp.py; UNHEAD_PNPM=the unhead corpus pnpm store): Attacks on config loading (issue #2): define helpers skipped (real vite, vitest, unbuild and
# @playwright/test linked from the unhead corpus), node processes shared and run side by side, -D.
import json, os, glob
PN = os.environ.get('UNHEAD_PNPM', 'corpus/unhead/node_modules/.pnpm')  # the unhead corpus project's pnpm store
def real(pat, sub):
    return sorted(glob.glob(f'{PN}/{pat}/node_modules/{sub}'))[0]
VITE = real('vite@8.3.0_*', 'vite'); VITEST = real('vitest@5.0.0*', 'vitest'); UNBUILD = real('unbuild@3.6.1*', 'unbuild')
PW = real('@playwright+test@1.63.0', '@playwright/test')
LINKS = {'node_modules/vite': VITE, 'node_modules/vitest': VITEST, 'node_modules/unbuild': UNBUILD, 'node_modules/@playwright/test': PW}
def pkg(dev=None, extra=None, name='app'):
    m = {'name': name, 'version': '1.0.0', 'type': 'module'}
    if dev: m['devDependencies'] = {d: '1' for d in dev}
    if extra: m.update(extra)
    return json.dumps(m, indent=2) + '\n'
SRC = {'src/index.ts': "import { a } from './a';\nconsole.log(a);\n", 'src/a.ts': 'export const a = 1;\nexport const b = 2;\n',
       'src/orphan.ts': 'export {};\n', 'test/x.test.ts': "import '../src/a';\n", 'test/setup.ts': 'export {};\n', 'e2e/a.spec.ts': 'export {};\n'}
CASES = {}
def case(name, files, args=None, links=None):
    f = dict(SRC); f.update(files)
    f['__links__'] = {k: v for k, v in dict(LINKS, **(links or {})).items() if v}
    if args: f['__args__'] = args
    CASES[name] = f
DEV = ['vite', 'vitest', 'unbuild', '@playwright/test']
VT = "  test: { setupFiles: ['./test/setup.ts'], include: ['test/**/*.test.ts'] },\n"
case('kp_vite_plain', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "});\n"})
case('kp_vite_two_args', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "}, { extra: 1 } as any);\n"})
case('kp_vite_loadenv', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig, loadEnv } from 'vite';\nexport default defineConfig(({ mode }) => { loadEnv(mode, process.cwd()); return {\n" + VT + "}; });\n"})
case('kp_vite_alias_type', {'package.json': pkg(DEV), 'vite.config.mts': "/* header */\n// comment\nimport { type UserConfig, defineConfig as dc } from 'vite'\nimport { resolve } from 'node:path'\nconst c: UserConfig = {\n" + VT + "  resolve: { alias: { '@': resolve(__dirname, 'src') } },\n};\nexport default dc(c)\n"})
case('kp_vite_fn', {'package.json': pkg(DEV), 'vite.config.ts': "import {\n  defineConfig, // the helper\n} from \"vite\";\nexport default defineConfig(async ({ command }) => ({\n  test: { include: [command === 'serve' ? 'test/**/*.test.ts' : 'nothing'] },\n}));\n"})
case('kp_vitest_two', {'package.json': pkg(DEV), 'vitest.config.ts': "import { defineConfig } from 'vitest/config';\nimport { defineConfig as viteDefine } from 'vite';\nexport default defineConfig(viteDefine({\n" + VT + "}));\n"})
case('kp_vitest_workspace_gone', {'package.json': pkg(DEV), 'vitest.config.ts': "import { defineWorkspace } from 'vitest/config';\nexport default defineWorkspace(['packages/*']);\n"})
case('kp_vitest_configdefaults', {'package.json': pkg(DEV), 'vitest.config.ts': "import { configDefaults, defineConfig } from 'vitest/config';\nexport default defineConfig({ test: { exclude: [...configDefaults.exclude, 'e2e/**'], include: ['test/**/*.test.ts'] } });\n"})
case('kp_vite_throws', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nconst x: any = undefined;\nexport default defineConfig({ test: { include: [x.y] } });\n"})
case('kp_vite_missing', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "});\n"}, links={'node_modules/vite': None})
case('kp_vite_missing_other', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nimport nope from 'not-installed-anywhere';\nexport default defineConfig({ plugins: [nope()],\n" + VT + "});\n"})
case('kp_vite_syntax', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({ test: { include: ['a' } });\n"})
case('kp_vite_js', {'package.json': pkg(DEV), 'vite.config.js': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "});\n"})
case('kp_vite_cts', {'package.json': pkg(DEV, {'type': 'commonjs'}), 'vite.config.cts': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "});\n"})
case('kp_unbuild', {'package.json': pkg(DEV), 'build.config.ts': "import { defineBuildConfig } from 'unbuild';\nexport default defineBuildConfig([{ entries: ['src/index'] }, null as any, { entries: ['src/orphan'] }]);\n"})
case('kp_unbuild_obj', {'package.json': pkg(DEV), 'build.config.ts': "import { defineBuildConfig } from 'unbuild'\nexport default defineBuildConfig({ entries: [{ input: 'src/orphan', name: 'o' }] })\n"})
case('kp_playwright', {'package.json': pkg(DEV), 'playwright.config.ts': "import { defineConfig } from '@playwright/test';\nexport default defineConfig({ testDir: './e2e', testMatch: '*.spec.ts' });\n"})
case('kp_playwright_merge', {'package.json': pkg(DEV), 'playwright.config.ts': "import { defineConfig } from '@playwright/test';\nexport default defineConfig({ testDir: './e2e' }, { testMatch: '*.spec.ts' });\n"})
case('kp_fake_vite_repo', {'package.json': pkg(['vite', 'vitest']), 'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "});\n",
    'node_modules/vite/package.json': json.dumps({'name': 'vite', 'version': '5.0.0', 'main': 'index.js'}), 'node_modules/vite/index.js': 'exports.defineConfig = c => ({ ...c, test: { include: ["e2e/**"] } });\n'}, links={'node_modules/vite': None})
# a monorepo: configs in each workspace, loaded by node processes side by side; -W and -D
WS = {'package.json': pkg(DEV, {'workspaces': ['packages/*'], 'private': True}, name='root'),
      'vitest.config.ts': "import { defineConfig } from 'vitest/config';\nexport default defineConfig({ test: { projects: ['packages/*'] } });\n"}
for i in range(6):
    WS[f'packages/p{i}/package.json'] = pkg(['vite', 'vitest'], name=f'p{i}')
    WS[f'packages/p{i}/src/index.ts'] = "export const x = 1;\nexport const y = 2;\n"
    WS[f'packages/p{i}/src/orphan.ts'] = 'export {};\n'
    WS[f'packages/p{i}/test/x.test.ts'] = "import '../src/index';\n"
    WS[f'packages/p{i}/vite.config.ts'] = ("import { defineConfig } from 'vite';\n" if i % 2 else "import { defineConfig, mergeConfig } from 'vite';\n") + \
        f"export default defineConfig({{ test: {{ include: ['test/**/*.test.ts'], name: 'p{i}' }} }});\n"
    WS[f'packages/p{i}/build.config.ts'] = "import { defineBuildConfig } from 'unbuild';\nexport default defineBuildConfig({ entries: ['src/index'] });\n"
case('kp_mono', WS, args=[[], ['-W', 'packages/p3'], ['--production'], ['--reporter', 'json'], ['-D', '../kp_mono', '-W', 'packages/p1']])
# round 2: a config imported by another (cached either way), large answers, output, import attributes
case('kp_reimport', {'package.json': pkg(DEV),
    'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({ resolve: { alias: { '@': '/src' } } });\n",
    'vitest.config.ts': "import { defineConfig, mergeConfig } from 'vitest/config';\nimport viteConfig from './vite.config';\nexport default mergeConfig(viteConfig, defineConfig({\n" + VT + "}));\n"})
case('kp_reimport_pure', {'package.json': pkg(DEV),
    'vite.config.ts': "import { defineConfig } from 'vite';\nexport default defineConfig({\n" + VT + "});\n",
    'vitest.config.ts': "import { defineConfig } from 'vitest/config';\nimport v from './vite.config';\nexport default defineConfig({ ...v, test: { ...v.test, include: ['test/**/*.ts'] } });\n"})
case('kp_big', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nconst many = Array.from({ length: 200000 }, (_, i) => `x${i}é`);\nexport default defineConfig({ define: { many } as any,\n" + VT + "});\n"})
case('kp_noisy', {'package.json': pkg(DEV), 'vite.config.ts': "import { defineConfig } from 'vite';\nfor (let i = 0; i < 20000; i++) console.log('noise ' + i + ' '.repeat(50));\nprocess.stderr.write('err noise\\n');\nexport default defineConfig({\n" + VT + "});\n"})
case('kp_attr_first', {'package.json': pkg(DEV), 'data.json': '{"inc": ["test/**/*.test.ts"]}\n',
    'vite.config.ts': "import data from './data.json' with { type: 'json' };\nimport { defineConfig } from 'vite';\nexport default defineConfig({ test: { include: data.inc } });\n"})
case('kp_after_code', {'package.json': pkg(DEV), 'vite.config.ts': "const inc = ['test/**/*.test.ts'];\nimport { defineConfig } from 'vite';\nexport default defineConfig({ test: { include: inc } });\n"})
case('kp_default_import', {'package.json': pkg(DEV), 'vite.config.ts': "import * as vite from 'vite';\nexport default vite.defineConfig({\n" + VT + "});\n"})
