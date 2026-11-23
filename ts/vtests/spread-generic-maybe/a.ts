// a spread of T | undefined, T a conditional or an indexed access: its constraint's properties,
// all optional (getAnonymousPartialType); an element of a tuple union some member lacks: undefined
type Step = 'A' | 'B';
type Data<N extends Step> = N extends 'A' ? { a: number } : { b: string };
export const mk = <N extends Step>(name: N, ...data: keyof Data<N> extends never ? [] : [data: Data<N>]) => {
  const q = { name, ...data[0] };
  const r: number = q;
  const e: number = data[0];
  return q;
};
export function idx<T extends { x?: { k: number } }>(t: T) {
  const o = { ...t['x'] };
  const p: string = o;
  return o;
}
declare const u: [] | [number];
const u0: string = u[0];
declare const v: [];
const v0 = v[0];
