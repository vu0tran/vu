// optional chains on this; element access and spreads on intersections
export {};
class P {
	data?: { run?: { names: string[] } };
	m() {
		const that = this;
		if (!that?.data?.run?.names.includes("a")) { return 1; }
		const n: number = that.data.run.names;
		const q: number = that;
		return 2;
	}
}
function g<T extends { a?: { b: number } }>(x: T) {
	if (x?.a) { const n: string = x.a.b; }
}
type D2 = { [key: string]: string | number | D2 | undefined };
type K = D2 & { $tool?: { name: string }; $n: number };
declare const k2: K;
const ax: boolean = k2.$tool;
const bx: boolean = k2['$tool'];
const cx: boolean = k2.$n;
const dx: boolean = k2.other;
const ex: boolean = k2['other'];
const fx: boolean = k2['$n'];
type Q = { a: 1 } & { b: 2 };
declare const q: Q;
const gx: boolean = q['a'];
type E = { a: number; b?: string };
declare const o: object;
const s = { ...o, q: 1 }; const s1: number = s;
