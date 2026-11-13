// targets indexed by a generic object's key (R["k"]) and generic mapped targets over a type parameter
export {};
interface Reg { _schema: { s: string }; _meta: number; opt?: string }
function f<R extends Reg>(x: { s: string }, y: number, z: string) {
	const a: R["_schema"] = x;
	const b: R["_meta"] = y;
	const d: R["opt"] = z;
	const e: R["_schema"] = y;
}
function g<T extends string>(e: {}, o: { a: true }) {
	const a: { [k in T]: true } = e;
	const b: { [k in T]?: true } = e;
}
