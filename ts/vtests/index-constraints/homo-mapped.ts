export interface DH { n: string }
export function def<T extends Record<string, { n: string }>>(evs: T) {
	const r = evs as unknown as { readonly [K in keyof T]: T[K] & DH & { v: 1 } };
	const x: Record<string, DH> = r;
	const z: { [k: string]: unknown } = r;
	return r;
}
