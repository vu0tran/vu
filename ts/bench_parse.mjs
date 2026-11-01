// Parse-only throughput: each parser parses every file once (the sources read first), best of N runs.
import { readFileSync } from "node:fs";
const [, , which, listFile, runsArg] = process.argv;
const files = readFileSync(listFile, "utf8").split(/\s+/).filter(Boolean);
const srcs = files.map((f) => [f, readFileSync(f, "utf8")]);
const runs = Number(runsArg || 5);
let parse;
if (which === "oxc") {
  const { parseSync } = await import("oxc-parser");
  parse = (f, s) => parseSync(f, s, { lang: "ts" });
} else if (which === "swc") {
  const swc = await import("@swc/core");
  parse = (f, s) => swc.parseSync(s, { syntax: "typescript" });
} else if (which === "esbuild") {
  const esbuild = await import("esbuild");
  // esbuild has no parse-only API: transform (parse, lower, print) is the closest
  parse = (f, s) => esbuild.transformSync(s, { loader: "ts" });
} else if (which === "ts") {
  const ts = (await import("typescript")).default;
  parse = (f, s) => ts.createSourceFile(f, s, ts.ScriptTarget.Latest, false, ts.ScriptKind.TS);
} else if (which === "bun") {
  const tr = new Bun.Transpiler({ loader: "ts" });
  parse = (f, s) => tr.scan(s);
}
let best = Infinity;
for (let r = 0; r < runs; r++) {
  const t0 = performance.now();
  for (const [f, s] of srcs) parse(f, s);
  const t = performance.now() - t0;
  if (t < best) best = t;
}
let bytes = 0;
for (const [, s] of srcs) bytes += Buffer.byteLength(s);
console.log(`${which}: ${files.length} files, ${bytes} bytes, best ${best.toFixed(1)} ms`);
