type O = { a: { x: 1 } | { y: 2 }; b: { z: 3 } };
type S1 = O[keyof O];
declare const v: S1;
export const q: 1 = v;
type U = 'x' | 'y';
declare const u: U;
export const q2: 1 = u;
