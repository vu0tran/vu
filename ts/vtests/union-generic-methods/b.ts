const R = { a: ['x', 'y'] as const, b: ['z'] as const, c: ['p', 'q', 'r'] as const };
export function f() {
  const s = Object.entries(R).flatMap(([res, ops]) => [...ops.map((op) => `${res}:${op}` as const)]);
  const n: number = s;
}
