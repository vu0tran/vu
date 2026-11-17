// A type parameter in a conditional type's check type is bivariant (its instantiations relate
// when either check type relates to the other).
type CB = () => void;
type F<B extends boolean> = (onComplete: B extends true ? CB : never) => void;
declare const f1: F<boolean>;
export const f2: F<false> = f1;
export const f3: F<boolean> = null as unknown as F<false>;
declare const g1: (x: CB) => void;
export const g2: (x: never) => void = g1;
export const g3: (x: CB) => void = null as unknown as ((x: never) => void);
declare const h: F<boolean>;
export const hn: number = h;
type FFF<B extends boolean> = (onComplete: B extends true ? CB : never) => void;
type H<B extends boolean> = (onComplete: [B] extends [true] ? CB : never) => void;
export const f3: FF<boolean> = null as unknown as FF<false>;
export const h3: H<true> = null as unknown as H<false>;
type FF2<B extends boolean> = { x: (onComplete: B extends true ? CB : never) => void };
export const f4: FF2<boolean> = null as unknown as FF2<false>;
