// an intersection source with a member (or all of an intersection member) of the union target:
// related, before the generic members are tried
type M<O, P extends string> = { [K in keyof O as `${P}${K & string}`]: O[K] };
type A = { a: 1 };
type B = { b: 2 };
export function f<O, P extends string>(x: M<O, P> & A & B, y: M<O, P> & A): void {
  const u: M<O, `/${P}`> | (A & B) = x;
  const v: M<O, `/${P}`> | A = y;
}
