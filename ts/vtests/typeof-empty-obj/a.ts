// {} stays in a typeof's false branch; {} | null | undefined from unknown joins back to unknown.
export function sizeOf(value: unknown, m: WeakMap<object, number>): number {
	if (value !== null && typeof value === 'object') {
		return Math.max(m.get(value) ?? 1, 1);
	}
	if (typeof value === 'string') {
		return Math.max(value.length, 1);
	}
	return 1;
}
declare const v2: unknown;
if (v2 !== null) {
	if (typeof v2 !== 'object') { const a: number = v2; }
}
if (v2 !== null && typeof v2 === 'object') {} else { const b: number = v2; }
declare const w: {} | undefined;
if (typeof w !== 'object') { const c: number = w; }
