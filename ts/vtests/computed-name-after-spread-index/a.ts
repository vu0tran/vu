// Several computed names of one kind after a spread with index signatures: the part's index
// signature united with the spread's (getSpreadType's getUnionIndexInfos).
declare const k: string;
declare const k2: string;
declare const n: number;
declare const h: Record<string, boolean>;
declare const hn: { [i: number]: boolean };
const o1 = { ...h, [k]: 'a', [k2]: 2 };
const t1: boolean = o1.foo;
const o2 = { ...hn, [n]: 'a', [n + 1]: 2 };
const t2: boolean = o2[3];
const o3 = { ...h, [k]: 'a', [k2]: 2, ...h, [k]: null };
const t3: boolean = o3.foo;
