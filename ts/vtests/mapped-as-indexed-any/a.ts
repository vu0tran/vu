// inference to a mapped type with an as clause over keyof M['attrs'], M's constraint making
// M['attrs'] any: no properties, nothing inferred (M comes from `this`)
declare class Model<A = any> { _attributes: A; static findOne<M extends Model>(this: { new(): M }, o: { where?: Where<M['_attributes']> }): M | null; }
type Where<T> = { [K in keyof T as K extends string ? `${K}.${string}` : never]?: unknown };
class Val extends Model<{ id: number; name: string }> {}
const v = Val.findOne({ where: { 'id.x': 1 } });
const n: number = v;
