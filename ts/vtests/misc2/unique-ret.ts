const D = Symbol('d');
const N = Symbol('n');
export type DD = typeof D | typeof N;
interface R { d(): DD; n(): DD }
export function cr(f: () => void): R {
	return { d() { f(); return D; }, n() { return N; } };
}
const g: () => DD = () => D;
let h = () => D;
const b: boolean = h;
const k: DD[] = [D, N];
