// An assertion call through an intersection's property that one member has (assert/strict's ok).
declare namespace A {
	function ok(v: unknown, m?: string): asserts v;
	function eq(a: unknown, b: unknown): void;
	const strict: Omit<typeof A, "ok" | "strict"> & { ok: typeof ok };
}
declare const x: string | undefined;
A.strict.ok(x);
export const n: string = x;
declare const y: string | undefined;
A.strict.eq(y, 1);
export const m: string = y;
