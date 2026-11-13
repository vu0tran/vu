export interface CM<T> { m: T } 
export class YM<T> implements CM<T> { m!: T; g() { return 1; } }
export class YA { a = 1 }
export class W<T> {
	set(value: T | CM<unknown> | YA) {
		if (value instanceof YM) { return; }
		else if (value instanceof YA) { const b: boolean = value; }
		else { const c: boolean = value; }
	}
}
