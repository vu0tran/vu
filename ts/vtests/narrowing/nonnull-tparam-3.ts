// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
function f<T>(x: T, y: T | undefined, d: number) {
	if (x !== undefined) { const a: T = x; const b: T | undefined = x; const c: {} | null = x; const e: {} = x; }
	if (y != null) { const a: T = y; const b: {} = y; const s: string = String(y); }
	if (y !== undefined) { return y; }
	const z = y ?? d;
	const n: string = z;
	if (y) { const q: T = y; }
	return x;
}
function g<T>(arr: (T | undefined)[]) {
	const out: T[] = [];
	for (const a of arr) { if (a !== undefined) out.push(a); }
	return out;
}
function h<T>(v: T | null) {
	if (v === null) return;
	const n: number = v;
	const m: T = v;
}
function k<T>(v: T | undefined, cb: (t: T) => void) {
	if (v !== undefined) cb(v);
	if (v) cb(v);
}
