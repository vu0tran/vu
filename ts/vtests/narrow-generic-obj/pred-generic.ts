export {};
declare function isP(value: unknown): value is Record<string, unknown>;
declare function isS(value: unknown): value is { a: string };
interface Box<T> { v: T }
export function f<T>(source: Partial<T>, b: Box<T>, r: Readonly<T>, p: Pick<T, keyof T>) {
	if (isP(source)) { const n: number = source; }
	if (isP(b)) { const n: number = b; }
	if (isS(b)) { const n: number = b; }
	if (isP(r)) { const n: number = r; }
	if (isP(p)) { const n: number = p; }
	const q: Record<string, unknown> = source;
}
