type R = { a: number; b: number };
declare const r: R;
declare const k: string;
export const o1: 'z' = { ...r, [k]: 1 };
export const o2: 'z' = { ...r, [k]: 1, c: 's' };
export const o3: R = { ...r, [k]: 'x' };
declare const n: number;
export const o4: 'z' = { ...r, [n]: true };
export const o6 = Object.keys(r).reduce((acc, key) => ({ ...acc, [key]: 1 }), {} as R);
