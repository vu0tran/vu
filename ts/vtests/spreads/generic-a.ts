export {};
const SYM = Symbol('x');
function f<K extends string, T extends object>(r: Record<K, string>, t: T, u: Partial<T>) {
	const a: Record<K, string> & { [SYM]: number } = { ...r, [SYM]: 1 };
	const b: boolean = { ...r, [SYM]: 1 };
	const c: boolean = { ...t, x: 1 };
	const d: boolean = { a: 1, ...t };
	const e: boolean = { a: 1, ...t, x: 1 };
	const g: boolean = { ...r };
	const h: boolean = { ...t, ...u };
	const i: boolean = { ...u, y: "s" };
}
