// "k" in x of a union with null or undefined in it: those members intersected with Record<"k",
// unknown> (never), not left unknown, narrowTypeByInKeyword; the operand checked for null and
// undefined (checkInExpression's checkNonNullType).
declare const x: { a: number } | { b: string } | undefined;
declare function ok(v: unknown): asserts v;
export function f() {
  if ('a' in x) { const n: string = x.a; }
  ok(x !== undefined && 'c' in x);
  const m: number = x.c;
}
