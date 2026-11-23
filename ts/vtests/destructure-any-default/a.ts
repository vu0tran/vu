// destructuring any: the defaults and computed names are still checked (their contextual type any)
declare const input: any;
declare const k: string;
export function f() {
  const { a, b = [], c = 50, [k]: d = 1 } = input;
  const n: string = c;
  const { e = nope } = input;
  return [a, b.length, n, d, e];
}
