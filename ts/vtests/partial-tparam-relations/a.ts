// Partial<T> to T, and a primitive to Partial<O> with O extends object: unrelated
export function f<C extends object, D>(m: Partial<C>, d: Partial<D>) {
  const a: C = m;
  const b: D = d;
  const p = new Proxy(m, {}) as C;
  return [a, b, p];
}
export function g<U extends { a: number }, O extends object>(n: number, s: string) {
  const x6: Partial<O> = n;
  const x7: Partial<O> = s;
}
