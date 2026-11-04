#!/usr/bin/env node
// Makes a drop-in tool's npm packages from its release archives (packaging/tools/build.sh's), the way
// oxlint and esbuild ship: one package per platform holding the binary (os/cpu fields, so npm
// installs only the one that fits) and a main package with a Node launcher, the commands (the tool's
// and the original's: vlint and oxlint, vsc and shellcheck, vjq and jq, vknip and knip) and the
// platform packages as optionalDependencies.
//
//   node packaging/npm/make.mjs --tool vlint --version 0.1.0 --dist dist --out npm [--scope @vu0tran] [--allow-missing]
//
// writes npm/TOOL-linux-x64/, npm/TOOL-linux-arm64/, npm/TOOL-darwin-x64/, npm/TOOL-darwin-arm64/
// and npm/TOOL/ (publish them in that order: the main package names the others). Without
// --allow-missing every platform's archive must be in --dist. The Linux binaries are static, so
// their packages have no libc field: one binary serves glibc and musl.
// The tools are in TOOLS below; each has packaging/npm/TOOL/README.md (the main package's README).
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");

const PLATFORMS = [
  { name: "linux-x64", os: "linux", cpu: "x64", desc: "Linux x64 (static: glibc or musl)", sc: "linux.x86_64", jq: "linux-amd64" },
  { name: "linux-arm64", os: "linux", cpu: "arm64", desc: "Linux ARM64 (static: glibc or musl)", sc: "linux.aarch64", jq: "linux-arm64" },
  { name: "darwin-x64", os: "darwin", cpu: "x64", desc: "macOS on Intel (12 or later)", sc: "darwin.x86_64", jq: "macos-amd64" },
  { name: "darwin-arm64", os: "darwin", cpu: "arm64", desc: "macOS on Apple silicon (12 or later)", sc: "darwin.aarch64", jq: "macos-arm64" },
];
const repo = "https://github.com/vu0tran/vu";

// archive(version, platform): the archive's file name without the extension, and the name of the
// folder in it unless folder(version, platform) says otherwise
// launcher: the launcher template (one file per command, bin/COMMAND.js, unless `shared`, vlint's
// one file for both); extra: more files for the main package, from packaging/npm/TOOL/
const TOOLS = {
  vlint: {
    archive: (v, p) => `vlint-${v}-${p.name}`,
    ext: "tar.gz",
    dir: "ts",
    homepage: `${repo}/tree/main/ts#vlint-an-oxlint-compatible-linter-written-in-vu`,
    what: "vlint (an oxlint-compatible linter written in Vu)",
    description: "An oxlint-compatible linter written in Vu: oxlint's default rules, the same diagnostics",
    keywords: ["linter", "oxlint", "eslint", "javascript", "typescript", "vu"],
    commands: ["vlint", "oxlint"],
    launcher: { template: "vlint/bin/vlint.js", shared: "vlint.js" },
  },
  vsc: {
    archive: (v, p) => `vsc-v${v}.${p.sc}`,
    folder: (v) => `vsc-v${v}`,
    ext: "tar.xz",
    dir: "shellcheck",
    homepage: `${repo}/tree/main/shellcheck#readme`,
    what: "vsc (ShellCheck 0.11.0 written in Vu)",
    description: "ShellCheck 0.11.0 written in Vu: the same checks, options and output, byte for byte, with the shellcheck command",
    keywords: ["shellcheck", "shell", "bash", "sh", "lint", "linter", "vu"],
    commands: ["vsc", "shellcheck"],
    launcher: { template: "launcher.js" },
  },
  vjq: {
    archive: (v, p) => `vjq-${v}-${p.jq}`,
    ext: "tar.gz",
    dir: "jq",
    homepage: `${repo}/tree/main/jq#readme`,
    what: "vjq (jq 1.7.1 written in Vu)",
    description: "jq 1.7.1 written in Vu: the same language, options, output and messages, with the jq command",
    keywords: ["jq", "json", "cli", "query", "vu"],
    commands: ["vjq", "jq"],
    launcher: { template: "launcher.js" },
  },
  vknip: {
    archive: (v, p) => `vknip-${v}-${p.name}`,
    ext: "tar.gz",
    dir: "knip",
    homepage: `${repo}/tree/main/knip#readme`,
    what: "vknip (knip 6.44.1 written in Vu)",
    description: "knip 6.44.1 written in Vu: finds unused files, dependencies and exports, with knip's options, config and output",
    keywords: ["knip", "unused", "dependencies", "exports", "dead code", "lint", "vu"],
    commands: ["vknip", "knip"],
    launcher: { template: "launcher.js", jiti: true },
    // jiti loads JavaScript and TypeScript configs (knip depends on it too); the types and
    // `knip/config`'s defineConfig, so `import type { KnipConfig } from "knip"` and
    // `import { defineConfig } from "knip/config"` keep working; knip's JSON schema
    // (and yaml, knip's YAML parser, for the YAML configs vknip's own reader isn't sure about)
    dependencies: { jiti: "^2.7.0", yaml: "^2.9.1" },
    extra: ["index.mjs", "types.d.ts", "config.mjs", "config.d.ts", "schema.json", "schema-jsonc.json", "LICENSE.knip"],
    fields: {
      types: "./types.d.ts",
      exports: {
        ".": { types: "./types.d.ts", default: "./index.mjs" },
        "./config": { types: "./config.d.ts", default: "./config.mjs" },
        "./schema.json": "./schema.json",
        "./schema-jsonc.json": "./schema-jsonc.json",
        "./package.json": "./package.json",
      },
    },
  },
};

