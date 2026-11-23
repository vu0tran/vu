// destructuring any with defaults: the defaults are typed, so the file's rules run
declare const input: any;
export function f() {
  const { a, b = [], c = 50 } = input;
  return [a, b.length, c];
}
