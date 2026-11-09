// Tokens and comments as oxlint gives them to JS plugins (oxc's lexer tokens, with their kinds
// changed as oxc_estree_tokens does for JS-style ESTree tokens). The lexing is guided by the ESTree
// Program: where regular expressions, template parts, JSX text and JSX names are, which words are
// identifiers, and which `>` close type arguments. Offsets are UTF-16 (the JS string's own).
//
// Token records are 16 bytes (start, end as i32; kind at byte 8; "escaped" at byte 10), comment
// records 24 bytes (start, end; kind at byte 17: 0 line, 1 block), as oxlint's raw transfer has them.

const TK_IDENT = 0, TK_KEYWORD = 1, TK_PRIVATE = 2, TK_PUNCT = 3, TK_NUM = 4, TK_STRING = 5, TK_BOOL = 6,
  TK_NULL = 7, TK_REGEX = 8, TK_TEMPLATE = 9, TK_JSXTEXT = 10, TK_JSXIDENT = 11;

const RESERVED = new Set(["await", "break", "case", "catch", "class", "const", "continue", "debugger", "default",
  "delete", "do", "else", "enum", "export", "extends", "false", "finally", "for", "function", "if", "import", "in",
  "instanceof", "new", "null", "return", "super", "switch", "this", "throw", "true", "try", "typeof", "var",
  "void", "while", "with", "yield", "let", "static", "implements", "interface", "package", "private",
  "protected", "public"]);

