// The identity relation (isTypeIdenticalTo) on object types with signatures and on interfaces:
// signaturesIdenticalTo (as many, each compareSignaturesIdentical: parameter counts, rest
// parameters, a rest tuple spread, type parameters' constraints, predicates, return types), what
// expect-type's and xstate's Equals<A, B> decide through two conditional types whose extends
// types are (A & T) | T and (B & T) | T, the check type a generic function type (not deferred).
type Equals<A1, A2> = (<A>() => A extends A2 ? true : false) extends <A>() => A extends A1 ? true : false ? true : false;
type MC = Record<string, any>;
interface Ctx { a: number; b?: string }
interface Ctx2 { a: number; b?: string }
interface Ctx3 { a: number; readonly b?: string }
type F1 = (x: number, y?: string) => void;
type F2 = (x: number, y?: string) => void;
type F3 = (x: number, y: string) => void;
type F4 = (x: number, ...y: string[]) => void;
type G1 = <T>(x: T) => T;
type G2 = <U>(x: U) => U;
type G3 = <T extends string>(x: T) => T;
type P1 = (x: unknown) => x is string;
type P2 = (x: unknown) => x is string;
type P3 = (x: unknown) => boolean;
type O1 = { (x: number): string; (x: string): number };
type O2 = { (x: string): number; (x: number): string };
type C1 = new (x: number) => Ctx;
type C2 = new (x: number) => Ctx2;
type R1 = (...a: [number, string?]) => void;
type R2 = (...a: [number, string]) => void;
type UF = (...args: unknown[]) => unknown;
const e1: Equals<MC, Ctx> = false;
const e2: Equals<Ctx, Ctx2> = true;
const e3: Equals<Ctx, Ctx3> = false;
const e4: Equals<F1, F2> = true;
const e5: Equals<F1, F3> = false;
const e6: Equals<F1, F4> = false;
const e7: Equals<G1, G2> = true;
const e8: Equals<G1, G3> = false;
const e9: Equals<P1, P2> = true;
const e10: Equals<P1, P3> = false;
const e11: Equals<O1, O2> = false;
const e12: Equals<O1, O1> = true;
const e13: Equals<C1, C2> = true;
const e14: Equals<{ f: F1 }, { f: F2 }> = true;
const e15: Equals<{ f: F1 }, { f: F3 }> = false;
const e16: Equals<{ m(x: number): void }, { m: (x: number) => void }> = true;
const r1: Equals<R1, F1> = true;
const r2: Equals<R2, F3> = true;
const r3: Equals<R2, F1> = false;
const r4: Equals<R1, UF> = false;
const r5: Equals<UF, UF> = true;
// the wrong answers, each an error
const w1: Equals<MC, Ctx> = true;
const w2: Equals<Ctx, Ctx2> = false;
const w4: Equals<F1, F2> = false;
const w5: Equals<F1, F3> = true;
const w7: Equals<G1, G2> = false;
const w8: Equals<G1, G3> = true;
const w10: Equals<P1, P3> = true;
const w11: Equals<O1, O2> = true;
const w13: Equals<C1, C2> = false;
const w16: Equals<{ m(x: number): void }, { m: (x: number) => void }> = false;
const q1: Equals<R1, F1> = false;
const q3: Equals<R2, F1> = true;
// (inside a generic: Equals<G, UF> decided false while G is a type parameter, so the outer
// conditional is deferred)
type Useless<F> = Equals<F, UF>;
type Pick1<F> = F extends [infer Fn] ? (Useless<Fn> extends true ? never : Fn) : never;
const p1: Pick1<[() => string]> = () => "x";
const p2: Pick1<[UF]> = () => "x";
function f<G>() {
  const u: Useless<G> = true;
  const v: Useless<G> = false;
  return [u, v];
}
export { e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14, e15, e16, r1, r2, r3, r4, r5, w1, w2, w4, w5, w7, w8, w10, w11, w13, w16, q1, q3, p1, p2, f };
interface I1 { self: I1; n: number }
interface I2 { self: I2; n: number }
interface I3 { self: I3; n: string }
export const h1: Equals<HTMLSpanElement, HTMLElement> = true;
export const h2: Equals<HTMLSpanElement, HTMLElement> = false;
export const h3: Equals<HTMLDivElement, HTMLElement> = false;
export const i1: Equals<I1, I2> = true;
export const i2: Equals<I1, I3> = true;
