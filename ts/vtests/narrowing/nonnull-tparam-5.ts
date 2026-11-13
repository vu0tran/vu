// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
type O<T> = { fallbackValue?: T };
export const f = <T,>(options?: O<T>): T | 1 => {
	if (options?.fallbackValue !== undefined) {
		const n: number = options.fallbackValue;
	}
	return 1;
};
export const g = (options?: O<string>): 1 => {
	if (options?.fallbackValue !== undefined) {
		const n: number = options.fallbackValue;
	}
	return 1;
};
