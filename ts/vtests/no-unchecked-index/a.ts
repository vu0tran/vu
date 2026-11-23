declare const arr: number[];
declare const rec: Record<string, string>;
declare const tup: [number, string];
declare const rest: [number, ...string[]];
declare const i: number;
declare const k: string;
export const a1: number = arr[0];
export const a2: number = arr[i];
export const a3: string = rec[k];
export const a4: string = rec.foo;
export const a5: number = tup[0];
export const a6: string = rest[1];
export const a7: number = rest[0];
arr[0] = 1;
arr[i] += 1;
arr[i]++;
rec.x = "s";
rec[k] = "t";
const [d1, d2] = arr;
export const d3: number = d1;
const { foo } = rec;
export const d4: string = foo;
const [t1, t2] = tup;
export const d5: number = t1;
if (arr[0] !== undefined) { const n0: number = arr[0]; }
const v = arr[i];
if (v) { const n1: number = v; }
for (const x of arr) { const n2: number = x; }
for (const kk in rec) { const s1: string = rec[kk]; }
export const m1 = arr.map((x) => x + 1);
declare const nested: number[][];
export const nn: number = nested[0][0];
export const opt: number | undefined = nested[0]?.[0];
interface Dict { [key: string]: number; known: number }
declare const dict: Dict;
export const kn: number = dict.known;
export const un: number = dict.other;
export { d2, t2 };
declare let mu: number | undefined;
mu++;
export const neg = -mu;
