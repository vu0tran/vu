// inference to a tuple target (readonly too) from a tuple or an array: element by element, not through
// the members (readonly [PropertyKey, T] from [string, string | null] made T null, so Object.fromEntries
// took its any overload); a mutable array to a readonly tuple infers nothing (typesDefinitelyUnrelated)
declare const v: string | null;
declare function g<T>(x: readonly [PropertyKey, T]): T;
export const n1: number = g(['a', v]);
declare const tup: [string, string | null];
export const n5: number = g(tup);
declare const rows: { badgeName: string; personEmail: string | null }[];
const aliases = Object.fromEntries(rows.map((row) => [row.badgeName, row.personEmail]));
export const n: number = aliases;
declare function h<A, B>(x: [A, ...B[]]): [A, B];
declare const t3: [1, 2, 3];
export const n6: number = h(t3);
declare const arr: string[];
declare function k<A, B>(x: readonly [A, B?]): [A, B];
export const n7: number = k(arr);
