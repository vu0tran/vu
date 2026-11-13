type A = { type: 'A'; a: 1 };
type B = { type: 'B'; b: 1 };
export function f(args: (A | B)[]) {
  const z: 'z' = args.filter((v) => v.type !== 'B');
  const g = (v: A | B) => v.type !== 'B';
  const z2: 'z' = g;
  if (args.every(g)) { const z3: 'z' = args; }
}
