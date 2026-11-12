type JV = null | string | JA;
type JA = JV[];
declare const r: JV;
export const q: number = r;
declare const a: JA;
export const q2: number = a;
