#!/usr/bin/env node
// The launcher of a drop-in tool's npm package (vsc, vjq, vknip): runs the native binary from the
// platform package npm installed with it (one of the optionalDependencies, picked by their os/cpu
// fields), as oxlint's and esbuild's launchers do. make.mjs writes it once per command, named after
// it (bin/vsc.js and bin/shellcheck.js, bin/vjq.js and bin/jq.js, bin/vknip.js and bin/knip.js), and
// fills in the constants; the binary gets the command's name as argv[0], so its messages name the
// program as the original's do (jq's and ShellCheck's use argv[0]). The name comes from this file's,
// not from process.argv[1], which pnpm's and yarn's shims don't set to the command.
"use strict";
const { spawnSync } = require("node:child_process");
const path = require("node:path");

const TOOL = "tool";
const SCOPE = "@vu0tran";
const VERSION = "0.0.0";
const ENV = "TOOL_BINARY";
const JITI = false;
const PLATFORMS = ["linux-x64", "linux-arm64", "darwin-x64", "darwin-arm64"];

function die(msg) {
  process.stderr.write(`${TOOL}: ${msg}\n`);
  process.exit(2);
}

function binary() {
  if (process.env[ENV]) return process.env[ENV];
  const key = `${process.platform}-${process.arch}`;
  if (!PLATFORMS.includes(key)) {
    die(`there's no ${TOOL} binary for ${key} (there are: ${PLATFORMS.join(", ")}); ${ENV}=PATH runs one you built`);
  }
  const pkg = `${SCOPE}/${TOOL}-${key}`;
  try {
    return path.join(path.dirname(require.resolve(`${pkg}/package.json`)), "bin", TOOL);
  } catch {
    die(`${pkg}@${VERSION} isn't installed: npm installs it with ${SCOPE}/${TOOL} unless optional dependencies are left out (--omit=optional, --no-optional); reinstall with them`);
  }
}

const env = { ...process.env };
if (JITI) {
  // vknip loads JavaScript and TypeScript configs in a node process, through jiti as knip does: the
  // project's when it has one, else this package's (found through NODE_PATH, which node's require
  // reads after node_modules). And that node is the one running this launcher.
  try {
    let dir = path.dirname(require.resolve("jiti"));
    while (path.basename(dir) !== "jiti" && path.dirname(dir) !== dir) dir = path.dirname(dir);
    if (path.basename(dir) === "jiti") {
      env.NODE_PATH = [path.dirname(dir), env.NODE_PATH].filter(Boolean).join(path.delimiter);
    }
  } catch {}
  env.PATH = [path.dirname(process.execPath), env.PATH].filter(Boolean).join(path.delimiter);
}
const exe = binary();
const name = path.basename(__filename, ".js");
const r = spawnSync(exe, process.argv.slice(2), { stdio: "inherit", env, argv0: name });
if (r.error) die(`can't run ${exe}: ${r.error.message}`);
if (r.signal) process.kill(process.pid, r.signal);
process.exit(r.status ?? 1);
