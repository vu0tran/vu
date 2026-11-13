// === a literal on a type parameter: unchanged; comparability through constraints
export {};
function f<V>(value: V, w: V | string) {
	if (value === '') { const n: number = value; } else { const n: number = value; }
	if (value === undefined || value === null || value === '') { const n: number = value; } else { const n: number = value; }
	if (w === 'a') { const n: number = w; } else { const n: number = w; }
	if (value === 1) { const n: string = value; }
}
function g<V extends string | number>(value: V) {
	if (value === 'a') { const n: boolean = value; } else { const n: boolean = value; }
}
