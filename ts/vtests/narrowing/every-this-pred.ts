type A = { type: 'A'; a: 1 };
type B = { type: 'B'; b: 1 };
declare function use(x: A): void;
export function f(args: (A | B)[], o: { args: (A | B)[] }) {
  if (args.every((v) => v.type !== 'B')) {
    use(args[0]);
  }
  if (args.every((v): v is A => v.type !== 'B')) {
    use(args[0]);
  }
  if (o.args.every((v): v is A => v.type !== 'B')) {
    use(o.args[0]);
  }
}
