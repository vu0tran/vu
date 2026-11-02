# Generated projects for configuration, workspaces and the command line: each case is
# {path: content}, with "__args__" the command lines to compare (default: no arguments) and
# "__links__" symlinks {path: target} (workspace packages in node_modules).
import json

def pkg(name="app", deps=None, dev=None, scripts=None, extra=None, peer=None):
    m = {"name": name, "version": "1.0.0"}
    if deps: m["dependencies"] = {d: "1" for d in deps}
    if dev: m["devDependencies"] = {d: "1" for d in dev}
    if peer: m["peerDependencies"] = {d: "1" for d in peer}
    if scripts: m["scripts"] = scripts
    if extra: m.update(extra)
    return json.dumps(m, indent=2) + "\n"

def mod(name, extra=None):  # an installed package
    m = {"name": name, "version": "1.0.0", "main": "index.js"}
    if extra: m.update(extra)
    return {f"node_modules/{name}/package.json": json.dumps(m), f"node_modules/{name}/index.js": "module.exports = {};\n"}

BASE_SRC = {
    "src/index.ts": "import { used } from './lib';\nimport x from 'dep-a';\nconsole.log(used, x);\n",
    "src/lib.ts": "export const used = 1;\nexport const unusedExport = 2;\nexport type UnusedType = string;\n",
    "src/orphan.ts": "export const o = 1;\n",
    "scripts/build.ts": "import 'dep-b';\nexport const b = 1;\n",
    "test/a.test.ts": "import { used } from '../src/lib';\nconsole.log(used);\n",
}

def base(**kw):
    files = dict(BASE_SRC)
    files["package.json"] = pkg(deps=["dep-a", "dep-unused"], dev=["dep-b", "dev-unused"], **kw)
    files.update(mod("dep-a")); files.update(mod("dep-b")); files.update(mod("dep-unused")); files.update(mod("dev-unused"))
    return files

CASES = {}

def case(name, files, args=None, links=None):
    files = dict(files)
    if args: files["__args__"] = args
    if links: files["__links__"] = links
    CASES[name] = files

# ---- configuration files

case("cfg_json", {**base(), "knip.json": json.dumps({"entry": ["src/index.ts", "scripts/*.ts"], "project": ["src/**/*.ts", "scripts/**/*.ts"]})})
case("cfg_jsonc", {**base(), "knip.jsonc": '{\n  // comment\n  "entry": ["src/index.ts"],\n  /* block */ "project": ["src/**"],\n}\n'})
case("cfg_dot_json", {**base(), ".knip.json": json.dumps({"entry": ["src/index.ts", "test/**/*.test.ts"], "ignore": ["scripts/**"]})})
case("cfg_dot_jsonc", {**base(), ".knip.jsonc": '{"entry": ["src/index.ts"], // x\n"ignoreDependencies": ["dep-unused"]}'})
case("cfg_pkg_field", {**base(extra={"knip": {"entry": ["src/index.ts", "scripts/build.ts"], "ignoreDependencies": ["dev-unused"]}})})
case("cfg_ts", {**base(), "knip.ts": "import type { KnipConfig } from 'knip';\nconst config: KnipConfig = {\n  entry: ['src/index.ts', 'scripts/build.ts'],\n  project: ['src/**/*.ts', 'scripts/**/*.ts'],\n  ignoreDependencies: [/^dev-/],\n};\nexport default config;\n"})
case("cfg_js_fn", {**base(), "knip.config.js": "export default async () => ({ entry: ['src/index.ts'], ignore: ['src/orphan.ts'] });\n"})
case("cfg_js_cjs", {**base(), "knip.js": "module.exports = { entry: ['src/index.ts', 'test/*.test.ts'], ignoreBinaries: ['foo'] };\n"})
case("cfg_config_ts", {**base(), "knip.config.ts": "export default { entry: ['src/index.ts'], project: ['src/**/*.ts'] } satisfies Record<string, unknown>;\n"})
case("cfg_merge_pkg", {**base(extra={"knip": {"ignore": ["src/orphan.ts"], "entry": ["x.ts"]}}), "knip.json": json.dumps({"entry": ["src/index.ts"]})})
case("cfg_custom_path", {**base(), "config/k.json": json.dumps({"entry": ["src/index.ts", "scripts/build.ts"]})}, args=[["--config", "config/k.json"], ["-c", "missing.json"]])
case("cfg_ignore_lists", {**base(scripts={"x": "foo --bar && baz"}), "src/u.ts": "import 'nope-unresolved/x';\nimport './missing';\nexport {};\n",
                          "knip.json": json.dumps({"entry": ["src/index.ts", "src/u.ts"], "ignoreDependencies": ["dep-unused", "dev-.*", "not-there"], "ignoreBinaries": ["foo", "unused-bin"], "ignoreUnresolved": ["./missing", "nothing"]})})
