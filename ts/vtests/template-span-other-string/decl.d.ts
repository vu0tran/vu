export type J<A, B> = `${A & string}.${B extends string ? B : unknown & {}}`;
export type T1<X> = `p.${X}`;
export type U1 = T1<unknown>;
export type U2 = T1<{ a: 1 }>;
export type U3 = T1<'a' | object>;
export type U4 = T1<never>;
export type U5 = `${'a' | 'b'}-${T1<string[]>}`;
export type U6 = J<'k', 3>;
