// two instantiations of one conditional type with infer: check types related, extends types alike, branches related
export {};
type A<T> = T extends { x: infer F } ? F : T;
type B<T> = T extends object & { then(f: infer F): any } ? F : T;
function f<T, U extends T>(a: A<U>, b: A<T>, c: B<U>, d: B<T>) {
	const x1: A<T> = a;
	const x3: B<T> = c;
}
