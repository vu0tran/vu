// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
function f<T>(x: T, y: T | undefined, z: T | null | undefined) {
	if (x !== undefined) { if (x !== null) { const n: number = x; } }
}
