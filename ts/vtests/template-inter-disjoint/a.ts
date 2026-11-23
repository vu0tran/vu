// a template literal type is string-like: with number never, with a literal it matches that literal,
// a pattern template a literal doesn't match never (extractRedundantTemplateLiterals)
type ToString<T> = T extends string | number ? `${T}` : never;
type NK<Keys extends PropertyKey> = Keys | ToString<Keys & number>;
export const a: NK<`${number}`> = 1n;
type T2<K> = `x${K & number}`;
export const d: T2<`${number}` | 5> = 1n;
type K1<T extends readonly unknown[]> = keyof T & `${number}` extends never ? 'empty' : 'has';
export const e: K1<[true]> = 1n;
export const f: K1<[]> = 1n;
export const g: '1' & `${number}` = 1n;
export const h: `a${string}` & 'ab' = 1n;
