export {};
const ROOTS = ['$json', '$p'] as const;
declare function isOneOf<T extends string>(ops: readonly T[], op: unknown): op is T;
declare function isOne2<T>(op: unknown, t: T): op is T;
function f(x: string, y: string | number) {
	if (isOneOf(ROOTS, x)) { const n: boolean = x; }
	if (isOne2(y, 1 as const)) { const n: boolean = y; }
}
