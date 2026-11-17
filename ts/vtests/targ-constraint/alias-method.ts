export {};
interface B<T> { v: T }
interface O<T> { pk<K extends keyof T>(k: K): Pick<T, K>; }
declare const a: O<{ a: string; b: number }>;
const x: number = a.pk("a");
interface P<T> { pk<K extends keyof T>(k: K): B<Pick<T, K>>; }
declare const b: P<{ a: string; b: number }>;
const z: number = b.pk("a").v;
