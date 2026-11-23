// An element access by a union of keys with a template literal type in it: each key's type.
type Kind = 'upside' | 'source' | `document:${string}`;
declare const panels: Record<Kind, number> | null;
declare const k: Kind;
const v: boolean = panels?.[k]!;
declare const o: { a: string; [x: string]: string };
declare const k2: 'a' | `b${string}`;
const w: boolean = o[k2];
declare const t: { a: number; [x: `b${string}`]: number };
const u: boolean = t[k2];
// (a value type that may mention type variables, an interface with defaults: the template literal
// index signature the key fits)
type C<P> = (props: P) => El | null;
interface El<P = any, T extends string | C<any> = string | C<any>> { type: T; props: P }
declare const p1: Record<Kind, El>;
declare const dk: `document:${string}`;
const v1: boolean = p1[dk];
const v2: boolean = p1[k];
