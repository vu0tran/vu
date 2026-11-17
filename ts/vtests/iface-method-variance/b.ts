export {};
interface M<T> { m(a: T): void }
interface N<T> { m(a: T): void; g(): T }
declare function f<T extends string>(a: M<string>, b: N<string>): void;
function g<T extends string>(a: M<T>, b: N<T>, c: M<string>, d: N<string>) {
	const x: M<string> = a;
	const y: M<T> = c;
	const z: N<string> = b;
	const w: N<T> = d;
}
