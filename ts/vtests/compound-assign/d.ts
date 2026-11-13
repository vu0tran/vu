type P = { [k: string]: number | string };
declare const xs: P[];
const [g = {}] = xs;
export const q: 'z' = g;
declare const ys: { a: number }[];
const [h = { a: 1 }] = ys;
export const q2: 'z' = h;
const [i = { b: 1 }] = ys;
export const q3: 'z' = i;
const { k = {} } = {} as { k?: P };
export const q4: 'z' = k;
function f({ m = {} }: { m?: P }) { const q5: 'z' = m; }
export { f };
