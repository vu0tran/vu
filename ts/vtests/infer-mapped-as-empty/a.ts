type Bad<T> = T extends Function ? true : false;
type P<T> = { [K in keyof T as Bad<T[K]> extends true ? never : K]: T[K] };
declare function f<T>(x: P<T>): T;
const r = f({});
const n: number = r;
const r2 = f({ a: 1 });
