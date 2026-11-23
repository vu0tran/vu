// truthiness narrowing of Partial<{...}>[K] and of a conditional type with no computed constraint
type AnyFn = (...args: any) => any;
type ResultMap<F extends Record<string, AnyFn>> = Partial<{ [K in keyof F]: ReturnType<F[K]> }>;
export class Cache<F extends Record<string, AnyFn>> {
  private readonly cache: ResultMap<F> = {};
  public get<K extends keyof F>(name: K): ReturnType<F[K]> {
    if (this.cache[name]) {
      return this.cache[name];
    }
    const z: string = 1;
    throw 1;
  }
}
