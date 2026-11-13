export interface CMb<T> { m: T }
export class YMb<T = unknown> implements CMb<T> { m!: T; g() { return 1; } }
export class Wb<T> {
	set(value: T | CMb<unknown>) {
		if (value instanceof YMb) { const b: boolean = value; value.g(); }
	}
}
