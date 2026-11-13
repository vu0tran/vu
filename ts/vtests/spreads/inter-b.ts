// spreads of intersections: their properties, optional ones printed without undefined
export {};
type E = { a: number; b?: string; readonly c: 1 };
type I = E & { b?: string; a: 1 | 2 };
declare const i: I;
const r1 = { ...i };
const k1: number = r1.b;
const k2: boolean = r1.a;
r1.c = 1;
const r3: { a: 1; b?: string; c: 1 } = { ...i };
const r4: { a: number } = { ...i, q: 1 };
function f(x: I | { z: 1 }) { const r = { ...x }; const n: number = r; }
