// Spreads with index signatures (kept into an empty literal, else only those both sides have),
// interface methods spread as methods
export {};
declare const r: Record<string, number>;
declare const r2: Record<string, string>;
const a = { ...r };
const na: boolean = a;
const b = { ...r, x: 's' };
const nb: boolean = b;
const c2 = { x: 's', ...r };
const nc: boolean = c2;
const d = { ...r, ...r2 };
const nd: boolean = d;
declare const u: Record<string, number> | undefined;
const e = { ...u };
const ne: boolean = e;
interface I { a: number; m(): void; [k: string]: unknown }
declare const i: I;
const f = { ...i };
const nf: boolean = f;
