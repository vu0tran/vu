// An object indexed by the error type (an unresolved import): its index signatures, as by any;
// a mapped type over the error type has a string index signature, and keyof it is the error type.
import { Product } from './missing_pb';

type S = { [x: string]: number };
declare const e1: S[typeof Product];
type M = { [k in typeof Product]: number };
declare const e2: M[keyof M];
type N = { [x: number]: boolean };
declare const e3: N[typeof Product];
export const b1: string = e1;
export const b2: string = e2;
export const b3: string = e3;

type ToEnum<T extends string> = { [k in T]: k };
declare function en<const T extends readonly string[]>(v: T): ToEnum<T[number]>;
const a = en(Product);
type E = typeof a;
declare const e4: E[keyof E];
export const b4: string = e4;
