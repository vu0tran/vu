export {};
export function f2<T>(target: T, u: unknown) {
	const r4: Record<string, unknown> = null! as NonNullable<T>;
	if (target !== null) {
	  const r5: Record<string, unknown> = target;
	}
	if (u !== null && u !== undefined) {
	  const r6: Record<string, unknown> = u;
	}
}
