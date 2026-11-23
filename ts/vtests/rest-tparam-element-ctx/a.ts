// ...args: A with A inferred from another parameter: a context-sensitive argument's contextual
// type is A[k] of what A was inferred as (jotai's store.set(atom, (prev) => ...)).
interface WA<V, A extends unknown[], R> { read: () => V; write: (...args: A) => R }
declare function mk<V>(v: V): WA<V, [V | ((prev: V) => V)], void>;
declare function set<V, A extends unknown[], R>(atom: WA<V, A, R>, ...args: A): R;
const b = mk<number>(1);
set(b, (p) => {
  const n: string = p;
  return p;
});
declare function mk2(): WA<string, [number, (s: string) => void], boolean>;
export const r: string = set(mk2(), 1, (s) => {
  const n: number = s;
});
declare function cb<A extends unknown[]>(f: (...a: A) => void, ...args: A): A;
export const u: number = cb((a: number, b: string) => {}, 1, 's');
