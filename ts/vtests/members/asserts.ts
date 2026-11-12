declare function assert(value: unknown, message?: string): asserts value;
declare function isStr(v: unknown): asserts v is string;
export function f(d?: { get?: () => number }) {
  const g = d?.get;
  assert(g, "x");
  const n: number = g();
  return n + d.get!();
}
export function h(v: unknown) {
  isStr(v);
  return v.length;
}
export function k(v: unknown) {
  return v.length;
}
let resolveFn: (() => void) | null = null;
export const p = new Promise<void>((resolve) => { resolveFn = resolve; });
