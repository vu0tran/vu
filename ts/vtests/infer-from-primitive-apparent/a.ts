// A primitive argument infers through its apparent type: a string to Iterable<T> or ArrayLike<T>
// gives T = string (String's iterator and index signature), so Uint8Array.from(s, (ch) => ...)
// types ch.
declare const padded: string;
declare function it1<T>(e: Iterable<T>, f?: (v: T) => number): T;
const a1: number = it1(padded);
const a2 = it1(padded, (c) => c.charCodeAt(0));
const a3: number = a2;
declare function al<T>(e: ArrayLike<T>, f: (v: T) => number): T;
const b1: number = al(padded, (c) => 1);
const bytes = Uint8Array.from(padded, (character) => character.charCodeAt(0));
const n: number = bytes;
const arr: number = Array.from('abc');
declare function len<T extends { length: number }>(x: T): T;
const l1: boolean = len('xy');
declare function keyed<K>(x: { toFixed(d?: K): string }): K;
const k1: string = keyed(3);
declare function tupr<T, U>(): [T, U];
const t1: 'z' = tupr();
declare function ro<U>(cb: () => U | ReadonlyArray<U>): U[];
const r1: 'z' = ro(() => (Math.random() ? 'a' : []));
