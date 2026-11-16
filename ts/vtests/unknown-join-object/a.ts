// object beside the {} of narrowing unknown: the join is unknown again.
export const f = (value: unknown): unknown[] => {
	if (typeof value === 'object' && Array.isArray(value)) {
		return value;
	}
	const n: number = value;
	return [String(value)];
};
