// spreads of falsy-or-object unions (cond && {...}), and of types that aren't objects
export {};
type C = { v: 1; t?: string; p?: { a: number } };
declare const c: C;
const r = { v: c.v, ...(c.t !== undefined && { t: c.t }), ...(c.p !== undefined && { p: c.p }) };
const n: number = r;
declare const b: boolean;
const r2 = { ...(b && { x: 1 }), ...(b ? { y: 2 } : {}), ...(c.t && { z: c.t }) };
const n2: number = r2;
