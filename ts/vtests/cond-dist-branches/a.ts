// two instantiations of Extract whose check types relate one way but whose true branches don't: through the source's default constraint, which a distribution-dependent target never takes (so the second overload)
type X = { case: "a"; value: { n: number } };
type Y = { case: "a"; value: { n: number; m: string } };
export function f<C extends string>(a: Extract<X, { case: C }>, b: Extract<Y, { case: C }>) {
  function g(x: Extract<Y, { case: C }>): string;
  function g(x: unknown): boolean;
  function g(x: unknown) { return x as any; }
  const r1: number = g(a);
  function h(x: Extract<X, { case: C }>): string;
  function h(x: unknown): boolean;
  function h(x: unknown) { return x as any; }
  const r2: number = h(b);
}
