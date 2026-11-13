export {};
function f<T extends object>(target: T, key: string) {
	const value = Reflect.get(target, key);
	const b0: boolean = value;
}
