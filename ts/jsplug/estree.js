// vlint's tree (ts/ast.vu, sent as flat arrays by ljs.vu) as oxc's ESTree, the AST oxlint gives JS
// plugins: the same node types, fields (in oxc's order), spans in UTF-16 offsets, `parent` links,
// and `loc` from NodeProto. Where vlint's tree keeps a name but not its span, the span is found in
// the source (skipping spaces and comments).

const N_LIST = 1, N_VAR = 10, N_DECL = 11, N_FUNC = 12, N_PARAM = 13, N_RETURN = 14, N_IF = 15, N_BLOCK = 16,
  N_EXPRSTMT = 17, N_WHILE = 18, N_DO = 19, N_FOR = 20, N_FORIN = 21, N_BREAK = 22, N_CONTINUE = 23, N_THROW = 24,
  N_TRY = 25, N_SWITCH = 26, N_CASE = 27, N_LABEL = 28, N_EMPTY = 29, N_INTERFACE = 30, N_TYPEALIAS = 31,
  N_CLASS = 32, N_ENUM = 33, N_ENUMMEMBER = 34, N_MODULE = 35, N_IMPORT = 36, N_EXPORT = 37, N_EXPORTDEFAULT = 38,
  N_IMPORTEQ = 39, N_DEBUGGER = 40, N_WITH = 41, N_EXPORTASSIGN = 42, N_SPEC = 43, N_EXTERNALREF = 44,
  N_NSEXPORT = 45, N_PROP = 50, N_METHOD = 51, N_CALLSIG = 52, N_CTORSIG = 53, N_INDEXSIG = 54, N_CTOR = 55,
  N_GET = 56, N_SET = 57, N_SIG = 58, N_STATICBLOCK = 59, N_COMPUTED = 60, N_PRIVNAME = 61, N_SEMIMEMBER = 62,
  N_TREF = 70, N_QNAME = 71, N_TKW = 72, N_TLIT = 73, N_TUNION = 74, N_TINTER = 75, N_TARRAY = 76, N_TTUPLE = 77,
  N_TTUPLEEL = 78, N_TFUNC = 79, N_TOBJ = 80, N_TPAREN = 81, N_TQUERY = 82, N_TOP = 83, N_TINDEXED = 84,
  N_TCOND = 85, N_TINFER = 86, N_TMAPPED = 87, N_TTEMPLATE = 88, N_TPRED = 89, N_TTHIS = 90, N_TIMPORT = 91,
  N_TPARAM = 92, N_TSPAN = 93, N_TOPTIONAL = 94, N_TREST = 95, N_ID = 100, N_NUM = 101, N_BIGINT = 102,
  N_STR = 103, N_TEMPL = 104, N_NOSUBTEMPL = 105, N_REGEX = 106, N_TRUE = 107, N_FALSE = 108, N_NULL = 109,
  N_THIS = 110, N_SUPER = 111, N_ARRAY = 112, N_OBJECT = 113, N_PROPASSIGN = 114, N_SHORTHAND = 115,
  N_SPREAD = 116, N_OMIT = 117, N_FUNCEXPR = 118, N_ARROW = 119, N_CALL = 120, N_NEW = 121, N_PROPACCESS = 122,
  N_ELEMACCESS = 123, N_BINARY = 124, N_PREFIX = 125, N_POSTFIX = 126, N_COND = 127, N_PAREN = 128, N_AS = 129,
  N_SATISFIES = 130, N_NONNULL = 131, N_TYPEASSERT = 132, N_TYPEOF = 133, N_VOIDEXPR = 134, N_DELETE = 135,
  N_AWAIT = 136, N_YIELD = 137, N_CLASSEXPR = 138, N_TAGGED = 139, N_OBJPAT = 140, N_ARRPAT = 141,
  N_BINDEL = 142, N_METAPROP = 143, N_IMPORTCALL = 144, N_EXPRTARGS = 145, N_JSXELEM = 147, N_JSXATTR = 148,
  N_JSXSPREAD = 149, N_JSXEXPR = 150, N_JSXTEXT = 151;

const M_EXPORT = 1, M_DECLARE = 2, M_DEFAULT = 4, M_ABSTRACT = 8, M_ASYNC = 16, M_CONST = 32, M_STATIC = 64,
  M_READONLY = 128, M_PUBLIC = 256, M_PRIVATE = 512, M_PROTECTED = 1024, M_OVERRIDE = 2048, M_ACCESSOR = 4096,
  M_OPTIONAL = 8192, M_EXCL = 16384, M_GENERATOR = 32768, M_REST = 65536, M_TYPEONLY = 131072, M_IN = 262144,
  M_OUT = 524288, MOD_GLOBAL = 1048576, MOD_NAMESPACE = 2097152;
const MAP_READONLY = 1, MAP_NOREADONLY = 2, MAP_OPTIONAL = 4, MAP_NOOPTIONAL = 8;

// scanner tokens (ts/scan.vu)
const OPS = {
  30: "<", 31: ">", 32: "<=", 33: ">=", 34: "==", 35: "!=", 36: "===", 37: "!==", 39: "+", 40: "-", 41: "*",
  42: "**", 43: "/", 44: "%", 45: "++", 46: "--", 47: "<<", 48: ">>", 49: ">>>", 50: "&", 51: "|", 52: "^",
  53: "!", 54: "~", 55: "&&", 56: "||", 57: "??", 62: "=", 63: "+=", 64: "-=", 65: "*=", 66: "**=", 67: "/=",
  68: "%=", 69: "<<=", 70: ">>=", 71: ">>>=", 72: "&=", 73: "|=", 74: "^=", 75: "&&=", 76: "||=", 77: "??=",
  29: ",", 120: "in", 121: "instanceof",
};
const T_COMMA = 29, W_KEYOF = 163, W_UNIQUE = 178, W_READONLY = 170, W_NEW = 122, W_IMPORT = 119;
const KW_TYPES = {
  152: "TSAnyKeyword", 179: "TSUnknownKeyword", 167: "TSNumberKeyword", 174: "TSStringKeyword",
  157: "TSBooleanKeyword", 156: "TSBigIntKeyword", 175: "TSSymbolKeyword", 168: "TSObjectKeyword",
  166: "TSNeverKeyword", 177: "TSUndefinedKeyword", 133: "TSVoidKeyword", 123: "TSNullKeyword",
};

let src = "", nd = null, Ls = null, nm = null, u16 = null, npos = null, decoAt = null, baseOff = 0;

// a byte offset (in vlint's text) as a UTF-16 offset in the text the plugins see
function u(p) {
  return (u16 === null ? p : u16[p]) - baseOff;
}

function K(n) { return nd[n * 9]; }
function P(n) { return nd[n * 9 + 1]; }
function E(n) { return nd[n * 9 + 2]; }
function A(n) { return nd[n * 9 + 3]; }
function B(n) { return nd[n * 9 + 4]; }
function C(n) { return nd[n * 9 + 5]; }
function D(n) { return nd[n * 9 + 6]; }
function F(n) { return nd[n * 9 + 7]; }
function S(n) { return nd[n * 9 + 8]; }
function items(l) {
  if (l < 0) return [];
  const st = A(l), len = B(l), out = new Array(len);
  for (let i = 0; i < len; i++) out[i] = Ls[st + i];
  return out;
}
function name(n) { return nm[S(n)]; }

// positions in the source (byte offsets; the source is kept as bytes for this)
let bytes = null;
function ch(i) { return i < bytes.length ? bytes[i] : 0; }
function isWs(c, i) {
  if (c === 32 || c === 9 || c === 10 || c === 13 || c === 11 || c === 12) return 1;
  if (c === 0xc2 && ch(i + 1) === 0xa0) return 2;
  if (c === 0xef && ch(i + 1) === 0xbb && ch(i + 2) === 0xbf) return 3;
  if (c === 0xe2 && ch(i + 1) === 0x80 && (ch(i + 2) === 0xa8 || ch(i + 2) === 0xa9 || (ch(i + 2) >= 0x80 && ch(i + 2) <= 0x8a) || ch(i + 2) === 0xaf)) return 3;
  if (c === 0xe1 && ch(i + 1) === 0x9a && ch(i + 2) === 0x80) return 3;
  if (c === 0xe2 && ch(i + 1) === 0x81 && ch(i + 2) === 0x9f) return 3;
  if (c === 0xe3 && ch(i + 1) === 0x80 && ch(i + 2) === 0x80) return 3;
  return 0;
}
// past spaces and comments from i
function skip(i) {
  for (;;) {
    const c = ch(i);
    const w = isWs(c, i);
    if (w) { i += w; continue; }
    if (c === 47 && ch(i + 1) === 47) { while (i < bytes.length && ch(i) !== 10 && ch(i) !== 13) i++; continue; }
    if (c === 47 && ch(i + 1) === 42) {
      i += 2;
      while (i < bytes.length && !(ch(i) === 42 && ch(i + 1) === 47)) i++;
      i += 2;
      continue;
    }
    return i;
  }
}
function isIdByte(c) {
  return (c >= 97 && c <= 122) || (c >= 65 && c <= 90) || (c >= 48 && c <= 57) || c === 95 || c === 36 || c === 92 || c >= 128;
}
// the end of the identifier (or keyword) starting at i
function idEnd(i) {
  if (ch(i) === 35) i++;
  while (i < bytes.length && isIdByte(ch(i))) {
    // (a non-ASCII byte: only identifier characters are expected here)
    if (ch(i) >= 128 && isWs(ch(i), i)) break;
    i++;
  }
  return i;
}
// the word at i (ASCII)
function wordAt(i) {
  let e = i;
  while (e < bytes.length && isIdByte(ch(e))) e++;
  return srcBytes(i, e);
}
function srcBytes(a, b) {
  return u16 === null ? src.slice(a, b) : src.slice(u16[a], u16[b]);
}
// skips the words in ws (in any order) at i: the position after them
function skipWords(i, ws) {
  for (;;) {
    i = skip(i);
    const w = wordAt(i);
    if (ws.includes(w)) { i += w.length; continue; }
    return i;
  }
}
// the position of the first c (a byte) at or after i, outside comments
function find(i, c) {
  for (;;) {
    i = skip(i);
    if (i >= bytes.length) return i;
    if (ch(i) === c) return i;
    i++;
  }
}
// backwards: the last byte before i that isn't a space or in a comment
function back(i) {
  i--;
  for (;;) {
    while (i > 0 && (ch(i) === 32 || ch(i) === 9 || ch(i) === 10 || ch(i) === 13)) {
      if (ch(i) === 10 || ch(i) === 13) {
        // a line comment at the end of the line above?
        const lc = lineComment(i);
        if (lc >= 0) { i = lc; }
      }
      i--;
    }
    if (i > 1 && ch(i) === 47 && ch(i - 1) === 42) {
      // the end of a block comment: back to its start
      let j = i - 2;
      while (j > 0 && !(ch(j) === 47 && ch(j + 1) === 42)) j--;
      i = j - 1;
      continue;
    }
    return i;
  }
}
// where a // comment starts on the line that ends at i (a line break), or -1
function lineComment(i) {
  let a = i - 1;
  while (a >= 0 && ch(a) !== 10 && ch(a) !== 13) a--;
  a++;
  let q = 0;
  for (let j = a; j < i; j++) {
    const c = ch(j);
    if (q !== 0) {
      if (c === 92) j++;
      else if (c === q) q = 0;
      continue;
    }
    if (c === 34 || c === 39 || c === 96) q = c;
    else if (c === 47 && ch(j + 1) === 47) return j;
    else if (c === 47 && ch(j + 1) === 42) {
      const e = bytes.indexOf("*/", j + 2);
      if (e < 0 || e >= i) return -1;
      j = e + 1;
    }
  }
  return -1;
}

