export {};
function f<T extends object>(target: T, key: string) {
	const value = Reflect.get(target, key);
	const b0: boolean = value;
	if (typeof value !== 'object' || value === null) return value;
	const b1: boolean = value;
	if ('toJSON' in value && typeof value.toJSON === 'function') { const b2: boolean = value; return value.toJSON() as T; }
	const b3: boolean = value;
	return value;
}
