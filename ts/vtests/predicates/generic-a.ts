export {};
const ROOTS = ['$json', '$p'] as const;
const isOneOf = <T extends string>(ops: readonly T[], op: unknown): op is T => (ops as readonly unknown[]).includes(op);
interface Id { type: "Identifier"; name: string }
function f(node: Id, param: string | null) {
	if (node.name === param) return 1;
	if (isOneOf(ROOTS, node.name)) {
		const n: boolean = node.name;
		return { kind: 'root', name: node.name };
	}
	const m: boolean = node.name;
	if (node.name === 'undefined') { const q: boolean = node.name; return 2; }
	return null;
}
