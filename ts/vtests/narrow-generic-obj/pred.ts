export {};
declare function isP(value: unknown): value is Record<string, unknown>;
export function f1<T>(target: T) {
	if (!isP(target)) return;
	const r: number = { ...target };
}
export function f2<T>(target: T) {
	if (target === null || target === undefined) return;
	const r: number = target;
	if (!isP(target)) return;
	const r2: number = target;
}