// ---- nodes

function fin(o, s, e) {
  o.start = u(s);
  o.end = u(e);
  o.range = [o.start, o.end];
  o.parent = null;
  return o;
}
function setEnd(o, e) {
  o.end = e;
  o.range[1] = e;
}
function setStart(o, s) {
  o.start = s;
  o.range[0] = s;
}

function ident(nameStr, s, e) {
  return fin({ __proto__: NodeProto, type: "Identifier", decorators: [], name: nameStr, optional: false, typeAnnotation: null }, s, e);
}
// an identifier node at its own span (N_ID)
function idNode(n) {
  return ident(name(n), P(n), E(n));
}
// a name of node n kept only as text: found at i
function identAt(nameStr, i) {
  return ident(nameStr, i, idEnd(i));
}

function typeAnn(t, colon) {
  // `: T` (colon: where the colon is)
  return fin({ __proto__: NodeProto, type: "TSTypeAnnotation", typeAnnotation: t }, colon, null);
}
// a type annotation for type node n, starting at the colon before it
function annot(n) {
  if (n < 0) return null;
  const t = type(n);
  const o = { __proto__: NodeProto, type: "TSTypeAnnotation", typeAnnotation: t };
  const ts = Math.min(P(n), backToBytes(t.start));
  o.start = u(back(ts));
  o.end = Math.max(u(E(n)), t.end);
  o.range = [o.start, o.end];
  o.parent = null;
  return o;
}

// ---- literals

function strValue(raw) {
  // the value of a string literal's text (with its quotes)
  const q = raw[0];
  const body = raw.slice(1, raw.length - 1);
  if (!body.includes("\\")) return body;
  return unescape(body, false);
}
function unescape(s, tmpl) {
  let out = "";
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c !== "\\") {
      if (tmpl && c === "\r") {
        out += "\n";
        if (s[i + 1] === "\n") i++;
        continue;
      }
      out += c;
      continue;
    }
    i++;
    const d = s[i];
    switch (d) {
      case "n": out += "\n"; break;
      case "t": out += "\t"; break;
      case "r": out += "\r"; break;
      case "b": out += "\b"; break;
      case "f": out += "\f"; break;
      case "v": out += "\v"; break;
      case "\r": if (s[i + 1] === "\n") i++; break;
      case "\n": case "\u2028": case "\u2029": break;
      case "x": {
        const h = s.slice(i + 1, i + 3);
        if (!/^[0-9a-fA-F]{2}$/.test(h)) { if (tmpl) return null; out += "x"; break; }
        out += String.fromCharCode(parseInt(h, 16));
        i += 2;
        break;
      }
      case "u": {
        if (s[i + 1] === "{") {
          const e = s.indexOf("}", i);
          const h = s.slice(i + 2, e);
          if (e < 0 || !/^[0-9a-fA-F]+$/.test(h) || parseInt(h, 16) > 0x10ffff) { if (tmpl) return null; out += "u"; break; }
          out += String.fromCodePoint(parseInt(h, 16));
          i = e;
        } else {
          const h = s.slice(i + 1, i + 5);
          if (!/^[0-9a-fA-F]{4}$/.test(h)) { if (tmpl) return null; out += "u"; break; }
          out += String.fromCharCode(parseInt(h, 16));
          i += 4;
        }
        break;
      }
      default:
        if (d >= "0" && d <= "7") {
          if (tmpl) {
            if (d === "0" && !(s[i + 1] >= "0" && s[i + 1] <= "9")) { out += "\0"; break; }
            return null;
          }
          // legacy octal: up to 3 digits, value < 256
          let j = i, v = 0;
          while (j < s.length && j < i + 3 && s[j] >= "0" && s[j] <= "7" && v * 8 + (s.charCodeAt(j) - 48) < 256) {
            v = v * 8 + (s.charCodeAt(j) - 48);
            j++;
          }
          out += String.fromCharCode(v);
          i = j - 1;
        } else if (tmpl && (d === "8" || d === "9")) {
          return null;
        } else out += d;
    }
  }
  return out;
}
function numValue(raw) {
  let r = raw.replace(/_/g, "");
  if (/^0[0-7]+$/.test(r)) return parseInt(r, 8);
  if (/^0[0-9]+$/.test(r)) return parseFloat(r);
  if (/^0[bB]/.test(r)) return parseInt(r.slice(2), 2);
  if (/^0[oO]/.test(r)) return parseInt(r.slice(2), 8);
  return Number(r);
}
function literal(value, raw, s, e) {
  return fin({ __proto__: NodeProto, type: "Literal", value, raw }, s, e);
}
function strLit(n) {
  const raw = srcBytes(P(n), E(n));
  return literal(strValue(raw), raw, P(n), E(n));
}
function numLit(n) {
  const raw = srcBytes(P(n), E(n));
  return literal(numValue(raw), raw, P(n), E(n));
}
function bigLit(n) {
  const raw = srcBytes(P(n), E(n));
  let digits = raw.slice(0, -1).replace(/_/g, "");
  const big = BigInt(digits);
  const o = { __proto__: NodeProto, type: "Literal", value: big, raw, bigint: big.toString() };
  return fin(o, P(n), E(n));
}
function regexLit(n) {
  const raw = srcBytes(P(n), E(n));
  const slash = raw.lastIndexOf("/");
  const pattern = raw.slice(1, slash);
  let flags = raw.slice(slash + 1);
  let value = null;
  try { value = new RegExp(pattern, flags); } catch {}
  // (oxc writes the flags in the canonical order)
  flags = [...flags].sort((a, b) => "dgimsuvy".indexOf(a) - "dgimsuvy".indexOf(b)).join("");
  const o = { __proto__: NodeProto, type: "Literal", value, raw, regex: { pattern, flags } };
  return fin(o, P(n), E(n));
}
function templElem(s, e, tail, rawStart, rawEnd) {
  const raw = srcBytes(rawStart, rawEnd).replace(/\r\n?/g, "\n");
  const cooked = unescape(srcBytes(rawStart, rawEnd), true);
  return fin({ __proto__: NodeProto, type: "TemplateElement", value: { raw, cooked }, tail }, s, e);
}
// the quasis and expressions of a template (n: N_TEMPL or N_NOSUBTEMPL or N_TTEMPLATE), conv for
// the expressions
function template(n, conv) {
  const quasis = [], exprs = [];
  const s = P(n), e = E(n);
  if (K(n) === N_NOSUBTEMPL || (K(n) === N_TLIT)) {
    quasis.push(templElem(s, e, true, s + 1, e - 1));
    return { quasis, exprs };
  }
  const spans = items(A(n));
  // each element spans its delimiters (` or } before, ${ or ` after)
  let at = s + 1, delim = s;
  for (let k = 0; k < spans.length; k++) {
    const sp = spans[k];
    const x = A(sp);
    let open = at;
    while (open < e && !(ch(open) === 36 && ch(open + 1) === 123 && !escapedAt(open))) open++;
    quasis.push(templElem(delim, open + 2, false, at, open));
    exprs.push(conv(x));
    let close = x >= 0 ? exprEndOf(x) : open + 2;
    close = find(close, 125);
    delim = close;
    at = close + 1;
  }
  quasis.push(templElem(delim, e, true, at, e - 1));
  return { quasis, exprs };
}
function escapedAt(i) {
  let k = 0;
  while (i - 1 - k >= 0 && ch(i - 1 - k) === 92) k++;
  return k % 2 === 1;
}
// the extent of an expression node in the source (parentheses included as written by vlint)
function exprStartOf(n) { return P(n); }
function exprEndOf(n) { return E(n); }

// ---- the program

function program(root, sourceType) {
  const stmts = items(root);
  const body = [];
  let directives = true;
  for (const st of stmts) {
    if (directives && K(st) === N_EXPRSTMT && K(A(st)) === N_STR) {
      const lit = strLit(A(st));
      const o = { __proto__: NodeProto, type: "ExpressionStatement", expression: lit, directive: lit.raw.slice(1, -1) };
      body.push(fin(o, P(st), E(st)));
      continue;
    }
    directives = false;
    body.push(stmt(st));
  }
  const end = src.length - baseOff;
  const prog = {
    __proto__: NodeProto,
    type: "Program",
    body,
    sourceType,
    get comments() {
      return comments === null && initComments(), comments;
    },
    get tokens() {
      return tokens === null && initTokens(), tokens;
    },
    start: 0,
    end,
    range: [0, end],
    parent: null,
  };
  let start = end;
  if (body.length > 0) {
    const first = body[0];
    start = first.start;
    if ((first.type === "ExportNamedDeclaration" || first.type === "ExportDefaultDeclaration") && first.declaration && first.declaration.type === "ClassDeclaration" && first.declaration.decorators.length > 0) {
      const ds = first.declaration.decorators[0].start;
      if (ds < start) start = ds;
    }
  }
  prog.start = prog.range[0] = start;
  return prog;
}

// ---- statements

function stmtList(l) {
  return items(l).map(stmt);
}
// a function body: directives first
function funcBody(n) {
  const stmts = items(A(n));
  const body = [];
  let directives = true;
  for (const st of stmts) {
    if (directives && K(st) === N_EXPRSTMT && K(A(st)) === N_STR) {
      const lit = strLit(A(st));
      const o = { __proto__: NodeProto, type: "ExpressionStatement", expression: lit, directive: lit.raw.slice(1, -1) };
      body.push(fin(o, P(st), E(st)));
      continue;
    }
    directives = false;
    body.push(stmt(st));
  }
  return fin({ __proto__: NodeProto, type: "BlockStatement", body }, P(n), E(n));
}

