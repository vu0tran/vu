declare const A: readonly ("a" | "b")[];
declare const B: readonly ("c")[];
const T = ['x', ...A, 'y', ...B, 'z'] as const;
export const n: number = T;
const U = [...A, ...B] as const;
export const m: number = U;
