declare const x: { a: { b: number } | undefined, c: { d: number }[] } | undefined;
declare const y: { a: { b: number } | undefined, c: { d: number }[] };
export const z1 = (y).a.b;
export const z2 = y.c[0].d;
export const z3 = y?.a.b;
export const z4 = x?.c[0]?.d;
export const z5 = (x?.a).b;
export const z6: number = x?.c.length;
export function f(s?: string) { return s?.split(",").map((p) => p.trim()).filter(Boolean).length; }
export const z7: number = f();
