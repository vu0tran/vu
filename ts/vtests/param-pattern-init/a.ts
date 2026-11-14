const f1 = ({ a = false } = {}) => { const s: string = a; return a; };
const r1: string = f1();
f1({ a: true });
f1({ b: 1 });
function f2({ x = 1, y = "s" } = {}) { const n: string = x; const m: number = y; }
function f3({ x = 1 } = { x: 2 }) { const n: string = x; }
const { p = 3 } = {};
const q: string = p;
const { r } = {};
export {};
