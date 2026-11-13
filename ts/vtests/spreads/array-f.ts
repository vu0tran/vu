// spreading arrays into object literals: Array's members, related to arrays
export {};
declare const arr: number[];
const r = { ...arr };
const t: number[] = r;
const u: readonly number[] = r;
