// a deprecated property read through a mapped type (Pick, Partial, Readonly): the source's comment
interface S {
  /** @deprecated Use {@link b} instead. */
  a: (x: string) => void;
  b(): void;
  /** @deprecated old */
  c: number;
}
type P = Pick<S, 'a' | 'b' | 'c'>;
declare const p: P;
declare const q: Partial<S>;
declare const r: Readonly<S>;
p.a('x');
export const n = p.c;
q.a?.('y');
r.a('z');
// an object literal's key in a union context: the union's property, none when a member has neither
// it nor an index signature (zod's refine(fn, string | params))
declare function refine(p?: string | Partial<S>): void;
declare function opt(p?: Partial<S>): void;
refine({ c: 1 });
opt({ c: 1 });
