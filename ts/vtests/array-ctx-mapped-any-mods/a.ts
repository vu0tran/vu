// An array literal whose contextual type is an intersection of generic mapped types over
// keyof M["_attributes"], M still being inferred (sequelize's WhereAttributeHash): the mapped
// types resolve over the apparent type any, a string index signature.
declare const opAnd: unique symbol;
declare class Model<A extends {} = any> {
  _attributes: A;
}
type Hash<T = any> = {
  [K in keyof T as K extends string ? K | `$${K}$` : never]?: T[K] | { eq: T[K] };
} & {
  [K in keyof T as K extends string ? `${K}.${string}` : never]?: unknown;
} & {
  [k: `$${string}.${string}$`]: unknown;
};
interface Where { kind: "where" }
type Opts<T> = AllowArray<Hash<T> | Where | { [opAnd]: AllowArray<Opts<T>> }>;
type AllowArray<T> = T | T[];
interface Static<M extends Model> { new (): M }
declare function findAll<M extends Model>(this: Static<M>, o: { where?: Opts<M["_attributes"]> }): M[];
declare function where(a: string): Where;
class Run extends Model<{ id: string; n: number }> {}
declare const R: Static<Run> & { findAll: typeof findAll };

const a = R.findAll({ where: { id: "x", [opAnd]: [where("a"), { n: 1 }] } });
const b = R.findAll({ where: { [opAnd]: [{ n: 2 }, [where("b")]] } });
const s: string = [a, b];
