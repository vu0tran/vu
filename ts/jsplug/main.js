// The host's requests (ljs.vu, ljs_glue.c): one JSON line on fd 3 each, one answer line on fd 4.
//   {"op":"load", "url", "name", "alias"}       -> oxlint's loadPlugin answer (JSON text)
//   {"op":"setup", "json"}                      -> null, or the error message
//   {"op":"lint", "path", "src", "bom", "jsx", "sourceType", "base", "tree", "rules", "opts",
//    "settings", "globals"}                      -> null, or lintFile's answer (JSON text)
// (the built-in modules taken as they are, not imported: an import makes each one's ES module
// facade, which reads every export, node:fs's streams among them; about 4 ms of the host's start)
const __vlBuiltin = (name) => process.getBuiltinModule ? process.getBuiltinModule(name) : import(name);
const { writeSync: __vlWriteSync } = await __vlBuiltin("node:fs");
const { Socket: __vlSocket } = await __vlBuiltin("node:net");
const { isUtf8: __vlIsUtf8 } = await __vlBuiltin("node:buffer");

const __vlAnswer = (v) => __vlWriteSync(4, JSON.stringify(v) + "\n");
// (in the startup snapshot, gen_host.py --snapshot, the host's code is named vlint-js-host-HASH.js:
// its frames in answers get the host script's URL, as without the snapshot)
let __vlHostName = null, __vlHostUrl = null;
const __vlRename = (s) => __vlHostName === null || typeof s !== "string" ? s : s.split(__vlHostName).join(__vlHostUrl);
// (stack traces end where oxlint's do: at its wrapper, called from Rust)
const __vlCut = (s, name) => {
  if (typeof s !== "string") return s;
  s = __vlRename(s);
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
function __vlHandleOnce(line, done) {
  const answer = __vlAnswer;
  return __vlHandle(line, (v) => { answer(v); done(); });
}
function __vlHandle(line, __vlAnswer) {
  if (line === "") return;
  let req;
  if (typeof line !== "string") req = line;
  else try {
    req = JSON.parse(line);
  } catch (err) {
    __vlAnswer({ Failure: "vlint: bad request" });
    return;
  }
  if (req.op === "load") return loadPluginWrapper(req.url, req.name, req.alias).then((res) => __vlAnswer(__vlCut(res, "loadPluginWrapper")));
  if (req.op === "setup") return __vlAnswer(__vlCut(setupRuleConfigsWrapper(req.json), "setupRuleConfigsWrapper"));
  if (req.op === "lint" || req.op === "lintb") return __vlAnswer(__vlCut(lintFileWrapper(req), "lintFileWrapper"));
  __vlAnswer(null);
}
let __vlChain = Promise.resolve();
// What runs when the host starts: everything above only defines (and in the startup snapshot,
// gen_host.py --snapshot, it ran when the snapshot was built; this runs in each process).
function __vlMain() {
// (standard output and error are vlint's: Node makes pipes non-blocking, which would make vlint's
// own writes fail half-way; back to blocking, as oxlint's cli.js does)
process.stdout._handle?.setBlocking?.(true);
process.stderr._handle?.setBlocking?.(true);
// (fd 3 read as a pipe, from the event loop: a file stream would leave a blocking read in libuv's
// thread pool, and process.exit() in a plugin would wait for it forever)
__vlIn = new __vlSocket({ fd: 3, readable: true, writable: false });
// (when fd 3 ends, every request has come: the host ends once they're answered, even if a plugin
// keeps the event loop alive; if reading it fails, the host ends at once, so vlint sees its pipes
// close rather than a process that no longer reads: issue #7)
__vlIn.on("end", () => { setImmediate(() => __vlChain.then(() => process.exit(0))); });
__vlIn.on("error", (err) => {
  if (process.env.VLINT_JS_DEBUG && process.env.VLINT_JS_DEBUG !== "0") {
    try { process.stderr.write("vlint js: process " + process.pid + ": reading fd 3 failed: " + String(err && err.message || err) + "\n"); } catch {}
  }
  process.exit(1);
});
// A lint frame (ljs.lint_frame): its JSON, then the text, zeros to a multiple of 4, the nodes and
// the lists as int32 arrays, read in place. Its text is given as its bytes too when they are valid
// UTF-8 (the bytes the tree's positions count; estree.js reads them as they are).
function __vlFrame(head, buf) {
  const [sl, nl, ll] = head.bin;
  const sb = Buffer.from(buf.buffer, buf.byteOffset, sl);
  head.src = sb.toString("utf8");
  if (__vlIsUtf8(sb)) head.srcBuf = sb;
  const at = buf.byteOffset + sl + ((4 - sl % 4) % 4);
  head.tree.nd = new Int32Array(buf.buffer, at, nl);
  head.tree.L = new Int32Array(buf.buffer, at + 4 * nl, ll);
  return head;
}
// fd 3's bytes split into requests: lines, a frame's bytes after its line
__vlIn.on("data", (chunk) => {
  let c = chunk;
  for (;;) {
    if (__vlBody !== null) {
      const n = Math.min(c.length, __vlBody.length - __vlFill);
      __vlBody.set(n === c.length ? c : c.subarray(0, n), __vlFill);
      __vlFill += n;
      c = c.subarray(n);
      if (__vlFill < __vlBody.length) return;
      const req = __vlFrame(__vlHead, __vlBody);
      __vlBody = __vlHead = null;
      __vlRequest(req);
      continue;
    }
    if (c.length === 0) return;
    const nl = c.indexOf(10);
    if (nl < 0) { __vlPend = __vlPend === null ? Buffer.from(c) : Buffer.concat([__vlPend, c]); return; }
    let lb = c.subarray(0, nl);
    if (__vlPend !== null) { lb = Buffer.concat([__vlPend, lb]); __vlPend = null; }
    c = c.subarray(nl + 1);
    const line = lb.toString("utf8");
    if (line.startsWith('{"op":"lintb"')) {
      let head = null;
      try { head = JSON.parse(line); } catch {}
      if (head !== null && Array.isArray(head.bin)) {
        const [sl, nl2, ll] = head.bin;
        __vlHead = head;
        // (a fresh buffer: the int32 arrays need it aligned)
        __vlBody = new Uint8Array(sl + ((4 - sl % 4) % 4) + 4 * (nl2 + ll));
        __vlFill = 0;
        continue;
      }
    }
    __vlRequest(line);
  }
});
}
let __vlIn = null, __vlPend = null, __vlBody = null, __vlFill = 0, __vlHead = null;
function __vlRequest(line) {
  // (every request is answered exactly once: if handling it throws, the error is the answer, and
  // the chain goes on to the next request rather than stopping for good; issue #7)
  __vlChain = __vlChain.then(() => {
    let answered = false;
    const fail = (err) => {
      if (answered) return;
      answered = true;
      try { __vlAnswer(JSON.stringify({ Failure: { message: "vlint: the plugin host failed: " + __vlRename(String(err && err.stack || err)) } })); } catch {}
    };
    let r;
    try {
      r = __vlHandleOnce(line, () => { answered = true; });
    } catch (err) {
      fail(err);
      return;
    }
    if (r && typeof r.then === "function") return r.then(undefined, fail);
  });
}
__vlMain();
