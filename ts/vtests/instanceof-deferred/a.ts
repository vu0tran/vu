// x instanceof C where x is a deferred type (ReturnType<C[M]>, T[K]): getNarrowedType with
// checkDerived by its base constraint; the intersection it gives inferred from as its other members
type Fn = (...a: any[]) => unknown;
type Client = { [k: string]: Fn };
declare function call<C extends Client, M extends keyof C>(c: C, m: M): ReturnType<C[M]>;
declare function awaitP<T>(p: Promise<T>): T;
class Base { b = 1 }
class Derived extends Base { d = 2 }

export async function f<C extends Client, M extends keyof C & string>(c: C, m: M) {
  const result = call(c, m);
  if (!(result instanceof Promise)) {
    const s: string = result;
    throw new Error('x');
  }
  const n: number = result;
  const v = awaitP(result);
  v.foo;
  const w = await result;
  const ww: number = w;
}

export function g<T extends { a: Base; b: string }>(j: T['a']) {
  if (j instanceof Derived) {
    const y: number = j;
  } else {
    const z: number = j;
  }
  if (j instanceof Base) {
    const y: number = j;
  } else {
    const z: number = j;
  }
}
