export {};
interface Span { s: 1 }
declare function startSpan<T>(o: string, cb: (span: Span) => T): T;
export async function f<T>(spanCb: (span: Span) => Promise<T>): Promise<T> {
	return await startSpan('x', async (span) => {
		return await spanCb(span);
	});
}
export async function g<T>(spanCb: (span: Span) => Promise<T>): Promise<T> {
	return await startSpan('x', async (span) => spanCb(span));
}
export async function h<T>(spanCb: (span: Span) => Promise<T>): Promise<number> {
	return await startSpan('x', async (span) => {
		return await spanCb(span);
	});
}
