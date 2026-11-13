export {};
const CA = Symbol('a');
type M = { [K in typeof CA | "x"]: number };
declare const m: M;
const b1: boolean = m;
const b2: boolean = m[CA];
const b3: string = { [CA]: 1, x: 2 } satisfies M;
declare const r: Record<typeof CA, string>;
const b4: boolean = r;
