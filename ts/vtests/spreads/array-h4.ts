// spreading arrays into object literals: Array's members, related to arrays
export {};
interface P { [key: string]: number }
declare const arr: P[];
const r = { __rl: true, ...arr };
const t1: { [n: number]: P } = r;
const t2: { length: number } = r;
const t3: Pick<P[], "push" | "pop" | "sort" | "concat" | "splice"> = r;
const t5: Pick<P[], "map" | "filter" | "every" | "some" | "reduce" | "flat" | "flatMap" | "find" | "keys"> = r;
