// typeof a.b<T>: an instantiation expression of a qualified name
declare namespace ns {
  function fn<T extends (...a: any[]) => any>(impl?: T): { mock: T; calls: Parameters<T>[] };
  function id<T>(x: T): T;
  function id<T, U>(x: T, y: U): [T, U];
  const inner: { make<K extends string>(k: K): K };
}
type M1 = ReturnType<typeof ns.fn<(a: number) => string>>;
const m1: number = null as unknown as M1;
type M2 = typeof ns.id<string>;
const m2: number = null as unknown as M2;
type M3 = typeof ns.inner.make<"a">;
const m3: number = null as unknown as M3;
export {};
