// An optional chain's arguments and element index are evaluated past its ?.: the receivers of
// its ?. links aren't null or undefined there (bindOptionalChain), typeof queries included
// (a package's `x.before?.[k as keyof typeof x.before]`).
type A = { x: number; y: string; f(n: number): number };
export function f(p: { a?: A | null }, k: string, q?: (n: number) => void, r?: A) {
  p.a?.f(p.a.x);
  q?.(q.length);
  r?.f(r.x);
  const v = p.a?.[p.a.y === "" ? "x" : "y"];
  const w = p.a?.[k as keyof typeof p.a];
  const z: 1 = w;
  p.a?.f(1).toFixed(p.a.x);
  const u = p.a.x;
  return [v, u];
}
