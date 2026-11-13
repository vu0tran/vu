// a constraint union written with an intersection: narrowing keeps the written form; Array.isArray on T & object
export {};
type P = string | null;
function g3<T extends ((object | Date) & { toJSON?: () => string }) | P>(s: T) {
	const m: number = s;
	if (typeof s === 'object') { const n: number = s; }
	if (typeof s !== 'string') { const n: number = s; }
	let x: ((object | Date) & { toJSON?: () => string }) | P = null as any;
	if (typeof x !== 'string') { const n: number = x; }
	if (x !== null) { const n: number = x; }
}

function f1<T extends ((object | Date) & { toJSON?: () => string }) | P>(s: T) {
	if (typeof s !== 'object' || s === null) return;
	const a: number = s;
	if (typeof s.toJSON === 'function') return;
	const b: number = s;
	if (Array.isArray(s)) { const c: number = s; return; }
	const d: number = s;
	for (const i in s) { const e: number = i; }
}
function f2<T>(s: T) {
	if (typeof s !== 'object' || s === null) return;
	if (Array.isArray(s)) { const c: number = s; return; }
	const d: number = s;
	for (const i in s) { const e: number = i; }
}

function g5<T extends ((object | Date) & { toJSON?: () => string }) | P>(s: T) {
	if (typeof s === 'object' && s && typeof s.toJSON === 'function') { }
	if (typeof s === 'object' && s) { s.toJSON; }
	if (s && typeof s === 'object') { s.toJSON; }
}
function h5<T>(s: T): T {
	if (Array.isArray(s)) { return [] as T; }
	return s;
}
