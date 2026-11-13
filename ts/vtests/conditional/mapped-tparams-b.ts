// generic mapped types related to each other; type parameters through constraints that are type parameters
export {};
function f<T, U extends T, V extends U, W extends T | string>(t: T, u: U, v: V, w: W) {
	const a: T = u; const b: T = v; const c: U = t; const d: T = w; const e: T | string = w; const g: V = u;
}
