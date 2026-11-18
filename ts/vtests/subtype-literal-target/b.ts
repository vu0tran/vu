declare const d: { a: 1 };
declare const e: { a: 1; b: 2 };
declare const f: { a: 1; b?: 2 };
declare const g: { a: 1; b: undefined };
const x1 = [d, {}]; export const q1: 'z' = x1;
const x2 = [e, { a: 1 as const }]; export const q2: 'z' = x2;
const x3 = [f, { a: 1 as const }]; export const q3: 'z' = x3;
const x4 = [g, { a: 1 as const }]; export const q4: 'z' = x4;
const x6 = [e, d]; export const q6: 'z' = x6;
