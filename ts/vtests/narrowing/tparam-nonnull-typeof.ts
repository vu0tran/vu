// typeof and truthiness on T & {}; joins reduce by strict subtypes
export {};
function ifEmpty<T, V>(value: V, defaultValue: T) {
	if (value === undefined || value === null || value === '') {
		return defaultValue;
	}
	const a: number = value;
	if (typeof value === 'object') {
		const b: number = value;
		if (Array.isArray(value) && !value.length) {
			return defaultValue;
		}
		const c: number = value;
		if (!Object.keys(value).length) {
			return defaultValue;
		}
	} else { const d: number = value; }
	if (typeof value === 'string') { const e: number = value; } else { const f: number = value; }
	if (typeof value === 'function') { const g: number = value; }
	if (value) { const h: number = value; } else { const i: number = value; }
	return value;
}
