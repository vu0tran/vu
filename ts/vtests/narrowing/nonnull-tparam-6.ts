// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
export const f = <T,>(options?: { fallbackValue?: T }): T | 1 => {
	if (options?.fallbackValue !== undefined) {
		if (options.fallbackValue instanceof Function) {
			const n: number = options.fallbackValue;
			return options.fallbackValue();
		}
		const m: number = options.fallbackValue;
		return options.fallbackValue;
	}
	return 1;
};
