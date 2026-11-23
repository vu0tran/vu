// object has no properties: indexed while reading a constraint it is unknown, and an intersection's
// object member is passed over (drizzle's Column<..., TTypeConfig extends object = object>)
interface Base { data: unknown; driverParam: unknown }
type Cfg<T extends Base, TT extends object> = T & { data: T['data'] } & TT;
interface Col<T extends Base = Base, TT extends object = object> { readonly _: Cfg<T, TT> }
type Data<C extends Col> = C['_']['data'];
declare function inArray<C extends Col>(c: C, values: ReadonlyArray<Data<C>>): C;
declare const col: Col<{ data: string; driverParam: string }, {}>;
export const a = inArray(col, ['x']);
export const b = inArray(col, [1]);
export const c: number = null! as Cfg<Base, object>['data'];
