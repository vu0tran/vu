type C2<T, U> = { cmp: (a: U, b: U) => boolean; sel: (v: T) => U };
declare function ua<T, U>(x: T, c: C2<T, U>): T[];
const r3: number = ua("x", { cmp: (a, b) => a.length === b.length, sel: (v) => v });
export {};
