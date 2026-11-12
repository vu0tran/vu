type JV = null | string | number | boolean | JO | JA;
type JO = { [key: string]: JV | undefined };
type JA = JV[];
declare const result: JV;
export function g1() { if (result === null) return; const x: number = result; return x; }
export function g2() { if (result === null || Array.isArray(result)) return; const x: number = result; return x; }
export function g3() { if (Array.isArray(result)) return; const x: number = result; return x; }
export function g4() { if (typeof result !== 'object') return; const x: number = result; return x; }
