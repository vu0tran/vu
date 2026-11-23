// 'k' in x with x {} | undefined (unknown !== null): undefined & Record<'k', unknown> is never, left out;
// the right side's errors, checkInExpression
declare function ok(v: unknown): asserts v;
export function f(body: unknown) {
  ok(body !== null && 'max_tokens' in body);
  const n: number = body;
}
export function g(x: unknown, y: {}, z: object | undefined, w: { a: 1 } | null) {
  if (x !== null && x !== undefined && 'k' in x) {}
  if ('k' in y) {}
  if (z && 'k' in z) { const m: number = z; }
  if ('a' in z) {}
  if ('a' in w) {}
}
