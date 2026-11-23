// calling C[M]: its base constraint's signatures (an index signature's function)
export function g<C extends Record<string, () => number>, M extends keyof C>(c: C, m: M) {
  const r = c[m]();
  const s: string = r;
}
export function h<C extends { [k: string]: () => number }, M extends keyof C>(c: C, m: M) {
  const s: string = c[m]();
}
export function k<C extends { a: () => number; b: () => number }, M extends keyof C>(c: C, m: M) {
  const s: string = c[m]();
}
