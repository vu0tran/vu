export {};
type W<T> = [T, 1];
type P = [1, 2];
type A<T> = T[];
type RA<T> = readonly T[];
declare const w: W<1>; declare const p: P; declare const a: A<1>; declare const ra: RA<2>;
const b1: boolean = w; const b2: boolean = p; const b3: boolean = a; const b4: boolean = ra;
