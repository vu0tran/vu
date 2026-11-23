// a protobuf-like init shape: a oneof's selected message as { case, value: Init<V> }
export type Sel<K extends string, V> = { case: K; value: V };
export type Init<T> = T | { [P in keyof T]?: FieldInit<T[P]> };
type FieldInit<F> = F extends Sel<infer C, infer V> ? { case: C; value: Init<V> } : F;
