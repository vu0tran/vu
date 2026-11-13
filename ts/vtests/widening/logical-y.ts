declare const b: number[] | null;
for (const [i, v] of (b ?? []).entries()) { const q: 'z' = v; i; }
declare const s: string;
export const t1: 'z' = s || {};
declare const o: { a: 1 } | null;
export const t2: 'z' = o ?? { a: 1 as const, b: 2 };
export const t3: 'z' = o || { b: 2 };
declare const u: { a: 1 } | { b: 2 } | undefined;
export const t4: 'z' = u ?? { c: 3 };
declare const fn: (() => void) | undefined;
export const t5: 'z' = fn ?? (() => {});
