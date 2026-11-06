// The host's requests (ljs.vu, ljs_glue.c): one JSON line on fd 3 each, one answer line on fd 4.
//   {"op":"load", "url", "name", "alias"}       -> oxlint's loadPlugin answer (JSON text)
//   {"op":"setup", "json"}                      -> null, or the error message
//   {"op":"lint", "path", "src", "bom", "jsx", "sourceType", "base", "tree", "rules", "opts",
//    "settings", "globals"}                      -> null, or lintFile's answer (JSON text)
import { createReadStream as __vlCreateReadStream, writeSync as __vlWriteSync } from "node:fs";
import { createInterface as __vlCreateInterface } from "node:readline";

// (standard output and error are vlint's: Node makes pipes non-blocking, which would make vlint's
// own writes fail half-way; back to blocking, as oxlint's cli.js does)
process.stdout._handle?.setBlocking?.(true);
process.stderr._handle?.setBlocking?.(true);
const __vlAnswer = (v) => __vlWriteSync(4, JSON.stringify(v) + "\n");
// (stack traces end where oxlint's do: at its wrapper, called from Rust)
const __vlCut = (s, name) => {
  if (typeof s !== "string") return s;
  s = s.replace(/\\n    at process\.processTicksAndRejections \(node:internal\/process\/task_queues:\d+:\d+\)/g, "");
  s = s.replace(/\n    at process\.processTicksAndRejections \(node:internal\/process\/task_queues:\d+:\d+\)/g, "");
  return s.replace(new RegExp("(\\\\n    at " + name + " [^\\\\]*?\\))(\\\\n    at [^\\\\]*?)*(?=\\\\n|\")", "g"), "$1");
};
function loadPluginWrapper(url, name, alias) {
  return loadPlugin(url, name, alias, null);
}
function lintFileWrapper(req) {
  return lintFile(req.path, 0, req, req.rules, req.opts, req.settings, req.globals, false, null);
}
function setupRuleConfigsWrapper(json) {
  try {
    setOptions(json);
    return null;
  } catch (err) {
    return getErrorMessage(err);
  }
}
// (requests are handled one after another; promises are chained with then() rather than awaited,
// so a plugin's async stack trace doesn't show this loop)
function __vlHandle(line) {
  if (line === "") return;
  let req;
  try {
    req = JSON.parse(line);
  } catch (err) {
    __vlAnswer({ Failure: "vlint: bad request" });
    return;
  }
  if (req.op === "load") return loadPluginWrapper(req.url, req.name, req.alias).then((res) => __vlAnswer(__vlCut(res, "loadPluginWrapper")));
  if (req.op === "setup") return __vlAnswer(__vlCut(setupRuleConfigsWrapper(req.json), "setupRuleConfigsWrapper"));
  if (req.op === "lint") return __vlAnswer(__vlCut(lintFileWrapper(req), "lintFileWrapper"));
  __vlAnswer(null);
}
let __vlChain = Promise.resolve();
__vlCreateInterface({ input: __vlCreateReadStream(null, { fd: 3 }), crlfDelay: Infinity }).on("line", (line) => {
  __vlChain = __vlChain.then(() => __vlHandle(line));
});
