declare function f<T>(x: T): T[];
const r: number = f(1);
declare function g<T>(x: T, c?: { m?: (v: T) => void }): T[];
const r2: number = g(1, {});
const r3: number = g(1, { m: (v) => {} });
declare function h<T>(x: T, c: { m: (a: T, b: T) => boolean }): T[];
const r4: number = h(1, { m: (a, b) => a === b });
export {};
