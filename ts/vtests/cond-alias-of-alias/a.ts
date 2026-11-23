// A conditional alias referred to as another alias's whole body (type SF<T> = Exclude<T, Error>) keeps its own name; a property missing from a conditional receiver names it.
type C1<T> = T extends Error ? never : T;
type C2<T> = C1<T>;
type SF<T> = Exclude<T, Error>;
function f<L>(a: C2<L>, c: SF<L>) { const x: number = a; const z: number = c; a.zz; c.zz; }
type Cond0<T> = T extends string ? { s: T } : { o: number };
function f2<L, Q extends { id: string }>(a: Exclude<L, Error>, b: Exclude<Q, Error>, c: Cond0<L>) {
  a.addressId;
  b.id;
  b.nope;
}