const opts = { scope: "@vu0tran", allowMissing: false };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === "--tool") opts.tool = argv[++i];
  else if (a === "--version") opts.version = argv[++i];
  else if (a === "--dist") opts.dist = argv[++i];
  else if (a === "--out") opts.out = argv[++i];
  else if (a === "--scope") opts.scope = argv[++i];
  else if (a === "--allow-missing") opts.allowMissing = true;
  else throw new Error(`make.mjs: unknown argument ${a}`);
}
if (!opts.tool || !opts.version || !opts.dist || !opts.out) {
  console.error(`usage: make.mjs --tool ${Object.keys(TOOLS).join("|")} --version X.Y.Z --dist DIR --out DIR [--scope @name] [--allow-missing]`);
  process.exit(2);
}
const tool = opts.tool;
const t = TOOLS[tool];
if (!t) throw new Error(`make.mjs: unknown tool ${tool} (${Object.keys(TOOLS).join(", ")})`);
const version = opts.version.replace(new RegExp(`^${tool}-`), "").replace(/^v/, "");
if (!/^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$/.test(version)) throw new Error(`make.mjs: '${version}' isn't a semver version`);
if (!/^@[a-z0-9][a-z0-9._-]*$/.test(opts.scope)) throw new Error(`make.mjs: '${opts.scope}' isn't an npm scope`);

const common = {
  version,
  license: "MIT",
  author: "vu0tran",
  homepage: t.homepage,
  bugs: `${repo}/issues`,
  repository: { type: "git", url: "git+https://github.com/vu0tran/vu.git", directory: t.dir },
};
const license = path.join(root, "LICENSE");
const own = path.join(here, tool);

function writeJson(file, obj) {
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + "\n");
}

