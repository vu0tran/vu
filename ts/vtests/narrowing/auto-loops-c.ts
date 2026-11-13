// variables without a type (let x;) through loops, for-of over them, for-in keys indexing arrays
export {};
interface IC { node: string; index: number }
declare const m: { [k: string]: (IC[] | null)[] };
function f() {
	let ci;
	for (const k in m) {
		for (const i in m[k]) {
			for (ci of m[k][i] ?? []) {
				const n: string = ci.index;
			}
		}
	}
	const q: number = ci;
	let d;
	for (d of [1, 2]) { const s: string = d; }
	const r: string = d;
}
