type JP<T, Key extends keyof T = keyof T> = Key extends string ? T[Key] extends Record<string, any> ? `${Key}.${JP<T[Key]>}` : `${Key}` : never;
type M1 = { e: boolean };
const x1: number = null as any as JP<M1>;
type M2 = { a: { b: boolean } };
const x2: number = null as any as JP<M2>;
type In = JP<{ b: boolean }>;
const x3: number = null as any as In;
export {};
