// A generic mapped type has the members its keys' lower bound gives: not empty when it has a key.
type AnyFn = (...args: any) => any;
type ResultMap<FuncMap extends Record<string, AnyFn>> = Partial<{
  [Key in keyof FuncMap]: ReturnType<FuncMap[Key]>;
}>;
export class Cache<F extends Record<string, AnyFn>> {
  cache: ResultMap<F> = {};
}
type Opts = { a: string; b?: number };
type Picked<D extends Partial<Opts>> = Pick<Opts, Extract<keyof D, keyof Opts>>;
export function g<D extends Partial<Opts>>(x: Picked<D>): Picked<D> {
  return x;
}
type Ev = { meta: 1; raw: 2; x: 3 };
type Rest<E extends Ev> = Omit<E, 'meta' | 'raw'>;
export function h<E extends Ev>(x: Rest<E>): Rest<E> {
  return x;
}
type Loaders<T extends Record<string, unknown>> = Partial<Record<keyof T, number>>;
export function k<T extends Record<string, unknown>>(x: Loaders<T>): Loaders<T> {
  return x;
}
