type StartsWith<R extends [readonly unknown[], readonly unknown[]]> = R[0] extends [...R[1], ...infer Remain extends readonly unknown[]] ? Remain : never;
type A = StartsWith<[[1, 2, 3], [1]]>;
const a: string = null as unknown as A;
type Cat<X extends unknown[], Y extends unknown[]> = [...X, ...Y];
const b: string = null as unknown as Cat<[1], [2, 3]>;
type Tail<T> = T extends [infer _H, ...infer R] ? R : never;
const c: string = null as unknown as Tail<[1, 2, 3]>;
