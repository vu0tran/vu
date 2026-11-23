// Extract<A, { case: C }> to Extract<B, { case: C }>, A's value wider than B's: not related (the
// source's default constraint, an object, to a conditional target)
type V = { n: number };
type A = { case: 'a'; value: V | { n?: number } };
type B = { value: V; case: 'a' };
function f<C extends 'a'>(x: Extract<A, { case: C }>, y: Extract<B, { case: C }>) {
  const a: Extract<B, { case: C }> = x;
  const b: Extract<A, { case: C }> = y;
  const n: number = x;
}
