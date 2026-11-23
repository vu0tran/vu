// A default type argument naming an aliased union of function types keeps its name when the
// other parameters are instantiated: a function type's instantiation by the type parameters it
// may mention (React's ReactElement<any, string | JSXElementConstructor<any>>).
type JC<P> = ((props: P) => number) | (new (props: P) => { x: 1 });
interface RE<P = any, T extends string | JC<any> = string | JC<any>> { p: P; t: T }
declare const a: RE<1>;
export const z1: 1 = a;
interface R2<T = string | JC<any>> { t: T }
declare const b: R2;
export const z2: 1 = b;
interface R3<T extends string | JC<any> = string | JC<any>> { t: T }
declare const c: R3;
export const z3: 1 = c;
