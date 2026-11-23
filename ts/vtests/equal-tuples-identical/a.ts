// The Equal<X, Y> trick on tuples: identical tuples have the same element flags, readonly-ness and identical elements; a tuple is never identical to another object type.
type Equal<X, Y> = (<T>() => T extends X ? 1 : 2) extends (<T>() => T extends Y ? 1 : 2) ? true : false;
declare function f<A, B>(a: A, b: B): Equal<A, B>;
declare const t1: [];
declare const t2: [];
const a: false = f(t1, t2);
const b: true = f([1, "x"] as [number, string], [2, "y"] as [number, string]);
const c: true = f([1] as [number], [2] as [number?]);
const d: true = f([1] as readonly [number], [2] as [number]);
const e: true = f([1] as [number], [2] as number[]);
const g: false = f({ a: 1 }, { a: 2 });
