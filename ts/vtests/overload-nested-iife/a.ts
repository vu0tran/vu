declare function red<T>(f: (a: T, b: number) => T, init: T): T;
declare function red<T, U>(f: (a: U, b: number) => U, init: U): U;
export const r = red<string[]>((errs, x) => ((res) => (res.length ? [...errs, res] : errs))(String(x)), []);
