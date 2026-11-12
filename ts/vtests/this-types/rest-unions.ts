// Tuple contexts from a type parameter's constraint, rest parameters typed as unions of tuples,
// and inference from a type parameter source through its constraint
interface Ret<T extends any[]> {
  (name: string, fn: (...args: T) => void, options?: number): void;
}
interface Each {
  <T extends any[] | [any]>(cases: ReadonlyArray<T>): Ret<T>;
  <T>(cases: ReadonlyArray<T>): Ret<T[]>;
}
declare const each: Each;
each([['a', null, 1], ['b', 'x', 2]])('x', (label, input, n) => {
  const s: string = label;
  const t: number = input;
});
declare function e2<T extends any[] | [any]>(cases: T): T;
const t2: number = e2(['a', 1]);
type TV = string | number | null;
function g<T extends Record<string, TV>>(p: T) {
  for (const [k, v] of Object.entries(p)) { const x: TV = v; const y: string = v; }
}
declare function gi<U>(o: { [s: string]: U }): U;
function h<T extends { a: number }>(p: T) { const r: string = gi(p); }
