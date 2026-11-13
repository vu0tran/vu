// spreads of falsy-or-object unions (cond && {...}), and of types that aren't objects
export {};
declare const b: boolean;
declare const o: { a: number } | undefined;
declare const s: string;
declare const u: { a: 1 } | { b: 2 } | undefined;
declare const n0: number;
const r1 = { ...(o || {}) }; const k1: number = r1;
const r2 = { ...(b ? o : undefined) }; const k2: number = r2;
const r5 = { q: 1, ...(s && { s }) }; const k5: number = r5;
const r6 = { ...(b && { a: 1, b: "x" }), a: 2 }; const k6: number = r6;
const r7 = { a: "s", ...(b && { a: 1 }) }; const k7: number = r7;
const r3 = { ...(b && n0), x: 1 }; const k3: number = r3;
const r8 = { ...(b && 0), ...("" as const), y: 1 }; const k8: number = r8;
