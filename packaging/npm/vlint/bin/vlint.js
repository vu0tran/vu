#!/usr/bin/env node
// vlint's launcher: runs the native binary from the platform package npm installed with it (one of
// the optionalDependencies, picked by their os/cpu fields), as oxlint's own launcher does.
// The same file is the package's `vlint` and `oxlint` commands. make.mjs fills in the constants.
"use strict";
const { spawnSync } = require("node:child_process");
const path = require("node:path");

const SCOPE = "@vu0tran";
const VERSION = "0.0.0";
const OXLINT = "1.90.0";
const PLATFORMS = ["linux-x64", "linux-arm64", "darwin-x64", "darwin-arm64"];

function die(msg) {
  process.stderr.write(`vlint: ${msg}\n`);
  process.exit(2);
}

function binary() {
  if (process.env.VLINT_BINARY) return process.env.VLINT_BINARY;
  const key = `${process.platform}-${process.arch}`;
  if (!PLATFORMS.includes(key)) {
    die(`there's no vlint binary for ${key} (there are: ${PLATFORMS.join(", ")}); VLINT_BINARY=PATH runs one you built`);
  }
  const pkg = `${SCOPE}/vlint-${key}`;
  try {
    return path.join(path.dirname(require.resolve(`${pkg}/package.json`)), "bin", "vlint");
  } catch {
    die(`${pkg} isn't installed: npm installs it with ${SCOPE}/vlint unless optional dependencies are left out (--omit=optional, --no-optional); reinstall with them`);
  }
}

const args = process.argv.slice(2);
if (args.length === 1 && (args[0] === "--version" || args[0] === "-V")) {
  process.stdout.write(`vlint ${VERSION} (oxlint ${OXLINT}'s default rules)\n`);
  process.exit(0);
}
if (args.length === 1 && (args[0] === "--help" || args[0] === "-h")) {
  process.stdout.write(
    `vlint ${VERSION}: oxlint ${OXLINT}'s default rules, written in Vu\n\n` +
      "Usage: vlint [--fix] [--jobs N] [--cache] [--cache-location PATH] [PATH ...]\n\n" +
      "With no paths it lints the current folder (without node_modules). Diagnostics are printed one\n" +
      "per line, as oxlint prints them for agents and CI. https://github.com/vu0tran/vu/tree/main/ts\n",
  );
  process.exit(0);
}
const r = spawnSync(binary(), args, { stdio: "inherit" });
if (r.error) die(`can't run ${binary()}: ${r.error.message}`);
if (r.signal) process.kill(process.pid, r.signal);
process.exit(r.status ?? 1);
