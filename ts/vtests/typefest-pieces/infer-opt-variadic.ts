type P<T> = T extends readonly [(infer F)?, ...infer R] ? [F, R] : 'no';
const a: 5 = null as unknown as P<[true, false]>;
const b: 5 = null as unknown as P<[]>;
const c: 5 = null as unknown as P<[1?, 2?]>;
const d: 5 = null as unknown as P<string[]>;
type K<T> = keyof T & `${number}`;
const e: 5 = null as unknown as K<[true, false]>;
export {};
