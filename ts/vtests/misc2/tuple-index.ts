export {};
type T1 = [string, ...number[]];
type T2 = [string, boolean?];
type T3 = readonly [1, 2, ...3[]];
const a: T1[1] = "s";
const b: T1[5] = "s";
const c: T2[1] = "s";
const d: T3[2] = "s";
const e: T3[0] = "s";
