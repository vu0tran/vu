# Generated projects for the plugins whose resolveConfig / resolveFromAST / resolve were ported in
# the third round (knip3): Next.js, webpack, Nuxt, the flat ESLint config's AST, Vite's babel
# options, and the smaller ones; each with a used and an unused file or dependency.
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

PROD = [[], ["--production"]]

case("p7_next_basic", {
    "package.json": pkg(deps=["next", "react"], dev=["@svgr/webpack", "unused-dev"]), **mods("next", "react", "@svgr/webpack", "unused-dev"),
    "next.config.js": "module.exports = { pageExtensions: ['page.tsx', 'ts'], turbopack: { rules: { '*.svg': { loaders: ['@svgr/webpack'], as: '*.js' } }, resolveAlias: { underscore: './src/lodash-shim.ts' } } };\n",
    "app/layout.page.tsx": "export default function L() { return null }\n", "app/page.page.tsx": "import { a } from '../lib/a';\nexport default function P() { return a }\n",
    "app/api/route.ts": "export const GET = 1;\n", "lib/a.ts": "export const a = 1;\nexport const b = 2;\n", "lib/orphan.ts": "export {};\n",
    "src/lodash-shim.ts": "export const x = 1;\n", "middleware.ts": "export function middleware() {}\n", "pages/old.tsx": "export {};\n",
}, PROD)
case("p7_next_fn_src", {
    "package.json": pkg(deps=["next"]), **mods("next"),
    "next.config.mjs": "export default (phase, { defaultConfig }) => ({ pageExtensions: phase === 'phase-production-build' ? ['tsx'] : ['jsx'] });\n",
    "src/app/page.tsx": "export default function P() { return null }\n", "src/app/x.jsx": "export {};\n", "src/pages/index.tsx": "export {};\n",
})
case("p7_next_load_error", {
    "package.json": pkg(deps=["next", "nonexistent-pkg"]), **mods("next"),
    "next.config.ts": "import x from 'nonexistent-pkg';\nexport default { pageExtensions: ['tsx'], turbopack: { resolveAlias: { a: { browser: './shim.ts' } } }, x };\n",
    "app/page.tsx": "export default 1;\n", "shim.ts": "export {};\n", "app/z.ts": "export {};\n",
})
case("p7_webpack", {
    "package.json": pkg(dev=["webpack", "webpack-cli", "babel-loader", "@babel/preset-env", "css-loader", "style-loader", "ts-loader", "lodash", "unused-dev", "ts-node"]),
    **mods("webpack", "webpack-cli", "babel-loader", "@babel/preset-env", "css-loader", "style-loader", "ts-loader", "lodash", "unused-dev", "ts-node"),
    "webpack.config.js": "const path = require('path');\nmodule.exports = (env, argv) => ({\n  entry: { main: './src/main.js', admin: ['./src/admin.js'] },\n  module: { rules: [\n    { test: /\\.js$/, use: { loader: 'babel-loader', options: { presets: ['@babel/preset-env'] } } },\n    { test: /\\.css$/, use: ['style-loader', 'css-loader?modules'] },\n    { test: /\\.ts$/, loader: 'ts-loader' },\n  ] },\n  resolve: { alias: { '@lib': path.resolve(__dirname, 'src/lib') } },\n});\n",
    "src/main.js": "import { x } from '@lib/x';\nconsole.log(x);\n", "src/admin.js": "", "src/lib/x.js": "export const x = 1;\nexport const y = 2;\n", "src/orphan.js": "",
}, PROD)
case("p7_webpack_ts_context", {
    "package.json": pkg(dev=["webpack", "ts-node"]), **mods("webpack", "ts-node"),
    "webpack.config.ts": "import * as path from 'path';\nexport default { context: path.resolve(__dirname, 'app') };\n",
    "app/src/index.ts": "export {};\n", "app/other.ts": "export {};\n",
})
case("p7_nuxt", {
    "package.json": pkg(deps=["nuxt", "@nuxt/ui", "vue"], dev=["unused-dev"]), **mods("nuxt", "@nuxt/ui", "vue", "unused-dev"),
    "nuxt.config.ts": "export default defineNuxtConfig({ modules: ['@nuxt/ui', './modules/local'], css: ['~/assets/main.css'], alias: { '@utils': './utils' } });\n",
    "app/app.vue": "<script setup lang=\"ts\">\nimport { u } from '@utils/u';\nconsole.log(u);\n</script>\n<template><div/></template>\n",
    "app/pages/index.vue": "<template><div/></template>\n", "app/assets/main.css": "", "modules/local.ts": "export default {};\n",
    "utils/u.ts": "export const u = 1;\nexport const v = 2;\n", "utils/orphan.ts": "export {};\n", "server/api/hello.ts": "export default 1;\n",
    "shared/s.ts": "export const s = 1;\n", "components/C.vue": "<template><div/></template>\n",
}, PROD)
case("p7_eslint_flat", {
    "package.json": pkg(dev=["eslint", "eslint-import-resolver-typescript", "eslint-import-resolver-webpack", "@typescript-eslint/parser", "unused-dev"]),
    **mods("eslint", "eslint-import-resolver-typescript", "eslint-import-resolver-webpack", "@typescript-eslint/parser", "unused-dev"),
    "eslint.config.js": "export default [{ settings: { 'import/resolver': { webpack: {}, node: {} } }, languageOptions: { parserOptions: { parser: '@typescript-eslint/parser' } } }];\n",
    "index.js": "",
})
case("p7_vite_babel", {
    "package.json": pkg(dev=["vite", "@vitejs/plugin-react", "babel-plugin-styled-components", "@babel/preset-flow", "unused-dev"]),
    **mods("vite", "@vitejs/plugin-react", "babel-plugin-styled-components", "@babel/preset-flow", "unused-dev"),
    "vite.config.ts": "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\nexport default defineConfig({ plugins: [react({ babel: { plugins: ['babel-plugin-styled-components'], presets: [['@babel/preset-flow', {}]] } })] });\n",
    "index.html": "<script type=\"module\" src=\"./src/main.ts\"></script>\n", "src/main.ts": "export {};\n",
})
case("p7_small", {
    "package.json": pkg(deps=["@tanstack/react-router", "drizzle-orm", "react-native", "my-rn-lib", "oclif", "@oclif/plugin-help", "msw"], dev=["@swc/core", "@swc/plugin-emotion", "@swc/helpers", "drizzle-kit", "wrangler", "@svgr/cli", "@svgr/plugin-jsx", "unused-dev"], extra={"msw": {"workerDirectory": ["public"]}, "oclif": {"plugins": ["@oclif/plugin-help"]}}),
    **mods("@tanstack/react-router", "drizzle-orm", "react-native", "my-rn-lib", "oclif", "@oclif/plugin-help", "msw", "@swc/core", "@swc/plugin-emotion", "@swc/helpers", "drizzle-kit", "wrangler", "@svgr/cli", "@svgr/plugin-jsx", "unused-dev"),
    ".swcrc": json.dumps({"jsc": {"experimental": {"plugins": [["@swc/plugin-emotion", {}]]}, "externalHelpers": True}}),
    "tsr.config.json": json.dumps({"generatedRouteTree": "./src/gen/routes.ts"}),
    "src/gen/routes.ts": "export {};\n", "src/router.tsx": "export {};\n",
    "drizzle.config.ts": "export default { schema: './db/schema.ts' };\n", "db/schema.ts": "export const t = 1;\n", "db/orphan.ts": "export {};\n",
    "wrangler.toml": "name = \"w\"\nmain = \"worker/index.ts\"\n[vars]\nA = \"1\"\n", "worker/index.ts": "export default {};\n",
    ".svgrrc": json.dumps({"plugins": ["@svgr/plugin-jsx"]}),
    "react-native.config.js": "module.exports = { dependencies: { 'my-rn-lib': {} } };\n",
    "public/mockServiceWorker.js": "", "commands/hello.ts": "export default 1;\n",
}, PROD)
case("p7_prisma_metro", {
    "package.json": pkg(deps=["prisma", "@prisma/client", "metro", "react-native-svg-transformer", "unused-dep"], dev=["tsx"]), **mods("prisma", "@prisma/client", "metro", "react-native-svg-transformer", "unused-dep", "tsx"),
    "prisma.config.ts": "export default { schema: 'db', migrations: { seed: 'tsx db/seed.ts' } };\n",
    "db/a.prisma": "generator client { provider = \"prisma-client-js\" }\n", "db/seed.ts": "export {};\n",
    "metro.config.js": "module.exports = { transformer: { babelTransformerPath: require.resolve('react-native-svg-transformer') }, resolver: { sourceExts: ['ts', 'svg'] } };\n",
    "src/app.ios.ts": "export {};\n", "src/app.ts": "export {};\n",
})
case("p7_biome_nitro_icons", {
    "package.json": pkg(deps=["nitropack", "unplugin-icons"], dev=["@biomejs/biome", "@iconify-json/mdi", "biome-shared"]), **mods("nitropack", "unplugin-icons", "@biomejs/biome", "@iconify-json/mdi", "biome-shared"),
    "biome.json": json.dumps({"extends": ["biome-shared/biome.json"]}),
    "nitro.config.ts": "export default defineNitroConfig({ srcDir: 'server', routesDir: 'r' });\n",
    "server/r/a.ts": "import '#nitro-internal-virtual/x';\nimport Icon from '~icons/mdi/home';\nexport default Icon;\n", "server/api/b.ts": "export default 1;\n", "server/x.ts": "export {};\n",
})
case("p7_external_reexport", {
    "package.json": pkg(dev=["prettier", "@acme/prettier-config", "prettier-plugin-x"]), **mods("prettier", "@acme/prettier-config", "prettier-plugin-x"),
    "prettier.config.mjs": "export { default } from '@acme/prettier-config';\n",
    "node_modules/@acme/prettier-config/index.js": "module.exports = { plugins: ['prettier-plugin-x'] };\n",
})
case("p7_prettier_transitive", {
    "package.json": pkg(dev=["prettier", "@acme/prettier-config", "prettier-plugin-x", "prettier-plugin-y"]), **mods("prettier", "@acme/prettier-config", "prettier-plugin-x", "prettier-plugin-y"),
    "prettier.config.mjs": "import base from '@acme/prettier-config';\nexport default { ...base, plugins: [...base.plugins, 'prettier-plugin-y'] };\n",
    "node_modules/@acme/prettier-config/index.js": "module.exports = { plugins: ['prettier-plugin-x'] };\n",
})
case("p7_github_action", {
    "package.json": pkg(), "action.yml": "name: a\nruns:\n  using: node20\n  main: dist/index.js\n  pre: src/pre.js\n",
    "src/pre.js": "", "src/index.ts": "export {};\n", "src/orphan.ts": "export {};\n",
})

