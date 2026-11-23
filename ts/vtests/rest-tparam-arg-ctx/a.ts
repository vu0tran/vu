// A callback at a rest parameter typed by a type parameter: its contextual type is its position
// in the type argument inferred from the other arguments (jotai's set(atom, prev => ...)).
interface WA<V, A extends unknown[], R> { read: V; write: (...args: A) => R }
type Setter = <V, A extends unknown[], R>(atom: WA<V, A, R>, ...args: A) => R;
type SSA<V> = V | ((prev: V) => V);
declare const doneAtom: WA<Record<string, string[]>, [SSA<Record<string, string[]>>], void>;
declare const set: Setter;
set(doneAtom, (prev) => {
  const n: number = prev;
  return prev;
});

declare function set1<A extends unknown[]>(w: (...args: A) => void, ...args: A): A;
declare const w1: (x: (prev: string) => string, y: number) => void;
const r = set1(w1, (prev) => prev, 1);
const n1: number = r;
set1(w1, (prev) => {
  const s: number = prev;
  return prev;
}, 2);
