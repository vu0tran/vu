// a static method whose this parameter is an alias that reads the class's statics (sequelize's
// findAll(this: ModelStatic<M>), ModelStatic = Pick<typeof Model, NonConstructorKeys<typeof Model>>
// & { new (): M }): its parameters are made after the alias, as tsc resolves them lazily
declare class Model<A = any> {
  static findAll<M extends Model>(this: ModelStatic<M>, options?: { limit?: number }): Promise<M[]>;
  static init(): void;
  a: A;
}
type NonConstructorKeys<T> = ({ [P in keyof T]: T[P] extends new () => any ? never : P })[keyof T];
type NonConstructor<T> = Pick<T, NonConstructorKeys<T>>;
type ModelStatic<M extends Model> = NonConstructor<typeof Model> & { new (): M };
type ModelCtor<M extends Model> = ModelStatic<M>;
interface Inst extends Model<{ x: 1 }> { actorId: string }
declare function define<M extends Model>(): ModelCtor<M>;
const Log = define<Inst>();
export async function f() {
  const ds = await Log.findAll();
  const n: number = ds[0]!.actorId;
  return n;
}
type MS2 = Pick<typeof M2, NonConstructorKeys<typeof M2>> & { new (): M2 };
declare class M2 {
  static fa<M extends M2>(this: { new (): M } & MS2): M[];
  static init(): void;
}
declare const L2: MS2;
export const k: number = L2.fa();
