declare class B<T> { v: T; both<U>(o: B<U>): B<T & U> }
declare function mk<T>(): B<T>;
type K = 'a' | 'b';
export const b1: B<K> = mk();
declare function f<T>(x: T & { tag: 1 }): T;
export const f1: 'z' = f({ tag: 1 as const, n: 2 });
declare function g<T, U>(x: T & U): [T, U];
export const g1: 'z' = g('a');
declare function h<T>(x: T & string): T;
export const h1: 'z' = h('s');
