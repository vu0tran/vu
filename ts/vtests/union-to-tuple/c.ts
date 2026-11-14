type UnionToIntersection<U> = (U extends any ? (arg: U) => void : never) extends (arg: infer I) => void ? I : never;
type X2 = UnionToIntersection<{ a: 1 } | { b: 2 }>;
declare const x2: X2;
const y: string = x2;
type F = ((arg: { a: 1 }) => void) | ((arg: { b: 2 }) => void);
type I3 = F extends (arg: infer I) => void ? I : never;
declare const i3: I3;
const z: string = i3;
export {};
