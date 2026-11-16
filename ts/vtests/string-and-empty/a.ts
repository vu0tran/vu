// string & {} as written stays an intersection (NoSupertypeReduction); typeof decides an
// intersection with a primitive by the primitive; === keeps a comparable non-primitive member.
type X = string & {};
declare const x: X;
export const n: number = x;
declare const y: 'a' | (string & {});
export const m: number = y;
export const l: number = y.length;
export const s1: X = "lit";
export const s2: string = x;
if (typeof y === 'string') { const q: number = y; }
if (y === 'a') { const q2: 'a' = y; }
export const t: number & {} = 3;
export const u: {} & string = "x";
declare const v: { a: 1 } & {};
export const w: number = v;
declare const z: string & {};
if (typeof z === "string") { z.foo; }
if (typeof z === "number") { z.foo; }
declare const br: string & { __brand: 1 };
if (typeof br === "string") { const bb: number = br; }
