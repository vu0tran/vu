export {};
declare function isP(value: unknown): value is Record<string, unknown>;
export function f<T>(target: T, source: Partial<T>): T {
	if (source === null || source === undefined) {
		return isP(target) ? { ...target } : target;
	}
	if (target === null || target === undefined) {
		return source as T;
	}
	if (!isP(target) || !isP(source)) {
		return source as T;
	}
	const result: number = { ...target };
	return result as T;
}
