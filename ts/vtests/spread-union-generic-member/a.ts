// a spread of a union with a generic member (a package's useToast: D | undefined, then a conditional
// tuple's element): each member spread, the generic one an intersection part
export {};
type Opts = { message?: string; variant?: 'a' | 'b' };
type Arg<D extends Partial<Opts>> = Omit<Opts, keyof D> & Partial<Pick<Opts, keyof D & keyof Opts>>;
export function use<D extends Partial<Opts>>(defaults?: D) {
  const ref = { current: defaults };
  return (...args: {} extends Arg<D> ? [options?: Arg<D>] : [options: Arg<D>]) => {
    const merged = { ...ref.current, ...args[0] } as Opts;
    const n: number = merged;
  };
}
