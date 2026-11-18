interface Px<T> { _p: T }
declare const mock: <T, R extends Px<T> & T = Px<T> & T>(impl?: Partial<T>) => R;
interface W { a: string; b: number }
const m = mock<W>({ zz: 1 });
m.c;
const n: null = m;
const ok = mock<W>({ a: 'x' });
const n2: null = ok;
declare function f<A, B = A[]>(x: A): B;
const r = f<string>(1);
const n3: null = r;
declare function takesW(w: W): void;
takesW(m);
type MP<T> = { [K in keyof T]: () => T[K] };
function g<T>(x: MP<T>, y: MP<T> & T) { takesW(x); takesW(y); }
