// generic mapped types related to each other; type parameters through constraints that are type parameters
export {};
type M<T extends string, V> = { [k in T]: V };
type O<T extends string, V> = { [k in T]?: V };
function f<T extends string, U extends T>(a: M<T, true>, b: M<T, boolean>, c: O<T, true>, d: M<U, true>) {
	const x1: M<T, boolean> = a;
	const x2: M<T, true> = b;
	const x3: O<T, true> = a;
	const x4: M<T, true> = c;
	const x5: M<U, true> = a;
	const x6: M<T, true> = d;
}
