interface O { a?: number; b?: string | undefined; c: number }
declare const o: O;
export const r1: number = o.a;
export const r2: number | undefined = o.a;
const p: O = { c: 1, a: 2 };
const q: O = { c: 1, b: undefined };
function f(x: O) { return x.a ?? 0; }
f({ c: 2 });
const parts: Partial<O> = { c: 3 };
const pick: Pick<O, "a" | "c"> = { c: 1 };
o.a = 5;
o.b = undefined;
type R = Required<O>;
const req: R = { a: 1, b: "s", c: 2 };
export const z: string = req.a;
declare const maybe: { a?: number };
const copy: O = { ...maybe, c: 1 };
export { p, q, parts, pick, copy };
const bad1: O = { c: 1, a: undefined };
o.a = undefined;
declare function g(x: O): void;
g({ c: 1, a: undefined });
