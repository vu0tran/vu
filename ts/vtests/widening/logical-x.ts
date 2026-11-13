declare const b: number[] | null;
const x = b ?? [];
export const x2: 'z' = x;
declare const c: { a: 1 } | undefined;
const y = c ?? {};
export const y2: 'z' = y;
const z = b || [];
export const z2: 'z' = z;
