#!/usr/bin/env python3
"""Builds vlint's JS plugin host: oxlint 1.90.0's own plugin runtime (npm package `oxlint`, dist/,
MIT licence) with its raw-transfer reads replaced by vlint's tree (estree.js) and tokens (tokens.js),
plus the request loop (main.js). Writes jsplug/host.mjs and lhost.vu (the host as a Vu string).

    python3 ts/jsplug/gen_host.py PATH/TO/node_modules/oxlint/dist
    python3 ts/jsplug/gen_host.py --from-lhost     (oxlint's part taken from the current lhost.vu)

estree.js's node literals (`{ __proto__: NodeProto, k: v, ... }`) become constructor calls (`new
NdN(v, ...)`, one constructor per list of keys, its prototype NodeProto): the same objects, with the
same keys in the same order, made about eight times faster than V8 makes a literal with __proto__
(and read faster too).
"""
import hashlib, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
dist = sys.argv[1]
OURS_START = "const { buildEstree, lexProgram, tokenRecords, commentRecords } = (() => {\n"


def read(name):
    with open(os.path.join(dist, name), encoding="utf8") as f:
        return f.read()


def strip_exports(s):
    return re.sub(r"^export \{[^}]*\};?\s*$", "", s, flags=re.M)


def replace_fn(src, name, body):
    """Replaces `function name(...) {...}` (top level, tab-indented body) with body."""
    m = re.search(r"^function " + re.escape(name) + r"\(.*?\n\}\n", src, flags=re.M | re.S)
    if not m:
        raise SystemExit("function not found: " + name)
    return src[: m.start()] + body.strip() + "\n" + src[m.end():]


def must_replace(src, old, new):
    if old not in src:
        raise SystemExit("text not found: " + old[:60])
    return src.replace(old, new, 1)


# ---- estree.js's node literals as constructor calls

NODE_LIT = re.compile(r"\{\s*__proto__:\s*NodeProto,")
KEY_VAL = re.compile(r"^([A-Za-z_$][\w$]*)\s*:\s*(.*)$", re.S)
NAME = re.compile(r"^[A-Za-z_$][\w$]*$")


def skip_string(s, i):
    """past the string or template literal starting at i"""
    q = s[i]
    j = i + 1
    while s[j] != q:
        if s[j] == "\\":
            j += 2
        elif q == "`" and s[j] == "$" and s[j + 1] == "{":
            j = match_close(s, j + 2)[0] + 1
        else:
            j += 1
    return j + 1


def match_close(s, i):
    """from just after an opening bracket: where its closing one is, and the top-level commas"""
    depth, commas, prev = 0, [], "("
    while True:
        c = s[i]
        if c in "\"'`":
            i, prev = skip_string(s, i), "a"
            continue
        if c == "/" and s[i + 1] in "/*":
            raise SystemExit("gen_host: a comment inside a node literal at %d" % i)
        if c == "/" and prev in "(,=:[!&|?{};+-*%<>~^":
            j, cls = i + 1, False
            while cls or s[j] != "/":
                if s[j] == "\\":
                    j += 1
                elif s[j] == "[":
                    cls = True
                elif s[j] == "]":
                    cls = False
                j += 1
            j += 1
            while s[j].isalpha():
                j += 1
            i, prev = j, "a"
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                return i, commas
            depth -= 1
        elif c == "," and depth == 0:
            commas.append(i)
        if not c.isspace():
            prev = "a" if (c.isalnum() or c in "_$") else c
        i += 1


def node_ctors(src, shapes):
    out, i = [], 0
    while True:
        m = NODE_LIT.search(src, i)
        if not m:
            out.append(src[i:])
            return "".join(out)
        j = m.start()
        out.append(src[i:j])
        end, commas = match_close(src, j + 1)
        cuts = [j] + commas + [end]
        parts = [src[a + 1:b].strip() for a, b in zip(cuts, cuts[1:])]
        parts = [x for x in parts[1:] if x]
        keys, vals = [], []
        for x in parts:
            kv = KEY_VAL.match(x)
            if kv:
                keys.append(kv.group(1))
                vals.append(node_ctors(kv.group(2), shapes))
            elif NAME.match(x):
                keys.append(x)
                vals.append(x)
            else:
                # (a getter or a spread: left as it is)
                keys = None
                break
        if keys is None:
            out.append(src[j:end + 1])
        else:
            name = shapes.setdefault(tuple(keys), "Nd%d" % len(shapes))
            out.append("new %s(%s)" % (name, ", ".join(vals)))
        i = end + 1


