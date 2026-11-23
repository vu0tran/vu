// a generic class's overloaded method: the class's type parameter instantiated in every overload,
// though the first doesn't mention it (isTypeParameterPossiblyReferenced on all declarations)
interface B2 { base: true }
interface C2 extends B2 { user: string }
declare class S2<in out C extends B2 = B2> {
  run2<T = string>(req: number): T;
  run2<T = string>(req: { v?: T }, opts?: { ctx: C }): Promise<T[]>;
  run3<T = string>(req: number): T;
  run3<T = string>(req: { v?: T }, opts?: C): Promise<T[]>;
}
declare const t2: S2<C2>;
const b3: number = t2.run2({}, { ctx: { base: true, user: 'u' } });
const b4: number = t2.run2<boolean>({}, { ctx: { base: true, user: 'u' } });
const b5: number = t2.run3<boolean>({}, { base: true, user: 'u' });
const b6: number = t2.run2<boolean>({}, { ctx: { base: true } });
export { b3, b4, b5, b6 };