case("p7_expo", {
    "package.json": pkg(deps=["expo", "expo-router", "expo-dev-client", "react-native-web", "react-dom", "expo-updates", "expo-camera", "expo-system-ui", "unused-dep"], extra={"main": "expo-router/entry"}),
    **mods("expo", "expo-router", "expo-dev-client", "react-native-web", "react-dom", "expo-updates", "expo-camera", "expo-system-ui", "unused-dep"),
    "app.config.ts": "export default ({ config }) => ({ ...config, platforms: ['ios', 'web'], backgroundColor: '#fff', plugins: ['expo-camera', ['expo-router', { root: './src/routes' }], './plugins/local.js'] });\n",
    "src/routes/index.tsx": "export default 1;\n", "app/old.tsx": "export {};\n", "plugins/local.js": "module.exports = () => {};\n",
}, PROD)
case("p7_expo_json", {
    "package.json": pkg(deps=["expo", "expo-notifications", "@expo/metro-runtime", "react-native-web", "react-dom"]), **mods("expo", "expo-notifications", "@expo/metro-runtime", "react-native-web", "react-dom"),
    "app.json": json.dumps({"expo": {"platforms": ["web"], "notification": {}, "updates": {"enabled": False}}}),
})
case("p7_rspack", {
    "package.json": pkg(dev=["@rspack/core", "@rspack/cli", "sass-loader"]), **mods("@rspack/core", "@rspack/cli", "sass-loader"),
    "rspack.config.mjs": "export default { entry: './src/main.js', module: { rules: [{ test: /\\.jsx$/, use: { loader: 'builtin:swc-loader' } }, { test: /\\.s[ac]ss$/, loader: 'sass-loader' }] } };\n",
    "src/main.js": "", "src/other.js": "",
})
case("p7_codegen", {
    "package.json": pkg(dev=["@graphql-codegen/cli", "@graphql-codegen/typescript", "@graphql-codegen/typescript-operations", "@graphql-codegen/client-preset", "@graphql-codegen/near-operation-file-preset", "unused-dev"]),
    **mods("@graphql-codegen/cli", "@graphql-codegen/typescript", "@graphql-codegen/typescript-operations", "@graphql-codegen/client-preset", "@graphql-codegen/near-operation-file-preset", "unused-dev"),
    "codegen.ts": "export default { schema: 'schema.graphql', generates: { 'src/gql/': { preset: 'client' }, 'src/types.ts': { plugins: ['typescript', 'typescript-operations'] }, 'src/': { preset: 'near-operation-file', presetConfig: { extension: '.gen.ts', baseTypesPath: 'types.ts' }, plugins: ['./local-plugin.js'] } } };\n",
    "src/gql/index.ts": "export const g = 1;\n", "src/types.ts": "export type T = 1;\n", "src/a/q.gen.ts": "export const q = 1;\n", "local-plugin.js": "", "src/other.ts": "export {};\n",
}, PROD)
case("p7_knex_pm2_karma", {
    "package.json": pkg(deps=["knex", "pg", "sqlite3", "pm2"], dev=["karma", "karma-jasmine", "karma-chrome-launcher", "jasmine-core", "unused-dev"]),
    **mods("knex", "pg", "sqlite3", "pm2", "karma", "karma-jasmine", "karma-chrome-launcher", "jasmine-core", "unused-dev"),
    "knexfile.js": "module.exports = { development: { client: 'sqlite3', migrations: { directory: './db/migrations' } }, production: { client: 'pg', seeds: { directory: ['./db/seeds'] } } };\n",
    "db/migrations/001.js": "", "db/seeds/s.ts": "export {};\n", "db/other.js": "",
    "ecosystem.config.js": "module.exports = { apps: [{ name: 'a', script: './server/app.js' }, { name: 'b', script: 'npm' }] };\n", "server/app.js": "", "server/x.js": "",
    "karma.conf.js": "module.exports = (config) => config.set({ frameworks: ['jasmine'], files: ['test/**/*.spec.js', { pattern: 'test/fixtures/*.js' }], exclude: ['test/skip.spec.js'] });\n",
    "test/a.spec.js": "", "test/skip.spec.js": "", "test/fixtures/f.js": "", "test/helper.js": "",
})
case("p7_pwa", {
    "package.json": pkg(dev=["vite", "vite-plugin-pwa"]), **mods("vite", "vite-plugin-pwa"),
    "vite.config.ts": "import { VitePWA } from 'vite-plugin-pwa';\nexport default { plugins: [VitePWA({ strategies: 'injectManifest', srcDir: 'src', filename: 'my-sw.ts' })] };\n",
    "src/my-sw.ts": "export {};\n", "src/x.ts": "export {};\n",
})
case("p7_mdx_tsconfig", {
    "package.json": pkg(dev=["astro", "remark-gfm", "remark-toc", "unused-dev"]), **mods("astro", "remark-gfm", "remark-toc", "unused-dev"),
    "tsconfig.json": json.dumps({"compilerOptions": {}, "mdx": {"plugins": ["remark-gfm", ["remark-toc", {}]]}}),
    "src/pages/index.astro": "---\n---\n<div/>\n",
})

