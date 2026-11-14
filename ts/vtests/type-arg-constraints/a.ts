type IsNever<T> = [T] extends [never] ? true : false;
type StrictEqual<L, R> = (<T>() => T extends (L & T) | T ? true : false) extends <T>() => T extends (R & T) | T ? true : false ? IsNever<L> extends IsNever<R> ? true : false : false;
type E1 = StrictEqual<readonly unknown[], readonly unknown[]>;
const e1: E1 = true;
type E2 = StrictEqual<string, number>;
const e2: E2 = true;
type E3 = StrictEqual<{ a: 1 }, { a: 1 }>;
const e3: E3 = true;
interface ET<Actual> {
  toEqualTypeOf: <Expected extends StrictEqual<Actual, Expected> extends true ? unknown : { mismatch: true }>(...m: StrictEqual<Actual, Expected> extends true ? [] : [never]) => true;
}
declare function expectTypeOf<A>(a?: A): ET<A>;
declare const v: readonly unknown[];
expectTypeOf(v).toEqualTypeOf<readonly unknown[]>();
export {};
