// Symbol index signatures from mapped types over symbol (Record<PropertyKey, T>)
export {};
declare const rec: Record<PropertyKey, unknown>;
declare const pk: PropertyKey;
const r5 = rec[pk];
const r6: number = rec[pk];
declare const sy: symbol;
const r7: number = rec[sy];
const lit: Record<PropertyKey, number> = { a: 1 };
interface I { a: number }
declare const i: I;
const fromI: Record<PropertyKey, number> = i;
type RS = Record<symbol, string>;
declare const rs: RS;
const s1: number = rs;