def with_ctors(src):
    shapes = {}
    body = node_ctors(src, shapes)
    defs = []
    for keys, name in shapes.items():
        args = ["a%d" % k for k in range(len(keys))]
        sets = " ".join("this.%s = %s;" % (k, a) for k, a in zip(keys, args))
        defs.append("function %s(%s) { %s }\n%s.prototype = NodeProto;\n" % (name, ", ".join(args), sets, name))
    return "".join(defs) + body


def body_of(name):
    with open(os.path.join(here, name), encoding="utf8") as f:
        return f.read()


ours = (OURS_START + with_ctors(body_of("estree.js")) + "\n" + body_of("tokens.js")
        + "\nreturn { buildEstree, lexProgram, tokenRecords, commentRecords };\n})();\n")
main = body_of("main.js")


def vu_str(s):
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "{":
            out.append("{{")
        elif ch == "}":
            out.append("}}")
        elif ord(ch) < 32:
            out.append("\\u{%04x}" % ord(ch))
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def vu_unstr(s):
    """a Vu string literal's text (as vu_str below writes it) back"""
    out, i = [], 1
    while s[i] != '"':
        c = s[i]
        if c == "\\":
            n = s[i + 1]
            if n == "u":
                e = s.index("}", i)
                out.append(chr(int(s[i + 3:e], 16)))
                i = e + 1
                continue
            out.append({"n": "\n", "t": "\t", "r": "\r"}.get(n, n))
            i += 2
        elif c in "{}":
            out.append(c)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


# Changes to oxlint's part that make the host start sooner, the same behaviour (each applied once:
# --from-lhost finds them made)
STARTUP = [
    # (a built-in module taken as it is rather than imported: no ES module facade to build)
    ('import { createRequire } from "node:module";\n',
     'const { createRequire } = process.getBuiltinModule ? process.getBuiltinModule("node:module") : await import("node:module");\n'),
    # (imported for nothing: nothing of it is used, and loading it loads node's assertion internals)
    ('import "node:assert";\n', ''),
    # (uri-js, as ajv compiles its meta schema at load: the IPv6 pattern, compiled on its first use,
    # tried on hosts with no ':', which no IPv6 address lacks; about 5 ms of every start)
    ('function _normalizeIPv6(host, protocol) {\n',
     'function _normalizeIPv6(host, protocol) {\n\t\t\tif (host.indexOf(":") < 0) return host;\n'),
    ('components.host && !protocol.IPV6ADDRESS.test(components.host)',
     'components.host && (String(components.host).indexOf(":") < 0 || !protocol.IPV6ADDRESS.test(components.host))'),
]


def startup_patches(host):
    for old, new in STARTUP:
        if (new and new in host) or (not new and old not in host):
            continue
        if old not in host:
            raise SystemExit("text not found: " + old[:60])
        if host.count(old) != 1:
            raise SystemExit("text found more than once: " + old[:60])
        host = host.replace(old, new, 1)
    return host


def write_host(host):
    """writes jsplug/host.mjs and lhost.vu"""
    host = startup_patches(host)
    with open(os.path.join(here, "host.mjs"), "w", encoding="utf8") as f:
        f.write(host)

    digest = hashlib.sha256(host.encode("utf8")).hexdigest()[:16]
    with open(os.path.join(here, "..", "lhost.vu"), "w", encoding="utf8") as f:
        f.write("# Generated by ts/jsplug/gen_host.py: vlint's JS plugin host (oxlint 1.90.0's plugin runtime, MIT,\n")
        f.write("# with vlint's tree in place of oxc's raw transfer). Don't edit; edit jsplug/ and regenerate.\n\n")
        f.write('const HOST_HASH = "%s"\n' % digest)
        f.write("const HOST_JS = " + vu_str(host) + "\n")
    print("host.mjs", len(host), "bytes, hash", digest)


if dist == "--from-lhost":
    with open(os.path.join(here, "..", "lhost.vu"), encoding="utf8") as f:
        old = vu_unstr(re.search(r'^const HOST_JS = (".*")$', f.read(), flags=re.M).group(1))
    prefix = old[: old.index(OURS_START)]
    # (main.js's imports, whose names start with __vl, are the header's last ones: replaced by its
    # current ones)
    lines = prefix.split("\n")
    vl = [i for i, x in enumerate(lines) if x.startswith("import ") and " as __vl" in x]
    imps = [i for i, x in enumerate(lines[:40]) if x.startswith("import ")]
    at = vl[0] if vl else (max(imps) + 1 if imps else next(i for i, x in enumerate(lines) if not x.startswith("//")))
    lines = [x for i, x in enumerate(lines) if i not in vl]
    lines[at:at] = re.findall(r"^import .*;$", main, flags=re.M)
    write_host("\n".join(lines) + ours + re.sub(r"^import .*;\n", "", main, flags=re.M))
    sys.exit(0)


