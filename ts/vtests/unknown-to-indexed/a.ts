// unknown to T[K]: not assignable when T[K]'s constraint has no any or unknown, or there's none
export function f<T extends { a: string; b: number }, K extends keyof T, V, W extends keyof V>(t: T, k: K, v: V, w: W, u: unknown) {
  function h(x: T[K]): 1;
  function h(x: unknown): 2;
  function h(x: unknown) { return x ? 1 : 2; }
  const r: 3 = h(u);
  function g(x: V[W]): 1;
  function g(x: unknown): 2;
  function g(x: unknown) { return x ? 1 : 2; }
  const r2: 3 = g(u);
  return [r, r2, t[k], v[w]];
}
