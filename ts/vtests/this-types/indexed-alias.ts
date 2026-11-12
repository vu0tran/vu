// An alias of an indexed access that resolves prints the resolved type (T[keyof T] keeps the name)
export {};
type O = { a: { x: 1 }; b: string | number };
type A = O['a'];
type B = O['b'];
const a: A = 5;
const b: B = true;
type G<T> = T[keyof T];
const g: G<O> = true;
