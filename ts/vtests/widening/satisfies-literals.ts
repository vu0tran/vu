type Opt = { mode: 'a' | 'b'; n: number; inner: { k: 'x' | 'y' } };
const o = { mode: 'a', n: 1, inner: { k: 'x' } } satisfies Opt;
export const q: 'z' = o;
const o2: Opt = { mode: 'a', n: 1, inner: { k: 'x' } };
export const q2: 'z' = o2.mode;
let o3 = { mode: 'a' } satisfies { mode: 'a' | 'b' };
export const q4: 'z' = o3;
