declare class Catch<X> { inner: X }
declare class T<O, D, I = O> { readonly _o: O; readonly _i: I; d: D; c(def: O): Catch<this>; c(def: (ctx: { e: string; input: I }) => O): Catch<this>; }
declare class N extends T<never, { k: 1 }, never> {}
declare const n: N;
export const a: T<any, any, any> = n;
