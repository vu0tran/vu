// an aliased intersection instantiated over a union, distributed into a union: the union keeps the
// alias (vitest's ReturnType<typeof vi.fn>, Mock<Constructable | Procedure>)
type Z<T> = { a: T } & (T extends string ? { s: 1 } : { n: 1 });
declare function fz<T extends string | number>(): Z<T>;
const w2: ReturnType<typeof fz> = 1;
interface MI<T> { m: T }
type M2<T extends string | number = string> = MI<T> & (T extends string ? { (): 1 } : { (): 2 });
declare function fn<T extends string | number = string>(impl?: T): M2<T>;
const x: ReturnType<typeof fn> = 1;
