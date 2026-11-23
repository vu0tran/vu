// A homomorphic mapped type over a tuple with a rest element before others (Promise.all of
// [...xs, y]): the elements before the rest by their keys, the rest one and those after it by
// the mapped type over an array of the element (instantiateMappedTupleType), not by keys "0", "1".
declare const xs: Promise<number>[];
declare const y: Promise<string>;
declare const z: Promise<boolean>;
export async function f() {
  const r = await Promise.all([...xs, y]);
  const n1: number = r;
  const r2 = await Promise.allSettled([...xs, y, z]);
  const n2: number = r2[0];
  type M<T extends readonly unknown[]> = { -readonly [P in keyof T]: Awaited<T[P]> };
  const r3: M<[...Promise<number>[], Promise<string>]> = null!;
  const n3: number = r3;
  const r4: M<[Promise<boolean>, ...Promise<number>[], Promise<string>]> = null!;
  const n4: number = r4;
  type O<T extends readonly unknown[]> = { [P in keyof T]?: T[P] };
  const r5: O<[number, ...string[], boolean]> = [1];
  const n5: number = r5;
}
type P1 = Partial<string[]>;
const p1: number = null! as P1;
type R1 = Required<[number?, ...string[]]>;
const q1: number = null! as R1;
type O2<T extends readonly unknown[]> = { [P in keyof T]?: T[P] };
const o2: number = null! as O2<[...string[], number]>;
