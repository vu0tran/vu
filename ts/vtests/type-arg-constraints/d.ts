type IsNever<T> = [T] extends [never] ? true : false;
type Extends<L, R> = IsNever<L> extends true ? IsNever<R> : [L] extends [R] ? true : false;
type AP = { role: { slug: string } };
type P = AP & { readonly id: string; readonly email?: string };
type E1 = Extends<P, AP>;
const e1: E1 = false;
interface ET<Actual> {
  toExtend: <Expected extends Extends<Actual, Expected> extends true ? unknown : { mismatch: Actual }>() => true;
}
declare function expectTypeOf<A>(): ET<A>;
expectTypeOf<P>().toExtend<AP>();
export {};