function stmt(n) {
  const k = K(n);
  switch (k) {
    case N_BLOCK:
      return fin({ __proto__: NodeProto, type: "BlockStatement", body: stmtList(A(n)) }, P(n), E(n));
    case N_EMPTY:
      return fin({ __proto__: NodeProto, type: "EmptyStatement" }, P(n), E(n));
    case N_EXPRSTMT:
      return fin({ __proto__: NodeProto, type: "ExpressionStatement", expression: expr(A(n)), directive: null }, P(n), E(n));
    case N_IF:
      return fin({ __proto__: NodeProto, type: "IfStatement", test: expr(A(n)), consequent: stmt(B(n)), alternate: C(n) >= 0 ? stmt(C(n)) : null }, P(n), E(n));
    case N_RETURN:
      return fin({ __proto__: NodeProto, type: "ReturnStatement", argument: A(n) >= 0 ? expr(A(n)) : null }, P(n), E(n));
    case N_WHILE:
      return fin({ __proto__: NodeProto, type: "WhileStatement", test: expr(A(n)), body: stmt(B(n)) }, P(n), E(n));
    case N_DO:
      return fin({ __proto__: NodeProto, type: "DoWhileStatement", body: stmt(A(n)), test: expr(B(n)) }, P(n), E(n));
    case N_FOR: {
      const init = A(n) < 0 ? null : (K(A(n)) === N_VAR ? varDecl(A(n)) : expr(A(n)));
      return fin({ __proto__: NodeProto, type: "ForStatement", init, test: B(n) >= 0 ? expr(B(n)) : null, update: C(n) >= 0 ? expr(C(n)) : null, body: stmt(D(n)) }, P(n), E(n));
    }
    case N_FORIN: {
      const left = K(A(n)) === N_VAR ? varDecl(A(n)) : target(A(n));
      if (F(n) === 0) return fin({ __proto__: NodeProto, type: "ForInStatement", left, right: expr(B(n)), body: stmt(C(n)) }, P(n), E(n));
      return fin({ __proto__: NodeProto, type: "ForOfStatement", await: F(n) === 2, left, right: expr(B(n)), body: stmt(C(n)) }, P(n), E(n));
    }
    case N_BREAK:
    case N_CONTINUE: {
      let label = null;
      if (S(n) > 0) {
        const at = skip(P(n) + (k === N_BREAK ? 5 : 8));
        label = identAt(name(n), at);
      }
      return fin({ __proto__: NodeProto, type: k === N_BREAK ? "BreakStatement" : "ContinueStatement", label }, P(n), E(n));
    }
    case N_THROW:
      return fin({ __proto__: NodeProto, type: "ThrowStatement", argument: expr(A(n)) }, P(n), E(n));
    case N_TRY: {
      const block = stmt(A(n));
      let handler = null;
      if (C(n) >= 0) {
        const cs = skip(E(A(n)));
        let param = null;
        if (B(n) >= 0) {
          const d = B(n);
          param = pattern(A(d));
          if (B(d) >= 0) {
            param.typeAnnotation = annot(B(d));
            setEnd(param, param.typeAnnotation.end);
          }
        }
        handler = fin({ __proto__: NodeProto, type: "CatchClause", param, body: stmt(C(n)) }, cs, E(C(n)));
      }
      return fin({ __proto__: NodeProto, type: "TryStatement", block, handler, finalizer: D(n) >= 0 ? stmt(D(n)) : null }, P(n), E(n));
    }
    case N_SWITCH: {
      const cases = items(B(n)).map((c) => fin({ __proto__: NodeProto, type: "SwitchCase", test: A(c) >= 0 ? expr(A(c)) : null, consequent: stmtList(B(c)) }, P(c), E(c)));
      return fin({ __proto__: NodeProto, type: "SwitchStatement", discriminant: expr(A(n)), cases }, P(n), E(n));
    }
    case N_LABEL:
      return fin({ __proto__: NodeProto, type: "LabeledStatement", label: identAt(name(n), P(n)), body: stmt(A(n)) }, P(n), E(n));
    case N_DEBUGGER:
      return fin({ __proto__: NodeProto, type: "DebuggerStatement" }, P(n), E(n));
    case N_WITH:
      return fin({ __proto__: NodeProto, type: "WithStatement", object: expr(A(n)), body: stmt(B(n)) }, P(n), E(n));
    case N_VAR:
      return exported(n, D(n), (s) => varDecl(n, s));
    case N_FUNC:
      return exported(n, F(n), (s) => func(n, s, true));
    case N_CLASS:
      return exported(n, F(n), (s) => klass(n, s, true));
    case N_INTERFACE:
      return exported(n, D(n), (s) => iface(n, s));
    case N_TYPEALIAS:
      return exported(n, D(n), (s) => typeAlias(n, s));
    case N_ENUM:
      return exported(n, F(n), (s) => enumDecl(n, s));
    case N_MODULE:
      return exported(n, F(n), (s) => moduleDecl(n, s));
    case N_IMPORT:
      return importDecl(n);
    case N_EXPORT:
      return exportDecl(n);
    case N_EXPORTDEFAULT: {
      // export default <expression>
      const x = A(n);
      return fin({ __proto__: NodeProto, type: "ExportDefaultDeclaration", declaration: expr(x), exportKind: "value" }, P(n), E(n));
    }
    case N_IMPORTEQ:
      return exported(n, F(n), (s) => importEq(n, s));
    case N_EXPORTASSIGN:
      return fin({ __proto__: NodeProto, type: "TSExportAssignment", expression: expr(A(n)) }, P(n), E(n));
    case N_NSEXPORT: {
      const at = skipWords(P(n), ["export", "as", "namespace"]);
      return fin({ __proto__: NodeProto, type: "TSNamespaceExportDeclaration", id: identAt(name(n), at) }, P(n), E(n));
    }
  }
  // an expression where a statement was expected (error recovery)
  return fin({ __proto__: NodeProto, type: "ExpressionStatement", expression: expr(n), directive: null }, P(n), E(n));
}

// export / export default around a declaration whose modifiers are mods: build(start of the
// declaration itself)
function exported(n, mods, build) {
  if (K(n) === N_VAR) return exportedVar(n, mods, build);
  if (K(n) === N_IMPORTEQ) {
    // export import a = b: one declaration from `export`
    const d = build(P(n));
    const w = (mods & M_EXPORT) ? wordBefore(P(n)) : null;
    if (w === null || w.word !== "export") return d;
    return fin({ __proto__: NodeProto, type: "ExportNamedDeclaration", declaration: d, specifiers: [], source: null, exportKind: "value", attributes: [] }, w.at, E(n));
  }
  if ((mods & M_EXPORT) === 0) return build(P(n));
  const isDefault = (mods & M_DEFAULT) !== 0;
  const s = skipWords(P(n), isDefault ? ["export", "default"] : ["export"]);
  const decl = build(s);
  if (isDefault) return fin({ __proto__: NodeProto, type: "ExportDefaultDeclaration", declaration: decl, exportKind: "value" }, P(n), E(n));
  const tk = declKind(decl);
  return fin({ __proto__: NodeProto, type: "ExportNamedDeclaration", declaration: decl, specifiers: [], source: null, exportKind: tk, attributes: [] }, P(n), E(n));
}

// vlint's N_VAR starts at its keyword (var, let, const, using, await): export and declare are before
function wordBefore(i) {
  let j = back(i);
  if (j < 0 || !isIdByte(ch(j))) return null;
  let a = j;
  while (a > 0 && isIdByte(ch(a - 1))) a--;
  return { word: srcBytes(a, j + 1), at: a };
}
function exportedVar(n, mods, build) {
  let s = P(n);
  let declStart = s, exportStart = -1;
  if (mods > 0 && (mods & (M_EXPORT | M_DECLARE))) {
    let w = wordBefore(s);
    if (w && w.word === "declare" && (mods & M_DECLARE)) { declStart = w.at; w = wordBefore(w.at); }
    if (w && w.word === "export" && (mods & M_EXPORT)) exportStart = w.at;
  }
  const decl = build(declStart);
  if (exportStart < 0) return decl;
  return fin({ __proto__: NodeProto, type: "ExportNamedDeclaration", declaration: decl, specifiers: [], source: null, exportKind: declKind(decl), attributes: [] }, exportStart, E(n));
}
function declKind(decl) {
  return decl.declare === true || decl.type === "TSInterfaceDeclaration" || decl.type === "TSTypeAliasDeclaration" ? "type" : "value";
}

function varDecl(n, s) {
  const f = F(n);
  let kind = ["var", "let", "const", "using"][f];
  if (f === 3 && wordAt(skipWords(s, ["declare"])) === "await") kind = "await using";
  const declarations = items(A(n)).map((d) => {
    const id = pattern(A(d));
    if (B(d) >= 0) {
      id.typeAnnotation = annot(B(d));
      setEnd(id, id.typeAnnotation.end);
    }
    return fin({ __proto__: NodeProto, type: "VariableDeclarator", id, init: C(d) >= 0 ? expr(C(d)) : null, definite: (F(d) & M_EXCL) !== 0 }, P(d), E(d));
  });
  const declare = D(n) > 0 && (D(n) & M_DECLARE) !== 0;
  if (s === undefined) s = P(n);
  return fin({ __proto__: NodeProto, type: "VariableDeclaration", kind, declarations, declare }, s, E(n));
}

// a function (declaration or expression): n is N_FUNC / N_FUNCEXPR
function func(n, s, isDecl) {
  const f = F(n);
  const hasBody = D(n) >= 0;
  let type = isDecl ? (hasBody ? "FunctionDeclaration" : "TSDeclareFunction") : "FunctionExpression";
  let id = null;
  if (S(n) > 0) {
    const np = npos.get(n);
    if (np !== undefined) id = identAt(name(n), np);
    else {
      let at = skipWords(s, ["async", "function"]);
      if (ch(at) === 42) at = skip(at + 1);
      id = identAt(name(n), at);
    }
  }
  const o = {
    __proto__: NodeProto,
    type,
    id,
    generator: (f & M_GENERATOR) !== 0,
    async: (f & M_ASYNC) !== 0,
    declare: (f & M_DECLARE) !== 0,
    typeParameters: A(n) >= 0 ? typeParams(A(n)) : null,
    params: params(B(n)),
    returnType: C(n) >= 0 ? returnType(C(n)) : null,
    body: hasBody ? funcBody(D(n)) : null,
    expression: false,
  };
  return fin(o, s, E(n));
}

// a return type (after a colon, or => in a function type)
function returnType(n) {
  const t = K(n) === N_TPRED ? typePred(n) : type(n);
  const colon = back(Math.min(P(n), backToBytes(t.start)));
  const o = { __proto__: NodeProto, type: "TSTypeAnnotation", typeAnnotation: t };
  // (=> in a function type: the annotation starts at =)
  o.start = u(ch(colon) === 62 && ch(colon - 1) === 61 ? colon - 1 : colon);
  o.end = Math.max(u(E(n)), t.end);
  o.range = [o.start, o.end];
  o.parent = null;
  return o;
}

function params(l) {
  return items(l).map(param);
}

function decoratorsBefore(s) {
  // the decorators that end before s and haven't been attached (vlint keeps them in a list)
  const out = [];
  while (decoAt.length > 0 && decoStart(decoAt[0]) < s) {
    out.push(decorator(decoAt.shift()));
  }
  return out;
}
function decoStart(x) {
  // the @ before the expression
  let i = P(x) - 1;
  while (i > 0 && ch(i) !== 64) i--;
  return i;
}
function decorator(x) {
  return fin({ __proto__: NodeProto, type: "Decorator", expression: expr(x) }, decoStart(x), E(x));
}

