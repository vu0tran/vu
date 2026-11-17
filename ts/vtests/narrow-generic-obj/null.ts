export {};
interface Box<T> { v: T }
export function f<T>(target: T, source: Partial<T>, b: Box<T>, u: Box<T> | null): T {
	if (source === null || source === undefined) {
		const n: number = source;
	}
	if (b == null) { const q: number = b; } else { const q: number = b; }
	if (u !== null) { const q: number = u; } else { const q: number = u; }
	if (u === undefined) { const q: number = u; }
	return target;
}
