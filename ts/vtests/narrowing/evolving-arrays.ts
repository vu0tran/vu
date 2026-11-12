// Evolving arrays (const xs = []) pushed or indexed in loops and branches join their elements
export {};
declare const xs: string[];
function a1() {
  const out = [];
  for (const x of xs) { out.push(x.length); }
  const n: string = out;
}
function a2() {
  const out = [];
  for (let i = 0; i < 3; i++) { out[i] = String(i); }
  return out;
}
const r: number = a2();
function a3() {
  const out = [];
  let i = 0;
  while (i < 3) { if (i) out.push(1); else out.push('s'); i++; }
  const n: boolean = out;
}
declare const c2: boolean;
function b1() { const out = []; if (c2) out.push(1); const n: string = out; }
function b2() { const out = []; out.push('a'); if (c2) out.push(1); const n: boolean = out; }
function b3() { const out = []; if (c2) { out.push(1); } else { out.push(true); } const n: string = out; }
function b4() { const out = []; switch (c2 ? 1 : 2) { case 1: out.push(1); break; default: out.push('x'); } const n: boolean = out; }
