// spreads of unions with empty members after written properties; spreads of arrays
export {};
declare const arr: string[];
const r = { a: 1, ...arr };
const n: number = r.length;
const m: number = r.a;
const f: string = r.join(",");
const x: { a: number; length: number } = r;
