// destructuring an intersection of tuples: each element the members' elements intersected
type P = [message: string, meta?: { a: number }];
declare const calls: (P & P)[];
declare const two: [string, number] & [string, 1];
export function f() {
  const [message] = calls[0];
  const n: number = message;
  const [a, b] = two;
  const m: string = b;
}
