// Computed names of string or number type before a spread with index signatures: the literal's own
// index signatures, united with the spread's where both have one (getSpreadType).
declare const k: string;
declare const n: number;
declare const h: Record<string, boolean>;
declare const hn: { [i: number]: boolean; x: 1 };
const o1 = { [k]: 'a', z: 2, ...h };
const t1: boolean = o1.foo;
const o2 = { [n]: 'a', ...hn };
const t2: boolean = o2[3];
const o3 = { [k]: 'a', ...hn };
const t3: boolean = o3.x;
const o4 = { [k]: 'a', ...(h as Record<string, boolean> | undefined) };
const t4: boolean = o4.y;