case("cfg_ignore_members", {"package.json": pkg(), "src/index.ts": "import { E, N } from './e';\nconsole.log(E.A, N.x);\n",
                            "src/e.ts": "export enum E { A, B, C, Keep }\nexport namespace N { export const x = 1; export const y = 2; export const KeepMe = 3; }\n",
                            "knip.json": json.dumps({"ignoreMembers": ["Keep", "Keep.*"]})})
case("cfg_include_entry_exports", {**base(extra={"main": "src/index.ts"}), "src/index.ts": "export const fromEntry = 1;\nimport { used } from './lib';\nconsole.log(used);\n",
                                   "knip.json": json.dumps({"includeEntryExports": True})})
case("cfg_paths", {"package.json": pkg(), "src/index.ts": "import { a } from '@lib/a';\nimport { b } from '~/b';\nconsole.log(a, b);\n", "lib/a.ts": "export const a = 1;\nexport const a2 = 2;\n",
                   "src/b.ts": "export const b = 1;\n", "knip.json": json.dumps({"paths": {"@lib/*": ["lib/*"], "~/*": ["src/*"]}})})
case("cfg_rules", {**base(), "knip.json": json.dumps({"rules": {"files": "warn", "exports": "off", "dependencies": "warn", "nope": "error"}})}, args=[[], ["--reporter", "markdown"]])
case("cfg_rules_all_warn", {**base(), "knip.json": json.dumps({"rules": {"files": "warn", "types": "warn", "exports": "warn", "dependencies": "warn", "devDependencies": "warn", "unlisted": "warn"}})})
case("cfg_include_exclude", {**base(), "knip.json": json.dumps({"exclude": ["types", "devDependencies"], "include": ["files", "exports", "types", "dependencies"]})})
case("cfg_exclude_bad", {**base(), "knip.json": json.dumps({"exclude": ["files", "badtype"]})})
case("cfg_ignore_unused_hint", {**base(), "knip.json": json.dumps({"ignore": ["src/orphan.ts", "nothing/**"], "ignoreFiles": ["scripts/build.ts", "nada.ts"]})})
case("cfg_ignore_issues", {**base(), "knip.json": json.dumps({"ignoreIssues": {"src/lib.ts": ["exports"], "package.json": ["dependencies"]}})})
case("cfg_entry_hints", {**base(), "knip.json": json.dumps({"entry": ["src/index.ts", "nomatch/*.ts", "src/lib.ts"], "project": ["src/**/*.ts", "nothing/**"]})})
case("cfg_production", {**base(scripts={"start": "node dist/start.js", "test": "node test/a.test.ts"}),
                        "knip.json": json.dumps({"entry": ["src/index.ts!", "scripts/build.ts", "test/**/*.test.ts"], "project": ["src/**/*.ts!", "scripts/**/*.ts", "test/**"]})},
     args=[[], ["--production"], ["--strict"], ["--production", "--include-entry-exports"]])
case("cfg_plugin_off", {"package.json": pkg(dev=["vitest", "mocha"]), "src/index.ts": "export {};\n", "src/a.test.ts": "import './h';\n", "src/h.ts": "export const h = 1;\n",
                        "test/m.js": "require('../src/index.ts');\n", **mod("vitest"), **mod("mocha"), "knip.json": json.dumps({"vitest": False, "mocha": {"entry": ["test/*.js"]}})})
