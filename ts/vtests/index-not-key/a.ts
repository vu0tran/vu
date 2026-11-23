declare const el: { a: number };
declare const u: unknown;
declare const o: object;
export const r1 = el[u];
export const r2 = el[o];
export const r3 = el[null];
export const r4: number = el[true];
