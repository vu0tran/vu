export type Box<T, O = { k?: unknown }> = { t: T; o: O; n: number };
export type Ob<A extends string = string> = { a: A };
export type Sh<D> = D extends number ? never : Ob;
