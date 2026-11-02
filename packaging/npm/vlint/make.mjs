#!/usr/bin/env node
// Makes vlint's npm packages from the release archives (packaging/tools/build.sh's), the way oxlint
// ships: one package per platform holding the binary (os/cpu fields, so npm installs only the one
// that fits) and a main package with the launcher, the `vlint` and `oxlint` commands and the
// platform packages as optionalDependencies.
//
//   node packaging/npm/vlint/make.mjs --version 0.1.0 --dist dist --out npm [--scope @vu0tran] [--allow-missing]
//
// writes npm/vlint-linux-x64/, npm/vlint-linux-arm64/, npm/vlint-darwin-x64/, npm/vlint-darwin-arm64/
// and npm/vlint/ (publish them in that order). Without --allow-missing every platform's archive must
// be in --dist. The Linux binaries are static, so their packages have no libc field: one binary
// serves glibc and musl.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..", "..");
const opts = { scope: "@vu0tran", allowMissing: false };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === "--version") opts.version = argv[++i];
  else if (a === "--dist") opts.dist = argv[++i];
  else if (a === "--out") opts.out = argv[++i];
  else if (a === "--scope") opts.scope = argv[++i];
  else if (a === "--allow-missing") opts.allowMissing = true;
  else throw new Error(`make.mjs: unknown argument ${a}`);
}
if (!opts.version || !opts.dist || !opts.out) {
  console.error("usage: make.mjs --version X.Y.Z --dist DIR --out DIR [--scope @name] [--allow-missing]");
  process.exit(2);
}
const version = opts.version.replace(/^vlint-/, "").replace(/^v/, "");
if (!/^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$/.test(version)) throw new Error(`make.mjs: '${version}' isn't a semver version`);
if (!/^@[a-z0-9][a-z0-9._-]*$/.test(opts.scope)) throw new Error(`make.mjs: '${opts.scope}' isn't an npm scope`);

const platforms = [
  { name: "linux-x64", os: "linux", cpu: "x64", desc: "Linux x64 (static: glibc or musl)" },
  { name: "linux-arm64", os: "linux", cpu: "arm64", desc: "Linux ARM64 (static: glibc or musl)" },
  { name: "darwin-x64", os: "darwin", cpu: "x64", desc: "macOS on Intel (12 or later)" },
  { name: "darwin-arm64", os: "darwin", cpu: "arm64", desc: "macOS on Apple silicon (12 or later)" },
];
const repository = { type: "git", url: "git+https://github.com/vu0tran/vu.git", directory: "ts" };
const common = {
  version,
  license: "MIT",
  author: "vu0tran",
  homepage: "https://github.com/vu0tran/vu/tree/main/ts#vlint-an-oxlint-compatible-linter-written-in-vu",
  bugs: "https://github.com/vu0tran/vu/issues",
  repository,
};
const license = path.join(root, "LICENSE");

function writeJson(file, obj) {
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + "\n");
}

fs.mkdirSync(opts.out, { recursive: true });
const made = [];
for (const p of platforms) {
  const archive = path.join(opts.dist, `vlint-${version}-${p.name}.tar.gz`);
  if (!fs.existsSync(archive)) {
    if (opts.allowMissing) {
      console.error(`make.mjs: no ${archive}: no ${p.name} package`);
      continue;
    }
    throw new Error(`make.mjs: no ${archive}`);
  }
  const dir = path.join(opts.out, `vlint-${p.name}`);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(path.join(dir, "bin"), { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "vlint-npm-"));
  execFileSync("tar", ["xzf", path.resolve(archive), "-C", tmp]);
  const bin = path.join(dir, "bin", "vlint");
  fs.copyFileSync(path.join(tmp, `vlint-${version}-${p.name}`, "vlint"), bin);
  fs.chmodSync(bin, 0o755);
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.copyFileSync(license, path.join(dir, "LICENSE"));
  const name = `${opts.scope}/vlint-${p.name}`;
  fs.writeFileSync(
    path.join(dir, "README.md"),
    `# ${name}\n\nThe vlint binary for ${p.desc}. Install [${opts.scope}/vlint](https://www.npmjs.com/package/${opts.scope}/vlint) instead: it picks this package when it fits.\n`,
  );
  writeJson(path.join(dir, "package.json"), {
    name,
    ...common,
    description: `vlint (an oxlint-compatible linter written in Vu) for ${p.desc}`,
    os: [p.os],
    cpu: [p.cpu],
    files: ["bin/vlint", "README.md", "LICENSE"],
    preferUnplugged: true,
    publishConfig: { access: "public" },
  });
  made.push({ name, dir });
}
if (made.length === 0) throw new Error("make.mjs: no platform packages");

const main = path.join(opts.out, "vlint");
fs.rmSync(main, { recursive: true, force: true });
fs.mkdirSync(path.join(main, "bin"), { recursive: true });
let launcher = fs.readFileSync(path.join(here, "bin", "vlint.js"), "utf8");
launcher = launcher
  .replace(/^const SCOPE = ".*";$/m, `const SCOPE = ${JSON.stringify(opts.scope)};`)
  .replace(/^const VERSION = ".*";$/m, `const VERSION = ${JSON.stringify(version)};`);
fs.writeFileSync(path.join(main, "bin", "vlint.js"), launcher, { mode: 0o755 });
fs.writeFileSync(path.join(main, "README.md"), fs.readFileSync(path.join(here, "README.md"), "utf8").replaceAll("@vu0tran/", `${opts.scope}/`));
fs.copyFileSync(license, path.join(main, "LICENSE"));
const optionalDependencies = {};
for (const m of made) optionalDependencies[m.name] = version;
writeJson(path.join(main, "package.json"), {
  name: `${opts.scope}/vlint`,
  ...common,
  description: "An oxlint-compatible linter written in Vu: oxlint's default rules, the same diagnostics",
  keywords: ["linter", "oxlint", "eslint", "javascript", "typescript", "vu"],
  bin: { vlint: "bin/vlint.js", oxlint: "bin/vlint.js" },
  files: ["bin/vlint.js", "README.md", "LICENSE"],
  engines: { node: ">=18" },
  optionalDependencies,
  publishConfig: { access: "public" },
});
for (const m of made) console.log(m.dir);
console.log(main);
