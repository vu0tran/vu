// A method's type parameters inside its body; defaults in a function type's type parameters
class Store {
  m = new Map<string, unknown>();
  get<V>(k: string): V | undefined { return this.m.get(k) as V; }
  all<V>(): V[] { const xs: V[] = []; return xs; }
}
declare const mock: <T, R extends T[] = T[]>(x?: T) => R;
const r1: number[] = mock<number>();
const r2: string = mock<number>();
