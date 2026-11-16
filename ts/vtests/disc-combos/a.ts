// An object whose discriminant is a union of literals relates to a union combination by combination.
type PS = { readonly kind: 'name'; readonly value: string } | { readonly kind: 'package'; readonly value: string } | { readonly kind: 'extends'; readonly value: string };
declare const kind: 'name' | 'package';
export const p: PS = { kind, value: 'x' };
declare function f(s: PS): void;
f({ kind, value: 'x' });
declare const k2: 'name' | 'other';
