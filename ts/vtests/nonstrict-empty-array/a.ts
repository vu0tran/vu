// [] with strictNullChecks off: undefined[] (undefinedWideningType), any[] once widened and as a
// method's object in a call ([].concat), in inferred return types
declare const tuples: [number, string][];
declare const id: number;
export const a = [].concat(tuples, [[id, 'x']]);
export const b: number = [].concat(tuples);
const e = [];
export const f: number = e;
export const g: string = [null];
function h() { return []; }
export const i: number = h();
function j() { return null; }
export const k: number = j();
function l(x: boolean) { if (x) return [null]; return [1]; }
export const m: string = l(true);
export const o: string = [].length;
