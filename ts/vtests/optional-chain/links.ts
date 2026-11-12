type A = { a(): number; b: { c: string }; d?: { e: number }; f: (() => number) | undefined; g: number[] };
declare const q: A | undefined;
declare const w: A;
export const r1 = q?.a();
export const r2: number = q?.a();
export const r3 = q?.b.c;
export const r4: string = q?.b.c;
export const r5 = q?.d.e;
export const r6 = q?.d?.e;
export const r8 = w.f?.();
export const r9 = q?.g[0];
export const r10: number = q?.g[0];
export const r11 = q?.["b"].c.length;
export const r12 = (q?.b).c;
export const r13 = q?.b.c.toUpperCase().length;
export function h(n: string | null | undefined) { return n?.trim().length; }
export const r14: number = h("x");
