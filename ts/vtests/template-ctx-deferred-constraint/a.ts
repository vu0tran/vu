// A template expression whose contextual type is a type parameter of an instantiated signature,
// constrained by a conditional type still deferred there (a path type like react-hook-form's
// FieldPath<T> in UseFormWatch<F>): a template literal context (its base constraint has template
// literal types), so the argument is `rows.${number}.region` and N is inferred from it.
type Prim = string | number | boolean | null | undefined;
type Impl<K extends string | number, V> = V extends Prim ? `${K}` : `${K}` | `${K}.${Internal<V>}`;
type Internal<T> = T extends ReadonlyArray<infer V> ? Impl<number, V> : { [K in keyof T]-?: Impl<K & string, T[K]> }[keyof T];
type Path<T> = T extends any ? Internal<T> : never;
type Val<T, P extends string> = T extends any ? P extends `${infer K}.${infer R}` ? K extends keyof T ? Val<T[K], R> : K extends `${number}` ? T extends ReadonlyArray<infer V> ? Val<V, R> : never : never : P extends keyof T ? T[P] : P extends `${number}` ? T extends ReadonlyArray<infer V> ? V : never : never : never;
type F = { rows: { name: string; region: string }[] };
type W<T> = {
  <N extends Path<T>>(name: N): Val<T, N>;
};
declare const w: W<F>;
declare const idx: number;
export const r: 1 = w(`rows.${idx}.region`);
declare function d<N extends Path<F>>(name: N): Val<F, N>;
export const r2: 1 = d(`rows.${idx}.region`);
