declare const m: RegExpMatchArray;
const [whole, a, b = 1] = m;
const s1: number = whole;
const s2: number = a;
const s3: boolean = b;
declare const e: RegExpExecArray | null;
if (e) { const [x, y] = e; const z: number = x; const w: number = y; }
interface Pair extends Array<number | string | undefined> { 0: number; 1?: string }
declare const p: Pair;
const [p0, p1, p2] = p;
const t0: string = p0; const t1: boolean = p1; const t2: string = p2;
function f([q, r]: RegExpMatchArray) { const u: number = q; const v: number = r; }
export {};
