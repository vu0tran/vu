// A call with a const type parameter: a function argument whose return isn't the const type parameter,
// null, and an array literal of references (a package's mapDefinedValues) aren't changed by a const context.
type NonNullableTuple<T extends readonly unknown[]> = { [K in keyof T]: NonNullable<T[K]> };
export function mapDefinedValues<const T extends readonly unknown[]>(values: readonly [...T]): NonNullableTuple<T> | false;
export function mapDefinedValues<const T extends readonly unknown[], R>(values: readonly [...T], fn: (...args: NonNullableTuple<T>) => R, defaultValue: R): R;
export function mapDefinedValues(...a: unknown[]): unknown { return a; }
declare const a: number | null;
declare const b: number | undefined;
const t = mapDefinedValues([a, b], (x, y) => x + y, null);
const n: string = t;
const u = mapDefinedValues([a, b]);
const m: string = u;
