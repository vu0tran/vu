// T[K] with K constrained to keys some of which the object lacks (Path<T>'s template literal key
// `a.${number}`, no index signature for it): no constraint (getIndexedAccessTypeOrUndefined
// without an access node), related as unknown is (react-hook-form's getValues and setValue,
// compared when the array literal [getValues, setValue] is subtype-reduced).
type Primitive = null | undefined | string | number | boolean | symbol | bigint;
type ArrayKey = number;
type PathImpl<K extends string | number, V> = V extends Primitive ? `${K}` : `${K}` | `${K}.${PathInternal<V>}`;
type PathInternal<T> = T extends ReadonlyArray<infer V> ? PathImpl<ArrayKey, V> : {
  [K in keyof T]-?: PathImpl<K & string, T[K]>;
}[keyof T];
type Path<T> = T extends any ? PathInternal<T> : never;
type PathValueImpl<T, P extends string> = T extends any ? P extends `${infer K}.${infer R}` ? K extends keyof T ? undefined extends T[K] ? PathValueImpl<T[K], R> | undefined : PathValueImpl<T[K], R> : K extends `${ArrayKey}` ? T extends ReadonlyArray<infer V> ? PathValueImpl<V, R> : never : never : P extends keyof T ? T[P] : P extends `${ArrayKey}` ? T extends ReadonlyArray<infer V> ? V : T extends undefined ? undefined : never : never : never;
type PathValue<T, P extends Path<T>> = PathValueImpl<T, P>;
type Config = { dirty?: boolean; touched?: boolean };
type Get<T> = <N extends Path<T>>(name: N, config?: Config) => PathValue<T, N>;
type Set<T> = <N extends Path<T>>(name: N, value: PathValue<T, N>, options?: Config) => void;
type V = { a: string[]; b: number };
declare const get: Get<V>;
declare const set: Set<V>;
export const deps = [get, set];
export const n: number = deps;
export const s1: Set<V> = get;
export const g1: Get<V> = set;