function param(p) {
  const f = F(p);
  const decorators = decoratorsBefore(P(p));
  const nameNode = A(p);
  // `this` parameter
  if (K(nameNode) === N_ID && name(nameNode) === "this" && P(nameNode) === P(p) && wordAt(P(p)) === "this") {
    const id = ident("this", P(nameNode), E(nameNode));
    id.decorators = decorators;
    if (B(p) >= 0) {
      id.typeAnnotation = annot(B(p));
      setEnd(id, id.typeAnnotation.end);
    }
    return id;
  }
  const access = f & M_PUBLIC ? "public" : f & M_PRIVATE ? "private" : f & M_PROTECTED ? "protected" : null;
  const readonly = (f & M_READONLY) !== 0, override = (f & M_OVERRIDE) !== 0;
  const optional = (f & M_OPTIONAL) !== 0;
  let pat;
  if (f & M_REST) {
    // ...x: the rest element starts at ...
    const dots = back(P(nameNode)) - 2;
    const arg = pattern(nameNode);
    pat = { __proto__: NodeProto, type: "RestElement", decorators, argument: arg, optional, typeAnnotation: null, value: null };
    fin(pat, dots, E(nameNode));
    if (decorators.length > 0) setStart(pat, decorators[0].start);
    if (B(p) >= 0) {
      pat.typeAnnotation = annot(B(p));
      setEnd(pat, pat.typeAnnotation.end);
    } else if (optional) setEnd(pat, u(E(p)));
    if (C(p) >= 0) {
      // (a rest parameter with a default: invalid, kept)
      const ap = { __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left: pat, right: expr(C(p)), optional: false, typeAnnotation: null };
      return fin(ap, P(p), E(p));
    }
    return pat;
  }
  const left = pattern(nameNode);
  if (access === null && !readonly && !override) {
    if (C(p) >= 0) {
      left.decorators = [];
      left.optional = false;
      if (B(p) >= 0) {
        left.typeAnnotation = annot(B(p));
        setEnd(left, left.typeAnnotation.end);
      }
      const ap = { __proto__: NodeProto, type: "AssignmentPattern", decorators, left, right: expr(C(p)), optional, typeAnnotation: null };
      return fin(ap, P(p), E(p));
    }
    left.decorators = decorators;
    left.optional = optional;
    if (B(p) >= 0) {
      left.typeAnnotation = annot(B(p));
      setEnd(left, left.typeAnnotation.end);
    } else if (optional) setEnd(left, u(E(p)));
    return left;
  }
  // a parameter property
  const pp = { __proto__: NodeProto, type: "TSParameterProperty", accessibility: access, decorators, override, parameter: null, readonly, static: false };
  fin(pp, P(p), E(p));
  if (decorators.length > 0) setStart(pp, decorators[0].start);
  left.decorators = [];
  if (C(p) >= 0) {
    left.optional = false;
    if (B(p) >= 0) {
      left.typeAnnotation = annot(B(p));
      setEnd(left, left.typeAnnotation.end);
    }
    const right = expr(C(p));
    const ap = { __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left, right, optional: false, typeAnnotation: null };
    ap.start = left.start;
    ap.end = right.end;
    ap.range = [ap.start, ap.end];
    ap.parent = null;
    pp.parameter = ap;
  } else {
    left.optional = optional;
    if (B(p) >= 0) {
      left.typeAnnotation = annot(B(p));
      setEnd(left, left.typeAnnotation.end);
    } else if (optional) setEnd(left, u(E(p)));
    pp.parameter = left;
  }
  return pp;
}

// a binding pattern: N_ID, N_OBJPAT, N_ARRPAT
function pattern(n) {
  const k = K(n);
  if (k === N_ID) return idNode(n);
  if (k === N_OBJPAT) {
    const properties = items(A(n)).map((e) => {
      if (F(e) & M_REST) {
        const arg = pattern(B(e));
        return fin({ __proto__: NodeProto, type: "RestElement", decorators: [], argument: arg, optional: false, typeAnnotation: null, value: null }, P(e), E(e));
      }
      const shorthand = A(e) < 0;
      const keyNode = shorthand ? B(e) : A(e);
      const computed = K(keyNode) === N_COMPUTED;
      const key = propKey(keyNode);
      let value = pattern(B(e));
      if (C(e) >= 0) {
        const right = expr(C(e));
        value = fin({ __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left: value, right, optional: false, typeAnnotation: null }, shorthand ? P(B(e)) : P(B(e)), E(e));
      }
      return fin({ __proto__: NodeProto, type: "Property", kind: "init", key, value, method: false, shorthand, computed, optional: false }, P(e), E(e));
    });
    return fin({ __proto__: NodeProto, type: "ObjectPattern", decorators: [], properties, optional: false, typeAnnotation: null }, P(n), E(n));
  }
  if (k === N_ARRPAT) {
    const elements = items(A(n)).map((e) => {
      if (K(e) === N_OMIT) return null;
      if (F(e) & M_REST) {
        const arg = pattern(B(e));
        return fin({ __proto__: NodeProto, type: "RestElement", decorators: [], argument: arg, optional: false, typeAnnotation: null, value: null }, P(e), E(e));
      }
      let value = pattern(B(e));
      if (C(e) >= 0) {
        value = fin({ __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left: value, right: expr(C(e)), optional: false, typeAnnotation: null }, P(e), E(e));
      }
      return value;
    });
    return fin({ __proto__: NodeProto, type: "ArrayPattern", decorators: [], elements, optional: false, typeAnnotation: null }, P(n), E(n));
  }
  return expr(n);
}

// an expression on the left of an assignment (or for-in/of): patterns written as expressions
function target(n) {
  const k = K(n);
  if (k === N_OBJECT) {
    const properties = items(A(n)).map((pr) => {
      const pk = K(pr);
      if (pk === N_SPREAD) return fin({ __proto__: NodeProto, type: "RestElement", decorators: [], argument: target(A(pr)), optional: false, typeAnnotation: null, value: null }, P(pr), E(pr));
      if (pk === N_SHORTHAND) {
        const key = identAt(name(pr), P(pr));
        let value = identAt(name(pr), P(pr));
        if (B(pr) >= 0) value = fin({ __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left: value, right: expr(B(pr)), optional: false, typeAnnotation: null }, P(pr), E(pr));
        return fin({ __proto__: NodeProto, type: "Property", kind: "init", key, value, method: false, shorthand: true, computed: false, optional: false }, P(pr), E(pr));
      }
      if (pk === N_PROPASSIGN) {
        const computed = K(A(pr)) === N_COMPUTED;
        return fin({ __proto__: NodeProto, type: "Property", kind: "init", key: propKey(A(pr)), value: targetWithDefault(B(pr)), method: false, shorthand: false, computed, optional: false }, P(pr), E(pr));
      }
      return objMember(pr);
    });
    return fin({ __proto__: NodeProto, type: "ObjectPattern", decorators: [], properties, optional: false, typeAnnotation: null }, P(n), E(n));
  }
  if (k === N_ARRAY) {
    const elements = items(A(n)).map((x) => {
      if (K(x) === N_OMIT) return null;
      if (K(x) === N_SPREAD) return fin({ __proto__: NodeProto, type: "RestElement", decorators: [], argument: target(A(x)), optional: false, typeAnnotation: null, value: null }, P(x), E(x));
      return targetWithDefault(x);
    });
    return fin({ __proto__: NodeProto, type: "ArrayPattern", decorators: [], elements, optional: false, typeAnnotation: null }, P(n), E(n));
  }
  if (k === N_PAREN) return target(A(n));
  return expr(n);
}
// x = default inside a pattern written as an expression
function targetWithDefault(n) {
  if (K(n) === N_BINARY && F(n) === 62) {
    return fin({ __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left: target(A(n)), right: expr(B(n)), optional: false, typeAnnotation: null }, P(n), E(n));
  }
  return target(n);
}

