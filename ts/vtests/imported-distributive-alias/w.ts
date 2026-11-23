export type U = 'a' | 'b' | 'c';
export type W<T> = T extends 'a' ? { k: 1 } : { k: 2; t: T };
export type M<T> = T extends 'a' ? { k: 1 } : T;
export type V2 = W<U>;
