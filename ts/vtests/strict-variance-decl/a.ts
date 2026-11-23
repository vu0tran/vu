// a namespace's function declaration compares its parameters strictly (strictVariance): the
// conditional's subtype reduction keeps the supertype
declare namespace A { function Root<P>(props: { open: boolean; payload?: P }): any; }
declare namespace B { function Root<P = unknown>(props: { open: boolean; payload?: P; swipe?: string }): any; }
declare namespace C { function Root(props: { open: boolean }): any; }
declare namespace D { function Root(props: { open: boolean; swipe?: string }): any; }
declare const m: boolean;
const S = m ? A : B;
const n: number = S;
const T = m ? C : D;
const n2: number = T;
const U = m ? D : C;
const n3: number = U;
S.Root({ open: true, payload: 3, swipe: "s" });
S.Root({ open: 1 });
// a function expression and an arrow too; a method's parameters stay bivariant
interface X { open: boolean }
interface Y { open: boolean; swipe?: string }
const fe = function (p: X) {};
const ar = (p: Y) => {};
const v1 = m ? fe : ar;
const n4: number = v1;
declare const o1: { f(p: X): void }; declare const o2: { f(p: Y): void };
const v2 = m ? o1 : o2;
const n5: number = v2;
// two generic signatures, one default unknown, the other none: identical type parameters
declare const g1: <P>(props: { a: P }) => P;
declare const g2: <P = unknown>(props: { a: P; b?: string }) => P;
declare const gu: typeof g1 | typeof g2;
const r: string = gu({ a: 1, b: "x" });
export {};
