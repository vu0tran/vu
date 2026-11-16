// typeof c of a constant is its fresh literal: a discriminant compared with it still matches.
const A = 'a';
const B = 'b';
interface IA { type: typeof A; text: string }
interface IB { type: typeof B; msg: string }
declare const p: IA | IB;
if (p.type === A) { p.text; }
declare const q: IA | IB;
if (q.type === 'a') { q.text; }
interface IA2 { type: typeof A; text: string }
declare const p: IA2;
export const t3: number = p.type;
declare const p2: IA2 | { type: 'b' };
export const t4: number = p2.type;
if (p2.type === 'a') { const z: number = p2; }
