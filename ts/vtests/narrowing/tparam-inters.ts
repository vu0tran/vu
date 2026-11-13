// T & object and T & null through || and && chains, and joins (subtype reduction)
export {};
type P = string | number | null | undefined;
function f3<T extends ((object | Date) & { toJSON?: () => string }) | P>(s: T): T {
	if (typeof s !== 'object' || s === null || typeof s === 'function') { const n: number = s; return s; }
	const m: number = s;
	return s;
}
function f4<T extends object | P>(s: T): T {
	if (typeof s !== 'object' || s === null || typeof s === 'function') { const n: number = s; return s; }
	const m: number = s;
	return s;
}
function f5<T>(s: T): T {
	if (typeof s === 'object') {
		if (typeof s === 'function') { const n: number = s; }
		else { const n: number = s; }
	}
	return s;
}
function f6<T extends Function | null | string>(s: T): T {
	if (typeof s === 'object') { const n: number = s; }
	else if (typeof s === 'function') { const n: number = s; }
	else { const n: number = s; }
	return s;
}
function f7<T>(s: T, b: boolean) {
	if (typeof s === 'object') { } else { }
	const n: number = s;
	if (b) { if (typeof s === 'object') {} } 
	const n2: number = s;
	if (typeof s === 'object' && s) { } else { const n3: number = s; }
	const n4: number = s;
}
