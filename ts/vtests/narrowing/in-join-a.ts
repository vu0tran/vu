export {};
interface Lit { type: "Literal"; value: string | boolean | null | number | RegExp | BigInt }
function p(node: Lit) {
	if ('regex' in node && node.regex) return null;
	const n1: boolean = node;
	if ('bigint' in node && node.bigint) return null;
	const n2: boolean = node;
	const value = node.value;
	const v: boolean = value;
	return value;
}
