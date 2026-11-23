// A homomorphic mapped type over a type variable instantiated to any, whose constraint is only
// arrays and tuples, is an array of the mapped element (Promise.all of an any).
declare const ids: any;
type M<T extends readonly unknown[] | []> = { -readonly [P in keyof T]: Awaited<T[P]> };
type R<T extends unknown[]> = { readonly [P in keyof T]?: T[P] };
type O<T extends object> = { [P in keyof T]: T[P] };
type N<T> = { [P in keyof T]: T[P] };
declare function all<T extends readonly unknown[] | []>(values: T): Promise<M<T>>;
const n1: number = all(ids);
const n2: number = Promise.all(ids);
const n3: number = null! as M<any>;
const n4: number = null! as R<any>;
const n5: number = null! as O<any>;
const n6: number = null! as N<any>;
Promise.all(ids).then((rs) => {
  const n7: number = rs;
});
