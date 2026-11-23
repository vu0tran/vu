// A template literal index type on an object that isn't generic but whose values are a type
// parameter: the template literal index signature it matches (execa's fd-specific options,
// Readonly<Partial<Record<'stdout' | `fd${number}` | ..., OptionType>>>[`fd${number}`]).
type K = 'stdout' | 'stderr' | 'all' | `fd${number}` | 'ipc';
type R<O> = Record<K, O>[`fd${number}`];
type P<O> = Partial<Record<K, O>>[`fd${number}`];
type Q<O> = Readonly<Partial<Record<K, O>>>[`fd${number}`];
type S<O> = Record<K, O>['stdout'];
type U<O> = Record<K, O>[`fd${number}` | 'ipc'];
type V<O> = { [k: `fd${number}`]: O, a: O }[`fd${number}`];
function f<O>(r: R<O>, p: P<O>, q: Q<O>, s: S<O>, u: U<O>, v: V<O>) {
  const x: number = r;
  const y: number = p;
  const z: number = q;
  const w: number = s;
  const t: number = u;
  const vv: number = v;
}
export const a: R<boolean> = 1;
export const b: P<boolean> = 1;
// (a generic object stays deferred)
function g<T extends Record<K, string>>(t: T) {
  const x: number = t[`fd${1 as number}`];
}
