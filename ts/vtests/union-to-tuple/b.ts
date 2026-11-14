type UnionToIntersection<U> = (U extends any ? (arg: U) => void : never) extends (arg: infer I) => void ? I : never;
type X1 = UnionToIntersection<((x: "a") => 0) | ((x: "b") => 0)>;
const x1: number = null as any as X1;
type L1 = X1 extends (x: infer L) => 0 ? L : never;
const l1: number = null as any as L1;
type X2 = UnionToIntersection<{ a: 1 } | { b: 2 }>;
const x2: number = null as any as X2;
export {};
