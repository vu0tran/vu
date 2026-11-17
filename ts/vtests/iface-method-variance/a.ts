export {};
type AnyFunction = (...args: any) => any;
interface A<T extends AnyFunction> { flush(): ReturnType<T> }
interface B<T extends AnyFunction> { (...args: Parameters<T>): void }
interface C<T extends AnyFunction> { r: ReturnType<T> }
export function f<T extends AnyFunction>(a: A<AnyFunction>, b: B<AnyFunction>, c: C<AnyFunction>) {
	const a1: A<T> = a;
	const b1: B<T> = b;
	const c1: C<T> = c;
}
