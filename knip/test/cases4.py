# Generated projects for plugins: config files in JSON, YAML and JavaScript/TypeScript (which knip
# and vknip both evaluate with Node.js), each read by its plugin.
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

case("pl_vite_ts", {
    "package.json": pkg(dev=["vite", "vitest", "jsdom", "@vitest/coverage-istanbul", "unused-dev", "@vitejs/plugin-react"]),
    **mods("vite", "vitest", "jsdom", "@vitest/coverage-istanbul", "unused-dev", "@vitejs/plugin-react"),
    "vite.config.ts": "import { defineConfig } from 'vite';\nexport default defineConfig({\n  resolve: { alias: { '@': '/src' } },\n  test: { environment: 'jsdom', setupFiles: ['./test/setup.ts'], include: ['test/**/*.check.ts'], coverage: { provider: 'istanbul' } },\n});\n",
    "index.html": "<!doctype html><html><body><script type=\"module\" src=\"/src/main.ts\"></script></body></html>\n",
    "src/main.ts": "import { x } from '@/lib';\nconsole.log(x);\n", "src/lib.ts": "export const x = 1;\nexport const y = 2;\n",
    "test/setup.ts": "export {};\n", "test/a.check.ts": "import '../src/lib';\n", "test/b.test.ts": "export {};\n",
})
case("pl_vitest_fn", {
    "package.json": pkg(dev=["vitest", "happy-dom"]), **mods("vitest", "happy-dom"),
    "vitest.config.mts": "export default ({ mode }) => ({ test: { environment: mode === 'production' ? 'node' : 'happy-dom', globalSetup: 'tests/global.ts' } });\n",
    "tests/global.ts": "export default () => {};\n", "src/a.spec.ts": "export {};\n", "src/orphan.ts": "export {};\n",
})
case("pl_vitest_projects", {
    "package.json": pkg(dev=["vitest"]), **mods("vitest"),
    "vitest.config.ts": "export default { test: { projects: ['packages/*', { test: { name: 'unit', setupFiles: ['./setup-unit.ts'] } }] } };\n",
    "setup-unit.ts": "export {};\n", "packages/p1/vitest.config.ts": "export default { test: { include: ['**/*.t.ts'] } };\n", "packages/p1/x.t.ts": "export {};\n", "packages/p1/y.ts": "export {};\n",
})
case("pl_jest_js", {
    "package.json": pkg(dev=["jest", "jest-environment-jsdom", "babel-jest", "identity-obj-proxy", "jest-junit", "unused-dev"]),
    **mods("jest", "jest-environment-jsdom", "babel-jest", "identity-obj-proxy", "jest-junit", "unused-dev"),
    "jest.config.js": "module.exports = {\n  testEnvironment: 'jsdom',\n  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],\n  moduleNameMapper: { '\\\\.css$': 'identity-obj-proxy', '^@/(.*)$': '<rootDir>/src/$1' },\n  transform: { '^.+\\\\.js$': 'babel-jest' },\n  reporters: ['default', 'jest-junit'],\n  testMatch: ['<rootDir>/specs/**/*.js'],\n};\n",
    "jest.setup.js": "", "specs/a.js": "require('../src/a');\n", "src/a.js": "module.exports = 1;\n", "src/__tests__/b.test.js": "", "src/__mocks__/m.js": "",
})
case("pl_jest_pkg", {
    "package.json": pkg(dev=["jest", "ts-jest"], extra={"jest": {"preset": "ts-jest", "setupFiles": ["./setup.ts"]}}), **mods("jest", "ts-jest"),
    "setup.ts": "export {};\n", "src/a.test.ts": "export {};\n", "src/b.ts": "export {};\n",
})
case("pl_eslint_legacy", {
    "package.json": pkg(dev=["eslint", "eslint-plugin-react", "@typescript-eslint/eslint-plugin", "@typescript-eslint/parser", "eslint-config-prettier", "eslint-plugin-prettier", "eslint-import-resolver-typescript", "unused-dev"]),
    **mods("eslint", "eslint-plugin-react", "@typescript-eslint/eslint-plugin", "@typescript-eslint/parser", "eslint-config-prettier", "eslint-plugin-prettier", "eslint-import-resolver-typescript", "unused-dev"),
    ".eslintrc.json": json.dumps({"extends": ["eslint:recommended", "plugin:react/recommended", "plugin:@typescript-eslint/recommended", "plugin:prettier/recommended"], "parser": "@typescript-eslint/parser", "plugins": ["react"], "settings": {"import/resolver": {"typescript": {}}}, "overrides": [{"files": ["*.js"], "extends": ["./config/extra.js"]}]}),
    "config/extra.js": "module.exports = {};\n", "index.js": "",
})
case("pl_eslint_yaml", {
    "package.json": pkg(dev=["eslint", "eslint-config-airbnb", "eslint-plugin-import"]), **mods("eslint", "eslint-config-airbnb", "eslint-plugin-import"),
    ".eslintrc.yml": "extends:\n  - airbnb\nplugins:\n  - import\n", "index.js": "",
})
case("pl_babel", {
    "package.json": pkg(dev=["@babel/core", "@babel/preset-env", "@babel/preset-typescript", "@babel/plugin-transform-runtime", "babel-plugin-macros", "@babel/runtime"]),
    **mods("@babel/core", "@babel/preset-env", "@babel/preset-typescript", "@babel/plugin-transform-runtime", "babel-plugin-macros", "@babel/runtime"),
    "babel.config.js": "module.exports = { presets: [['@babel/preset-env', { targets: 'node 18' }], '@babel/typescript'], plugins: ['@babel/plugin-transform-runtime', 'macros'] };\n", "index.js": "",
})
case("pl_postcss_tailwind", {
    "package.json": pkg(dev=["postcss", "tailwindcss", "autoprefixer", "cssnano"]), **mods("postcss", "tailwindcss", "autoprefixer", "cssnano"),
    "postcss.config.js": "module.exports = { plugins: { tailwindcss: {}, autoprefixer: {}, cssnano: false } };\n", "tailwind.config.js": "module.exports = {};\n", "index.js": "",
})
case("pl_commitlint", {
    "package.json": pkg(dev=["@commitlint/cli", "@commitlint/config-conventional", "commitlint-plugin-foo"]), **mods("@commitlint/cli", "@commitlint/config-conventional", "commitlint-plugin-foo"),
    "commitlint.config.js": "export default { extends: ['@commitlint/config-conventional'], plugins: ['foo'] };\n", "index.js": "",
})
case("pl_semantic_release", {
    "package.json": pkg(dev=["semantic-release", "@semantic-release/changelog", "@semantic-release/git", "@semantic-release/npm"]), **mods("semantic-release", "@semantic-release/changelog", "@semantic-release/git", "@semantic-release/npm"),
    ".releaserc": json.dumps({"plugins": ["@semantic-release/commit-analyzer", "@semantic-release/changelog", ["@semantic-release/git", {}], "@semantic-release/npm"]}), "index.js": "",
})
case("pl_changesets", {
    "package.json": pkg(dev=["@changesets/cli", "@changesets/changelog-github"]), **mods("@changesets/cli", "@changesets/changelog-github"),
    ".changeset/config.json": json.dumps({"$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json", "changelog": ["@changesets/changelog-github", {"repo": "a/b"}]}), "index.js": "",
})
case("pl_playwright", {
    "package.json": pkg(dev=["@playwright/test", "playwright-report-x"]), **mods("@playwright/test", "playwright-report-x"),
    "playwright.config.ts": "export default { testDir: './e2e', testMatch: '**/*.e2e.ts', reporter: [['list'], ['playwright-report-x']], globalSetup: './e2e/setup.ts', webServer: { command: 'node server.js' } };\n",
    "e2e/a.e2e.ts": "export {};\n", "e2e/setup.ts": "export {};\n", "e2e/b.spec.ts": "export {};\n", "server.js": "",
})
case("pl_prettier", {
    "package.json": pkg(dev=["prettier", "prettier-plugin-tailwindcss", "prettier-plugin-organize-imports"]), **mods("prettier", "prettier-plugin-tailwindcss", "prettier-plugin-organize-imports"),
    ".prettierrc": "plugins:\n  - prettier-plugin-tailwindcss\n", "index.js": "",
})
case("pl_stylelint", {
    "package.json": pkg(dev=["stylelint", "stylelint-config-standard", "stylelint-order"]), **mods("stylelint", "stylelint-config-standard", "stylelint-order"),
    ".stylelintrc.json": json.dumps({"extends": "stylelint-config-standard", "plugins": ["stylelint-order"]}), "index.js": "",
})
case("pl_tsup", {
    "package.json": pkg(dev=["tsup"], extra={"tsup": {"entry": ["src/cli.ts", "src/lib.ts"]}}), **mods("tsup"),
    "src/cli.ts": "export const c = 1;\n", "src/lib.ts": "export const l = 1;\n", "src/x.ts": "export const x = 1;\n",
})
case("pl_lint_staged", {
    "package.json": pkg(dev=["lint-staged", "eslint", "prettier"], extra={"lint-staged": {"*.ts": ["eslint --fix", "prettier --write"], "*.md": "markdownlint"}}), **mods("lint-staged", "eslint", "prettier"), "index.js": "",
})
case("pl_release_it", {
    "package.json": pkg(dev=["release-it", "@release-it/conventional-changelog"]), **mods("release-it", "@release-it/conventional-changelog"),
    ".release-it.json": json.dumps({"plugins": {"@release-it/conventional-changelog": {}}, "hooks": {"before:init": ["tsc --noEmit"]}}), "index.js": "",
})
case("pl_nx", {
    "package.json": pkg(dev=["nx", "@nx/js", "@nx/vite"]), **mods("nx", "@nx/js", "@nx/vite"),
    "nx.json": json.dumps({"plugins": ["@nx/vite/plugin"], "targetDefaults": {"@nx/js:tsc": {}}}),
    "libs/a/project.json": json.dumps({"targets": {"build": {"executor": "@nx/js:tsc"}, "x": {"command": "node tools/x.js"}}}), "tools/x.js": "", "index.js": "",
})
case("pl_config_load_error", {
    "package.json": pkg(dev=["vitest"]), **mods("vitest"),
    "vitest.config.ts": "import { nope } from 'not-installed-anywhere';\nexport default nope({});\n", "src/a.test.ts": "export {};\n",
})
case("pl_nested_ws_plugins", {
    "package.json": pkg("root", dev=["vitest", "eslint"], extra={"workspaces": ["packages/*"]}), **mods("vitest", "eslint"),
    "packages/x/package.json": pkg("x"), "packages/x/vitest.config.ts": "export default { test: { include: ['spec/*.ts'] } };\n", "packages/x/spec/a.ts": "export {};\n",
    "packages/x/index.ts": "export const z = 1;\n", "packages/x/b.test.ts": "export {};\n",
})
