// a spread of a union of tuples and arrays into a rest parameter: an array of their elements
declare function log(...args: unknown[]): void;
declare function nums(a: string, ...rest: number[]): void;
export function f(args: [string, number] | [null] | [undefined, string?], b: number[] | [1, 2], c: [string] | boolean[]) {
  log(...args);
  nums('x', ...b);
  nums('x', ...c);
  nums('x', ...args);
}
