// Instantiations of one declaration's signatures are compared pairwise with both erased, their
// type parameters any (signaturesRelatedTo's same-symbol rule): a generic method's
// F[K] return relates whatever F is, and only its other parameters can fail.
type Factory<O> = (n: number) => O[];
type FactoryMap = Record<string, Factory<any>>;
type DLF = { A: Factory<string>; B: Factory<number> };
interface DCache<F extends FactoryMap> {
  get<Key extends keyof F>(name: Key): ReturnType<F[Key]>;
}
declare const c1: DCache<{ A: Factory<string> }>;
const x1: Partial<DCache<DLF>> = c1;
declare const c3: DCache<{ A: Factory<number> }>;
const x3: Partial<DCache<DLF>> = c3;
declare class Cache2<F extends FactoryMap> {
  private readonly registry: F;
  get<Key extends keyof F>(name: Key): ReturnType<F[Key]>;
}
declare const c4: Cache2<{ A: Factory<string> }>;
const x4: Partial<Cache2<DLF>> = c4;
interface DC<F> { get<K extends keyof F>(n: K): F[K] }
interface DE<F> { get<K extends keyof F>(n: K, f: F): F[K] }
declare const a1: DC<{ A: number; B: number }>;
const b1: Partial<DC<{ A: string; B: number }>> = a1;
declare const a3: DE<{ A: number; B: number }>;
const b3: Partial<DE<{ A: string; B: number }>> = a3;
declare const a4: DC<{ A: number }>;
const b4: Partial<DC<{ A: number; B: number }>> = a4;
// (two declarations' methods: not erased, the source's K inferred from the target's)
interface M1 { get<Key extends "A">(name: Key): ReturnType<{ A: Factory<number> }[Key]> }
interface T1 { get<Key extends keyof DLF>(name: Key): ReturnType<DLF[Key]> }
declare const m1: M1;
const y1: T1 = m1;
export {};
