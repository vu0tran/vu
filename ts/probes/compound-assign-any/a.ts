// no-unsafe-assignment checks `=` only: a compound assignment (??=, ||=, +=) of an any value isn't
// reported (typescript-eslint's AssignmentExpression[operator = "="])
declare const a: any;
export function f(x?: string, n = 0, s = '') {
  x ??= a;
  x ||= a;
  n += a;
  s += a;
  let y: string;
  y = a;
  return [x, n, s, y];
}
