// keyof an unresolved name indexing a string index signature: its symbol part reports TS2538
import { SD } from './missing2';
const map: { [key in keyof SD]: (x?: number) => string } = {};
export const f = (key: keyof SD) => {
  const fn = map[key];
  const n: number = fn;
  return fn;
};
declare const k2: string | number | symbol;
declare const o2: { [x: string]: number };
const v2: boolean = o2[k2];
type Sym = { [x: string]: string }[symbol];
const s1: number = null as unknown as Sym;
const s2: Sym = 'x';