fs.mkdirSync(opts.out, { recursive: true });
const made = [];
for (const p of PLATFORMS) {
  const folder = t.archive(version, p);
  const archive = path.join(opts.dist, `${folder}.${t.ext}`);
  if (!fs.existsSync(archive)) {
    if (opts.allowMissing) {
      console.error(`make.mjs: no ${archive}: no ${p.name} package`);
      continue;
    }
    throw new Error(`make.mjs: no ${archive}`);
  }
  const dir = path.join(opts.out, `${tool}-${p.name}`);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(path.join(dir, "bin"), { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), `${tool}-npm-`));
  execFileSync("tar", ["xf", path.resolve(archive), "-C", tmp]);
  const bin = path.join(dir, "bin", tool);
  fs.copyFileSync(path.join(tmp, t.folder ? t.folder(version, p) : folder, tool), bin);
  fs.chmodSync(bin, 0o755);
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.copyFileSync(license, path.join(dir, "LICENSE"));
  const name = `${opts.scope}/${tool}-${p.name}`;
  fs.writeFileSync(
    path.join(dir, "README.md"),
    `# ${name}\n\nThe ${tool} binary for ${p.desc}. Install [${opts.scope}/${tool}](https://www.npmjs.com/package/${opts.scope}/${tool}) instead: it picks this package when it fits.\n`,
  );
  writeJson(path.join(dir, "package.json"), {
    name,
    ...common,
    description: `${t.what} for ${p.desc}`,
    os: [p.os],
    cpu: [p.cpu],
    files: [`bin/${tool}`, "README.md", "LICENSE"],
    preferUnplugged: true,
    publishConfig: { access: "public" },
  });
  made.push({ name, dir });
}
if (made.length === 0) throw new Error("make.mjs: no platform packages");

const main = path.join(opts.out, tool);
fs.rmSync(main, { recursive: true, force: true });
fs.mkdirSync(path.join(main, "bin"), { recursive: true });
const template = fs.readFileSync(path.join(here, t.launcher.template), "utf8");
const fill = (src) =>
  src
    .replace(/^const TOOL = ".*";$/m, `const TOOL = ${JSON.stringify(tool)};`)
    .replace(/^const SCOPE = ".*";$/m, `const SCOPE = ${JSON.stringify(opts.scope)};`)
    .replace(/^const VERSION = ".*";$/m, `const VERSION = ${JSON.stringify(version)};`)
    .replace(/^const ENV = ".*";$/m, `const ENV = ${JSON.stringify(`${tool.toUpperCase()}_BINARY`)};`)
    .replace(/^const JITI = .*;$/m, `const JITI = ${t.launcher.jiti ? "true" : "false"};`);
const bins = {};
const files = [];
if (t.launcher.shared) {
  fs.writeFileSync(path.join(main, "bin", t.launcher.shared), fill(template), { mode: 0o755 });
  for (const c of t.commands) bins[c] = `bin/${t.launcher.shared}`;
  files.push(`bin/${t.launcher.shared}`);
} else {
  for (const c of t.commands) {
    fs.writeFileSync(path.join(main, "bin", `${c}.js`), fill(template), { mode: 0o755 });
    bins[c] = `bin/${c}.js`;
    files.push(`bin/${c}.js`);
  }
}
fs.writeFileSync(path.join(main, "README.md"), fs.readFileSync(path.join(own, "README.md"), "utf8").replaceAll("@vu0tran/", `${opts.scope}/`));
fs.copyFileSync(license, path.join(main, "LICENSE"));
for (const f of t.extra ?? []) {
  fs.copyFileSync(path.join(own, f), path.join(main, f));
  files.push(f);
}
const optionalDependencies = {};
for (const m of made) optionalDependencies[m.name] = version;
writeJson(path.join(main, "package.json"), {
  name: `${opts.scope}/${tool}`,
  ...common,
  description: t.description,
  keywords: t.keywords,
  bin: bins,
  files: [...files.filter((f) => f.startsWith("bin/")), "README.md", "LICENSE", ...files.filter((f) => !f.startsWith("bin/"))],
  ...(t.fields ?? {}),
  engines: { node: ">=18" },
  ...(t.dependencies ? { dependencies: t.dependencies } : {}),
  optionalDependencies,
  publishConfig: { access: "public" },
});
for (const m of made) console.log(m.dir);
console.log(main);
