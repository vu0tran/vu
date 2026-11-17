export {};
declare const s: Set<string>;
const [only] = s;
const n: number = only;
const [a, ...rest] = s;
const r: number = rest;
declare const m: Map<string, number>;
const [[k, v]] = m;
const kk: number = k;
const vv: string = v;
function* gen() { yield 1; yield "a"; }
const [g1, g2 = true] = gen();
const gg: string = g1;
const gb: number = g2;
