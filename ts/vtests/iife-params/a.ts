export const a = ((res) => res.length)(String(1));
export function f(x: number) { return ((res) => res.length)(String(x)); }
export const g = (x: number) => ((res) => res.length)(String(x));
declare function red2(f: (a: string[], b: number) => string[]): void;
red2((errs) => { const q = ((res) => errs)('a'); return q; });
export const h = ((x, y) => { const n: number = x; return y; })('s');
export const k = ((x) => x)(nope);
export const l = (function (a, b = 2) { const z: string = b; return a; })(1);
