// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
function f<T>(x: T, y: T | undefined, z: T | null | undefined) {
	if (x !== undefined) { const n: number = x; }
	if (x !== null) { const n: number = x; }
	if (x != null) { const n: number = x; }
	if (x) { const n: number = x; }
	if (x === undefined) { const n: number = x; }
	if (x === null) { const n: number = x; }
	if (x == null) { const n: number = x; } else { const n: number = x; }
	if (y !== undefined) { const n: number = y; } else { const n: number = y; }
	if (y) { const n: number = y; } else { const n: number = y; }
	if (z != null) { const n: number = z; } else { const n: number = z; }
	if (z !== undefined && z !== null) { const n: number = z; }
}
