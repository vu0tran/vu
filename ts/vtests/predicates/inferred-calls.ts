// calls of functions with inferred predicates narrow their arguments
export {};
const f5 = (v: number | string) => typeof v === "number";
declare const a: number | string | boolean;
declare const b: number | string;
if (f5(b)) { const n: string = b; } else { const n: number = b; }
function isD(x: Date | string) { return x instanceof Date; }
declare const d: Date | string | undefined;
if (d !== undefined && isD(d)) { const n: number = d; } else { const m: number = d; }
const isDef = (x: string | undefined) => x !== undefined;
declare const q: string | undefined;
if (isDef(q)) { const n: number = q; }
const g = [1, "a", undefined].filter(isDef as any);
