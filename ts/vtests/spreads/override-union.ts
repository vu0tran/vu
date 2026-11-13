type A = { __rl: true; v: string };
type B = { [k: string]: unknown };
type C = { __rl: true; w: number };
export function f(a: A | B | string[], b: A | C, c: A | { v: 1 }) {
  const x = { __rl: true, ...a };
  const y = { __rl: true, ...b };
  const z = { __rl: true, ...c };
  return [x, y, z];
}
