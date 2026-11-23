// an index that can't be a key (an object or function type) made by instantiation: unknown
// (getIndexedAccessType without an access node); a homomorphic mapped type over a primitive is the
// primitive, so ts-essentials-style WritableKeys<'a'> is a union of String's member types
type IsEqual<A, B> = (<T>() => T extends A ? 1 : 2) extends <T>() => T extends B ? 1 : 2 ? true : false;
type WritableKeys<T> = { [K in keyof T]-?: IsEqual<{ [Q in K]: T[K] }, { -readonly [Q in K]: T[K] }> extends true ? K : never }[keyof T];
type ExcludeReadonly<T> = T extends {} ? T[WritableKeys<T>] : T;
export const a: ExcludeReadonly<{ readonly x: 1; y: 2 }> = 3;
type Ix<T, K> = K extends unknown ? T[K & keyof T] : never;
export const b: Ix<{ x: 1 }, 'x'> = 3;
export const d: ExcludeReadonly<'s'> = 3n;
export const e: WritableKeys<'s'> extends string ? 1 : 0 = 3n;
