declare function f(o: { a: number }, cb: (x: number) => void): 1;
declare function f(cb: (x: string) => void): 2;
export const r: 2 = f((x) => { const n: number = x; });
export const r2: 2 = f((x) => { x.foo; });
declare function g<T>(cb: (x: T) => void, o: { a: number }): 1;
declare function g(cb: (x: string) => void): 2;
export const r3 = g((x) => { const q: number = x; });
