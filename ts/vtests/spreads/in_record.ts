export const f = (value: unknown) => {
	if (value === null || value === undefined || typeof value !== 'object') return null;
	if (!('aa' in value) && !('bb' in value)) return null;
	const v0: boolean = value;
	const n = 'aa' in value ? value : { ...value, aa: 1 };
	const b: boolean = n;
	const m = { ...value, cc: 1 };
	const b2: boolean = m;
	return n;
};
