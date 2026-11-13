declare function assertU(cond: unknown, msg: string): asserts cond;
export function f(value: unknown, o: { a?: string }) {
  assertU(Array.isArray(value), 'x');
  const q: 'z' = value;
  assertU(o.a, 'y');
  const r: 'z' = o.a;
  assertU(typeof o === 'object' && o.a !== undefined, 'w');
}