case("p7_sveltekit", {
    "package.json": pkg(dev=["@sveltejs/kit", "svelte", "vite"]), **mods("@sveltejs/kit", "svelte", "vite"),
    "svelte.config.js": "export default { kit: { files: { lib: 'src/library' } } };\n",
    "src/routes/+page.svelte": "<script>\nimport { x } from '$lib/x';\nimport { env } from '$env/static/public';\nimport { goto } from '$app/navigation';\n</script>\n",
    "src/routes/about/+page.ts": "export const load = () => ({});\n", "src/library/x.ts": "export const x = 1;\nexport const y = 2;\n", "src/hooks.server.ts": "export {};\n", "src/other.ts": "export {};\n",
}, PROD)
case("p7_sveltekit_vite", {
    "package.json": pkg(dev=["@sveltejs/kit", "vite"]), **mods("@sveltejs/kit", "vite"),
    "vite.config.ts": "import { sveltekit } from '@sveltejs/kit/vite';\nexport default { plugins: [sveltekit({ files: { lib: 'src/l' } })] };\n",
    "svelte.config.js": "export default {};\n", "src/routes/+layout.ts": "import '$lib/a';\n", "src/l/a.ts": "export {};\n", "src/lib/b.ts": "export {};\n",
})
case("p7_stryker_tauri_buf_orval", {
    "package.json": pkg(dev=["@stryker-mutator/core", "@stryker-mutator/jest-runner", "@stryker-mutator/typescript-checker", "@tauri-apps/cli", "@bufbuild/buf", "@bufbuild/protoc-gen-es", "orval", "unused-dev"], scripts={"x": "echo"}),
    **mods("@stryker-mutator/core", "@stryker-mutator/jest-runner", "@stryker-mutator/typescript-checker", "@tauri-apps/cli", "@bufbuild/buf", "@bufbuild/protoc-gen-es", "orval", "unused-dev"),
    "node_modules/@bufbuild/protoc-gen-es/package.json": json.dumps({"name": "@bufbuild/protoc-gen-es", "version": "1.0.0", "bin": {"protoc-gen-es": "bin.js"}}),
    "stryker.config.json": json.dumps({"testRunner": "jest", "checkers": ["typescript"]}),
    "src-tauri/tauri.conf.json": json.dumps({"build": {"beforeDevCommand": "node scripts/dev.js", "beforeBuildCommand": {"script": "node build.js", "cwd": "tools"}}}),
    "scripts/dev.js": "", "tools/build.js": "", "scripts/other.js": "",
    "buf.gen.yaml": "version: v2\nplugins:\n  - local: protoc-gen-es\n    out: gen\n",
    "orval.config.ts": "export default { api: { input: './spec.yaml', output: { target: './src/api.ts', override: { transformer: './src/transform.ts' } } } };\n",
    "src/transform.ts": "export default 1;\n", "src/x.ts": "export {};\n",
})
case("p7_react_router", {
    "package.json": pkg(deps=["@react-router/dev", "@react-router/node", "isbot", "react-router"]), **mods("@react-router/dev", "@react-router/node", "isbot", "react-router"),
    "react-router.config.ts": "export default { appDirectory: 'web' };\n",
    "web/routes.ts": "export default [{ file: 'routes/home.tsx' }, { file: 'routes/parent.tsx', children: [{ file: 'routes/child.tsx' }] }];\n",
    "web/root.tsx": "export default 1;\n", "web/routes/home.tsx": "export default 1;\n", "web/routes/parent.tsx": "export default 1;\n", "web/routes/child.tsx": "export default 1;\n", "web/routes/unused.tsx": "export default 1;\n",
}, PROD)

