// A merged interface whose first declaration gives no defaults: the later one's, before anything
// reads it (@types/node's NodeJS.AsyncIterator<any>, getDefaultFromTypeParameter).
declare namespace NS { interface It<T, TReturn, TNext> { b: T } }
declare namespace NS { interface It<T, TReturn = undefined, TNext = any> { a: T; r: TReturn; n: TNext } }
interface J<T> { j: T }
interface J<T = string> { k: T }
declare const x: NS.It<1>;
declare const y: J;
export const z: 1 = x;
export const z2: 1 = x.r;
export const z3: 1 = y.k;
