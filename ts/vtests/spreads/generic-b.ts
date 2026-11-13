export {};
function f<T extends { a: number; b?: string }, U>(t: T, u: U, k: keyof T) {
	const x1 = { ...t, c: 1 };
	const n1: number = x1.a;
	const n2: string = x1.c;
	const x2: T = { ...t };
	const x3: T & { c: number } = { ...t, c: 1 };
	const x4: T = { ...t, c: 1 };
	const x5 = { a: 1, ...t };
	const x6 = { z: 1, ...t };
	const b6: boolean = x6;
	const x7 = { ...u, ...t, q: [1] };
	const b7: boolean = x7;
	const x8 = { ...t, ...{ m: 1 }, n: "s" };
	const b8: boolean = x8;
	return { ...t, extra: true };
}
const r = f({ a: 1 }, 2, "a");
const br: boolean = r;
