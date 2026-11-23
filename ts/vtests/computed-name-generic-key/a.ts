// A computed property name of a generic type that is a property key (E extends keyof Ev[C]): a
// string index signature of the value (checkObjectLiteral's hasComputedStringProperty).
type Ev = { a: { x: number; y: string }; b: { z: boolean } };
export function f<C extends keyof Ev, E extends keyof Ev[C]>(c: C, e: E, d: Ev[C][E]) {
  const o = { [e]: d };
  const t: boolean = o.anything;
  return c;
}
export function g<K extends string>(k: K) {
  const o = { [k]: 1, n: 'x' };
  const t: boolean = o.other;
}
