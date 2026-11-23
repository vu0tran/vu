// A call among an overloaded call's arguments is resolved once, in the first candidate's context
// (tsc caches its signature): the callback's array is the tuple that context gave it, though
// the second overload is the one chosen, so no-unsafe-return sees no any[].
declare const rows: any[];
export const byId = Object.fromEntries(rows.map((d) => [d.id, d.name]));
declare function fe<T = any>(entries: Iterable<readonly [PropertyKey, T]>): { [k: string]: T };
declare function fe(entries: Iterable<readonly any[]>): any;
export const b = fe(rows.map((d) => [d.id, d.name]));
// one signature: the array is any[]
declare function one(entries: Iterable<readonly any[]>): any;
export const c = one(rows.map((d) => [d.id, d.name]));
export const d = rows.map((r) => [r.id]);
