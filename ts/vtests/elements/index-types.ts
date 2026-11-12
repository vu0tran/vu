// Element access: an index of type any, string or number without an index signature (TS7053),
// of unknown (TS18046), never, a union of string and number keys; ambient declarations used
// before them
export {};
declare const a: any;
interface I { x: number }
declare const i: I;
const r1 = i[a];
const r2 = ({})[a];
declare const u: unknown;
const r3 = u[0];
declare const nv: never;
const r4 = nv[0];
declare const rec: Record<PropertyKey, unknown>;
declare const pk: PropertyKey;
const r5 = 1;
const r6: number = rec[sn];
declare const sn: string | number;
const r7: number = rec[sn];
declare const mix: Record<string, number> | { a: number };
declare const s: string;
const r8 = mix[s];
