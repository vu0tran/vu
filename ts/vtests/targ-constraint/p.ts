export {};
declare const r: Record<PropertyKey, number>;
type A = (typeof r)[symbol];
const a: string = null! as A;
function invert<T extends Record<PropertyKey, PropertyKey>>(obj: T) {
	const result = {} as Record<T[keyof T], keyof T>;
	for (const key in obj) {
		result[obj[key]] = key;
	}
	return result;
}
const q: number = invert({ a: 'x' });
