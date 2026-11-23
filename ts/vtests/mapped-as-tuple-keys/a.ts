// a mapped type with an as clause maps a tuple or array as an object, over all its keys (its
// well-known symbol members' unique symbols too); the as clause applies to index signature keys
type IOK<T extends object, K extends keyof T> = T extends unknown ? K extends keyof T ? T extends Record<K, T[K]> ? false : true : false : false;
type M<T> = { [K in keyof T as IOK<T & object, K> extends false ? never : K]: never };
export const a: keyof M<[true, true]> = 1n;
type M2<T> = { [K in keyof T as K]: 1 };
export const d: M2<[true]> = 1n;
type M3<T> = { [K in keyof T as K extends symbol ? K : never]: T[K] };
type M3K = keyof M3<{ a: 1; [Symbol.iterator](): void }>;
export const c: M3K extends symbol ? 1 : 0 = 1n;
type M4<T> = { [K in keyof T as K extends string ? never : K]: T[K] };
export const n: M4<{ [n: number]: 1; a: 2 }>[0] = 1n;
export const k: Exclude<keyof [1], number | `${number}` | 'length' | keyof unknown[]> = 1n;
// an index signature's key renamed: to a literal a property, to number a number index signature
type ChangePath<S, Path extends string> = { [K in keyof S as Path]: S[K] };
export const p1: ChangePath<{ [k: string]: 1 }, '/x'>['/x'] = 1n;
export const p2: ChangePath<{ a: 2; [k: string]: 1 | 3 }, '/x'>['/x'] = 1n;
type ToNum<S> = { [K in keyof S as K extends string ? number : K]: S[K] };
export const p3: ToNum<{ [k: string]: 1 }>[0] = 1n;
