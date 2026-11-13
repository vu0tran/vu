export {};
type R<T> = { a: T } & { b: T };
declare function f<T>(t: T): R<T>;
const r = f(1);
const b: boolean = r;
declare const r2: R<string>;
const b2: boolean = r2;
type U<T> = T[] | T;
declare function g<T>(t: T): U<T>;
const u = g("s");
const b3: boolean = u;
type V<T> = T | number;
declare function h<T>(t: T): V<T>;
const b4: boolean = h(1 as const);
const b5: boolean = h(true);
type W<T> = { x: T } & { y: 1 };
function q<T>(w: W<T>, w2: W<string>): W<T[]> { const b6: boolean = w; const b7: boolean = w2; return null!; }
const b8: boolean = q<number>(null!, null!);