case("p7_vite_plus_laravel", {
    "package.json": pkg(dev=["vite", "vite-plus", "laravel-vite-plugin", "tsx", "eslint"]), **mods("vite", "vite-plus", "laravel-vite-plugin", "tsx", "eslint"),
    "vite.config.ts": "import laravel from 'laravel-vite-plugin';\nexport default { plugins: [laravel({ input: ['resources/js/app.ts'], ssr: 'resources/js/ssr.ts' })], run: { tasks: { gen: { command: 'tsx scripts/gen.ts' } } }, staged: { '*.ts': 'eslint --fix' } };\n",
    "resources/js/app.ts": "export {};\n", "resources/js/ssr.ts": "export {};\n", "resources/js/other.ts": "export {};\n", "scripts/gen.ts": "export {};\n",
}, PROD)
case("p7_cucumber_rsbuild", {
    "package.json": pkg(dev=["@cucumber/cucumber", "@rsbuild/core", "cucumber-html-formatter", "less-loader", "unused-dev"]), **mods("@cucumber/cucumber", "@rsbuild/core", "cucumber-html-formatter", "less-loader", "unused-dev"),
    "cucumber.json": json.dumps({"default": {"import": ["steps/**/*.ts"], "format": ["cucumber-html-formatter:out.html", "progress"]}}),
    "steps/a.ts": "export {};\n", "features/x.js": "",
    "rsbuild.config.ts": "export default { source: { entry: { index: './src/index.ts', admin: ['./src/admin.ts'] } }, resolve: { alias: { '@': './src' } }, tools: { rspack: (config) => { config.module.rules.push({ test: /\\.less$/, loader: 'less-loader' }); return config; } } };\n",
    "src/index.ts": "import { u } from '@/u';\nconsole.log(u);\n", "src/admin.ts": "export {};\n", "src/u.ts": "export const u = 1;\nexport const w = 2;\n", "src/other.ts": "export {};\n",
}, PROD)
case("p7_cz_mdlint_convex_cspell_nextmdx", {
    "package.json": pkg(deps=["next", "@next/mdx", "convex", "remark-gfm"], dev=["commitizen", "cz-conventional-changelog", "markdownlint-cli", "markdownlint-rule-x", "cspell", "@cspell/dict-de", "unused-dev"], scripts={"lint:md": "markdownlint --rules markdownlint-rule-x ."}, extra={"config": {"commitizen": {"path": "cz-conventional-changelog"}}}),
    **mods("next", "@next/mdx", "convex", "remark-gfm", "commitizen", "cz-conventional-changelog", "markdownlint-cli", "markdownlint-rule-x", "cspell", "@cspell/dict-de", "unused-dev"),
    ".markdownlint.json": json.dumps({"default": True}), "cspell.json": json.dumps({"import": ["@cspell/dict-de/cspell-ext.json"]}),
    "convex.json": json.dumps({"functions": "backend/"}), "backend/f.ts": "export {};\n", "convex/old.ts": "export {};\n",
    "next.config.mjs": "import createMDX from '@next/mdx';\nconst withMDX = createMDX({ options: { remarkPlugins: ['remark-gfm'] } });\nexport default withMDX({});\n",
    "mdx-components.tsx": "export function useMDXComponents() {}\n", "app/page.tsx": "export default 1;\n",
})