case("cfg_plugin_entry", {"package.json": pkg(dev=["vitest"]), "src/index.ts": "export {};\n", "src/a.spec.ts": "import './h';\n", "src/h.ts": "export const h = 1;\n",
                          "e2e/x.e2e.ts": "export const z = 1;\n", **mod("vitest"), "knip.json": json.dumps({"vitest": {"entry": ["e2e/**/*.e2e.ts"]}})})
case("cfg_plugin_config_str", {"package.json": pkg(dev=["eslint"]), "src/index.ts": "export {};\n", "config/lint.json": json.dumps({"extends": ["plugin:foo/recommended"], "plugins": ["bar"]}),
                               **mod("eslint"), "knip.json": json.dumps({"eslint": "config/lint.json"})})
case("cfg_ignore_bins_regex", {"package.json": pkg(scripts={"a": "tool-one x", "b": "tool-two y", "c": "other z"}), "index.js": "", "knip.json": json.dumps({"ignoreBinaries": ["tool-.*"]})})
case("cfg_bad_type_cli", {**base()}, args=[["--include", "nope"], ["--exclude", "files,types"], ["--include", "nsExports"]])

# ---- the command line

cli_args = [[], ["--production"], ["--strict"], ["--dependencies"], ["--exports"], ["--files"], ["--include", "files,exports"], ["--exclude", "files"], ["--exclude", "dependencies"],
            ["--no-exit-code"], ["--max-issues", "100"], ["--max-issues", "3"], ["--reporter", "compact"], ["--reporter", "json"], ["--reporter", "markdown"], ["--reporter", "codeowners"],
            ["--reporter", "disclosure"], ["--max-show-issues", "1"], ["--treat-config-hints-as-errors"], ["--no-config-hints"], ["--include-entry-exports"], ["-n"], ["--no-progress"],
            ["--reporter", "compact", "--reporter", "json"], ["--tsConfig", "tsconfig.other.json"], ["--nope"], ["extra"], ["--max-issues", "x"], ["--version"], ["--include", "duplicates,enumMembers"]]
case("cli_basic", {**base(), "src/dup.ts": "const a = 1;\nexport { a, a as b };\nexport default a;\n", "src/en.ts": "export enum Q { A, B }\n", "src/index.ts": BASE_SRC["src/index.ts"] + "import { Q } from './en';\nimport { a } from './dup';\nconsole.log(Q.A, a);\n",
                   ".github/CODEOWNERS": "* @all\nsrc/ @src-team\n", "tsconfig.other.json": "{}"}, args=cli_args)
case("cli_dir", {"sub/package.json": pkg(), "sub/index.js": "require('./a');\n", "sub/a.js": "module.exports.x = 1;\n", "sub/b.js": ""}, args=[["--directory", "sub"], ["-D", "sub", "--reporter", "json"]])
case("cli_many_files", {"package.json": pkg(), "index.js": "", **{f"lib/f{i}.js": "" for i in range(30)}})

# ---- workspaces

def ws_files(manager):
    files = {
        "packages/a/package.json": pkg("@x/a", deps=["@x/b", "lodash", "unused-a"], extra={"main": "src/index.ts"}),
        "packages/a/src/index.ts": "import { b } from '@x/b';\nimport _ from 'lodash';\nimport c from '@x/c';\nimport 'unlisted-pkg';\nexport const a = b + 1;\nconsole.log(_, c);\n",
        "packages/a/src/unused.ts": "export const u = 1;\n",
        "packages/b/package.json": pkg("@x/b", dev=["unused-b"], extra={"main": "src/index.ts"}),
        "packages/b/src/index.ts": "export const b = 1;\nexport const notUsedB = 2;\n",
        "packages/c/package.json": pkg("@x/c", extra={"main": "index.js"}),
        "packages/c/index.js": "module.exports = 1;\n",
        "tools/x.ts": "export const x = 1;\n",
        **mod("lodash"), **mod("unused-a"), **mod("unused-b"),
    }
    links = {"node_modules/@x/a": "../../packages/a", "node_modules/@x/b": "../../packages/b", "node_modules/@x/c": "../../packages/c"}
    if manager == "pnpm":
        files["package.json"] = pkg("root", dev=["typescript", "root-unused"])
        files["pnpm-workspace.yaml"] = "packages:\n  - 'packages/*'\n"
    else:
        files["package.json"] = pkg("root", dev=["typescript", "root-unused"], extra={"workspaces": ["packages/*"], "private": True})
    files.update(mod("typescript")); files.update(mod("root-unused"))
    return files, links

