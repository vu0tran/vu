interface X { a: string; b: number; c: boolean }
type P1 = Pick<X, 'a'>;
type O1 = Omit<X, 'a'>;
type Pa = Partial<X>;
type PO = Partial<Omit<X, 'a'>>;
type MyOmit<T, K extends keyof T> = Omit<T, K>;
type O2 = MyOmit<X, 'b'>;
type NN<T> = T extends null ? never : { v: T };
type N1 = NN<string>;
type R1 = Record<string, X>;
type MyRec<V> = Record<string, V>;
type R2 = MyRec<X>;
declare const e: unknown;
export const b1: number = e as P1;
export const b2: number = e as O1;
export const b3: number = e as Pa;
export const b4: number = e as PO;
export const b5: number = e as O2;
export const b6: number = e as N1;
export const b7: number = e as R1;
export const b8: number = e as R2;
export const b9: number = e as Omit<X, 'a'>;
// An alias whose body is a generic alias whose body is a mapped type (Omit = Pick<...>, Record): named
// by the alias it is written for (getObjectTypeInstantiation keys by alias); Partial (homomorphic) not.
