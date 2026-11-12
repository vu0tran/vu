type JV = null | string | JO | JA;
type JO = { [key: string]: JV | undefined };
type JA = JV[];
declare const r: JV;
export const q: number = r;
type L = string | L2[];
type L2 = { l: L };
declare const l: L;
export const q2: number = l;
