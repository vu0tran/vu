// A deferred conditional source relates through its default constraint, its branches united, to
// any target (react-hook-form's FieldPathByValue<T, V> as a Path<T>); then through its
// distributive constraint; neither relating, it isn't related.
type FV = Record<string, any>;
type Paths<T> = T extends any ? keyof T & string : never;
type ByValue<T, V> = { [K in Paths<T>]: T[K] extends V ? K : never }[Paths<T>];
declare function take<T, N extends Paths<T>>(name: N): void;
export function f<T extends FV, N extends ByValue<T, boolean>>(n: N) {
  take<T, N>(n);
}
type Val<M, V> = M extends true ? V[] : V | null;
export function g<V, M extends boolean>(x: Val<M, V>) {
  const a: V[] | V | null = x;
  const b: { id: string } = x;
}
