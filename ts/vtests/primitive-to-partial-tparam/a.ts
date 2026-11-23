// a primitive to a mapped type over keyof an unconstrained type parameter: unrelated
export function f<T, U extends { a: number }>(n: number, s: string, o: { a: 1 }, e: {}) {
  const x1: Partial<T> = n;
  const x2: Partial<T> = s;
  const x4: Partial<T> = e;
  const x7: Partial<{ [K in keyof T]: T[K] }> = n;
  const x8: Partial<{ [K in keyof T]: string }> = n;
}
