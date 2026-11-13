// destructuring from X | {} (an object literal): its missing properties are undefined
export {};
type O = { a?: boolean; b?: string; c: number };
function f(o?: O, k?: boolean) {
	const { a = false, b, c } = o ?? {};
	const n1: string = a; const n2: number = b; const n3: string = c;
	let { a: x } = o ?? {};
	const n4: string = x;
	const { c: y } = k ? { c: 1 } : {};
	const n5: string = y;
	const { q } = o ?? {};
}
