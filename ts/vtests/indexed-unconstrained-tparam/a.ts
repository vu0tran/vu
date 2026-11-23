// T[K] of an unconstrained T and an unconstrained U: neither is assignable to the other (an
// overload taking U is passed over for one taking unknown)
export function f<T, U>(t: T, u: U, k: Extract<keyof T, string>) {
  function h(x: U): 1;
  function h(x: unknown): 2;
  function h(x: unknown) { return x ? 1 : 2; }
  const r: 3 = h(t[k]);
  function g(x: T[Extract<keyof T, string>]): 1;
  function g(x: unknown): 2;
  function g(x: unknown) { return x ? 1 : 2; }
  const r2: 3 = g(u);
  return [r, r2];
}
