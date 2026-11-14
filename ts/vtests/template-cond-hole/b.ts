const a: Record<string, any> = "x";
type C1 = string extends Record<string, any> ? 1 : 0;
const c1: C1 = 1;
const b: Record<string, unknown> = 5;
interface I { a: number }
declare const i: I;
const d: Record<string, any> = i;
const e: Record<string, unknown> = i;
export {};
