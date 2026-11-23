// a tuple with a variadic element to an array type: its elements, ...A as A[number]
function f<A extends string[], B extends readonly number[]>(a: [...A, string], b: [...B], c: readonly [...A]) {
  const x: string[] = a;
  const y: number[] = b;
  const z: readonly number[] = b;
  const v: readonly string[] = c;
  return [x, y, z, v];
}
type R1<S extends string, Acc extends string[] = []> = S extends `${infer H}.${infer T}` ? R1<T, [...Acc, H]> : [...Acc, S];
type R2<S extends string> = R1<S>;
type N1<S extends string> = S extends `${infer H}.${infer T}` ? [H, T] : 0;
type N2<S extends string> = N1<S>;
export const r: R2<'a.b.c'> = 1n;
export const n: N2<'a.b'> = 1n;
export { f };
// a conditional on a tuple with a generic variadic element is deferred (isGenericTupleType)
type D<T extends unknown[]> = [...T] extends string[] ? 'y' : 'n';
export function g<T extends string[]>(t: T): D<T> {
  return t.length > 0 ? 'y' : 'n';
}
