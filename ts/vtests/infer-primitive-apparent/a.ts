// A primitive source infers through its apparent type (String for a string), unless the two are
// definitely unrelated (typesDefinitelyUnrelated).
declare function it<T>(x: Iterable<T>): T;
declare function it2<T>(x: Iterable<T>, f?: (v: T) => number): T;
export const a: number = it('abc');
export const b: number = it2('abc', (v) => 0);
declare const s: string;
export const c: number = it2(s, (v) => {
  const q: number = v;
  return 0;
});
export const d: number = Uint8Array.from('xyz', (ch) => {
  const q: number = ch;
  return 0;
});
declare function len<T>(x: { length: T }): T;
export const e: string = len('abc');
declare function fm<U>(cb: () => U | ReadonlyArray<U>): U[];
export const f: 'z' = fm(() => (Math.random() ? 'a' : []));
declare function g<T, U>(x: T & U): [T, U];
export const g1: 'z' = g('a');
