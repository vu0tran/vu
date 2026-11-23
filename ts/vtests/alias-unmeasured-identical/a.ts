// two copies of one instantiation of an alias whose variance isn't measured (Omit, over keyof):
// related by their identical type arguments (drizzle's .where() result, inferred through a
// generic call, checked its select's object literal twice); different arguments still compare
class B<T> { constructor(public t: T) {} self(): Omit<B<T>, 'self'> { return this; } map<U>(f: (t: T) => U): B<U> { return new B(f(this.t)); } }
declare function g<T>(v: T): T;
declare function sel<S extends object>(s: S): B<S>;
export const a: Omit<B<{ v: string }>, 'self'> = g(sel({ v: 'x' }).self());
export const c: Omit<B<{ v: string | number }>, 'self'> = sel({ v: 'x' }).self();
export const d: number = g(sel({ v: 'x' }).self());
