type I = typeof Symbol.iterator;
export const a: 'z' = Symbol.iterator;
export const b: 'z' = null as unknown as I;
type R = ReturnType<any[][typeof Symbol.iterator]>;
export const c: 'z' = null as unknown as R;
export const d: 'z' = [1][Symbol.iterator]();
