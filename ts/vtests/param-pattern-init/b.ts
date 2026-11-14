function g1({ a = 1, b } = {}) { const s: string = b; return a; }
g1({ a: "x" });
g1({ a: 2, b: true });
const r1: string = g1();
function g2({ a = 1 } = { a: 5, c: "q" }) { return a; }
g2({ c: "z" });
g2({ a: 1, d: 1 });
function g4({ o: { p = 1 } = {} } = {}) { const s: string = p; }
const g5 = function ({ k = "s" } = {}) { const n: number = k; };
g5({ k: 1 });
export {};
