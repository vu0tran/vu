type U = 'day' | 'month';
type D = 'days' | 'months';
declare const M: Record<string, U>;
declare function so(u: U): void;
export function f(raw: D) {
  const unit = M[raw] || raw;
  so(unit);
  const n: 'z' = unit;
}
export function g(a: {}, b: { x: 1 }, c: object, d: 1 | 'a' | true) {
  const z2: 'z' = b || 5;
  const z3: 'z' = c || 5;
  const z4: 'z' = d || 5;
}
