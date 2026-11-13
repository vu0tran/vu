export const omit = <T extends object, K extends keyof T>(obj: T, ...keys: K[]): Omit<T, K> =>
	Object.keys(obj).reduce((acc: Record<string, unknown>, key) => {
		if (!keys.includes(key as K)) {
			acc[key] = obj[key as K];
		}

		return acc;
	}, {}) as Omit<T, K>;
export const z: 'z' = omit({ a: 1, b: '' }, 'a');
export function g<T extends object>(o: Omit<T, 'x'>): Record<string, unknown> { return o; }
