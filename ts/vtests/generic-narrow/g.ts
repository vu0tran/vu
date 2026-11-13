export {};
function f<T extends object>(target: T, key: string) {
	const value = Reflect.get(target, key);
	if (typeof value !== 'object' || value === null) return value;
	if ('toJSON' in value) { const t = value.toJSON; const b: boolean = t; }
	if ('toJSON' in value && typeof value.toJSON === 'function') { const u = value.toJSON(); const b2: boolean = u; }
	if (value instanceof RegExp) return value.toString();
	return value;
}
