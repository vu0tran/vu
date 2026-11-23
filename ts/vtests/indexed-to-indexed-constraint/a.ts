// S[K] to T[J], S not related to T: only through T[J]'s constraint for writing (T's and J's base
// constraints' access, the properties intersected), never the source's own constraint
// (structuredTypeRelatedTo skips it when both are indexed accesses).
type Factory<O> = (n: number) => O[];
type DLF = { A: Factory<string>; B: Factory<number> };
type NN = { A: Factory<number>; B: Factory<number> };
type Same = { A: Factory<number>; B: Factory<number>; C: string };
function f<Key extends keyof DLF>(b: NN[Key], d: DLF[Key], s: Same[Key]) {
  const y: DLF[Key] = b;
  const z: NN[Key] = d;
  const w: NN[Key] = s;
}
// (an object of one property for both keys: the target's writing constraint is the two
// properties intersected, which the source's constraint can't reach)
function g<K extends "a" | "b">(x: { a: number; b: number; c: 1 }[K], y: { a: 1; b: 1 }[K]) {
  const t: { a: number; b: number }[K] = x;
  const u: { a: number; b: number }[K] = y;
  const v: { a: 1; b: 2 }[K] = y;
}
// (a method's type parameter seen through its interface's instantiation: its constraint
// instantiated, keyof { A: string; B: number } is "A" | "B", and the writing constraint never)
interface DC<F> { get<K extends keyof F>(n: K): F[K] }
interface DD<F> { get<K extends keyof F>(n: K): F[K] }
declare const a1: DC<{ A: number; B: number }>;
const b2: Partial<DD<{ A: string; B: number }>> = a1;
declare const a4: DC<{ A: number }>;
const b5: Partial<DD<{ A: number; B: number }>> = a4;
const b6: Partial<DD<{ A: number }>> = a1;
export {};
