type SSA<V> = V | ((prev: V) => V);
interface WA<V, A extends unknown[], R> { v: V; write: (...a: A) => R }
type PA<V> = WA<V, [SSA<V>], void>;
declare const a: PA<ReadonlyMap<string, string>>;
declare const set: <V, A extends unknown[], R>(atom: WA<V, A, R>, ...args: A) => R;
set(a, (w) => { const q: number = w; return w; });
declare const set2: <V, A extends unknown[], R>(atom: WA<V, A, R>, ...args: A) => R;
set2(a, (w: ReadonlyMap<string, string>) => w);
declare const b: WA<number, [(p: number) => number], void>;
set(b, (w) => { const q: string = w; return w; });