function propKey(n) {
  const k = K(n);
  if (k === N_ID) return idNode(n);
  if (k === N_STR) return strLit(n);
  if (k === N_NUM) return numLit(n);
  if (k === N_BIGINT) return bigLit(n);
  if (k === N_COMPUTED) return expr(A(n));
  if (k === N_PRIVNAME) return privName(n);
  return expr(n);
}
function privName(n) {
  return fin({ __proto__: NodeProto, type: "PrivateIdentifier", name: name(n).replace(/^#/, "") }, P(n), E(n));
}

// ---- classes

function klass(n, s, isDecl) {
  const f = F(n);
  const decorators = decoratorsBefore(s);
  let id = null;
  if (S(n) > 0) {
    const np = npos.get(n);
    id = identAt(name(n), np !== undefined ? np : skipWords(s, ["abstract", "declare", "class"]));
  }
  let superClass = null, superTypeArguments = null;
  if (B(n) >= 0) {
    const h = B(n);
    superClass = expr(A(h));
    if (B(h) >= 0) superTypeArguments = typeArgs(B(h));
  }
  const impl = items(C(n)).map((h) => fin({ __proto__: NodeProto, type: "TSClassImplements", expression: entityExpr(A(h)), typeArguments: B(h) >= 0 ? typeArgs(B(h)) : null }, P(h), E(h)));
  const typeParameters = A(n) >= 0 ? typeParams(A(n)) : null;
  const bodyStart = find(C(n) >= 0 ? E(C(n)) : B(n) >= 0 ? E(B(n)) : A(n) >= 0 ? E(A(n)) : id ? idEnd(npos.get(n) ?? 0) : s + 5, 123);
  const members = items(D(n)).filter((m) => K(m) !== N_SEMIMEMBER).map(classMember);
  const body = fin({ __proto__: NodeProto, type: "ClassBody", body: members }, bodyStart, E(n));
  const o = {
    __proto__: NodeProto,
    type: isDecl ? "ClassDeclaration" : "ClassExpression",
    decorators,
    id,
    typeParameters,
    superClass,
    superTypeArguments,
    implements: impl,
    body,
    abstract: (f & M_ABSTRACT) !== 0,
    declare: (f & M_DECLARE) !== 0,
  };
  fin(o, s, E(n));
  // (decorators before `export` don't belong to the class's span)
  const wb = wordBefore(s);
  const afterExport = wb !== null && (wb.word === "export" || wb.word === "default");
  if (decorators.length > 0 && decorators[0].start < o.start && !afterExport) setStart(o, decorators[0].start);
  return o;
}

function accessibility(f) {
  return f & M_PUBLIC ? "public" : f & M_PRIVATE ? "private" : f & M_PROTECTED ? "protected" : null;
}

function classMember(m) {
  const o = classMember0(m);
  if (o.decorators && o.decorators.length > 0 && o.decorators[0].start < o.start) setStart(o, o.decorators[0].start);
  return o;
}
function classMember0(m) {
  const k = K(m);
  const f = F(m);
  const decorators = decoratorsBefore(P(m));
  if (k === N_STATICBLOCK) {
    return fin({ __proto__: NodeProto, type: "StaticBlock", body: stmtList(A(A(m))) }, P(m), E(m));
  }
  if (k === N_PROP) {
    const isAcc = (f & M_ACCESSOR) !== 0;
    const abstract = (f & M_ABSTRACT) !== 0;
    const computed = K(A(m)) === N_COMPUTED;
    const key = propKey(A(m));
    let type = isAcc ? (abstract ? "TSAbstractAccessorProperty" : "AccessorProperty") : abstract ? "TSAbstractPropertyDefinition" : "PropertyDefinition";
    if (isAcc) {
      return fin({ __proto__: NodeProto, type, decorators, key, typeAnnotation: B(m) >= 0 ? annot(B(m)) : null, value: C(m) >= 0 ? expr(C(m)) : null, computed, static: (f & M_STATIC) !== 0, override: (f & M_OVERRIDE) !== 0, definite: (f & M_EXCL) !== 0, accessibility: accessibility(f), declare: false, optional: false, readonly: false }, P(m), E(m));
    }
    return fin({ __proto__: NodeProto, type, decorators, key, typeAnnotation: B(m) >= 0 ? annot(B(m)) : null, value: C(m) >= 0 ? expr(C(m)) : null, computed, static: (f & M_STATIC) !== 0, declare: (f & M_DECLARE) !== 0, override: (f & M_OVERRIDE) !== 0, optional: (f & M_OPTIONAL) !== 0, definite: (f & M_EXCL) !== 0, readonly: (f & M_READONLY) !== 0, accessibility: accessibility(f) }, P(m), E(m));
  }
  if (k === N_INDEXSIG) return indexSig(m);
  // methods, accessors, constructors
  let kind = "method", keyNode = A(m), sig = B(m), body = C(m);
  if (k === N_GET) kind = "get";
  else if (k === N_SET) kind = "set";
  else if (k === N_CTOR) kind = "constructor";
  let key, computed = false;
  if (k === N_CTOR) {
    // the key `constructor` (or "constructor")
    const at = skipWords(P(m), ["public", "private", "protected", "static", "declare", "override", "async", "abstract", "readonly", "export", "default", "accessor"]);
    if (ch(at) === 34 || ch(at) === 39) {
      const e = at + 13;
      const raw = srcBytes(at, e);
      key = literal("constructor", raw, at, e);
    } else key = identAt("constructor", at);
  } else {
    computed = K(keyNode) === N_COMPUTED;
    key = propKey(keyNode);
  }
  const abstract = (f & M_ABSTRACT) !== 0;
  const value = funcValue(m, sig, body, f, keyEnd(keyNode, k, key));
  const type = abstract ? "TSAbstractMethodDefinition" : "MethodDefinition";
  return fin({ __proto__: NodeProto, type, decorators, key, value, kind, computed, static: (f & M_STATIC) !== 0, override: (f & M_OVERRIDE) !== 0, optional: (f & M_OPTIONAL) !== 0, accessibility: accessibility(f) }, P(m), E(m));
}
// where a method's function starts: its ( or <
function keyEnd(keyNode, k, key) {
  return null;
}
// the function of a method / accessor / constructor: from its ( (or <) to its end
function funcValue(m, sig, body, f, _) {
  const tp = A(sig) >= 0 ? typeParams(A(sig)) : null;
  const ps = params(B(sig));
  const rt = C(sig) >= 0 ? returnType(C(sig)) : null;
  const b = body >= 0 ? funcBody(body) : null;
  const type = body >= 0 ? "FunctionExpression" : "TSEmptyBodyFunctionExpression";
  const o = { __proto__: NodeProto, type, id: null, generator: (f & M_GENERATOR) !== 0, async: (f & M_ASYNC) !== 0, declare: false, typeParameters: tp, params: ps, returnType: rt, body: b, expression: false };
  // starts at the signature's ( or <
  const s = A(sig) >= 0 ? P(A(sig)) : P(B(sig));
  return fin(o, s, E(m));
}

function indexSig(m) {
  const f = F(m);
  const parameters = items(A(m)).map((p) => {
    const id = identAt(name(A(p)), P(A(p)));
    if (B(p) >= 0) {
      id.typeAnnotation = annot(B(p));
      setEnd(id, id.typeAnnotation.end);
    }
    return id;
  });
  return fin({ __proto__: NodeProto, type: "TSIndexSignature", parameters, typeAnnotation: B(m) >= 0 ? annot(B(m)) : null, readonly: (f & M_READONLY) !== 0, static: (f & M_STATIC) !== 0, accessibility: accessibility(f) }, P(m), E(m));
}

// ---- TypeScript declarations

function iface(n, s) {
  const np = npos.get(n);
  const id = identAt(name(n), np !== undefined ? np : skipWords(s, ["declare", "interface"]));
  const ext = items(B(n)).map((h) => fin({ __proto__: NodeProto, type: "TSInterfaceHeritage", expression: entityExpr(A(h)), typeArguments: B(h) >= 0 ? typeArgs(B(h)) : null }, P(h), E(h)));
  const bodyNode = C(n);
  const body = fin({ __proto__: NodeProto, type: "TSInterfaceBody", body: items(bodyNode).map(typeMember) }, P(bodyNode), E(bodyNode));
  return fin({ __proto__: NodeProto, type: "TSInterfaceDeclaration", id, typeParameters: A(n) >= 0 ? typeParams(A(n)) : null, extends: ext, body, declare: (D(n) & M_DECLARE) !== 0 }, s, E(n));
}

function typeAlias(n, s) {
  const np = npos.get(n);
  const id = identAt(name(n), np !== undefined ? np : skipWords(s, ["declare", "type"]));
  return fin({ __proto__: NodeProto, type: "TSTypeAliasDeclaration", id, typeParameters: A(n) >= 0 ? typeParams(A(n)) : null, typeAnnotation: type(B(n)), declare: (D(n) & M_DECLARE) !== 0 }, s, E(n));
}

function enumDecl(n, s) {
  const np = npos.get(n);
  const id = identAt(name(n), np !== undefined ? np : skipWords(s, ["declare", "const", "enum"]));
  const lst = A(n);
  const members = items(lst).map((m) => {
    const kn = A(m);
    const computed = K(kn) === N_COMPUTED;
    let key;
    if (K(kn) === N_ID) key = idNode(kn);
    else if (K(kn) === N_STR) key = strLit(kn);
    else if (computed && (K(A(kn)) === N_STR || K(A(kn)) === N_NOSUBTEMPL)) key = K(A(kn)) === N_STR ? strLit(A(kn)) : expr(A(kn));
    else key = propKey(kn);
    return fin({ __proto__: NodeProto, type: "TSEnumMember", id: key, initializer: B(m) >= 0 ? expr(B(m)) : null, computed }, P(m), E(m));
  });
  const body = fin({ __proto__: NodeProto, type: "TSEnumBody", members }, P(lst), E(n));
  return fin({ __proto__: NodeProto, type: "TSEnumDeclaration", id, body, const: (F(n) & M_CONST) !== 0, declare: (F(n) & M_DECLARE) !== 0 }, s, E(n));
}

function moduleDecl(n, s) {
  const f = F(n);
  const declare = (f & M_DECLARE) !== 0;
  if (f & MOD_GLOBAL) {
    const id = idNode(A(n));
    const body = B(n) >= 0 ? fin({ __proto__: NodeProto, type: "TSModuleBlock", body: stmtList(B(n)) }, P(B(n)), E(n)) : null;
    return fin({ __proto__: NodeProto, type: "TSModuleDeclaration", id, body, kind: "global", declare, global: true }, s, E(n));
  }
  const kind = f & MOD_NAMESPACE ? "namespace" : "module";
  const nameNode = A(n);
  let id;
  if (K(nameNode) === N_STR) id = strLit(nameNode);
  else id = entity(nameNode);
  if (B(n) < 0) {
    return fin({ __proto__: NodeProto, type: "TSModuleDeclaration", id, kind, declare, global: false }, s, E(n));
  }
  const body = fin({ __proto__: NodeProto, type: "TSModuleBlock", body: stmtList(B(n)) }, P(B(n)), E(n));
  return fin({ __proto__: NodeProto, type: "TSModuleDeclaration", id, body, kind, declare, global: false }, s, E(n));
}

function importEq(n, s) {
  const at = skipWords(s, ["import", "type"]);
  const id = identAt(name(n), at);
  const r = A(n);
  let moduleReference;
  if (K(r) === N_EXTERNALREF) {
    const req = skipWords(idEnd(at), []);
    const rs = skip(find(idEnd(at), 61) + 1);
    moduleReference = fin({ __proto__: NodeProto, type: "TSExternalModuleReference", expression: strLit(A(r)) }, rs, E(r) + (ch(E(r)) === 41 ? 1 : 0));
    // (the reference ends at its ')')
    const close = find(E(A(r)), 41);
    moduleReference.end = u(close + 1);
    moduleReference.range[1] = moduleReference.end;
  } else moduleReference = entity(r);
  const typeOnly = wordAt(skip(s + 6)) === "type" && skip(s + 6) !== at;
  return fin({ __proto__: NodeProto, type: "TSImportEqualsDeclaration", id, moduleReference, importKind: typeOnly ? "type" : "value" }, s, E(n));
}

// ---- modules

function modName(n) {
  if (K(n) === N_STR) return strLit(n);
  return idNode(n);
}

function importDecl(n) {
  const specifiers = [];
  if (B(n) >= 0) {
    const d = B(n);
    specifiers.push(fin({ __proto__: NodeProto, type: "ImportDefaultSpecifier", local: idNode(d) }, P(d), E(d)));
  }
  if (C(n) >= 0) {
    const c = C(n);
    const star = find(B(n) >= 0 ? E(B(n)) : skipWords(P(n), ["import", "type"]), 42);
    specifiers.push(fin({ __proto__: NodeProto, type: "ImportNamespaceSpecifier", local: idNode(c) }, star, E(c)));
  }
  for (const sp of items(D(n))) {
    const typeOnly = (F(sp) & M_TYPEONLY) !== 0;
    const local = identAt(name(sp), E(sp) - Buffer.byteLength(name(sp)));
    let imported;
    if (B(sp) >= 0) imported = modName(B(sp));
    else imported = identAt(name(sp), local.start === undefined ? 0 : backToBytes(local.start));
    // (a shorthand specifier: the imported name is the local one, same span)
    if (B(sp) < 0) {
      imported = ident(local.name, 0, 0);
      imported.start = local.start; imported.end = local.end; imported.range = [local.start, local.end];
    }
    specifiers.push(fin({ __proto__: NodeProto, type: "ImportSpecifier", imported, local, importKind: typeOnly ? "type" : "value" }, P(sp), E(sp)));
  }
  const typeOnly = (F(n) & M_TYPEONLY) !== 0;
  return fin({ __proto__: NodeProto, type: "ImportDeclaration", specifiers, source: strLit(A(n)), phase: null, attributes: attributesAfter(E(A(n))), importKind: typeOnly ? "type" : "value" }, P(n), E(n));
}
// with { type: "json" } after a module source (vlint's tree doesn't keep it): read from the source
function attributesAfter(e) {
  let i = skip(e);
  const w = wordAt(i);
  if (w !== "with" && w !== "assert") return [];
  i = skip(i + w.length);
  if (ch(i) !== 123) return [];
  i = skip(i + 1);
  const out = [];
  while (i < bytes.length && ch(i) !== 125) {
    let key;
    const ks = i;
    if (ch(i) === 34 || ch(i) === 39) {
      const q = ch(i);
      let j = i + 1;
      while (j < bytes.length && ch(j) !== q) { if (ch(j) === 92) j++; j++; }
      const raw = srcBytes(i, j + 1);
      key = literal(strValue(raw), raw, i, j + 1);
      i = j + 1;
    } else {
      const ke = idEnd(i);
      key = ident(srcBytes(i, ke), i, ke);
      i = ke;
    }
    i = skip(i);
    if (ch(i) !== 58) break;
    i = skip(i + 1);
    const q = ch(i);
    if (q !== 34 && q !== 39) break;
    let j = i + 1;
    while (j < bytes.length && ch(j) !== q) { if (ch(j) === 92) j++; j++; }
    const raw = srcBytes(i, j + 1);
    const value = literal(strValue(raw), raw, i, j + 1);
    out.push(fin({ __proto__: NodeProto, type: "ImportAttribute", key, value }, ks, j + 1));
    i = skip(j + 1);
    if (ch(i) === 44) i = skip(i + 1);
  }
  return out;
}

function backToBytes(p) {
  p += baseOff;
  if (u16 === null) return p;
  // (rare: a non-ASCII file) the byte offset of a UTF-16 offset
  let lo = 0, hi = u16.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (u16[mid] < p) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function exportDecl(n) {
  const typeOnly = (F(n) & M_TYPEONLY) !== 0;
  const kind = typeOnly ? "type" : "value";
  if (B(n) < 0) {
    // export * (as x) from "m"
    const exported = C(n) >= 0 ? modName(C(n)) : null;
    return fin({ __proto__: NodeProto, type: "ExportAllDeclaration", exported, source: strLit(A(n)), attributes: attributesAfter(E(A(n))), exportKind: kind }, P(n), E(n));
  }
  const specifiers = items(B(n)).map((sp) => {
    const spType = (F(sp) & M_TYPEONLY) !== 0;
    let local, exported;
    if (B(sp) >= 0) {
      local = modName(B(sp));
      const e = E(sp);
      // the exported name: a string or an identifier ending the specifier
      if (ch(e - 1) === 34 || ch(e - 1) === 39) {
        let q = e - 2;
        while (q > 0 && ch(q) !== ch(e - 1)) q--;
        const raw = srcBytes(q, e);
        exported = literal(strValue(raw), raw, q, e);
      } else exported = identAt(name(sp), e - Buffer.byteLength(name(sp)));
    } else {
      const e = E(sp);
      if (ch(e - 1) === 34 || ch(e - 1) === 39) {
        let q = e - 2;
        while (q > 0 && ch(q) !== ch(e - 1)) q--;
        const raw = srcBytes(q, e);
        local = literal(strValue(raw), raw, q, e);
        exported = literal(strValue(raw), raw, q, e);
      } else {
        local = identAt(name(sp), e - Buffer.byteLength(name(sp)));
        exported = identAt(name(sp), e - Buffer.byteLength(name(sp)));
      }
    }
    return fin({ __proto__: NodeProto, type: "ExportSpecifier", local, exported, exportKind: spType ? "type" : "value" }, P(sp), E(sp));
  });
  return fin({ __proto__: NodeProto, type: "ExportNamedDeclaration", declaration: null, specifiers, source: A(n) >= 0 ? strLit(A(n)) : null, exportKind: kind, attributes: A(n) >= 0 ? attributesAfter(E(A(n))) : [] }, P(n), E(n));
}

// ---- expressions

// whether n (an expression) is a link of an optional chain that contains `?.` below it
function chainHasOptional(n) {
  for (;;) {
    const k = K(n);
    if (k === N_CALL) { if (F(n) & 1) return true; n = A(n); continue; }
    if (k === N_PROPACCESS || k === N_ELEMACCESS) { if (F(n) & 1) return true; n = A(n); continue; }
    if (k === N_NONNULL) { n = A(n); continue; }
    if (k === N_TAGGED) { n = A(n); continue; }
    return false;
  }
}
function isChainLink(n) {
  const k = K(n);
  return k === N_CALL || k === N_PROPACCESS || k === N_ELEMACCESS || k === N_NONNULL;
}

// an expression, wrapped in ChainExpression when it ends an optional chain
function expr(n) {
  const k = K(n);
  if ((k === N_CALL || k === N_PROPACCESS || k === N_ELEMACCESS || k === N_NONNULL) && chainHasOptional(n)) {
    const inner = chainExpr(n);
    const o = { __proto__: NodeProto, type: "ChainExpression", expression: inner };
    return fin(o, P(n), E(n));
  }
  return expr0(n);
}
// a link of a chain (no ChainExpression around it)
function chainExpr(n) {
  return expr0(n, true);
}
function sub(n, inChain) {
  // the object / callee of a chain link: part of the same chain
  if (inChain && isChainLink(n)) return expr0(n, true);
  return expr(n);
}

function expr0(n, inChain) {
  const k = K(n);
  switch (k) {
    case N_ID:
      return idNode(n);
    case N_NUM: return numLit(n);
    case N_BIGINT: return bigLit(n);
    case N_STR: return strLit(n);
    case N_REGEX: return regexLit(n);
    case N_TRUE: return literal(true, "true", P(n), E(n));
    case N_FALSE: return literal(false, "false", P(n), E(n));
    case N_NULL: return literal(null, "null", P(n), E(n));
    case N_THIS: return fin({ __proto__: NodeProto, type: "ThisExpression" }, P(n), E(n));
    case N_SUPER: return fin({ __proto__: NodeProto, type: "Super" }, P(n), E(n));
    case N_TEMPL:
    case N_NOSUBTEMPL: {
      const { quasis, exprs } = template(n, expr);
      return fin({ __proto__: NodeProto, type: "TemplateLiteral", quasis, expressions: exprs }, P(n), E(n));
    }
    case N_PAREN:
      return expr(A(n));
    case N_ARRAY: {
      const elements = items(A(n)).map((x) => {
        if (K(x) === N_OMIT) return null;
        if (K(x) === N_SPREAD) return spread(x);
        return expr(x);
      });
      return fin({ __proto__: NodeProto, type: "ArrayExpression", elements }, P(n), E(n));
    }
    case N_OBJECT:
      return fin({ __proto__: NodeProto, type: "ObjectExpression", properties: items(A(n)).map(objMember) }, P(n), E(n));
    case N_SPREAD:
      return spread(n);
    case N_FUNCEXPR:
      return func(n, P(n), false);
    case N_ARROW:
      return arrow(n);
    case N_CLASSEXPR:
      return klass(n, P(n), false);
    case N_CALL: {
      const callee = sub(A(n), inChain);
      return fin({ __proto__: NodeProto, type: "CallExpression", callee, typeArguments: B(n) >= 0 ? typeArgs(B(n)) : null, arguments: args(C(n)), optional: (F(n) & 1) !== 0 }, P(n), E(n));
    }
    case N_NEW: {
      return fin({ __proto__: NodeProto, type: "NewExpression", callee: expr(A(n)), typeArguments: B(n) >= 0 ? typeArgs(B(n)) : null, arguments: C(n) >= 0 ? args(C(n)) : [] }, P(n), E(n));
    }
    case N_IMPORTCALL: {
      const as = items(C(n));
      const opts = as.length > 1 ? argExpr(as[1]) : null;
      return fin({ __proto__: NodeProto, type: "ImportExpression", source: as.length > 0 ? argExpr(as[0]) : null, options: opts, phase: null }, P(n), E(n));
    }
    case N_PROPACCESS: {
      const object = sub(A(n), inChain);
      const ps = D(n);
      const nmStr = name(n);
      const property = F(n) & 4
        ? fin({ __proto__: NodeProto, type: "PrivateIdentifier", name: nmStr.replace(/^#/, "") }, ps, E(n))
        : ident(nmStr, ps, E(n));
      return fin({ __proto__: NodeProto, type: "MemberExpression", object, property, optional: (F(n) & 1) !== 0, computed: false }, P(n), E(n));
    }
    case N_ELEMACCESS: {
      const object = sub(A(n), inChain);
      return fin({ __proto__: NodeProto, type: "MemberExpression", object, property: expr(B(n)), optional: (F(n) & 1) !== 0, computed: true }, P(n), E(n));
    }
    case N_TAGGED: {
      const q = C(n);
      const { quasis, exprs } = template(q, expr);
      const quasi = fin({ __proto__: NodeProto, type: "TemplateLiteral", quasis, expressions: exprs }, P(q), E(q));
      return fin({ __proto__: NodeProto, type: "TaggedTemplateExpression", tag: expr(A(n)), typeArguments: B(n) >= 0 ? typeArgs(B(n)) : null, quasi }, P(n), E(n));
    }
    case N_BINARY: {
      const op = F(n);
      if (op === T_COMMA) {
        // a sequence: flatten left-nested commas
        const list = [];
        let x = n;
        while (K(x) === N_BINARY && F(x) === T_COMMA) {
          list.push(B(x));
          x = A(x);
        }
        list.push(x);
        list.reverse();
        return fin({ __proto__: NodeProto, type: "SequenceExpression", expressions: list.map(expr) }, P(n), E(n));
      }
      const opStr = OPS[op];
      if (op === 62 || (op >= 63 && op <= 77)) {
        return fin({ __proto__: NodeProto, type: "AssignmentExpression", operator: opStr, left: op === 62 ? target(A(n)) : simpleTarget(A(n)), right: expr(B(n)) }, P(n), E(n));
      }
      if (op === 55 || op === 56 || op === 57) {
        return fin({ __proto__: NodeProto, type: "LogicalExpression", left: expr(A(n)), operator: opStr, right: expr(B(n)) }, P(n), E(n));
      }
      const left = K(A(n)) === N_PRIVNAME ? privName(A(n)) : expr(A(n));
      return fin({ __proto__: NodeProto, type: "BinaryExpression", left, operator: opStr, right: expr(B(n)) }, P(n), E(n));
    }
    case N_PREFIX: {
      const op = F(n);
      if (op === 45 || op === 46) return fin({ __proto__: NodeProto, type: "UpdateExpression", operator: OPS[op], prefix: true, argument: simpleTarget(A(n)) }, P(n), E(n));
      return fin({ __proto__: NodeProto, type: "UnaryExpression", operator: OPS[op], argument: expr(A(n)), prefix: true }, P(n), E(n));
    }
    case N_POSTFIX:
      return fin({ __proto__: NodeProto, type: "UpdateExpression", operator: OPS[F(n)], prefix: false, argument: simpleTarget(A(n)) }, P(n), E(n));
    case N_TYPEOF:
      return fin({ __proto__: NodeProto, type: "UnaryExpression", operator: "typeof", argument: expr(A(n)), prefix: true }, P(n), E(n));
    case N_VOIDEXPR:
      return fin({ __proto__: NodeProto, type: "UnaryExpression", operator: "void", argument: expr(A(n)), prefix: true }, P(n), E(n));
    case N_DELETE:
      return fin({ __proto__: NodeProto, type: "UnaryExpression", operator: "delete", argument: expr(A(n)), prefix: true }, P(n), E(n));
    case N_AWAIT:
      return fin({ __proto__: NodeProto, type: "AwaitExpression", argument: expr(A(n)) }, P(n), E(n));
    case N_YIELD:
      return fin({ __proto__: NodeProto, type: "YieldExpression", delegate: F(n) === 1, argument: A(n) >= 0 ? expr(A(n)) : null }, P(n), E(n));
    case N_COND:
      return fin({ __proto__: NodeProto, type: "ConditionalExpression", test: expr(A(n)), consequent: expr(B(n)), alternate: expr(C(n)) }, P(n), E(n));
    case N_AS:
      return fin({ __proto__: NodeProto, type: "TSAsExpression", expression: expr(A(n)), typeAnnotation: type(B(n)) }, P(n), E(n));
    case N_SATISFIES:
      return fin({ __proto__: NodeProto, type: "TSSatisfiesExpression", expression: expr(A(n)), typeAnnotation: type(B(n)) }, P(n), E(n));
    case N_NONNULL:
      return fin({ __proto__: NodeProto, type: "TSNonNullExpression", expression: sub(A(n), inChain) }, P(n), E(n));
    case N_TYPEASSERT:
      return fin({ __proto__: NodeProto, type: "TSTypeAssertion", typeAnnotation: type(B(n)), expression: expr(A(n)) }, P(n), E(n));
    case N_EXPRTARGS:
      return fin({ __proto__: NodeProto, type: "TSInstantiationExpression", expression: expr(A(n)), typeArguments: typeArgs(B(n)) }, P(n), E(n));
    case N_METAPROP: {
      const isNew = F(n) === W_NEW;
      const meta = ident(isNew ? "new" : "import", P(n), P(n) + (isNew ? 3 : 6));
      const prop = name(n);
      const ps = skip(find(P(n) + (isNew ? 3 : 6), 46) + 1);
      const pe = idEnd(ps);
      const property = ident(prop, ps, pe);
      return fin({ __proto__: NodeProto, type: "MetaProperty", meta, property }, P(n), pe);
    }
    case N_PRIVNAME:
      return privName(n);
    case N_JSXELEM:
      return jsxElem(n);
    case N_OMIT:
      return null;
  }
  // a type or something else where an expression was expected (recovery)
  return fin({ __proto__: NodeProto, type: "Identifier", decorators: [], name: "", optional: false, typeAnnotation: null }, P(n), E(n));
}

// the target of ++ / -- / op=: parentheses dropped
function simpleTarget(n) {
  return expr(n);
}

function spread(n) {
  return fin({ __proto__: NodeProto, type: "SpreadElement", argument: expr(A(n)) }, P(n), E(n));
}
function argExpr(x) {
  return K(x) === N_SPREAD ? spread(x) : expr(x);
}
function args(l) {
  return items(l).map(argExpr);
}

function objMember(pr) {
  const k = K(pr);
  if (k === N_SPREAD) return spread(pr);
  if (k === N_PROPASSIGN) {
    const computed = K(A(pr)) === N_COMPUTED;
    return fin({ __proto__: NodeProto, type: "Property", kind: "init", key: propKey(A(pr)), value: expr(B(pr)), method: false, shorthand: false, computed, optional: false }, P(pr), E(pr));
  }
  if (k === N_SHORTHAND) {
    const key = identAt(name(pr), P(pr));
    let value = identAt(name(pr), P(pr));
    if (B(pr) >= 0) {
      // x = 1 in an object literal (only valid as a pattern)
      value = fin({ __proto__: NodeProto, type: "AssignmentPattern", decorators: [], left: value, right: expr(B(pr)), optional: false, typeAnnotation: null }, P(pr), E(pr));
    }
    return fin({ __proto__: NodeProto, type: "Property", kind: "init", key, value, method: false, shorthand: true, computed: false, optional: false }, P(pr), E(pr));
  }
  if (k === N_METHOD || k === N_GET || k === N_SET) {
    const f = F(pr);
    const computed = K(A(pr)) === N_COMPUTED;
    const key = propKey(A(pr));
    const value = funcValue(pr, B(pr), C(pr), f, null);
    const kind = k === N_GET ? "get" : k === N_SET ? "set" : "init";
    return fin({ __proto__: NodeProto, type: "Property", kind, key, value, method: k === N_METHOD, shorthand: false, computed, optional: false }, P(pr), E(pr));
  }
  return expr(pr);
}

function arrow(n) {
  const f = F(n);
  const bodyN = D(n);
  const isExpr = K(bodyN) !== N_BLOCK;
  const o = {
    __proto__: NodeProto,
    type: "ArrowFunctionExpression",
    expression: isExpr,
    async: (f & M_ASYNC) !== 0,
    typeParameters: A(n) >= 0 ? typeParams(A(n)) : null,
    params: params(B(n)),
    returnType: C(n) >= 0 ? returnType(C(n)) : null,
    body: isExpr ? expr(bodyN) : funcBody(bodyN),
    id: null,
    generator: false,
  };
  return fin(o, P(n), E(n));
}

// ---- types

function entity(n) {
  const k = K(n);
  if (k === N_ID) return idNode(n);
  if (k === N_THIS) return fin({ __proto__: NodeProto, type: "ThisExpression" }, P(n), E(n));
  if (k === N_QNAME) {
    const right = name(n);
    const r = ident(right, E(n) - Buffer.byteLength(right), E(n));
    return fin({ __proto__: NodeProto, type: "TSQualifiedName", left: entity(A(n)), right: r }, P(n), E(n));
  }
  // a class's implements written as an expression (a.b)
  if (k === N_PROPACCESS) return expr(n);
  return expr(n);
}

// an entity name as an expression (interface extends a.b.C)
function entityExpr(n) {
  if (K(n) === N_QNAME) {
    const right = name(n);
    const r = ident(right, E(n) - Buffer.byteLength(right), E(n));
    return fin({ __proto__: NodeProto, type: "MemberExpression", object: entityExpr(A(n)), property: r, optional: false, computed: false }, P(n), E(n));
  }
  return entity(n);
}

function typeArgs(l) {
  // <...>: the list spans from < to >
  const ps = items(l).map(type);
  const close = find(ps.length > 0 ? E(items(l)[ps.length - 1]) : P(l) + 1, 62);
  return fin({ __proto__: NodeProto, type: "TSTypeParameterInstantiation", params: ps }, P(l), close + 1);
}
function typeParams(l) {
  const ps = items(l).map((tp) => {
    const f = F(tp);
    const at = f === 0 ? P(tp) : skipWords(P(tp), ["const", "in", "out"]);
    const nmStr = name(tp);
    const id = identAt(nmStr, at);
    return fin({ __proto__: NodeProto, type: "TSTypeParameter", name: id, constraint: A(tp) >= 0 ? type(A(tp)) : null, default: B(tp) >= 0 ? type(B(tp)) : null, in: (f & M_IN) !== 0, out: (f & M_OUT) !== 0, const: (f & M_CONST) !== 0 }, P(tp), E(tp));
  });
  const close = E(l) > P(l) && ch(E(l) - 1) === 62 ? E(l) : find(E(l), 62) + 1;
  return fin({ __proto__: NodeProto, type: "TSTypeParameterDeclaration", params: ps }, P(l), close);
}

function typePred(n) {
  const f = F(n);
  let at = P(n);
  if (f & 1) at = skip(at + 7);
  let parameterName;
  if (S(n) < 0) parameterName = fin({ __proto__: NodeProto, type: "TSThisType" }, at, at + 4);
  else parameterName = identAt(name(n), at);
  let typeAnnotation = null;
  if (A(n) >= 0) {
    const t = type(A(n));
    const isAt = skip(parameterName ? backToBytes(parameterName.end) : at);
    typeAnnotation = { __proto__: NodeProto, type: "TSTypeAnnotation", typeAnnotation: t };
    // (the annotation spans the type alone)
    typeAnnotation.start = t.start; typeAnnotation.end = t.end; typeAnnotation.range = [t.start, t.end]; typeAnnotation.parent = null;
  }
  return fin({ __proto__: NodeProto, type: "TSTypePredicate", parameterName, asserts: (f & 1) !== 0, typeAnnotation }, P(n), E(n));
}

function sigParts(sig) {
  return { tp: A(sig) >= 0 ? typeParams(A(sig)) : null, ps: params(B(sig)), rt: C(sig) >= 0 ? returnType(C(sig)) : null };
}

function typeMember(m) {
  const k = K(m);
  const f = F(m);
  if (k === N_PROP) {
    const computed = K(A(m)) === N_COMPUTED;
    return fin({ __proto__: NodeProto, type: "TSPropertySignature", computed, optional: (f & M_OPTIONAL) !== 0, readonly: (f & M_READONLY) !== 0, key: propKey(A(m)), typeAnnotation: B(m) >= 0 ? annot(B(m)) : null, accessibility: null, static: false }, P(m), E(m));
  }
  if (k === N_METHOD || k === N_GET || k === N_SET) {
    const computed = K(A(m)) === N_COMPUTED;
    const { tp, ps, rt } = sigParts(B(m));
    const kind = k === N_GET ? "get" : k === N_SET ? "set" : "method";
    return fin({ __proto__: NodeProto, type: "TSMethodSignature", key: propKey(A(m)), computed, optional: (f & M_OPTIONAL) !== 0, kind, typeParameters: tp, params: ps, returnType: rt, accessibility: null, readonly: false, static: false }, P(m), E(m));
  }
  if (k === N_CALLSIG || k === N_CTORSIG) {
    const { tp, ps, rt } = sigParts(B(m));
    return fin({ __proto__: NodeProto, type: k === N_CALLSIG ? "TSCallSignatureDeclaration" : "TSConstructSignatureDeclaration", typeParameters: tp, params: ps, returnType: rt }, P(m), E(m));
  }
  if (k === N_INDEXSIG) return indexSig(m);
  return type(m);
}

function type(n) {
  const k = K(n);
  switch (k) {
    case N_TKW: {
      // (vlint ends these nodes where they start)
      const t = KW_TYPES[F(n)];
      return fin({ __proto__: NodeProto, type: t || "TSAnyKeyword" }, P(n), idEnd(P(n)));
    }
    case N_TTHIS:
      return fin({ __proto__: NodeProto, type: "TSThisType" }, P(n), E(n));
    case N_TREF: {
      const nmNode = A(n);
      if (K(nmNode) === N_ID && name(nmNode) === "intrinsic" && false) {}
      return fin({ __proto__: NodeProto, type: "TSTypeReference", typeName: entity(nmNode), typeArguments: B(n) >= 0 ? typeArgs(B(n)) : null }, P(n), E(n));
    }
    case N_TLIT: {
      const x = A(n);
      let literal_;
      if (K(x) === N_NOSUBTEMPL) {
        const { quasis } = template(x, expr);
        return fin({ __proto__: NodeProto, type: "TSLiteralType", literal: fin({ __proto__: NodeProto, type: "TemplateLiteral", quasis, expressions: [] }, P(x), E(x)) }, P(n), E(n));
      }
      literal_ = expr(x);
      return fin({ __proto__: NodeProto, type: "TSLiteralType", literal: literal_ }, P(n), E(n));
    }
    case N_TUNION:
      return fin({ __proto__: NodeProto, type: "TSUnionType", types: items(A(n)).map(type) }, P(n), E(n));
    case N_TINTER:
      return fin({ __proto__: NodeProto, type: "TSIntersectionType", types: items(A(n)).map(type) }, P(n), E(n));
    case N_TARRAY:
      return fin({ __proto__: NodeProto, type: "TSArrayType", elementType: type(A(n)) }, P(n), E(n));
    case N_TINDEXED:
      return fin({ __proto__: NodeProto, type: "TSIndexedAccessType", objectType: type(A(n)), indexType: type(B(n)) }, P(n), E(n));
    case N_TTUPLE:
      return fin({ __proto__: NodeProto, type: "TSTupleType", elementTypes: items(A(n)).map(type) }, P(n), E(n));
    case N_TTUPLEEL: {
      const f = F(n);
      const at = f & M_REST ? skip(P(n) + 3) : P(n);
      const label = identAt(name(n), at);
      let el = { __proto__: NodeProto, type: "TSNamedTupleMember", label, elementType: type(A(n)), optional: (f & M_OPTIONAL) !== 0 };
      if (f & M_REST) {
        fin(el, at, E(n));
        return fin({ __proto__: NodeProto, type: "TSRestType", typeAnnotation: el }, P(n), E(n));
      }
      return fin(el, P(n), E(n));
    }
    case N_TOPTIONAL:
      if (A(n) >= 0 && !(ch(P(n)) === 63 || ch(P(n)) === 33)) return fin({ __proto__: NodeProto, type: "TSOptionalType", typeAnnotation: type(A(n)) }, P(n), E(n));
      return fin({ __proto__: NodeProto, type: ch(P(n)) === 33 ? "TSJSDocNonNullableType" : A(n) >= 0 ? "TSJSDocNullableType" : "TSJSDocUnknownType", ...(A(n) >= 0 ? { typeAnnotation: type(A(n)), postfix: false } : {}) }, P(n), E(n));
    case N_TREST:
      return fin({ __proto__: NodeProto, type: "TSRestType", typeAnnotation: type(A(n)) }, P(n), E(n));
    case N_TFUNC: {
      const { tp, ps, rt } = sigParts(B(n));
      const f = F(n);
      if (f === 0) return fin({ __proto__: NodeProto, type: "TSFunctionType", typeParameters: tp, params: ps, returnType: rt }, P(n), E(n));
      // (vlint's node starts after `new` / `abstract new`)
      let st = wordBefore(P(n)).at;
      if (f === 3) st = wordBefore(st).at;
      return fin({ __proto__: NodeProto, type: "TSConstructorType", abstract: f === 3, typeParameters: tp, params: ps, returnType: rt }, st, E(n));
    }
    case N_TOBJ:
      return fin({ __proto__: NodeProto, type: "TSTypeLiteral", members: items(A(n)).map(typeMember) }, P(n), E(n));
    case N_TPAREN:
      return type(A(n));
    case N_TQUERY:
      return fin({ __proto__: NodeProto, type: "TSTypeQuery", exprName: entity(A(n)), typeArguments: B(n) >= 0 ? typeArgs(B(n)) : null }, P(n), E(n));
    case N_TOP: {
      const op = F(n) === W_KEYOF ? "keyof" : F(n) === W_UNIQUE ? "unique" : "readonly";
      return fin({ __proto__: NodeProto, type: "TSTypeOperator", operator: op, typeAnnotation: type(A(n)) }, P(n), E(n));
    }
    case N_TCOND:
      return fin({ __proto__: NodeProto, type: "TSConditionalType", checkType: type(A(n)), extendsType: type(B(n)), trueType: type(C(n)), falseType: type(D(n)) }, P(n), E(n));
    case N_TINFER: {
      const tp = A(n);
      const tpo = fin({ __proto__: NodeProto, type: "TSTypeParameter", name: identAt(name(tp), P(tp)), constraint: A(tp) >= 0 ? type(A(tp)) : null, default: null, in: false, out: false, const: false }, P(tp), E(tp));
      return fin({ __proto__: NodeProto, type: "TSInferType", typeParameter: tpo }, P(n), E(n));
    }
    case N_TMAPPED: {
      const f = F(n);
      const tp = A(n);
      const key = identAt(name(tp), P(tp));
      const optional = f & MAP_OPTIONAL ? (ch(skip(E(tp))) === 43 ? "+" : true) : f & MAP_NOOPTIONAL ? "-" : false;
      const readonly = f & MAP_READONLY ? (ch(skip(P(n) + 1)) === 43 ? "+" : true) : f & MAP_NOREADONLY ? "-" : null;
      return fin({ __proto__: NodeProto, type: "TSMappedType", key, constraint: type(A(tp)), nameType: B(n) >= 0 ? type(B(n)) : null, typeAnnotation: C(n) >= 0 ? type(C(n)) : null, optional, readonly }, P(n), E(n));
    }
    case N_TTEMPLATE: {
      const { quasis, exprs } = template(n, type);
      return fin({ __proto__: NodeProto, type: "TSTemplateLiteralType", quasis, types: exprs }, P(n), E(n));
    }
    case N_TPRED:
      return typePred(n);
    case N_TIMPORT: {
      const isTypeof = F(n) === 1;
      const imp = fin({ __proto__: NodeProto, type: "TSImportType", source: strLit(A(n)), options: null, qualifier: B(n) >= 0 ? entity(B(n)) : null, typeArguments: C(n) >= 0 ? typeArgs(C(n)) : null }, isTypeof ? skip(P(n) + 6) : P(n), E(n));
      if (isTypeof) return fin({ __proto__: NodeProto, type: "TSTypeQuery", exprName: imp, typeArguments: null }, P(n), E(n));
      return imp;
    }
  }
  return expr(n);
}

// ---- JSX

function jsxName(n) {
  const k = K(n);
  if (k === N_ID) {
    const s = name(n);
    const colon = s.indexOf(":");
    if (colon >= 0) {
      const ns = fin({ __proto__: NodeProto, type: "JSXIdentifier", name: s.slice(0, colon) }, P(n), P(n) + colon);
      const nmo = fin({ __proto__: NodeProto, type: "JSXIdentifier", name: s.slice(colon + 1) }, P(n) + colon + 1, E(n));
      return fin({ __proto__: NodeProto, type: "JSXNamespacedName", namespace: ns, name: nmo }, P(n), E(n));
    }
    return fin({ __proto__: NodeProto, type: "JSXIdentifier", name: s }, P(n), E(n));
  }
  if (k === N_THIS) return fin({ __proto__: NodeProto, type: "JSXIdentifier", name: "this" }, P(n), E(n));
  if (k === N_PROPACCESS) {
    const prop = fin({ __proto__: NodeProto, type: "JSXIdentifier", name: name(n) }, D(n), E(n));
    return fin({ __proto__: NodeProto, type: "JSXMemberExpression", object: jsxName(A(n)), property: prop }, P(n), E(n));
  }
  if (k === N_EXPRTARGS) return jsxName(A(n));
  return fin({ __proto__: NodeProto, type: "JSXIdentifier", name: "" }, P(n), E(n));
}

function jsxText(s, e) {
  const raw = srcBytes(s, e);
  return fin({ __proto__: NodeProto, type: "JSXText", value: decodeEntities(raw), raw }, s, e);
}
const ENT = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: "\u00a0" };
function decodeEntities(s) {
  // (oxc keeps entities as written)
  return s;
  if (!s.includes("&")) return s;
  return s.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|[A-Za-z][A-Za-z0-9]*);/g, (m, g) => {
    if (g[0] === "#") {
      const cp = g[1] === "x" || g[1] === "X" ? parseInt(g.slice(2), 16) : parseInt(g.slice(1), 10);
      try { return String.fromCodePoint(cp); } catch { return m; }
    }
    const v = (typeof JSX_ENTITIES !== "undefined" ? JSX_ENTITIES : ENT)[g];
    return v === undefined ? m : v;
  });
}

function jsxChild(c) {
  const k = K(c);
  if (k === N_JSXTEXT) return jsxText(P(c), E(c));
  if (k === N_JSXEXPR) return jsxExprContainer(c);
  if (k === N_JSXSPREAD) return fin({ __proto__: NodeProto, type: "JSXSpreadChild", expression: expr(A(c)) }, P(c), E(c));
  return jsxElem(c);
}
function jsxExprContainer(c) {
  let e;
  if (A(c) < 0) {
    // {} or {/* comment */}: an empty expression from after { to before }
    e = fin({ __proto__: NodeProto, type: "JSXEmptyExpression" }, P(c) + 1, E(c) - 1);
  } else e = expr(A(c));
  return fin({ __proto__: NodeProto, type: "JSXExpressionContainer", expression: e }, P(c), E(c));
}

function jsxElem(n) {
  const isFrag = F(n) === 1;
  const kidsList = C(n);
  const children = kidsList >= 0 ? items(kidsList).map(jsxChild) : [];
  if (isFrag) {
    const openEnd = find(P(n) + 1, 62) + 1;
    const opening = fin({ __proto__: NodeProto, type: "JSXOpeningFragment" }, P(n), openEnd);
    const closeStart = kidsList >= 0 ? E(kidsList) : openEnd;
    const closing = fin({ __proto__: NodeProto, type: "JSXClosingFragment" }, closeStart, E(n));
    return fin({ __proto__: NodeProto, type: "JSXFragment", openingFragment: opening, children, closingFragment: closing }, P(n), E(n));
  }
  const nameNode = A(n);
  const nameO = jsxName(nameNode);
  const typeArguments = K(nameNode) === N_EXPRTARGS ? typeArgs(B(nameNode)) : null;
  const attributes = items(B(n)).map((at) => {
    if (K(at) === N_JSXSPREAD) return fin({ __proto__: NodeProto, type: "JSXSpreadAttribute", argument: expr(A(at)) }, P(at), E(at));
    const nmO = jsxName(A(at));
    let value = null;
    const v = B(at);
    if (v >= 0) {
      const vk = K(v);
      if (vk === N_STR) {
        const raw = srcBytes(P(v), E(v));
        value = literal(decodeEntities(raw.slice(1, -1)), raw, P(v), E(v));
      } else if (vk === N_JSXEXPR) value = jsxExprContainer(v);
      else value = jsxElem(v);
    }
    return fin({ __proto__: NodeProto, type: "JSXAttribute", name: nmO, value }, P(at), v >= 0 ? E(at) : E(A(at)));
  });
  const selfClosing = kidsList < 0;
  const openEnd = selfClosing ? E(n) : (kidsList >= 0 ? P(kidsList) : E(n));
  const opening = fin({ __proto__: NodeProto, type: "JSXOpeningElement", name: nameO, typeArguments, attributes, selfClosing }, P(n), openEnd);
  let closing = null;
  if (!selfClosing) {
    const closeStart = E(kidsList);
    closing = fin({ __proto__: NodeProto, type: "JSXClosingElement", name: D(n) >= 0 ? jsxName(D(n)) : null }, closeStart, E(n));
  }
  return fin({ __proto__: NodeProto, type: "JSXElement", openingElement: opening, children, closingElement: closing }, P(n), E(n));
}

// import / export statements or import.meta make an unambiguous file a module
function hasModuleSyntax(prog) {
  for (const st of prog.body) {
    const t = st.type;
    if (t === "ImportDeclaration" || t === "ExportNamedDeclaration" || t === "ExportDefaultDeclaration" || t === "ExportAllDeclaration") return true;
  }
  if (!src.includes("import")) return false;
  let found = false;
  const walk = (node) => {
    if (found) return;
    if (node.type === "MetaProperty" && node.meta.name === "import") { found = true; return; }
    for (const k in node) {
      if (k === "parent" || k === "comments" || k === "tokens") continue;
      const v = node[k];
      if (v === null || typeof v !== "object") continue;
      if (Array.isArray(v)) { for (const x of v) if (x !== null && typeof x === "object" && typeof x.type === "string") walk(x); }
      else if (typeof v.type === "string") walk(v);
    }
  };
  walk(prog);
  return found;
}

// ---- parents

function setParents(node, parent) {
  node.parent = parent;
  for (const key in node) {
    if (key === "parent" || key === "comments" || key === "tokens") continue;
    const v = node[key];
    if (v === null || typeof v !== "object") continue;
    if (Array.isArray(v)) {
      for (let i = 0; i < v.length; i++) {
        const x = v[i];
        if (x !== null && typeof x === "object" && typeof x.type === "string") setParents(x, node);
      }
    } else if (typeof v.type === "string" && key !== "value" && key !== "regex") setParents(v, node);
    else if (key === "value" && typeof v.type === "string") setParents(v, node);
  }
}

// The ESTree Program of a request: { src, tree: {nd, L, nm, deco, np, root}, sourceType }.
function buildEstree(req) {
  // (a .vue section, or a file without its BOM: vlint's positions start base bytes earlier)
  baseOff = req.base || 0;
  src = baseOff > 0 ? " ".repeat(baseOff) + req.src : req.src;
  const t = req.tree;
  nd = t.nd;
  Ls = t.L;
  nm = t.nm;
  bytes = Buffer.from(src, "utf8");
  if (bytes.length === src.length) u16 = null;
  else {
    // byte offset -> UTF-16 offset
    u16 = new Int32Array(bytes.length + 1);
    let j = 0;
    for (let i = 0; i < bytes.length; ) {
      const c = bytes[i];
      const len = c < 0x80 ? 1 : c < 0xe0 ? 2 : c < 0xf0 ? 3 : 4;
      for (let k = 0; k < len; k++) u16[i + k] = j;
      i += len;
      j += len === 4 ? 2 : 1;
    }
    u16[bytes.length] = j;
  }
  npos = new Map();
  const np = t.np || [];
  for (let i = 0; i + 1 < np.length; i += 2) npos.set(np[i], np[i + 1]);
  decoAt = (t.deco || []).slice().sort((a, b) => P(a) - P(b));
  let st = req.sourceType;
  const prog = program(t.root, st);
  if (st === "unambiguous") prog.sourceType = hasModuleSyntax(prog) ? "module" : "script";
  setParents(prog, null);
  return prog;
}