const PUNCTS = [">>>=", "...", "===", "!==", "**=", "<<=", ">>=", ">>>", "&&=", "||=", "??=", "=>", "==", "!=",
  "<=", ">=", "&&", "||", "??", "?.", "++", "--", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<", ">>", "**"];
const PUNCT_BY_CHAR = new Map();
for (const p of PUNCTS) {
  const c = p[0];
  if (!PUNCT_BY_CHAR.has(c)) PUNCT_BY_CHAR.set(c, []);
  PUNCT_BY_CHAR.get(c).push(p);
}

const ID_RE = /(?:[\p{ID_Start}$_]|\\u(?:\{[0-9a-fA-F]+\}|[0-9a-fA-F]{4}))(?:[\p{ID_Continue}$\u200c\u200d]|\\u(?:\{[0-9a-fA-F]+\}|[0-9a-fA-F]{4}))*/uy;
const NUM_RE = /0[xX][0-9a-fA-F_]*n?|0[oO][0-7_]*n?|0[bB][01_]*n?|(?:\d[\d_]*(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][+-]?[\d_]+)?n?/y;
const WS_RE = /[\t\v\f \u00a0\ufeff\u1680\u2000-\u200a\u202f\u205f\u3000\n\r\u2028\u2029]+/y;

function lexProgram(prog, text) {
  // what the tree says about places in the text
  const special = new Map(); // start -> [end, kind]
  const identAt = new Map(); // start -> TK_IDENT (identifier nodes)
  const closeAngle = new Set();
  const visit = (node, parent, key) => {
    switch (node.type) {
      case "Literal":
        if (node.regex) special.set(node.start, [node.end, TK_REGEX]);
        else if (parent && parent.type === "JSXAttribute" && key === "value" && typeof node.value === "string") special.set(node.start, [node.end, TK_JSXTEXT]);
        break;
      case "TemplateElement":
        special.set(node.start, [node.end, TK_TEMPLATE]);
        break;
      case "JSXText":
        special.set(node.start, [node.end, TK_JSXTEXT]);
        break;
      case "JSXIdentifier":
        special.set(node.start, [node.end, TK_JSXIDENT]);
        break;
      case "Identifier":
        // (import.meta's and new.target's first word stays a keyword)
        if (!(parent && parent.type === "MetaProperty" && key === "meta")) identAt.set(node.start, node.end);
        break;
      case "ThisExpression":
        if (parent && (parent.type === "TSQualifiedName" || parent.type === "TSTypeQuery")) identAt.set(node.start, node.end);
        break;
      case "TSTypeParameterInstantiation":
      case "TSTypeParameterDeclaration":
        closeAngle.add(node.end - 1);
        closeAngle.add(node.start);
        break;
    }
    for (const k in node) {
      if (k === "parent" || k === "loc" || k === "comments" || k === "tokens") continue;
      const v = node[k];
      if (v === null || typeof v !== "object") continue;
      if (Array.isArray(v)) {
        for (const x of v) if (x !== null && typeof x === "object" && typeof x.type === "string") visit(x, node, k);
      } else if (typeof v.type === "string") visit(v, node, k);
    }
  };
  visit(prog, null, null);
  // the sorted starts of special spans (a punctuator never runs into one)
  const specialStarts = [...special.keys()].sort((a, b) => a - b);
  let si = 0;

  const tStart = [], tEnd = [], tKind = [], tEsc = [];
  const cStart = [], cEnd = [], cKind = [];
  const n = text.length;
  let i = 0;
  if (text.startsWith("#!")) {
    let e = 2;
    while (e < n && !isLineBreak(text.charCodeAt(e))) e++;
    cStart.push(0); cEnd.push(e); cKind.push(0);
    i = e;
  }
  const push = (s, e, k, esc) => {
    tStart.push(s); tEnd.push(e); tKind.push(k); tEsc.push(esc ? 1 : 0);
  };
  while (i < n) {
    const sp0 = special.get(i);
    if (sp0 !== undefined) {
      push(i, sp0[0], sp0[1], false);
      i = sp0[0];
      continue;
    }
    WS_RE.lastIndex = i;
    if (WS_RE.test(text)) { i = WS_RE.lastIndex; continue; }
    const c = text.charCodeAt(i);
    if (c === 47) {
      const d = text.charCodeAt(i + 1);
      if (d === 47 && !special.has(i)) {
        let e = i + 2;
        while (e < n && !isLineBreak(text.charCodeAt(e))) e++;
        cStart.push(i); cEnd.push(e); cKind.push(0);
        i = e;
        continue;
      }
      if (d === 42 && !special.has(i)) {
        let e = text.indexOf("*/", i + 2);
        e = e < 0 ? n : e + 2;
        cStart.push(i); cEnd.push(e); cKind.push(1);
        i = e;
        continue;
      }
    }
    const sp = special.get(i);
    if (sp !== undefined) {
      push(i, sp[0], sp[1], false);
      i = sp[0];
      continue;
    }
    while (si < specialStarts.length && specialStarts[si] <= i) si++;
    const limit = si < specialStarts.length ? specialStarts[si] : n;
    // words
    if (c === 92 || c === 36 || c === 95 || (c >= 65 && c <= 90) || (c >= 97 && c <= 122) || c >= 128) {
      ID_RE.lastIndex = i;
      if (ID_RE.test(text)) {
        const e = ID_RE.lastIndex;
        const word = text.slice(i, e);
        const esc = word.includes("\\");
        let kind;
        const w = esc ? word.replace(/\\u(?:\{([0-9a-fA-F]+)\}|([0-9a-fA-F]{4}))/g, (_, a, b) => String.fromCodePoint(parseInt(a ?? b, 16))) : word;
        if (identAt.has(i)) kind = (w === "yield" || w === "let" || w === "static") ? TK_KEYWORD : TK_IDENT;
        else if (w === "true" || w === "false") kind = TK_BOOL;
        else if (w === "null") kind = TK_NULL;
        else if (w === "await") kind = TK_IDENT;
        else if (RESERVED.has(w)) kind = TK_KEYWORD;
        else kind = TK_IDENT;
        push(i, e, kind, esc);
        i = e;
        continue;
      }
    }
    if (c === 35) {
      // #name
      ID_RE.lastIndex = i + 1;
      if (ID_RE.test(text)) {
        const e = ID_RE.lastIndex;
        push(i, e, TK_PRIVATE, text.slice(i, e).includes("\\"));
        i = e;
        continue;
      }
    }
    if ((c >= 48 && c <= 57) || (c === 46 && isDigit(text.charCodeAt(i + 1)))) {
      NUM_RE.lastIndex = i;
      NUM_RE.test(text);
      let e = NUM_RE.lastIndex;
      if (e <= i) e = i + 1;
      push(i, e, TK_NUM, false);
      i = e;
      continue;
    }
    if (c === 34 || c === 39) {
      let e = i + 1;
      while (e < n) {
        const d = text.charCodeAt(e);
        if (d === 92) { e += 2; continue; }
        if (d === c) { e++; break; }
        if (d === 10 || d === 13) break;
        e++;
      }
      push(i, e, TK_STRING, false);
      i = e;
      continue;
    }
    if (c === 96) {
      // (a template the tree didn't place: up to the closing `)
      let e = i + 1;
      while (e < n && text.charCodeAt(e) !== 96) { if (text.charCodeAt(e) === 92) e++; e++; }
      push(i, e + 1, TK_TEMPLATE, false);
      i = e + 1;
      continue;
    }
    // punctuators
    const ch = text[i];
    let len = 1;
    if (!((c === 62 || c === 60) && closeAngle.has(i))) {
      const cands = PUNCT_BY_CHAR.get(ch);
      if (cands) {
        for (const p of cands) {
          if (i + p.length <= limit && text.startsWith(p, i)) {
            // ?. before a digit is ? and a number
            if (p === "?." && isDigit(text.charCodeAt(i + 2))) continue;
            // a `>` that closes type arguments is never joined
            if ((ch === ">" || ch === "<") && p.length > 1 && hasCloseAngle(closeAngle, i, p.length)) continue;
            len = p.length;
            break;
          }
        }
      }
    }
    push(i, i + len, TK_PUNCT, false);
    i += len;
  }
  return { tStart, tEnd, tKind, tEsc, cStart, cEnd, cKind };
}

function hasCloseAngle(set, i, len) {
  for (let k = 0; k < len; k++) if (set.has(i + k)) return true;
  return false;
}
function isDigit(c) {
  return c >= 48 && c <= 57;
}
function isLineBreak(c) {
  return c === 10 || c === 13 || c === 0x2028 || c === 0x2029;
}

// raw-transfer style records for the host's token and comment readers
function tokenRecords(lx) {
  const len = lx.tStart.length;
  const buf = new ArrayBuffer(len * 16 + 16);
  const u8 = new Uint8Array(buf, 0, len * 16), i32 = new Int32Array(buf, 0, len * 4);
  for (let k = 0; k < len; k++) {
    i32[k * 4] = lx.tStart[k];
    i32[k * 4 + 1] = lx.tEnd[k];
    u8[k * 16 + 8] = lx.tKind[k];
    u8[k * 16 + 10] = lx.tEsc[k];
  }
  return { u8, i32, len };
}
function commentRecords(lx) {
  const len = lx.cStart.length;
  const buf = new ArrayBuffer(len * 24 + 24);
  const u8 = new Uint8Array(buf, 0, len * 24), i32 = new Int32Array(buf, 0, len * 6);
  for (let k = 0; k < len; k++) {
    i32[k * 6] = lx.cStart[k];
    i32[k * 6 + 1] = lx.cEnd[k];
    u8[k * 24 + 17] = lx.cKind[k];
  }
  return { u8, i32, len };
}
