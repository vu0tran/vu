declare const rec: Record<string, number>;
declare const k: string;
const { a, ...r } = rec;
const x1: string = r;
const { [k]: v, ...r2 } = rec;
const x2: string = v;
const x3: string = r2;
declare const mixed: { [x: string]: number | string; p: string; q: number };
const { [k]: v2, ...r3 } = mixed;
const x4: boolean = v2;
const x5: boolean = r3;
const { ["p"]: v3, ...r4 } = mixed;
const x6: boolean = v3;
const x7: boolean = r4;
function f<T>(record: Record<string, T>, o: string, n: string): Record<string, T> {
  const { [o]: value, ...rest } = record;
  return { ...rest, [n]: value };
}
export {};
declare const ri: { [x: string]: number; [n: number]: 1 };
declare const kn: number;
const s1 = { ...ri, [k]: "a" };
const t1: boolean = s1;
const s2 = { ...ri, [kn]: 2 };
const t2: boolean = s2;
const s3 = { ...rec, [k]: 1 };
const t3: string = s3;
