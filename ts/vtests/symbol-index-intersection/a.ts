// (typeof globalThis & Record<symbol, X>[k], k a Symbol.for const: the intersection's symbol index
// signatures, from its members)
type Inst = { name: string };
const key = Symbol.for('app.instance');
const g = globalThis as typeof globalThis & Record<symbol, Inst | undefined>;
const existing = g[key];
const n: number = existing;
const k2 = Symbol('other');
const h = {} as { a: 1 } & { [s: symbol]: string } & { [s: symbol]: "x" | "y" };
const m: number = h[k2];
export {};
