declare const AND: unique symbol;
type V<A> = A | { eq: A };
type Hash<T = any> = {
  [K in keyof T as K extends string ? K | `$${K}$` : never]?: V<T[K]>;
} & {
  [K in keyof T as K extends string ? `${K}.${string}` | `$${K}$.${string}` : never]?: V<any>;
} & {
  [attribute: `$${string}.${string}$` | `$${string}.${string}$::${string}`]: V<any>;
};
type AA<T> = T | T[];
type Rec<T> = AA<T | { [AND]: AA<Rec<T>> }>;
interface Where { w: 1 }
declare function where(): Where;
type WO<T = any> = Rec<Hash<T> | Where>;
declare function find<M extends { _a: object }>(o: { where: WO<M["_a"]> }): M;
export function f<M extends { _a: { id: string } }>(): M {
  const r = find<M>({ where: { [AND]: [where()] } });
  const n: number = [where(), 1];
  return r;
}
