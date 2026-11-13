// iterating an intersection with one iterable member
export {};
const isObj = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
const { isArray } = Array;
function f(value: unknown) {
	if (!isObj(value)) return 1;
	if (isArray(value)) {
		const n: number = value;
		for (const element of value) { const m: number = element; }
	}
	return 0;
}
function g<T>(v: T, w: { a: 1 } & string[]) {
	if (Array.isArray(v)) { for (const e of v) { const m: string = e; } }
	for (const e of w) { const m: number = e; }
}
