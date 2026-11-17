export {};
type Expect<T extends true> = T;
type Equal<X, Y> = (<T>() => T extends X ? 1 : 2) extends <T>() => T extends Y ? 1 : 2 ? true : false;
declare function hasKey<T extends PropertyKey>(value: unknown, key: T): value is Record<T, unknown>;
declare function it(n: string, f: () => void): void;
it('a', () => {
  const x: unknown = { a: 3 };
  if (hasKey(x, '0')) {
    let q: typeof x = 1;
    const y: Expect<Equal<typeof x, Record<'0', unknown>>> = true;
    const y2: Equal<typeof x, Record<'0', unknown>> = 1;
  }
});
