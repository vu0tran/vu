// M[T] instantiated with T any: any
export {};
type M = { a: 1; b: "s" };
type R<T extends keyof M = keyof M> = { v?: M[T] };
declare function f<T extends keyof M>(k: T): R<T>;
const x = f("a" as any);
const n: string = x;
const m: number = x.v;
