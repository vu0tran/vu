export {};
type R = { headers: { a?: string } };
export const CA = Symbol.for('n8n.consumedAuth');
export const CB = Symbol('x');
function f(req: R) {
	const record = CA in req ? req[CA] : [];
	const b: boolean = record;
	const r2 = CB in req ? req[CB] : 1;
	const b2: boolean = r2;
	const b3: boolean = CA;
}
