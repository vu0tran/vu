let a: string | number = 1;
let b: string;
declare const s: { a: string; b: number };
({ a, b } = s);
const x: null = a;
let c: 'x' | 'y' = 'x';
({ c } = { c: 'y' });
const y: null = c;
({ c } = { c: 'z' });
let d: number[] = [];
({ d } = { d: [] });
({ a } = { a: true });
class K { readonly r = 1; }
const kk = new K();
({ r: kk.r } = { r: 2 });
export {};
