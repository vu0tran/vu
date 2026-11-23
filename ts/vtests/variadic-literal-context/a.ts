type V = { a: string; b: string[]; c: number };
type Path = "a" | "b" | "c" | `b.${number}`;
type PV<P> = P extends keyof V ? V[P] : P extends `b.${number}` ? string : never;
type M1<T extends readonly Path[]> = { [K in keyof T]: PV<T[K] & Path> };
declare function w2<T extends readonly Path[]>(p: readonly [...T]): M1<T>;
const z = w2(['b', 'c']);
const q: string = z;
declare function w3<T extends readonly Path[]>(p: readonly [...T]): T;
const z3: string = w3(['b', 'c']);
declare function w4<T extends readonly Path[]>(p: readonly [...T]): [M1<T>, T];
const z4: string = w4(['b', 'c']);
export {};

declare function w4<T extends readonly ("a"|"b"|"c")[]>(p: readonly [...T]): T;
const y4: number = w4(['b', 'c']);
declare function c7<T extends readonly ("a"|"b"|"c")[]>(p: T): T;
const y7: number = c7(['b', 'c']);
declare function c8<T extends ("a"|"b"|"c")[]>(p: [...T]): T;
const y8: number = c8(['b', 'c']);
declare function c9<T extends unknown[]>(p: [...T]): T;
const y9: number = c9(['b', 'c']);