f, l = ws_files("npm")
case("ws_npm", f, links=l, args=[[], ["--workspace", "packages/a"], ["-W", "@x/b"], ["--workspace", "@x/*", "--workspace", "!@x/c"], ["--production"], ["--strict"], ["--reporter", "json"], ["--workspace", "packages/b", "--strict"]])
f, l = ws_files("pnpm")
case("ws_pnpm", f, links=l)
f, l = ws_files("npm")
case("ws_config_map", {**f, "knip.json": json.dumps({"workspaces": {".": {"entry": ["tools/*.ts"]}, "packages/*": {"entry": ["src/index.ts"], "ignoreDependencies": ["unused-.*"]}, "packages/b": {"entry": ["src/*.ts"]}, "packages/gone": {}}})}, links=l)
f, l = ws_files("npm")
case("ws_top_level_entry", {**f, "knip.json": json.dumps({"entry": ["src/index.ts"], "ignoreWorkspaces": ["packages/c", "packages/nope"]})}, links=l)
f, l = ws_files("npm")
case("ws_no_links", f)
case("ws_nested_ancestor", {"package.json": pkg("root", deps=["shared-dep"], extra={"workspaces": ["apps/*", "apps/web/sub"]}), **mod("shared-dep"),
                            "apps/web/package.json": pkg("web"), "apps/web/index.ts": "import 'shared-dep';\nimport './sub/x';\n",
                            "apps/web/sub/package.json": pkg("web-sub"), "apps/web/sub/x.ts": "export const x = 1;\n", "apps/web/sub/index.ts": "import 'shared-dep';\n"})
case("ws_outdir", {"package.json": pkg("root", extra={"workspaces": ["packages/*"]}),
                   "packages/lib/package.json": pkg("lib", extra={"exports": {".": {"import": "./dist/index.js", "types": "./dist/index.d.ts"}, "./util": "./dist/util.js"}}),
                   "packages/lib/tsconfig.json": json.dumps({"compilerOptions": {"outDir": "dist", "rootDir": "src"}}),
                   "packages/lib/src/index.ts": "export const l = 1;\nexport const l2 = 2;\n", "packages/lib/src/util.ts": "export const u = 1;\n", "packages/lib/src/extra.ts": "export const e = 1;\n",
                   "packages/app/package.json": pkg("app", deps=["lib"]), "packages/app/index.ts": "import { l } from 'lib';\nimport { u } from 'lib/util';\nconsole.log(l, u);\n"},
     links={"node_modules/lib": "../packages/lib", "packages/app/node_modules/lib": "../../lib"})
case("ws_unlisted_ws_dep", {"package.json": pkg("root", extra={"workspaces": ["packages/*"]}),
                            "packages/p1/package.json": pkg("p1"), "packages/p1/index.ts": "import { v } from 'p2';\nconsole.log(v);\n",
                            "packages/p2/package.json": pkg("p2", extra={"main": "index.ts"}), "packages/p2/index.ts": "export const v = 1;\nexport const w = 2;\n"},
     links={"node_modules/p2": "../packages/p2", "node_modules/p1": "../packages/p1"})
case("ws_scripts_bins", {"package.json": pkg("root", dev=["tool"], extra={"workspaces": ["packages/*"]}), **mod("tool", {"bin": {"tool": "cli.js"}}),
                         "packages/p/package.json": pkg("p", scripts={"build": "tool build && missing-bin", "test": "node test.js"}), "packages/p/index.js": "", "packages/p/test.js": "require('./index.js');\n"})
