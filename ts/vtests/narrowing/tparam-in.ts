// in and instanceof on T & object; joins reducing a type parameter's intersections
export {};
function f<T>(value: T) {
	if (typeof value !== 'object' || value === null || value instanceof RegExp) return value;
	const a: number = value;
	if ('toJSON' in value) { const b: number = value; const c: number = value.toJSON; }
	const d: number = value;
}
function g<T>(value: T) {
	if (typeof value !== 'object' || value === null) return value;
	if (value instanceof RegExp) { const r: number = value; }
	const a: number = value;
}
function f9<T>(value: T) {
	if (value === null || value instanceof RegExp) { const z: number = value; } else { const a: number = value; }
}
