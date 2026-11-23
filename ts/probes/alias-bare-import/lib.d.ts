export type Typed<K extends string, I, O> = { kind: K } & { i: I; o: O };
export type Unary<I extends object = object, O extends object = object> = Typed<'unary', I, O>;
export type Either<T = string> = { a: T } | { b: T };
