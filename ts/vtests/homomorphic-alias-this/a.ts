type identity<T> = T;
type flatten<T> = identity<{ [k in keyof T]: T[k] }>;
type P<T> = { [k in keyof T]?: T[k] };
export const a: flatten<{ x: number } & { y: string }> = 1;
export const b: P<{ x: number }> = 1;
export const c: flatten<{ x: 1 } | { y: 2 }> = 1;
declare class ZT<O> { readonly _output: O; optional(): ZO<this>; }
declare class ZO<T extends ZT<any>> extends ZT<T['_output'] | undefined> {}
declare class ZS extends ZT<string> {}
interface Like<O> { readonly _output: O; optional?(): Like<O | undefined>; }
type Out<T> = T extends Like<infer O> ? O : never;
export const d: Out<ZS> = 1;
declare function inf<O>(x: Like<O>): O;
declare const zs: ZS;
export const e: number = inf(zs);
