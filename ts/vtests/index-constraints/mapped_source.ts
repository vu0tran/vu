export {};
type F = { template: string; n: number };
function g<K extends string>(fields: Record<K, F>, f2: Record<K, number>, f3: { [P in K]?: F }) {
	for (const [k, e] of Object.entries<F>(fields)) {
		const b: boolean = e;
		const kk: boolean = k;
	}
	Object.entries<F>(f2);
	const a1: { [s: string]: F } = fields;
	const a2: { [s: string]: number } = fields;
	const a3: { x: F } = fields;
	const a4: { x?: F; [s: string]: F } = fields;
	const a5: { [s: string]: F | undefined } = f3;
	const a6: { [s: string]: F } = f3;
	const a7: ArrayLike<F> = fields;
	const a8: {} = fields;
	const a9: object = fields;
}