runtime = strip_exports(read("rolldown-runtime.js"))
workspace = strip_exports(read("workspace2.js"))
utils = strip_exports(read("utils.js"))
lint = read("lint.js")
lint = re.sub(r'^import .* from "\./[a-z0-9_-]+\.js";\n', "", lint, flags=re.M)
lint = strip_exports(lint)

lint = replace_fn(lint, "initSourceText", """
function initSourceText() {
	sourceText = buffer.src;
}""")
lint = replace_fn(lint, "initAst", """
function initAst() {
	sourceText === null && initSourceText(), ast = buildEstree(buffer);
}""")
lint = replace_fn(lint, "fileIsJsx", """
function fileIsJsx() {
	return buffer.jsx === true;
}""")
lint = replace_fn(lint, "initTokensBuffer", """
function initTokensBuffer() {
	sourceText === null && initSourceText();
	if (buffer.lx === void 0) ast === null && initAst(), buffer.lx = lexProgram(ast, sourceText);
	let r = tokenRecords(buffer.lx);
	if (tokensLen = r.len, tokensUint8 = r.u8, tokensInt32 = r.i32, cachedTokens.length < tokensLen) {
		do
			cachedTokens.push(new Token());
		while (cachedTokens.length < tokensLen);
		let indexesLen = deserializedTokenIndexes.length;
		indexesLen < tokensLen && (deserializedTokenIndexes = new Int32Array(MathMax$4(tokensLen, indexesLen === 0 ? 16 : indexesLen << 1)));
	}
}""")
lint = replace_fn(lint, "initCommentsBuffer", """
function initCommentsBuffer() {
	sourceText === null && initSourceText();
	if (buffer.lx === void 0) ast === null && initAst(), buffer.lx = lexProgram(ast, sourceText);
	let r = commentRecords(buffer.lx);
	if (commentsLen = r.len, commentsLen === 0) {
		comments = EMPTY_COMMENTS, commentsUint8 = EMPTY_UINT8_ARRAY, commentsInt32 = EMPTY_INT32_ARRAY, allCommentsDeserialized = !0;
		return;
	}
	if (commentsUint8 = r.u8, commentsInt32 = r.i32, cachedComments.length < commentsLen) {
		do
			cachedComments.push(new Comment());
		while (cachedComments.length < commentsLen);
		let indexesLen = deserializedCommentIndexes.length;
		indexesLen < commentsLen && (deserializedCommentIndexes = new Int32Array(MathMax$3(commentsLen, indexesLen === 0 ? 16 : indexesLen << 1)));
	}
	commentsInt32[0] === 0 && sourceText.startsWith("#!") && (getComment(0).type = "Shebang");
}""")
lint = must_replace(lint, """	if (buffer === null) buffer = buffers[bufferId];
	else {
		let { buffer: arrayBuffer, byteOffset } = buffer;
		buffer.int32 = new Int32Array(arrayBuffer, byteOffset), buffer.float64 = new Float64Array(arrayBuffer, byteOffset);
		for (let i = bufferId - buffers.length; i >= 0; i--) buffers.push(null);
		buffers[bufferId] = buffer;
	}
""", "")
lint = must_replace(lint, "let hasBOM = buffer[2147483574] === 1;", "let hasBOM = buffer.bom === !0;")


imports = "".join(re.findall(r"^import .*;\n", runtime + main, flags=re.M))
runtime = re.sub(r"^import .*;\n", "", runtime, flags=re.M)
main = re.sub(r"^import .*;\n", "", main, flags=re.M)
lint_imports = "".join(re.findall(r'^import "[^"]+";\n', lint, flags=re.M))
lint = re.sub(r'^import "[^"]+";\n', "", lint, flags=re.M)

header = ("// vlint's JS plugin host, generated by ts/jsplug/gen_host.py: oxlint 1.90.0's plugin runtime\n"
          "// (https://github.com/oxc-project/oxc, MIT licence) with vlint's tree and tokens in place of\n"
          "// oxc's raw transfer buffer.\n")
host = header + imports + lint_imports + runtime + workspace + utils + lint + ours + main

write_host(host)
