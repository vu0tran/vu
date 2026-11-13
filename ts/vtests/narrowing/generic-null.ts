interface S { id: number; a: string | null; b?: number }
export function f<T extends string | null, K extends keyof S>(x: T, s: S, k: K) {
	if (x !== null) { const b1: boolean = x; }
	if (x != null) { const b2: boolean = x; }
	const v = s[k];
	if (v === null || v === undefined) { throw 1; }
	const b3: boolean = v;
	const b4: NonNullable<S[K]> = v;
	if (v !== undefined) { const b5: boolean = v; }
}
