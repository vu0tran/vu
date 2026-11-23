const q3 = { f: () => { const y = q3; const n: number = y; return 1; } };
const q4 = { xs: [1, 2], f: () => { q4.xs.forEach(x => { const s: string = x; }); return 1; } };
const q5 = { f: () => { const s: string = 5; return 1; } };
const q6 = { f: () => { q6.xs.map(x => x); return 1; } };
function g7(a: string | number) {
  if (typeof a === 'string') {
    const q7 = { f: () => { const n: number = a; return 1; } };
  }
}
declare function make<T>(o: { init: (n: number) => T; use: (t: T) => void }): T;
const m8 = make({ init: (n) => { const s: string = m8; return n; }, use: (t) => { const u: string = t; } });
declare function mk<T>(o: { cb: () => T }): { a9: T; b9: string };
const { a9, b9 } = mk({ cb: () => { const n: number = b9; return 1; } });
const q12 = { f: () => { return [1].map(x => { const n: string = q12; return x; }); } };
const q13 = { f: () => { const { a, b } = { a: q13, b: 1 }; const n: number = a; const m: string = b; return 2; } };
const q14 = { f: async () => { await null; const n: number = q14; return 'x'; } };
const q15 = { f: () => { if (Math.random()) return 1; const n: number = q15; return 'a'; } };
let q16 = { f: () => { const n: number = q16; return 1; } };
const q17 = [1].map((v) => { const n: string = q17; return v; });
function createDoc(opts: { stopScript: () => Promise<void> }) {
  const calls: string[] = [];
  return { doc: { name: 'x', opts }, calls };
}
const { doc, calls } = createDoc({
  stopScript: async () => {
    const n: number = calls;
    calls.push('stop');
  },
});
const p = { browser: () => ({ pages: async () => { const n: number = p; return [1]; } }) };
const q = { f: () => { const n: number = q; return 1; } };
const r1 = [() => { const n: number = r1; return 'a'; }];
const g = { go() { const n: number = g; return 3; } };
const h = { get x() { const n: number = h; return 3; } };
const h1 = () => { const n: number = h1; };
const h2 = async () => { const n: number = h2; };
const o3 = { go: () => { const n: string = o3.go; } };
const o4 = { go: () => { const n: string = o4.go; return 1; } };
function g5() {
  const o5 = { go: () => { const n: string = o5.go; } };
}
const q18 = { f: () => { const n = h18(1); return n; } };
const h18 = (x: number): number => { const s: string = x; return x; };
const q19 = { f: () => { return h19(1); } };
function h19(x: number) { const s: string = x; return x; }
export {};
