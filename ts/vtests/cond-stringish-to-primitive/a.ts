// A conditional type whose every branch is a string (react-hook-form's Path/PathImpl: template literals, through aliases and indexed mapped types): never related to a primitive that isn't one.
type Prim = string | number | null | undefined;
type PI<K extends string, V> = V extends Prim ? `${K}` : `${K}` | `${K}.${keyof V & string}`;
type PNum<V> = V extends Prim ? 1 : "a";
function f<K extends string, V>(p: PI<K, V>, q: PNum<V>) {
  const a: undefined = null as unknown as PI<K, V>;
  const b: number | string = p;
  const c: null = q;
}
type PInt<T> = T extends readonly (infer V)[] ? PI<`${number}`, V> : { [K in keyof T]-?: PI<K & string, T[K]> }[keyof T];
type Path<T> = T extends any ? PInt<T> : never;
function g<T>(p: Path<T>) {
  const a: undefined = null as unknown as Path<T>;
  const b: number = null as unknown as PInt<T>;
}
