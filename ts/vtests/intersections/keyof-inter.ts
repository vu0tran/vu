// keyof T & string: related through its concrete member; keyof T to a concrete type
export {};
function f<T extends object>(k: keyof T & string, j: keyof T, m: keyof T & number) {
	const a: string = k;
	const b: string = j;
	const c: string | number | symbol = j;
	const d: number = m;
	const e: boolean = k;
}
