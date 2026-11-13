// 'name' in x on intersections (Record<...> after in checks, A & B)
export {};
const f = (expr: unknown): boolean => {
	if (typeof expr !== 'object' || expr === null || !('type' in expr) || expr.type !== 'MemberExpression' || !('property' in expr) || !('object' in expr)) {
		return false;
	}
	const property = expr.property;
	const n: number = expr;
	const t: number = expr.type;
	return true;
};
const g = (expr: unknown): boolean => {
	if (typeof expr !== 'object' || expr === null || !('type' in expr)) return false;
	const n: number = expr;
	if (expr.type !== 'M') return false;
	const m: number = expr;
	const t: number = expr.type;
	return true;
};
type A = { a: 1 }; type B = { b: 2 }; type C = { c: 3 };
function f3(x: (A & B) | C, y: A & B, z: (A & { o?: 1 }) | C) {
	if ('a' in x) { const n: number = x; } else { const n: number = x; }
	if ('b' in y) { const n: number = y; } else { const n: number = y; }
	if ('q' in y) { const n: number = y; } else { const n: number = y; }
	if ('o' in z) { const n: number = z; } else { const n: number = z; }
}
