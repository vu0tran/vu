// this as T: a mapped type over the class's keys is related to this (T, or a member of its intersection)
interface F { a: number; getMode?: () => string; zz: string; nope: number }
export class K {
  a = 1; zz = ""; getMode() { return ""; }
  m1() { return this as Pick<F, 'zz'> & { q: number }; }
  m2() { return this as Partial<F> & { q: number }; }
  m5() { return this as { [K in 'zz']?: string } & { q: number }; }
  m6() { return this as { readonly [K in 'zz']: string } & { q: number }; }
  m7() { return this as { [K in 'zz' as `x${K}`]: string } & { q: number }; }
  m9() { return this as Record<string, number> & { q: number }; }
  n1() { return this as { q: number } & { [K in 'getMode']: string }; }
  n2() { return this as { q: number } & { [K in 'getMode']: F[K] & {} }; }
  n3() { return this as { q: number } & { [K in 'getMode']: F[K] }; }
  n4() { return this as { q: number } & { [K in 'zz']: NonNullable<F[K]> }; }
  n5() { return this as { q: number } & { [K in 'nope']: NonNullable<F['a']> }; }
  n6() { return this as { [K in 'getMode']: NonNullable<F[K]> }; }
  n7() { return this as { [K in 'getMode']: unknown }; }
  n8() { return this as { q: number } & { [K in 'getMode']: unknown }; }
  n9() { return this as { q: number } & { [K in 'getMode']: any }; }
  n10() { return this as { q: number } & { [K in 'getMode']: () => number }; }
  p1() { return this as { q: number }; }
  p2() { return this as F; }
}
type WR<Keys extends keyof F> = F & { [K in Keys]: NonNullable<F[K]> };
export class K2 {
  a = 1; zz = ""; getMode() { return ""; }
  m1() { return this as WR<'getMode'>; }
  m2() { return this as WR<'getMode'> & { q: number }; }
}
